package ownedworld

import (
	"bytes"
	"errors"
	"fmt"
	"math"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

// Spec 030: original F2 UI, Go-owned data. Extended kinds are not routed into
// the original name/image tables. This first bridge rejects them explicitly.
type originalReviewRow struct{ Kind, Count, Monthly uint16 }
type originalArmyReview struct {
	Engine                              *game.Engine
	Port                                *worldArmyPort
	Code                                []byte
	Rows                                [6]originalReviewRow
	Active                              bool
	Ready                               bool
	Mode, RowReturn, RowArg             uint16
	RowDone, ReturnReady, ReturnPending bool
	Token                               string
	NativeRows                          []byte
	BP                                  uint16
	LastPost                            uint16
	LastValue                           uint16
	Reads                               [4]uint64
	Opens, Closes                       uint64
}

func originalReviewRows(c ArmyCatalog, w OwnedWorld) ([6]originalReviewRow, error) {
	var rows [6]originalReviewRow
	if err := w.Army.validate(c); err != nil {
		return rows, err
	}
	if w.Battle != nil {
		return rows, errors.New("F2 during battle")
	}
	idx, err := c.index()
	if err != nil {
		return rows, err
	}
	empty := false
	for i, s := range w.Army.Slots {
		if s.Unit == "" {
			empty = true
			continue
		}
		p := idx[s.Unit]
		if empty || p.Origin != "native" || p.NativeKind < 1 || p.NativeKind > 25 || s.Unit != fmt.Sprintf("native:%02d", p.NativeKind) {
			return rows, errors.New("original F2 requires compact original-kind rows; extended presentation pending")
		}
		if s.Count > 32767 || p.Gold > 32767 || p.Gold*uint64(s.Count) > 32767 {
			return rows, errors.New("original F2 numeric display range")
		}
		rows[i] = originalReviewRow{p.NativeKind, uint16(s.Count), uint16(p.Gold * uint64(s.Count))}
	}
	return rows, nil
}

func (v *originalArmyReview) check() error {
	o := v.Engine.Oracle
	r := o.Regs()
	if r.CS != 0x110 || r.DS != 0x1e88 || r.SS != 0x1e88 ||
		!bytes.Equal(v.Code[0x3e92:0x3f08], o.Bytes(oracle.Far(0x110, 0x3e92), 0x76)) ||
		!bytes.Equal(v.Code[0x75c6:0x775a], o.Bytes(oracle.Far(0x110, 0x75c6), 0x194)) ||
		(v.Mode != 1 && v.Mode != 2) || o.Word(oracle.Far(0x1e88, 0x56bc)) != v.Mode || o.Word(oracle.Far(0x1e88, 0x7484)) != 1 {
		return errors.New("original F2 source/segments/selector")
	}
	s, err := v.Port.snapshot()
	if err != nil {
		return err
	}
	if s.Token != v.Token {
		return errors.New("original F2 stale snapshot")
	}
	for i, n := range pairWorldResources(s.World).words() {
		if uint64(o.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
			return errors.New("original F2 resource binding")
		}
	}
	if !bytes.Equal(v.NativeRows, o.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
		return errors.New("original F2 shadow army changed")
	}
	return nil
}

func installOriginalArmyReview(e *game.Engine, p *worldArmyPort) (*originalArmyReview, error) {
	code, err := worldArmyCode(e.PAM)
	if err != nil {
		return nil, err
	}
	v := &originalArmyReview{Engine: e, Port: p, Code: code}
	p.OriginalReview = v
	fail := func(err error) { panic(&worldArmyPortFault{"original F2: " + err.Error()}) }
	swordOnCall(e.Oracle, oracle.Far(0x110, 0x3e92), func(o *oracle.Oracle) {
		if o.Word(oracle.Far(0x1e88, 0x56bc)) != 1 {
			return
		}
		r := o.Regs()
		s, err := p.snapshot()
		if err != nil {
			fail(err)
		}
		if v.Active {
			if v.Opens > v.Closes && v.BP == 0 {
				if err = v.check(); err != nil {
					fail(err)
				}
				return
			}
			fail(errors.New("unexpected dispatcher reentry"))
		}
		rows, err := originalReviewRows(p.Store.Catalog, s.World)
		if err != nil {
			fail(err)
		}
		if r.SP > 65529 || o.Word(oracle.Far(r.SS, r.SP+2)) != 0x110 || o.Word(oracle.Far(r.SS, r.SP+4)) != 1 {
			fail(errors.New("dispatcher frame"))
		}
		v.Token = s.Token
		v.Mode = 1
		v.NativeRows = o.Bytes(oracle.Far(0x1e88, 0x54a), 24)
		if err = v.check(); err != nil {
			fail(err)
		}
		v.Rows = rows
		v.Active = true
		v.Ready = false
		v.ReturnReady, v.ReturnPending = false, false
		v.BP = 0
		v.LastPost = 0
		v.Reads = [4]uint64{}
		v.Opens++
	})
	swordOnCall(e.Oracle, oracle.Far(0x110, 0x75c6), func(o *oracle.Oracle) {
		if !v.Active {
			fail(errors.New("row without F2 snapshot"))
		}
		if err := v.check(); err != nil {
			fail(err)
		}
		r := o.Regs()
		if r.SP > 65529 || o.Word(oracle.Far(r.SS, r.SP+2)) != 0x110 {
			fail(errors.New("row caller"))
		}
		ret, arg := o.Word(oracle.Far(r.SS, r.SP)), o.Word(oracle.Far(r.SS, r.SP+4))
		if !(v.Mode == 1 && ret == 0x3ebf && arg == 0x2f || v.Mode == 2 && (ret == 0x7782 || ret == 0x7b85) && arg == 0x30 && p.OriginalDismiss != nil) {
			fail(errors.New("row mode/caller"))
		}
		v.RowReturn, v.RowArg = ret, arg
		v.BP = 0
		v.Reads = [4]uint64{}
		v.LastPost = 0
		v.RowDone = false
		v.Ready = false
	})
	for _, ip := range []uint16{0x75fd, 0x76ad, 0x76e8, 0x770d} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0x110, ip), func(m *dg.Machine) (bool, error) { return v.supply(m, ip) })
	}
	for _, ip := range []uint16{0x7601, 0x76b1, 0x76ec, 0x771c} {
		ip := ip
		swordOnCall(e.Oracle, oracle.Far(0x110, ip), func(o *oracle.Oracle) {
			if !v.Active || v.LastPost != ip {
				fail(errors.New("Go data operation did not commit"))
			}
			r := o.Regs()
			got := r.AX
			if ip == 0x7601 {
				got = r.SI
			}
			if got != v.LastValue {
				fail(errors.New("Go data register changed"))
			}
		})
	}
	swordOnCall(e.Oracle, oracle.Far(0x110, 0x3ed5), func(*oracle.Oracle) {
		if !v.Active || v.Mode != 1 {
			return
		}
		if err := v.check(); err != nil {
			fail(err)
		}
		if err := v.finishRows(); err != nil {
			fail(err)
		}
	})
	swordOnCall(e.Oracle, oracle.Far(0x110, 0x3ed8), func(*oracle.Oracle) {
		if !v.Active || v.Mode != 1 {
			return
		}
		if err := v.check(); err != nil {
			fail(err)
		}
		v.Active = false
		v.Ready = false
		v.ReturnPending = true
		v.Closes++
	})
	// Source rendering commits the army panel at sub_1844C, after the CALL
	// at 3ED5 has actually been dispatched. Active alone still holds the map.
	swordOnCall(e.Oracle, oracle.Far(0x110, 0x844c), func(o *oracle.Oracle) {
		if !v.Active || v.Mode != 1 {
			return
		}
		r := o.Regs()
		if r.SP <= 65531 && o.Word(oracle.Far(r.SS, r.SP)) == 0x3ed8 && o.Word(oracle.Far(r.SS, r.SP+2)) == 0x110 {
			if err := v.check(); err != nil {
				fail(err)
			}
			v.Ready = true
		}
	})
	swordOnCall(e.Oracle, oracle.Far(0x110, 0x3e91), func(*oracle.Oracle) {
		if v.ReturnPending {
			v.ReturnReady = true
			v.ReturnPending = false
		}
	})
	return v, nil
}

