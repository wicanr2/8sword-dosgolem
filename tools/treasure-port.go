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

var errTreasureYield = errors.New("treasure checkpoint yield")

type treasurePort struct {
	Engine                              *game.Engine
	Army                                *worldArmyPort
	Code                                []byte
	Active, Pending, Committed, Awarded bool
	Waiting                             bool
	BP, EntrySP                         uint16
	Before                              progressPairSnapshot
	After                               OwnedWorld
	Award                               treasureAward
	Awards, Opens, Closes               uint64
	Events                              []map[string]any
}

var treasureCurrent *treasurePort

func (p *treasurePort) source(o *oracle.Oracle) bool {
	r := o.Regs()
	return r.CS == 0x110 && r.SS == 0x1e88 && r.DS == 0x1e88 && bytes.Equal(p.Code[0x20b0:0x2446], o.Bytes(oracle.Far(0x110, 0x20b0), 0x396))
}
func installTreasurePort(e *game.Engine, army *worldArmyPort) (*treasurePort, error) {
	code, x := worldArmyCode(e.PAM)
	if x != nil {
		return nil, x
	}
	p := &treasurePort{Engine: e, Army: army, Code: code}
	treasureCurrent = p
	fail := func(x error) { panic(&worldArmyPortFault{"treasure: " + x.Error()}) }
	e.Oracle.OnCall(oracle.Far(0x110, 0x20b0), func(o *oracle.Oracle) {
		r := o.Regs()
		if !p.source(o) || r.SP < 32 || o.Word(oracle.Far(r.SS, r.SP)) != 0x25e8 || o.Word(oracle.Far(r.SS, r.SP+2)) != 0x110 {
			fail(errors.New("entry source frame"))
		}
		if p.Active {
			if p.EntrySP != r.SP {
				fail(errors.New("overlapping event"))
			}
			return
		}
		before, x := army.snapshot()
		if x != nil {
			fail(x)
		}
		if army.ShopOpen || before.World.Battle != nil {
			fail(errors.New("event during shop/battle"))
		}
		for i, n := range pairWorldResources(before.World).words() {
			if uint64(o.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
				fail(errors.New("entry resource mismatch"))
			}
		}
		for g := 0; g < 8; g++ {
			for row := 0; row < 10; row++ {
				n, x := treasureAmount(before.Bytes.Native, g, row)
				if x != nil || n != o.Word(oracle.Far(0x1e88, uint16(0x4490+g*20+row*2))) {
					fail(errors.New("treasure table mismatch"))
				}
			}
		}
		p.Active = true
		p.Pending = false
		p.Committed = false
		p.Awarded = false
		p.Waiting = false
		p.EntrySP = r.SP
		p.BP = r.SP - 2
		p.Before = before
		p.Opens++
	})
	e.Oracle.OnCall(oracle.Far(0x110, 0x20d4), func(o *oracle.Oracle) {
		if p.Active && !p.Awarded && p.source(o) && o.Regs().BP == p.BP {
			p.Waiting = true
		}
	})
	for _, ip := range []uint16{0x22e9, 0x230e} {
		ip := ip
		e.Oracle.OnHostInstruction(oracle.Far(0x110, ip), func(m *dg.Machine) (bool, error) {
			o := e.Oracle
			r := o.Regs()
			if !p.Active || p.Awarded || !p.source(o) || r.BP != p.BP || r.SP != r.BP-10 {
				return false, errors.New("treasure award context")
			}
			g := int(o.Word(oracle.Far(0x1e88, 0x56d6)))
			row := int(o.Word(oracle.Far(0x1e88, r.BP-2)))
			choice := int(o.Word(oracle.Far(0x1e88, r.BP-6)))
			if choice != 1 && choice != 2 || ip == 0x22e9 && choice != 1 || ip == 0x230e && choice != 2 {
				return false, errors.New("treasure choice context")
			}
			amount, x := treasureAmount(p.Before.Bytes.Native, g, row)
			if x != nil || amount == 0 || amount != o.Word(oracle.Far(0x1e88, 0x448e)) {
				return false, errors.New("treasure value")
			}
			cx, cy := o.Word(oracle.Far(0x1e88, 0x8e12)), o.Word(oracle.Far(0x1e88, 0x8e44))
			matches := 0
			for i := 0; i < 10; i++ {
				if o.Word(oracle.Far(0x1e88, uint16(0x8c60+i*4))) == cx && o.Word(oracle.Far(0x1e88, uint16(0x8c62+i*4))) == cy {
					matches++
					if i != row {
						return false, errors.New("treasure coordinate identity")
					}
				}
			}
			if matches != 1 || r.BX+r.SI != uint16(g*20+row*2) {
				return false, errors.New("treasure address provenance")
			}
			a := treasureAward{g, row, choice, amount}
			w, _, x := buildTreasureWorld(p.Before, a)
			if x != nil {
				return false, x
			}
			m.Write16(0x1e880+uint32(0x4490+g*20+row*2), 0)
			for i, n := range pairWorldResources(w).words() {
				m.Write16(0x1e880+0x4f2+uint32(i*2), uint16(n))
			}
			m.CPU.IP = 0x22fa
			if choice == 2 {
				m.CPU.IP = 0x2325
			}
			m.CPU.Cycles++
			p.Awarded = true
			p.Waiting = false
			p.Award = a
			p.After = w
			return true, nil
		})
	}
	e.Oracle.OnHostInstruction(oracle.Far(0x110, 0x2440), func(*dg.Machine) (bool, error) {
		o := e.Oracle
		r := o.Regs()
		if !p.Active || !p.source(o) || r.BP != p.BP || r.SP != r.BP-10 {
			return false, errors.New("treasure completion context")
		}
		if p.Awarded && !p.Committed {
			p.Pending = true
			return false, errTreasureYield
		}
		return false, nil
	})
	e.Oracle.OnCall(oracle.Far(0x110, 0x2445), func(o *oracle.Oracle) {
		if !p.source(o) || o.Regs().SP != p.EntrySP {
			fail(errors.New("treasure return context"))
		}
		if !p.Active {
			return
		} // Same returned IP can be notified again after IRQ.
		if p.Awarded && !p.Committed {
			fail(errors.New("return before durable award"))
		}
		p.Active = false
		p.Waiting = false
		p.Closes++
	})
	return p, nil
}
func (p *treasurePort) Complete(root, input, scratch, evidence string) error {
	if !p.Pending || p.Committed || !p.Awarded || p.Army.Current.Token != p.Before.Token {
		return errors.New("no pending/stale treasure")
	}
	dir, e := os.MkdirTemp(p.Army.Store.Dir, ".treasure-capture-")
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
	native, files, e := serializeTreasureNative(root, filepath.Join(input, "PAM.AY"), state, filepath.Join(dir, "native"), maps)
	if e != nil {
		return e
	}
	if evidence != "" {
		folder := filepath.Join(evidence, fmt.Sprintf("treasure-%03d", p.Awards+1))
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
	updated, e := p.Army.Store.CommitTreasure(p.Before.Token, p.Award, native, files)
	if e != nil {
		return e
	}
	if worldDigest(updated.World) != worldDigest(p.After) {
		return errors.New("unexpected treasure world")
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
	p.Pending = false
	p.Committed = true
	p.Awards++
	p.Events = append(p.Events, map[string]any{"award": p.Award, "token": updated.Token, "native_sha256": updated.NativeSHA})
	return nil
}
