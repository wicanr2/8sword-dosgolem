//go:build ignore

// 030 isolated candidate: Go army existence and paired no-army gold loss.
package main

import (
	"bytes"
	"errors"
	"image"
	"math"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func planNoArmyLoss(c ArmyCatalog, cc game.OwnedCombatCatalog, w OwnedWorld, divisor uint16) (OwnedWorld, uint64, error) {
	if e := w.validate(c, cc); e != nil {
		return w, 0, e
	}
	m, e := measureWorldArmy(c, w.Army)
	if e != nil {
		return w, 0, e
	}
	if m.Total != 0 || w.Battle != nil || divisor < 2 || divisor > 14 || w.Revision == math.MaxUint64 {
		return w, 0, errors.New("no-army loss contract")
	}
	loss := w.Army.Gold / uint64(divisor)
	next := w
	next.Revision++
	next.Army.Gold -= loss
	return next, loss, nil
}

type armyPresence struct {
	Engine                                 *game.Engine
	Port                                   *worldArmyPort
	Code                                   []byte
	Active, HasArmy, Debited, Prompt       bool
	BP, SP                                 uint16
	Token                                  string
	NativeRows                             []byte
	Checks, Debits, Completed, NativeReads uint64
	Events                                 []map[string]any
}

func (p *armyPresence) machineCheck(m *dg.Machine, ip uint16) (progressPairSnapshot, error) {
	c := m.CPU
	ds := uint32(0x1e880)
	bp, sp := c.R[dg.BP], c.R[dg.SP]
	if c.IP != ip || c.Seg[dg.CS] != 0x110 || c.Seg[dg.DS] != 0x1e88 || c.Seg[dg.SS] != 0x1e88 || c.Cycles == math.MaxUint64 || bp < 32 || bp > 65520 || sp > bp || m.Read16(ds+uint32(bp)+2) != 0x0bd3 || m.Read16(ds+uint32(bp)+4) != 0x110 {
		return progressPairSnapshot{}, errors.New("presence frame/segments")
	}
	if !bytes.Equal(p.Code, m.Mem[0x1100+0x151c:0x1100+0x1796]) {
		return progressPairSnapshot{}, errors.New("presence source bytes")
	}
	s, e := p.Port.snapshot()
	if e != nil {
		return s, e
	}
	for i, n := range pairWorldResources(s.World).words() {
		if uint64(m.Read16(ds+0x4f2+uint32(i*2))) != n {
			return s, errors.New("presence resources")
		}
	}
	if p.Active && (p.Token != s.Token || p.BP != bp || p.SP != sp || !bytes.Equal(p.NativeRows, m.Mem[ds+0x54a:ds+0x562])) {
		return s, errors.New("presence active binding")
	}
	return s, nil
}

func (p *armyPresence) instruction(m *dg.Machine, ip uint16) (bool, error) {
	fail := func(e error) (bool, error) { return false, &worldArmyPortFault{"army presence: " + e.Error()} }
	if ip != 0x1650 && ip != 0x16a4 {
		return fail(errors.New("unknown presence gate"))
	}
	s, e := p.machineCheck(m, ip)
	if e != nil {
		return fail(e)
	}
	c := m.CPU
	ds := uint32(0x1e880)
	bp := c.R[dg.BP]
	if ip == 0x1650 {
		if p.Active {
			return fail(errors.New("presence repeated gate"))
		}
		metrics, e := measureWorldArmy(p.Port.Store.Catalog, s.World.Army)
		if e != nil {
			return fail(e)
		}
		p.Active = true
		p.HasArmy = metrics.Total > 0
		p.Debited = false
		p.Prompt = false
		p.BP = bp
		p.SP = c.R[dg.SP]
		p.Token = s.Token
		p.NativeRows = append([]byte(nil), m.Mem[ds+0x54a:ds+0x562]...)
		flag := uint16(1)
		if p.HasArmy {
			flag = 0
		}
		m.Write16(ds+uint32(bp)-2, flag)
		c.IP = 0x1671
		p.Checks++
		p.Events = append(p.Events, map[string]any{"kind": "presence", "has_army": p.HasArmy, "total": metrics.Total, "token": p.Token})
	} else {
		if !p.Active || p.HasArmy || p.Debited {
			return fail(errors.New("no-army debit phase"))
		}
		next, loss, e := planNoArmyLoss(p.Port.Store.Catalog, p.Port.Store.Combat, s.World, c.R[dg.CX])
		if e != nil {
			return fail(e)
		}
		if uint64(c.R[dg.AX]) != loss || uint64(m.Read16(ds+uint32(bp)-6)) != loss {
			return fail(errors.New("original loss quotient differs"))
		}
		updated, e := p.Port.Store.Commit(s.Token, next)
		if e != nil {
			return fail(e)
		}
		// Commit both files before publishing the one validated resource word.
		p.Port.Current = updated
		p.Token = updated.Token
		m.Write16(ds+0x4f8, uint16(next.Army.Gold))
		p.Debited = true
		p.Debits++
		c.IP = 0x16a8
		p.Events = append(p.Events, map[string]any{"kind": "no-army-loss", "before": s.World.Army.Gold, "divisor": c.R[dg.CX], "loss": loss, "after": next.Army.Gold, "token": p.Token})
	}
	c.Cycles++
	return true, nil
}

func installArmyPresence(e *game.Engine, port *worldArmyPort) (*armyPresence, error) {
	code, x := worldArmyCode(e.PAM)
	if x != nil {
		return nil, x
	}
	p := &armyPresence{Engine: e, Port: port, Code: append([]byte(nil), code[0x151c:0x1796]...)}
	if !bytes.Equal(p.Code, e.Oracle.Bytes(oracle.Far(0x110, 0x151c), len(p.Code))) {
		return nil, errors.New("presence runtime code")
	}
	for _, ip := range []uint16{0x1650, 0x16a4} {
		ip := ip
		e.Oracle.OnHostInstruction(oracle.Far(0x110, ip), func(m *dg.Machine) (bool, error) { return p.instruction(m, ip) })
	}
	fail := func(s string) { panic(&worldArmyPortFault{"army presence: " + s}) }
	e.Oracle.OnCall(oracle.Far(0x110, 0x165c), func(*oracle.Oracle) { p.NativeReads++; fail("native existence loop escaped") })
	e.Oracle.OnCall(oracle.Far(0x110, 0x16e0), func(*oracle.Oracle) {
		if !p.Active || !p.HasArmy {
			fail("unexpected confirmation")
		}
		p.Prompt = true
	})
	for _, ip := range []uint16{0x1713, 0x177a, 0x1782} {
		e.Oracle.OnCall(oracle.Far(0x110, ip), func(*oracle.Oracle) {
			if p.Active {
				fail("battle/refusal world handoff is not implemented")
			}
		})
	}
	e.Oracle.OnCall(oracle.Far(0x110, 0x16da), func(o *oracle.Oracle) {
		if !p.Active {
			return
		}
		r := o.Regs()
		if p.HasArmy || !p.Debited || r.CS != 0x110 || r.DS != 0x1e88 || r.SS != 0x1e88 || r.BP != p.BP || r.SP != p.SP {
			fail("empty encounter return")
		}
		if !bytes.Equal(p.Code, o.Bytes(oracle.Far(0x110, 0x151c), len(p.Code))) || !bytes.Equal(p.NativeRows, o.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
			fail("return source/native rows")
		}
		s, x := port.snapshot()
		if x != nil {
			fail(x.Error())
		}
		if s.Token != p.Token {
			fail("return token")
		}
		for i, n := range pairWorldResources(s.World).words() {
			if uint64(o.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
				fail("return resources")
			}
		}
		p.Active = false
		p.Prompt = false
		p.Completed++
	})
	return p, nil
}

type presenceExtra struct {
	Extra    armyScreenExtra
	Presence *armyPresence
}

func (p *presenceExtra) IsActive() bool { return p.Extra != nil && p.Extra.IsActive() }
func (p *presenceExtra) NoteKey(k byte, d bool) {
	if p.Extra != nil {
		p.Extra.NoteKey(k, d)
	}
}
func (p *presenceExtra) Click(x, y int) (byte, error) {
	if p.Extra != nil {
		return p.Extra.Click(x, y)
	}
	return 0, nil
}
func (p *presenceExtra) Paint(f *armyUIFonts, id string) (*image.RGBA, []armyUIText) {
	return p.Extra.Paint(f, id)
}
func (p *presenceExtra) State() map[string]any {
	s := map[string]any{}
	if p.Extra != nil {
		s = p.Extra.State()
	}
	v := p.Presence
	s["presence_active"], s["presence_has_army"], s["presence_prompt"] = v.Active, v.HasArmy, v.Prompt
	s["presence_checks"], s["presence_debits"], s["presence_completed"], s["presence_native_reads"], s["presence_events"] = v.Checks, v.Debits, v.Completed, v.NativeReads, v.Events
	return s
}
func init() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		v, x := previous(e, p)
		if x != nil {
			return nil, x
		}
		presence, x := installArmyPresence(e, p)
		if x != nil {
			return nil, x
		}
		return &presenceExtra{v, presence}, nil
	}
	armyReviewTitle = "神州八劍・軍隊試作・遇敵交接"
}
