//go:build ignore

package main

import (
	"bytes"
	"errors"
	"fmt"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
	"os"
	"path/filepath"
)

var errAlchemyYield = errors.New("alchemy checkpoint yield")

type alchemyPort struct {
	Engine                                                *game.Engine
	Army                                                  *worldArmyPort
	Code                                                  []byte
	Active, Applied, Charged, Pending, Committed, Waiting bool
	EntrySP, BP                                           uint16
	Before                                                progressPairSnapshot
	After                                                 OwnedWorld
	Award                                                 alchemyAward
	Amount, Casts, MenuVisits                             uint64
	MenuCursor                                            int
}

var alchemyCurrent *alchemyPort

func (p *alchemyPort) source(o *oracle.Oracle) bool {
	r := o.Regs()
	return r.CS == 0x110 && r.SS == 0x1e88 && r.DS == 0x1e88 && bytes.Equal(p.Code[0x68ce:0x693c], o.Bytes(oracle.Far(0x110, 0x68ce), 110)) && bytes.Equal(p.Code[0x6b20:0x6bea], o.Bytes(oracle.Far(0x110, 0x6b20), 202))
}
func installAlchemyPort(e *game.Engine, army *worldArmyPort) (*alchemyPort, error) {
	code, x := worldArmyCode(e.PAM)
	if x != nil {
		return nil, x
	}
	p := &alchemyPort{Engine: e, Army: army, Code: code, MenuCursor: -1}
	alchemyCurrent = p
	fail := func(x error) { panic(&worldArmyPortFault{"alchemy: " + x.Error()}) }
	e.Oracle.OnCall(oracle.Far(0x110, 0x67ac), func(o *oracle.Oracle) {
		r := o.Regs()
		if p.source(o) && r.BP >= 4 && bytes.Equal(code[0x6720:0x68ce], o.Bytes(oracle.Far(0x110, 0x6720), 0x1ae)) {
			v := int(o.Word(oracle.Far(0x1e88, r.BP-4)))
			if v <= 7 {
				p.MenuCursor = v
				p.MenuVisits++
			}
		}
	})
	e.Oracle.OnCall(oracle.Far(0x110, 0x68ce), func(o *oracle.Oracle) {
		if o.Arg(0) != 1 {
			return
		}
		r := o.Regs()
		if !p.source(o) || r.SP < 64 || o.Word(oracle.Far(r.SS, r.SP)) != 0x6896 || o.Word(oracle.Far(r.SS, r.SP+2)) != 0x110 {
			fail(errors.New("entry frame"))
		}
		if p.Active {
			if p.EntrySP != r.SP {
				fail(errors.New("overlapping cast"))
			}
			return
		}
		b, x := army.snapshot()
		if x != nil {
			fail(x)
		}
		uses, x := alchemyWord(b.Bytes.Native, alchemyUsesOffset)
		learned, y := alchemyWord(b.Bytes.Native, alchemyLearnedOffset)
		bonus, z := alchemyWord(b.Bytes.Native, alchemyBonusOffset)
		if x != nil || y != nil || z != nil || uses == 0 || uses > 32767 || learned != 1 || o.Word(oracle.Far(0x1e88, 0x26aa)) != learned || o.Word(oracle.Far(0x1e88, 0x26ae)) != bonus || o.Word(oracle.Far(0x1e88, 0x2b2a)) != uses || army.ShopOpen || b.World.Battle != nil {
			fail(errors.New("unavailable or mismatched spell"))
		}
		for i, n := range pairWorldResources(b.World).words() {
			if uint64(o.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
				fail(errors.New("entry resource mismatch"))
			}
		}
		p.Active = true
		p.Applied = false
		p.Charged = false
		p.Pending = false
		p.Committed = false
		p.Waiting = false
		p.EntrySP = r.SP
		p.BP = r.SP - 2
		p.Before = b
		p.Award = alchemyAward{Bonus: bonus == 1, UsesBefore: uses}
		p.Amount = 0
	})
	e.Oracle.OnHostInstruction(oracle.Far(0x110, 0x6b5b), func(m *dg.Machine) (bool, error) {
		o := e.Oracle
		r := o.Regs()
		if !p.Active || p.Applied || !p.source(o) || r.BP != p.BP-6 || r.SP != r.BP-4 || o.Word(oracle.Far(r.SS, r.BP+2)) != 0x6900 || o.Word(oracle.Far(r.SS, r.BP+4)) != 0x110 {
			return false, errors.New("alchemy roll frame")
		}
		p.Award.Roll = r.AX
		w, _, amount, x := buildAlchemyWorld(p.Before, p.Award)
		if x != nil {
			return false, x
		}
		m.Write16(0x1e880+uint32(r.BP)-4, uint16(amount))
		p.After = w
		p.Amount = amount
		m.CPU.IP = 0x6b6f
		m.CPU.Cycles++
		return true, nil
	})
	e.Oracle.OnHostInstruction(oracle.Far(0x110, 0x6bd6), func(m *dg.Machine) (bool, error) {
		o := e.Oracle
		r := o.Regs()
		if !p.Active || p.Applied || !p.source(o) || r.BP != p.BP-6 || r.SP != r.BP-4 || uint64(o.Word(oracle.Far(0x1e88, r.BP-4))) != p.Amount {
			return false, errors.New("alchemy value frame")
		}
		m.Write16(0x1e880+0x4f8, uint16(p.After.Army.Gold))
		p.Applied = true
		m.CPU.IP = 0x6bde
		m.CPU.Cycles++
		return true, nil
	})
	e.Oracle.OnCall(oracle.Far(0x110, 0x6be2), func(o *oracle.Oracle) {
		if p.Active && p.Applied && p.source(o) && o.Regs().BP == p.BP-6 {
			p.Waiting = true
		}
	})
	e.Oracle.OnHostInstruction(oracle.Far(0x110, 0x68f0), func(m *dg.Machine) (bool, error) {
		if !p.Active {
			return false, nil
		}
		o := e.Oracle
		r := o.Regs()
		if !p.Applied || p.Charged || !p.source(o) || r.BP != p.BP || r.SP != r.BP || o.Word(oracle.Far(r.SS, r.BP+6)) != 1 || o.Word(oracle.Far(0x1e88, 0x2b2a)) != p.Award.UsesBefore {
			return false, errors.New("alchemy charge frame")
		}
		m.Write16(0x1e880+0x2b2a, p.Award.UsesBefore-1)
		m.CPU.R[dg.BX] = 2
		m.CPU.IP = 0x68f9
		m.CPU.Cycles++
		p.Charged = true
		p.Waiting = false
		return true, nil
	})
	e.Oracle.OnHostInstruction(oracle.Far(0x110, 0x68f9), func(*dg.Machine) (bool, error) {
		if !p.Active {
			return false, nil
		}
		r := e.Oracle.Regs()
		if !p.source(e.Oracle) || r.BP != p.BP || r.SP != p.BP || !p.Charged {
			return false, errors.New("alchemy completion frame")
		}
		if !p.Committed {
			p.Pending = true
			return false, errAlchemyYield
		}
		return false, nil
	})
	e.Oracle.OnCall(oracle.Far(0x110, 0x68fa), func(o *oracle.Oracle) {
		if !p.Active {
			return
		}
		if !p.source(o) || o.Regs().SP != p.EntrySP || !p.Committed {
			fail(errors.New("return before durable cast"))
		}
		p.Active = false
	})
	return p, nil
}
func (p *alchemyPort) Complete(root, input, scratch, evidence string) error {
	if !p.Pending || p.Committed || !p.Charged || p.Army.Current.Token != p.Before.Token {
		return errors.New("no pending/stale alchemy")
	}
	dir, e := os.MkdirTemp(p.Army.Store.Dir, ".alchemy-capture-")
	if e != nil {
		return e
	}
	defer os.RemoveAll(dir)
	state := filepath.Join(dir, "held.state")
	if e = p.Engine.Oracle.SaveStateFile(state); e != nil {
		return e
	}
	maps, e := readNativeCheckpointMaps(scratch)
	if e != nil {
		return e
	}
	native, files, e := serializeAlchemyNative(root, filepath.Join(input, "PAM.AY"), state, filepath.Join(dir, "native"), maps)
	if e != nil {
		return e
	}
	if evidence != "" {
		folder := filepath.Join(evidence, fmt.Sprintf("cast-%03d", p.Casts+1))
		if e = os.Mkdir(folder, 0700); e != nil {
			return e
		}
		raw, x := os.ReadFile(state)
		if x != nil {
			return x
		}
		if e = os.WriteFile(filepath.Join(folder, "held.state"), raw, 0600); e != nil {
			return e
		}
		if e = os.WriteFile(filepath.Join(folder, "native.ay"), native, 0600); e != nil {
			return e
		}
	}
	updated, e := p.Army.Store.CommitAlchemy(p.Before.Token, p.Award, native, files)
	if e != nil {
		return e
	}
	if worldDigest(updated.World) != worldDigest(p.After) {
		return errors.New("unexpected alchemy world")
	}
	if e = os.WriteFile(filepath.Join(scratch, "gamedata.ay"), native, 0600); e != nil {
		return e
	}
	for n, b := range files {
		if e = os.WriteFile(filepath.Join(scratch, n), b, 0600); e != nil {
			return e
		}
	}
	p.Army.Current = updated
	p.Committed = true
	p.Pending = false
	p.Casts++
	return nil
}
