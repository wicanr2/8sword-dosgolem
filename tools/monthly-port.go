//go:build ignore

package main

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"path/filepath"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

var errMonthlyYield = errors.New("monthly checkpoint yield")

type monthlyPort struct {
	Engine                                *game.Engine
	Army                                  *worldArmyPort
	Code                                  []byte
	Active, StockDone, Pending, Committed bool
	BP, SP                                uint16
	Before                                progressPairSnapshot
	After                                 OwnedWorld
	Budget                                monthlyBudget
	Refreshed                             []byte
	Saves                                 uint64
	Events                                []map[string]any
}

var monthlyCurrent *monthlyPort

func (p *monthlyPort) source(o *oracle.Oracle) bool {
	r := o.Regs()
	return r.CS == 0x110 && r.DS == 0x1e88 && r.SS == 0x1e88 && bytes.Equal(p.Code[0x2446:0x2ddd], o.Bytes(oracle.Far(0x110, 0x2446), 0x997))
}
func installMonthlyPort(e *game.Engine, p *worldArmyPort) (*monthlyPort, error) {
	code, x := worldArmyCode(e.PAM)
	if x != nil {
		return nil, x
	}
	v := &monthlyPort{Engine: e, Army: p, Code: code}
	monthlyCurrent = v
	for _, profile := range p.Store.Catalog.Profiles {
		if profile.NativeKind > 0 {
			at := 0x1d780 + 0x2986 + int(profile.NativeKind)*2
			if at+2 > len(code) || uint64(uint16(code[at])|uint16(code[at+1])<<8) != profile.Gold {
				return nil, errors.New("monthly native fee catalog mismatch")
			}
		}
	}
	fail := func(err error) { panic(&worldArmyPortFault{"monthly: " + err.Error()}) }
	e.Oracle.OnCall(oracle.Far(0x110, 0x26ed), func(o *oracle.Oracle) {
		r := o.Regs()
		if !v.source(o) || r.BP < 32 || r.SP != r.BP-18 || o.Word(oracle.Far(r.SS, r.BP+2)) != 0xbc7 || o.Word(oracle.Far(r.SS, r.BP+4)) != 0x110 || int16(o.Word(oracle.Far(0x1e88, 0x56da))) > 0 {
			fail(errors.New("source frame"))
		}
		if v.Active {
			if v.BP != r.BP || v.SP != r.SP {
				fail(errors.New("overlapping month"))
			}
			return
		}
		before, x := p.snapshot()
		if x != nil {
			fail(x)
		}
		if p.ShopOpen {
			fail(errors.New("month during shop"))
		}
		w, b, stock, x := buildMonthlyWorld(before, p.Store.Catalog, e.PAM)
		if x != nil {
			fail(x)
		}
		for i, n := range pairWorldResources(before.World).words() {
			if uint64(o.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
				fail(errors.New("entry resources"))
			}
		}
		caps, x := monthlyCaps(e.PAM)
		if x != nil {
			fail(x)
		}
		for g := 0; g < 5; g++ {
			for row := 0; row < 24; row++ {
				rec, x := decodeCampRecord(before.Bytes.Native, g, row)
				if x != nil {
					fail(x)
				}
				for f, n := range rec.Words {
					if o.Word(oracle.Far(0x1e88, campDS(g, row)+uint16(f*2))) != n {
						fail(errors.New("live camp differs from checkpoint"))
					}
				}
				if o.Word(oracle.Far(0x1e88, uint16(0x3a56+g*240+row*10))) != caps[g*24+row] {
					fail(errors.New("cap source changed"))
				}
			}
		}
		v.Active = true
		v.StockDone = false
		v.Pending = false
		v.Committed = false
		v.BP = r.BP
		v.SP = r.SP
		v.Before = before
		v.After = w
		v.Budget = b
		v.Refreshed = stock
	})
	e.Oracle.OnHostInstruction(oracle.Far(0x110, 0x2867), func(m *dg.Machine) (bool, error) {
		o := e.Oracle
		r := o.Regs()
		if !v.Active || !v.source(o) || v.StockDone || o.Word(oracle.Far(r.SS, r.BP+2)) != 0x26fd || r.BP != v.SP-6 {
			return false, errors.New("monthly stock context")
		}
		for g := 0; g < 5; g++ {
			for row := 0; row < 24; row++ {
				rec, x := decodeCampRecord(v.Refreshed, g, row)
				if x != nil {
					return false, x
				}
				m.Write16(0x1e880+uint32(campDS(g, row))+8, rec.Words[4])
			}
		}
		v.StockDone = true
		m.CPU.IP = 0x29f9
		m.CPU.Cycles++
		return true, nil
	})
	for _, ip := range []uint16{0x26fd, 0x2803, 0x284d} {
		ip := ip
		e.Oracle.OnHostInstruction(oracle.Far(0x110, ip), func(m *dg.Machine) (bool, error) {
			o := e.Oracle
			r := o.Regs()
			if !v.Active || !v.source(o) || r.BP != v.BP || r.SP != v.SP || !v.StockDone {
				return false, errors.New("monthly source/phase")
			}
			switch ip {
			case 0x26fd:
				m.Write16(0x1e880+uint32(r.BP)-8, 6)
				m.Write16(0x1e880+uint32(r.BP)-10, uint16(v.Budget.Charged))
				m.CPU.IP = 0x2780
				if v.Budget.Disbanded {
					m.CPU.IP = 0x275c
				}
				m.CPU.Cycles++
				return true, nil
			case 0x2803:
				m.Write16(0x1e880+0x4f8, uint16(v.Budget.After))
				m.CPU.IP = 0x2810
				m.CPU.Cycles++
				return true, nil
			default:
				if v.Committed {
					return false, nil
				}
				v.Pending = true
				return false, errMonthlyYield
			}
		})
	}
	e.Oracle.OnCall(oracle.Far(0x110, 0x2855), func(*oracle.Oracle) {
		if v.Active {
			if !v.Committed {
				fail(errors.New("returned before durable monthly commit"))
			}
			v.Active = false
		}
	})
	return v, nil
}
func (p *monthlyPort) Complete(root, input, scratch, evidence string) error {
	if !p.Pending || p.Committed {
		return errors.New("no pending month")
	}
	if p.Army.Current.Token != p.Before.Token {
		return errors.New("monthly world changed")
	}
	dir, e := os.MkdirTemp(p.Army.Store.Dir, ".monthly-capture-")
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
	native, files, e := serializeMonthlyNative(root, filepath.Join(input, "PAM.AY"), state, filepath.Join(dir, "native"), maps)
	if e != nil {
		return e
	}
	if evidence != "" {
		folder := filepath.Join(evidence, fmt.Sprintf("month-%03d", p.Saves+1))
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
		for n, b := range files {
			if e = os.WriteFile(filepath.Join(folder, n), b, 0600); e != nil {
				return e
			}
		}
	}
	updated, e := p.Army.Store.CommitMonthly(p.Before.Token, native, files)
	if e != nil {
		return e
	}
	if worldDigest(updated.World) != worldDigest(p.After) {
		return errors.New("monthly committed unexpected world")
	}
	// Mirror the durable snapshot to the engine's disposable shadow, preserving
	// F7's existing read/write routing after this automatic full checkpoint.
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
	p.Saves++
	p.Events = append(p.Events, map[string]any{"token": updated.Token, "budget": p.Budget, "native_sha256": updated.NativeSHA, "world": updated.World})
	return nil
}
