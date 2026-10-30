//go:build ignore

// Controlled ABI prototype only. The scripted policy belongs to the probe.
package main

import (
	"bytes"
	"errors"
	"fmt"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

var errControlledBattleYield = errors.New("controlled Go battle owns execution")

type controlledBattle struct {
	Store                      *progressPairStore
	Current                    progressPairSnapshot
	Code                       []byte
	Pending, Settled, Returned bool
	SP, BP                     uint16
	Result                     uint16
	BeforeResources            [6]uint16
	NativeCalls                uint64
	Frames                     []map[string]any
}

func (b *controlledBattle) check(m *dg.Machine, ip uint16) error {
	c := m.CPU
	ds := uint32(0x1e880)
	sp, bp := c.R[dg.SP], c.R[dg.BP]
	if c.Seg[dg.CS] != 0x110 || c.IP != ip || c.Seg[dg.DS] != 0x1e88 || c.Seg[dg.SS] != 0x1e88 || sp > 65530 || bp > 65528 || c.Cycles == ^uint64(0) {
		return errors.New("controlled battle segments/bounds")
	}
	if !bytes.Equal(b.Code[0x32e0:0x3774], m.Mem[0x1100+0x32e0:0x1100+0x3774]) || !bytes.Equal(b.Code[0x151c:0x1796], m.Mem[0x1100+0x151c:0x1100+0x1796]) {
		return errors.New("controlled battle source")
	}
	s, e := b.Store.Recover()
	if e != nil {
		return e
	}
	if s.Token != b.Current.Token {
		return errors.New("controlled battle stale pair")
	}
	if ip == 0x32e0 {
		if m.Read16(ds+uint32(sp)) != 0x171d || m.Read16(ds+uint32(sp)+2) != 0x110 || m.Read16(ds+uint32(bp)+2) != 0x0bd3 || m.Read16(ds+uint32(bp)+4) != 0x110 {
			return errors.New("controlled battle caller")
		}
		for i, n := range pairWorldResources(b.Current.World).words() {
			want := uint16(n)
			if b.Pending {
				want = b.BeforeResources[i]
			}
			if m.Read16(ds+0x4f2+uint32(i*2)) != want {
				return errors.New("controlled battle resources")
			}
		}
	}
	return nil
}
func (b *controlledBattle) commit(w OwnedWorld) error {
	s, e := b.Store.Commit(b.Current.Token, w)
	if e != nil {
		return e
	}
	b.Current = s
	return nil
}
func (b *controlledBattle) enter(m *dg.Machine) (bool, error) {
	if b.Returned {
		return false, errors.New("controlled battle already returned")
	}
	if e := b.check(m, 0x32e0); e != nil {
		return false, e
	}
	c := m.CPU
	if !b.Pending {
		for i, n := range pairWorldResources(b.Current.World).words() {
			b.BeforeResources[i] = uint16(n)
		}
		w, e := b.Current.World.begin(b.Store.Catalog, b.Store.Combat, "random:controlled-r1", game.OwnedCombatConfig{Rules: b.Current.World.Army.Rules, Divisors: [2]uint32{5, 5}, Multipliers: [2]uint32{1, 1}})
		if e != nil {
			return false, e
		}
		if e = b.commit(w); e != nil {
			return false, e
		}
		b.Pending = true
		b.SP = c.R[dg.SP]
		b.BP = c.R[dg.BP]
	}
	if c.R[dg.SP] != b.SP || c.R[dg.BP] != b.BP {
		return false, errors.New("controlled battle changed frame")
	}
	if !b.Settled {
		return false, errControlledBattleYield
	}
	for i, n := range pairWorldResources(b.Current.World).words() {
		m.Write16(0x1e880+0x4f2+uint32(i*2), uint16(n))
	}
	// The verified far-call frame is consumed once; no native 25-kind code.
	c.R[dg.SP] += 4
	c.R[dg.AX] = b.Result
	c.IP = 0x171d
	c.Cycles++
	return true, nil
}
func (b *controlledBattle) after(m *dg.Machine) (bool, error) {
	if e := b.check(m, 0x171d); e != nil {
		return false, e
	}
	if !b.Pending || !b.Settled || b.Returned || m.CPU.R[dg.BP] != b.BP || m.CPU.R[dg.SP] != b.SP+4 {
		return false, errors.New("controlled return phase")
	}
	for i, n := range pairWorldResources(b.Current.World).words() {
		if uint64(m.Read16(0x1e880+0x4f2+uint32(i*2))) != n {
			return false, errors.New("controlled return resources")
		}
	}
	// Go has already applied the world result. Skip original duplicate reward,
	// including its native army accesses, and resume the original map redraw.
	m.CPU.IP = 0x172e
	m.CPU.Cycles++
	b.Returned = true
	return true, nil
}
func installControlledBattle(o *oracle.Oracle, s *progressPairStore, p progressPairSnapshot, code []byte) *controlledBattle {
	b := &controlledBattle{Store: s, Current: p, Code: code}
	o.OnHostInstruction(oracle.Far(0x110, 0x32e0), b.enter)
	o.OnHostInstruction(oracle.Far(0x110, 0x171d), b.after)
	for _, ip := range []uint16{0x3371, 0x3379, 0x3755, 0x375d, 0x1796, 0x32b4} {
		ip := ip
		o.OnCall(oracle.Far(0x110, ip), func(*oracle.Oracle) { b.NativeCalls++; panic(fmt.Sprintf("native battle path escaped at %04x", ip)) })
	}
	o.OnCall(oracle.Far(0x0f67, 8), func(*oracle.Oracle) { b.NativeCalls++; panic("native tactical path escaped") })
	return b
}
func (b *controlledBattle) apply(a game.OwnedCombatAction) (game.OwnedCombatOutcome, error) {
	w := b.Current.World
	if !b.Pending || w.Battle == nil || b.Settled {
		return game.OwnedCombatOutcome{}, errors.New("no pending Go battle")
	}
	n, event, e := w.Battle.State.Apply(b.Store.Combat, a)
	if e != nil {
		return event, e
	}
	v := *w.Battle
	v.State = n
	w.Battle = &v
	return event, b.commit(w)
}
func (b *controlledBattle) settle(input DefeatInput) error {
	if !b.Pending || b.Settled {
		return errors.New("not pending or already settled")
	}
	s, e := b.Current.World.resolveEncounter(b.Store.Catalog, b.Store.Combat, EncounterContext{Kind: "random"}, input)
	if e != nil {
		return e
	}
	if e = b.commit(s.After); e != nil {
		return e
	}
	b.Result = 0
	if input.Reason == "retreat" {
		b.Result = 1
	}
	if input.Reason == "annihilation" {
		b.Result = 2
	}
	b.Settled = true
	return nil
}
