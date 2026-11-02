package ownedworld

import (
	"bytes"
	"errors"
	"fmt"
	"image"
	"math"
	"math/bits"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

// Original F3 owns navigation, highlights and redraws. Go owns army data and
// the atomic transaction. No native army write or compactor is permitted.
type originalArmyDismiss struct {
	View                                               *originalArmyReview
	BP                                                 uint16
	LastPost, LastValue, LastFlags                     uint16
	LastCompare                                        bool
	SeenEnter                                          uint64
	Opens, Closes, Transactions, Redraws, IgnoredEnter uint64
}

var originalDismissMoves = []uint16{0x77cd, 0x7850, 0x78ad, 0x7930, 0x798d, 0x7a10, 0x7a6d, 0x7af0, 0x7baf}
var originalDismissComparisons = []uint16{0x781b, 0x78ff, 0x79db, 0x7abf}

func containsIP(xs []uint16, ip uint16) bool {
	for _, x := range xs {
		if x == ip {
			return true
		}
	}
	return false
}
func (d *originalArmyDismiss) active() bool { return d != nil && d.View.Active && d.View.Mode == 2 }
func (d *originalArmyDismiss) acceptsRead(ip uint16) bool {
	return d.active() && (containsIP(originalDismissMoves, ip) || containsIP(originalDismissComparisons, ip))
}
func (d *originalArmyDismiss) check() error {
	if !d.active() {
		return errors.New("original F3 inactive")
	}
	if err := d.View.check(); err != nil {
		return err
	}
	if !bytes.Equal(d.View.Code[0x775a:0x7bf2], d.View.Engine.Oracle.Bytes(oracle.Far(0x110, 0x775a), 0x498)) {
		return errors.New("original F3 source")
	}
	return nil
}
func (d *originalArmyDismiss) enterSerial() uint64 {
	var n uint64
	for _, k := range d.View.Engine.InputEvents {
		if k.Scan == 0x1c && k.Down {
			n++
		}
	}
	return n
}
func (d *originalArmyDismiss) frame(m *dg.Machine) error {
	if err := d.check(); err != nil {
		return err
	}
	c := m.CPU
	bp, sp := c.R[dg.BP], c.R[dg.SP]
	base := uint32(0x1e880)
	if bp < 16 || bp > 65520 || sp != bp-14 || m.Read16(base+uint32(bp)+2) != 0x3ede || m.Read16(base+uint32(bp)+4) != 0x110 || c.Cycles == math.MaxUint64 {
		return errors.New("original F3 parent frame")
	}
	if d.BP != 0 && d.BP != bp {
		return errors.New("original F3 BP changed")
	}
	return nil
}
func installOriginalArmyDismiss(e *game.Engine, p *worldArmyPort, v *originalArmyReview) (*originalArmyDismiss, error) {
	if v == nil || v.Port != p {
		return nil, errors.New("original F3 requires the shared Go row provider")
	}
	d := &originalArmyDismiss{View: v}
	p.OriginalDismiss = d
	fail := func(err error) { panic(&worldArmyPortFault{"original F3: " + err.Error()}) }
	swordOnCall(e.Oracle, oracle.Far(0x110, 0x775a), func(o *oracle.Oracle) {
		r := o.Regs()
		if r.CS != 0x110 || r.DS != 0x1e88 || r.SS != 0x1e88 || r.SP > 65531 || o.Word(oracle.Far(r.SS, r.SP)) != 0x3ede || o.Word(oracle.Far(r.SS, r.SP+2)) != 0x110 {
			fail(errors.New("entry frame"))
		}
		if d.active() {
			if d.BP == 0 {
				return
			}
			fail(errors.New("unexpected reentry"))
		}
		s, err := p.snapshot()
		if err != nil {
			fail(err)
		}
		rows, err := originalReviewRows(p.Store.Catalog, s.World)
		if err != nil {
			fail(err)
		}
		v.Mode = 2
		v.Token = s.Token
		v.NativeRows = o.Bytes(oracle.Far(0x1e88, 0x54a), 24)
		v.Rows = rows
		v.Active = true
		v.Ready = false
		v.ReturnReady = false
		v.ReturnPending = false
		v.BP = 0
		v.Opens++
		d.BP = 0
		d.LastPost = 0
		d.SeenEnter = d.enterSerial()
		d.Opens++
		if err = d.check(); err != nil {
			fail(err)
		}
	})
	for _, ip := range []uint16{0x7782, 0x7b85} {
		ip := ip
		swordOnCall(e.Oracle, oracle.Far(0x110, ip), func(*oracle.Oracle) {
			if !d.active() {
				return
			}
			if err := d.check(); err != nil {
				fail(err)
			}
			if !v.RowDone {
				if err := v.finishRows(); err != nil {
					fail(err)
				}
				d.Redraws++
			}
		})
	}
	for _, ip := range append(append([]uint16{}, originalDismissMoves...), originalDismissComparisons...) {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0x110, ip), func(m *dg.Machine) (bool, error) { return d.supply(m, ip) })
		post := ip + 4
		cmp := containsIP(originalDismissComparisons, ip)
		if cmp {
			post = ip + 5
		}
		swordOnCall(e.Oracle, oracle.Far(0x110, post), func(o *oracle.Oracle) {
			if !d.active() || d.LastPost != post || d.LastCompare != cmp {
				fail(errors.New("data operation did not commit"))
			}
			r := o.Regs()
			if cmp {
				if r.Flags&0x8d5 != d.LastFlags {
					fail(errors.New("comparison flags changed"))
				}
			} else if r.AX != d.LastValue {
				fail(errors.New("kind register changed"))
			}
		})
	}
	swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x7b2e), d.commit)
	for _, ip := range []uint16{0x7b43, 0x7b49} {
		ip := ip
		swordOnCall(e.Oracle, oracle.Far(0x110, ip), func(*oracle.Oracle) {
			if d.active() {
				fail(fmt.Errorf("native army write escaped at %04x", ip))
			}
		})
	}
	swordOnCall(e.Oracle, oracle.Far(0x110, 0x7bf2), func(*oracle.Oracle) {
		if d.active() {
			fail(errors.New("native compactor escaped"))
		}
	})
	swordOnCall(e.Oracle, oracle.Far(0x110, 0x779e), func(*oracle.Oracle) {
		if d.active() {
			if err := d.check(); err != nil {
				fail(err)
			}
			v.Ready = true
		}
	})
	swordOnCall(e.Oracle, oracle.Far(0x110, 0x77a3), func(*oracle.Oracle) {
		if d.active() {
			v.Ready = false
		}
	})
	swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x77a3), func(m *dg.Machine) (bool, error) {
		if !d.active() {
			return false, nil
		}
		if err := d.frame(m); err != nil {
			return false, err
		}
		if v.Rows[0].Kind != 0 || m.CPU.R[dg.AX] == 0x011b {
			return false, nil
		}
		// After dismissing the last stack the original selection may be -1.
		// An empty list accepts Escape but has no navigation/transaction target.
		m.Write16(0x1e880+uint32(m.CPU.R[dg.BP])-8, m.CPU.R[dg.AX])
		m.CPU.IP = 0x779e
		m.CPU.Cycles++
		return true, nil
	})
	swordOnCall(e.Oracle, oracle.Far(0x110, 0x3ede), func(*oracle.Oracle) {
		if !d.active() {
			return
		}
		if err := d.check(); err != nil {
			fail(err)
		}
		v.Active = false
		v.Ready = false
		v.ReturnPending = true
		v.Closes++
		d.Closes++
	})
	return d, nil
}

