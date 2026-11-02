package ownedworld

import (
	"bytes"
	"errors"
	"fmt"
	"math"
	"strconv"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

// Spec 030 READY. The original four-digit editor and feedback stay intact.
// All native-camp quantity arithmetic uses Go-owned army data and wide prices.
type originalRecruitPlan struct {
	Unit                        string
	Price, Command, Used, Limit uint64
	Stock                       uint32
	Preflight                   uint16
}

func originalRecruitPlanFor(c ArmyCatalog, a OwnedArmy, offer string) (originalRecruitPlan, error) {
	m, err := measureWorldArmy(c, a)
	if err != nil {
		return originalRecruitPlan{}, err
	}
	o, ok := a.Offers[offer]
	if !ok {
		return originalRecruitPlan{}, errors.New("original quantity missing offer")
	}
	idx, err := c.index()
	if err != nil {
		return originalRecruitPlan{}, err
	}
	u := idx[o.Unit]
	if u.Origin != "native" || u.NativeKind < 1 || u.NativeKind > 25 || o.Unit != fmt.Sprintf("native:%02d", u.NativeKind) || u.Gold == 0 || u.Command == 0 {
		return originalRecruitPlan{}, errors.New("original quantity native profile")
	}
	p := originalRecruitPlan{Unit: o.Unit, Price: u.Gold, Command: u.Command, Used: m.Used, Limit: (a.Leadership - m.Used) / u.Command, Stock: o.Stock, Preflight: 0x55f0}
	capacity, err := worldArmyCapacity(c, a, o.Unit)
	if err != nil {
		return p, err
	}
	switch {
	case u.Rank > a.RecruitRank:
		p.Preflight = 0x5533
	case !capacity:
		p.Preflight = 0x5574
	case a.Gold < u.Gold:
		p.Preflight = 0x55a0
	case p.Limit == 0:
		p.Preflight = 0x5774
	}
	if p.Limit > 32767 || p.Stock > 32767 {
		return p, errors.New("original quantity display range")
	}
	return p, nil
}

func (p originalRecruitPlan) result(count uint32, gold uint64) (uint16, error) {
	if count > 9999 {
		return 0, errors.New("original quantity outside four-digit editor")
	}
	if count == 0 {
		return 0x555f, nil
	}
	if p.Preflight != 0x55f0 {
		return 0, errors.New("original quantity cannot confirm a refused offer")
	}
	if uint64(count) > p.Limit || count > p.Stock {
		return 0x5699, nil
	}
	if p.Price > math.MaxUint64/uint64(count) {
		return 0, errors.New("original quantity price overflow")
	}
	if p.Price*uint64(count) > gold {
		return 0x55a0, nil
	}
	return 0x56ec, nil
}

type originalRecruitQuantity struct {
	Engine                                  *game.Engine
	Port                                    *worldArmyPort
	Code                                    []byte
	Plan                                    originalRecruitPlan
	InputSP, InputBP, InputParent           uint16
	InputPending, Returned                  bool
	Value                                   uint16
	Text                                    string
	ReturnIP                                uint16
	Preflights, Inputs, Results, Duplicates uint64
	Decisions                               []map[string]any
}

func (x *originalRecruitQuantity) source() error {
	o := x.Engine.Oracle
	if !bytes.Equal(x.Code[0x4e7e:0x50e2], o.Bytes(oracle.Far(0x110, 0x4e7e), 0x264)) {
		return errors.New("original numeric source changed")
	}
	for start, want := range x.Port.Expected {
		if !bytes.Equal(want, o.Bytes(oracle.Far(0x110, start), len(want))) {
			return errors.New("original shop source changed")
		}
	}
	return nil
}

func (x *originalRecruitQuantity) frame(m *dg.Machine) (progressPairSnapshot, originalRecruitPlan, error) {
	p := x.Port
	c := m.CPU
	bp, sp := c.R[dg.BP], c.R[dg.SP]
	base := uint32(0x1e880)
	fail := func(s string) (progressPairSnapshot, originalRecruitPlan, error) {
		return progressPairSnapshot{}, originalRecruitPlan{}, errors.New(s)
	}
	if !p.ShopOpen || p.ShopCommitted || c.Seg[dg.CS] != 0x110 || c.Seg[dg.DS] != 0x1e88 || c.Seg[dg.SS] != 0x1e88 || bp < 32 || p.ShopSP != bp+2 || sp != bp-14 || c.Cycles == math.MaxUint64 {
		return fail("original quantity shop frame")
	}
	if p.ShopGroup < 0 || p.ShopGroup >= 5 || m.Read16(base+uint32(bp)+2) != uint16(0x5a21+p.ShopGroup*0x90) || m.Read16(base+uint32(bp)+4) != 0x110 || m.Read16(base+uint32(bp)+6) != p.ShopKind || m.Read16(base+uint32(bp)+8) != p.ShopStock || m.Read16(base+0x26b8) != 0 {
		return fail("original quantity arguments/modifier")
	}
	if !bytes.Equal(x.Code[0x4e7e:0x50e2], m.Mem[0x1100+0x4e7e:0x1100+0x50e2]) {
		return fail("original numeric machine source changed")
	}
	for start, want := range p.Expected {
		if !bytes.Equal(want, m.Mem[0x1100+int(start):0x1100+int(start)+len(want)]) {
			return fail("original shop machine source changed")
		}
	}
	s, err := p.snapshot()
	if err != nil {
		return fail(err.Error())
	}
	for i, n := range pairWorldResources(s.World).words() {
		if uint64(m.Read16(base+0x4f2+uint32(i*2))) != n {
			return fail("original quantity resources")
		}
	}
	plan, err := originalRecruitPlanFor(p.Store.Catalog, s.World.Army, p.ShopID)
	if err != nil {
		return fail(err.Error())
	}
	if plan.Unit != p.ShopUnit || plan.Stock != uint32(p.ShopStock) {
		return fail("original quantity offer binding")
	}
	return s, plan, nil
}

func installOriginalRecruitQuantity(e *game.Engine, p *worldArmyPort) (*originalRecruitQuantity, error) {
	code, err := worldArmyCode(e.PAM)
	if err != nil {
		return nil, err
	}
	x := &originalRecruitQuantity{Engine: e, Port: p, Code: code}
	p.RecruitQuantity = x
	fail := func(err error) { panic(&worldArmyPortFault{"original quantity: " + err.Error()}) }
	if err = x.source(); err != nil {
		return nil, err
	}
	for _, ip := range []uint16{0x5523, 0x5689} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0x110, ip), func(m *dg.Machine) (bool, error) { return x.execute(m, ip) })
	}
	for _, ip := range []uint16{0x5526, 0x568c} {
		ip := ip
		swordOnCall(e.Oracle, oracle.Far(0x110, ip), func(*oracle.Oracle) {
			if p.ShopOpen {
				fail(fmt.Errorf("Go quantity gate escaped at %04x", ip))
			}
		})
	}
	swordOnCall(e.Oracle, oracle.Far(0x110, 0x4e7e), func(o *oracle.Oracle) {
		if !p.ShopOpen {
			return
		}
		r := o.Regs()
		if err := x.source(); err != nil {
			fail(err)
		}
		if r.CS != 0x110 || r.SS != 0x1e88 || r.DS != 0x1e88 || r.SP < 32 || r.SP > 65520 || o.Word(oracle.Far(r.SS, r.SP)) != 0x5683 || o.Word(oracle.Far(r.SS, r.SP+2)) != 0x110 || r.SP != r.BP-22 || r.BP+2 != p.ShopSP || o.Word(oracle.Far(r.SS, r.SP+6)) != 167 || o.Word(oracle.Far(r.SS, r.SP+4)) != o.Word(oracle.Far(r.SS, r.BP-4))+32 {
			fail(errors.New("original numeric caller/arguments"))
		}
		if x.InputPending {
			if x.InputSP == r.SP && !x.Returned {
				x.Duplicates++
				return
			}
			fail(errors.New("original numeric overlapping input"))
		}
		x.InputSP = r.SP
		x.InputBP = r.SP - 2
		x.InputParent = r.BP
		x.InputPending = true
		x.Returned = false
		x.Text = ""
		x.Inputs++
	})
	for _, ip := range []uint16{0x50c9, 0x50e1} {
		ip := ip
		swordOnCall(e.Oracle, oracle.Far(0x110, ip), func(o *oracle.Oracle) {
			if !p.ShopOpen {
				return
			}
			r := o.Regs()
			if err := x.source(); err != nil {
				fail(err)
			}
			if !x.InputPending || r.CS != 0x110 || r.DS != 0x1e88 || r.SS != 0x1e88 || r.SP != x.InputSP || r.BP != x.InputParent {
				fail(errors.New("original numeric return frame"))
			}
			n := o.Word(oracle.Far(0x1e88, x.InputBP-2))
			if n > 4 {
				fail(errors.New("original numeric length"))
			}
			raw := o.Bytes(oracle.Far(0x1e88, 0x8dbc), int(n)+1)
			if raw[n] != 0 {
				fail(errors.New("original numeric terminator"))
			}
			for _, c := range raw[:n] {
				if c < '0' || c > '9' {
					fail(errors.New("original numeric digit"))
				}
			}
			key := o.Word(oracle.Far(0x1e88, x.InputBP-8))
			value := uint64(0)
			if ip == 0x50e1 {
				if key != 0x1c0d {
					fail(errors.New("original numeric Enter"))
				}
				if n > 0 {
					var err error
					value, err = strconv.ParseUint(string(raw[:n]), 10, 16)
					if err != nil {
						fail(err)
					}
				}
			} else if key != 0x011b {
				fail(errors.New("original numeric Escape"))
			}
			if uint64(r.AX) != value {
				fail(errors.New("original numeric value differs from editor text"))
			}
			if x.Returned {
				if x.Value == r.AX && x.Text == string(raw[:n]) && x.ReturnIP == ip {
					x.Duplicates++
					return
				}
				fail(errors.New("original numeric repeated return changed"))
			}
			x.Value = r.AX
			x.Text = string(raw[:n])
			x.ReturnIP = ip
			x.Returned = true
		})
	}
	return x, nil
}