func (v *originalArmyReview) finishRows() error {
	if v.RowDone {
		return nil
	}
	var occupied uint64
	for _, r := range v.Rows {
		if r.Kind != 0 {
			occupied++
		}
	}
	if v.Reads != [4]uint64{6, occupied, occupied, occupied} {
		return fmt.Errorf("row operations %v", v.Reads)
	}
	v.RowDone = true
	return nil
}

func (v *originalArmyReview) acceptsRead(ip uint16) bool {
	return v != nil && v.Active && (ip == 0x75fd || ip == 0x76ad || ip == 0x76e8)
}

func (v *originalArmyReview) supply(m *dg.Machine, ip uint16) (bool, error) {
	fail := func(s string) (bool, error) { return false, &worldArmyPortFault{"original F2: " + s} }
	if !v.Active {
		return fail("inactive data operation")
	}
	if err := v.check(); err != nil {
		return fail(err.Error())
	}
	c := m.CPU
	bp, sp := c.R[dg.BP], c.R[dg.SP]
	base := uint32(0x1e880)
	if c.IP != ip || c.Cycles == math.MaxUint64 || bp < 18 || bp > 65520 || sp > bp || m.Read16(base+uint32(bp)+2) != v.RowReturn || m.Read16(base+uint32(bp)+4) != 0x110 || m.Read16(base+uint32(bp)+6) != v.RowArg {
		return fail("row frame")
	}
	if v.BP != 0 && v.BP != bp {
		return fail("row BP changed")
	}
	slot := int(m.Read16(base + uint32(bp) - 10))
	if slot < 0 || slot >= 6 {
		return fail("slot bounds")
	}
	row := v.Rows[slot]
	if ip != 0x770d && c.R[dg.BX] != uint16(slot*4) {
		return fail("slot operand")
	}
	var index int
	var post, value uint16
	switch ip {
	case 0x75fd:
		index = 0
		post = 0x7601
		value = row.Kind
	case 0x76ad:
		index = 1
		post = 0x76b1
		value = row.Kind
	case 0x76e8:
		index = 2
		post = 0x76ec
		value = row.Count
	case 0x770d:
		if row.Kind == 0 || m.Read16(base+uint32(bp)-12) != row.Kind {
			return fail("monthly row kind")
		}
		index = 3
		post = 0x771c
		value = row.Monthly
	default:
		return fail("unknown data operation")
	}
	if index > 0 && row.Kind == 0 {
		return fail("empty row fields")
	}
	// Validate everything before touching the VM. Native kinds are genuine IDs;
	// only original F2 drawing/control consumes them, never extended identities.
	if ip == 0x75fd {
		c.R[dg.SI] = value
	} else {
		c.R[dg.AX] = value
	}
	if ip == 0x770d {
		c.R[dg.BX] = row.Kind * 2
		c.R[dg.DX] = 0
		m.Write16(base+uint32(bp)-2, value)
	}
	v.BP = bp
	v.LastPost = post
	v.LastValue = value
	v.Reads[index]++
	c.IP = post
	c.Cycles++
	return true, nil
}