func (d *originalArmyDismiss) supply(m *dg.Machine, ip uint16) (bool, error) {
	if err := d.frame(m); err != nil {
		return false, err
	}
	c := m.CPU
	if c.IP != ip || c.R[dg.BX]%4 != 0 || c.R[dg.BX] > 20 {
		return false, errors.New("original F3 slot operand")
	}
	value := d.View.Rows[c.R[dg.BX]/4].Kind
	cmp := containsIP(originalDismissComparisons, ip)
	if !cmp && !containsIP(originalDismissMoves, ip) {
		return false, errors.New("original F3 unknown read")
	}
	post := ip + 4
	var flags uint16
	if cmp {
		post = ip + 5
		c.Flags = originalKindZeroFlags(c.Flags, value)
		flags = c.Flags & 0x8d5
	} else {
		c.R[dg.AX] = value
	}
	d.BP = c.R[dg.BP]
	d.LastPost = post
	d.LastValue = value
	d.LastFlags = flags
	d.LastCompare = cmp
	c.IP = post
	c.Cycles++
	return true, nil
}

func originalKindZeroFlags(prior, kind uint16) uint16 {
	flags := prior &^ 0x8d5
	if kind == 0 {
		flags |= 0x40
	}
	if bits.OnesCount8(uint8(kind))%2 == 0 {
		flags |= 4
	}
	return flags
}

