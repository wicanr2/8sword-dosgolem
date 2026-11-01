package ownedworld

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

var errSummonYield = errors.New("summon checkpoint yield")
var summonCurrent *summonPort

type summonPort struct {
	Engine                                                              *game.Engine
	Army                                                                *worldArmyPort
	Code                                                                []byte
	Active, PayloadReady, Applied, Charged, Pending, Committed, Waiting bool
	EntrySP, BP                                                         uint16
	Before                                                              progressPairSnapshot
	After                                                               OwnedWorld
	Award                                                               summonAward
	Result                                                              summonResult
	Casts                                                               uint64
}

func (p *summonPort) source(o *oracle.Oracle) bool {
	r := o.Regs()
	return r.CS == 0x110 && r.DS == 0x1e88 && r.SS == 0x1e88 && bytes.Equal(p.Code[0x68ce:0x693c], o.Bytes(oracle.Far(0x110, 0x68ce), 110)) && bytes.Equal(p.Code[0x6bea:0x6e32], o.Bytes(oracle.Far(0x110, 0x6bea), 584)) && bytes.Equal(p.Code[0x6226:0x6499], o.Bytes(oracle.Far(0x110, 0x6226), 627))
}
func (p *summonPort) effectFrame(o *oracle.Oracle) bool {
	r := o.Regs()
	return p.source(o) && r.BP == p.BP-6 && r.SP == r.BP-14 && o.Word(oracle.Far(r.SS, r.BP+2)) == 0x6906 && o.Word(oracle.Far(r.SS, r.BP+4)) == 0x110
}
func installSummonPort(e *game.Engine, army *worldArmyPort) (*summonPort, error) {
	code, x := worldArmyCode(e.PAM)
	if x != nil {
		return nil, x
	}
	p := &summonPort{Engine: e, Army: army, Code: code}
	summonCurrent = p
	fail := func(x error) { panic(&worldArmyPortFault{"summon: " + x.Error()}) }
	swordOnCall(e.Oracle, oracle.Far(0x110, 0x68ce), func(o *oracle.Oracle) {
		if o.Arg(0) != 2 {
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
		uses, x := alchemyWord(b.Bytes.Native, summonUsesOffset)
		access, y := alchemyWord(b.Bytes.Native, alchemyLearnedOffset)
		bonus, z := alchemyWord(b.Bytes.Native, summonBonusOffset)
		if x != nil || y != nil || z != nil || access != 1 || uses == 0 || uses > 32767 || o.Word(oracle.Far(0x1e88, 0x26aa)) != access || o.Word(oracle.Far(0x1e88, 0x26b0)) != bonus || o.Word(oracle.Far(0x1e88, 0x2b2c)) != uses || army.ShopOpen || b.World.Battle != nil {
			fail(errors.New("unavailable or mismatched spell"))
		}
		for i, n := range pairWorldResources(b.World).words() {
			if uint64(o.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
				fail(errors.New("entry resource mismatch"))
			}
		}
		p.Active = true
		p.PayloadReady = false
		p.Applied = false
		p.Charged = false
		p.Pending = false
		p.Committed = false
		p.Waiting = false
		p.EntrySP = r.SP
		p.BP = r.SP - 2
		p.Before = b
		p.Award = summonAward{Bonus: bonus == 1, UsesBefore: uses}
		p.Result = summonResult{Slot: -1}
	})
	swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x6c2b), func(m *dg.Machine) (bool, error) {
		o := e.Oracle
		r := o.Regs()
		if !p.Active || p.PayloadReady || !p.effectFrame(o) {
			return false, errors.New("summon roll frame")
		}
		p.Award.Roll = r.AX
		w, _, result, x := buildSummonWorld(p.Before, army.Store.Catalog, p.Award)
		if x != nil {
			return false, x
		}
		m.Write16(0x1e880+uint32(r.BP)-12, result.Kind)
		m.Write16(0x1e880+uint32(r.BP)-2, uint16(result.Count))
		p.After = w
		p.Result = result
		p.PayloadReady = true
		m.CPU.IP = 0x6c87
		m.CPU.Cycles++
		return true, nil
	})
	swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x6d76), func(m *dg.Machine) (bool, error) {
		o := e.Oracle
		r := o.Regs()
		if !p.Active || !p.PayloadReady || p.Applied || !p.effectFrame(o) || o.Word(oracle.Far(r.SS, r.BP-12)) != p.Result.Kind || uint32(o.Word(oracle.Far(r.SS, r.BP-2))) != p.Result.Count {
			return false, errors.New("summon army frame")
		}
		joined := uint16(0)
		if p.Result.Joined {
			joined = 1
		}
		m.Write16(0x1e880+uint32(r.BP)-8, joined)
		p.Applied = true
		m.CPU.IP = 0x6dfb
		m.CPU.Cycles++
		return true, nil
	})
	swordOnCall(e.Oracle, oracle.Far(0x110, 0x6e29), func(o *oracle.Oracle) {
		if p.Active && p.Applied && p.effectFrame(o) {
			p.Waiting = true
		}
	})
	// Use selector 2's private branch. Never overwrite alchemy's shared gates.
	swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x6906), func(m *dg.Machine) (bool, error) {
		o := e.Oracle
		r := o.Regs()
		if !p.Active || !p.Applied || !p.source(o) || r.BP != p.BP || r.SP != p.BP || o.Word(oracle.Far(r.SS, r.BP+6)) != 2 || o.Word(oracle.Far(r.SS, r.BP+2)) != 0x6896 || o.Word(oracle.Far(r.SS, r.BP+4)) != 0x110 {
			return false, errors.New("summon completion frame")
		}
		if !p.Charged {
			if o.Word(oracle.Far(0x1e88, 0x2b2c)) != p.Award.UsesBefore {
				return false, errors.New("summon stale uses")
			}
			m.Write16(0x1e880+0x2b2c, p.Award.UsesBefore-1)
			p.Charged = true
			p.Waiting = false
		}
		if !p.Committed {
			p.Pending = true
			return false, errSummonYield
		}
		m.CPU.R[dg.BX] = 4
		m.CPU.IP = 0x68f9
		m.CPU.Cycles++
		return true, nil
	})
	swordOnCall(e.Oracle, oracle.Far(0x110, 0x6896), func(o *oracle.Oracle) {
		if !p.Active {
			return
		}
		if !p.source(o) || !p.Committed || o.Regs().SP != p.EntrySP+4 {
			fail(errors.New("return before durable cast"))
		}
		p.Active = false
	})
	return p, nil
}
func (p *summonPort) Complete(root, input, scratch, evidence string) error {
	if !p.Pending || p.Committed || !p.Charged || p.Army.Current.Token != p.Before.Token {
		return errors.New("no pending/stale summon")
	}
	dir, e := os.MkdirTemp(p.Army.Store.Dir, ".summon-capture-")
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
	native, files, e := serializeSummonNative(root, filepath.Join(input, "PAM.AY"), state, filepath.Join(dir, "native"), maps)
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
	updated, e := p.Army.Store.CommitSummon(p.Before.Token, p.Award, native, files)
	if e != nil {
		return e
	}
	if worldDigest(updated.World) != worldDigest(p.After) {
		return errors.New("unexpected summon world")
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