func (x *originalRecruitQuantity) execute(m *dg.Machine, ip uint16) (bool, error) {
	s, plan, err := x.frame(m)
	if err != nil {
		return false, &worldArmyPortFault{err.Error()}
	}
	c := m.CPU
	bp := uint32(c.R[dg.BP])
	base := uint32(0x1e880)
	if c.IP != ip {
		return false, errors.New("original quantity host site")
	}
	var next uint16
	switch ip {
	case 0x5523:
		if x.InputPending {
			return false, errors.New("original quantity pending at preflight")
		}
		x.Plan = plan
		x.Preflights++
		next = plan.Preflight
		if next == 0x55f0 {
			m.Write16(base+bp-6, uint16(plan.Limit))
		}
	case 0x5689:
		count := m.Read16(base + bp - 2)
		if !x.InputPending || !x.Returned || count != x.Value || c.R[dg.AX] != count || c.R[dg.BP] != x.InputParent {
			return false, &worldArmyPortFault{"original quantity result binding"}
		}
		next, err = plan.result(uint32(count), s.World.Army.Gold)
		if err != nil {
			return false, &worldArmyPortFault{err.Error()}
		}
		x.InputPending = false
		x.Results++
		x.Plan = plan
		x.Decisions = append(x.Decisions, map[string]any{"text": x.Text, "count": count, "next_ip": next, "price": plan.Price, "limit": plan.Limit, "stock": plan.Stock, "gold": s.World.Army.Gold, "token": s.Token})
	default:
		return false, errors.New("unknown original quantity host site")
	}
	c.IP = next
	c.Cycles++
	return true, nil
}

func (x *originalRecruitQuantity) State() map[string]any {
	return map[string]any{"plan": x.Plan, "preflights": x.Preflights, "inputs": x.Inputs, "results": x.Results, "input_pending": x.InputPending, "returned": x.Returned, "text": x.Text, "value": x.Value, "duplicates": x.Duplicates, "decisions": x.Decisions}
}