func (d *originalArmyDismiss) commit(m *dg.Machine) (bool, error) {
	if err := d.frame(m); err != nil {
		return false, err
	}
	c := m.CPU
	bp := uint32(c.R[dg.BP])
	base := uint32(0x1e880)
	if c.IP != 0x7b2e || m.Read16(base+bp-8) != 0x1c0d {
		return false, errors.New("original F3 Enter gate")
	}
	serial := d.enterSerial()
	if serial == d.SeenEnter {
		d.IgnoredEnter++
		c.IP = 0x779e
		c.Cycles++
		return true, nil
	}
	col, row := m.Read16(base+bp-4), m.Read16(base+bp-6)
	if col >= 2 || row >= 3 {
		return false, errors.New("original F3 selection bounds")
	}
	slot := int(col*3 + row)
	v := d.View
	s, err := v.Port.snapshot()
	if err != nil {
		return false, err
	}
	if s.Token != v.Token {
		return false, errors.New("original F3 stale transaction")
	}
	selected := s.World.Army.Slots[slot]
	if selected.Count == 0 {
		return false, errors.New("original F3 empty selection")
	}
	next, err := dismissWholeStack(v.Port.Store.Catalog, v.Port.Store.Combat, s.World, armyDismissRequest{s.World.Revision, slot, selected.Unit, selected.Count})
	if err != nil {
		return false, err
	}
	rows, err := originalReviewRows(v.Port.Store.Catalog, next)
	if err != nil {
		return false, err
	}
	updated, err := v.Port.Store.Commit(s.Token, next)
	if err != nil {
		return false, err
	}
	v.Port.Current = updated
	v.Token = updated.Token
	v.Rows = rows
	v.Ready = false
	d.SeenEnter = serial
	d.Transactions++
	// Resume the original selection adjustment and row redraw, after both
	// original array writes and the original array compactor. SP is unchanged.
	m.Write16(base+bp-10, uint16(slot))
	c.R[dg.AX] = uint16(slot)
	c.R[dg.CX] = 2
	c.R[dg.SI] = uint16(slot * 4)
	c.IP = 0x7b53
	c.Cycles++
	return true, nil
}

// The shared original source renderer supplies the frame. These methods only
// let existing adapter layers delegate diagnostics without opening a card UI.
func (d *originalArmyDismiss) IsActive() bool               { return false }
func (d *originalArmyDismiss) NoteKey(byte, bool)           {}
func (d *originalArmyDismiss) Click(int, int) (byte, error) { return 0, nil }
func (d *originalArmyDismiss) Paint(*armyUIFonts, string) (*image.RGBA, []armyUIText) {
	return d.View.Engine.Frame(), nil
}
func (d *originalArmyDismiss) State() map[string]any {
	selected := -1
	if d.active() && d.BP >= 16 {
		col := d.View.Engine.Oracle.Word(oracle.Far(0x1e88, d.BP-4))
		row := d.View.Engine.Oracle.Word(oracle.Far(0x1e88, d.BP-6))
		if col < 2 && row < 3 && d.View.Rows[col*3+row].Kind != 0 {
			selected = int(col*3 + row)
		}
	}
	return map[string]any{"original_dismiss_active": d.active(), "original_dismiss_selected": selected, "original_dismiss_opens": d.Opens, "original_dismiss_closes": d.Closes, "original_dismiss_transactions": d.Transactions, "original_dismiss_redraws": d.Redraws, "original_dismiss_ignored_enter": d.IgnoredEnter}
}
func (d *originalArmyDismiss) String() string {
	return fmt.Sprintf("original F3 / Go transactions %d", d.Transactions)
}
