//go:build ignore

package main

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"strings"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

type guardedBinding struct {
	Context       EncounterContext `json:"context"`
	Rows          [6]ArmyStack     `json:"rows"`
	PresenceSkips uint64           `json:"presence_skips"`
}

func (g *guardedBinding) key() string {
	return fmt.Sprintf("guarded:%02d:%02d", g.Context.Region, g.Context.Index)
}
func guardedKey(s string) bool { return strings.HasPrefix(s, "guarded:") }
func guardedSignature(mem []byte) string {
	b := append([]byte{}, mem[0x1100+0x2446:0x1100+0x2dde]...)
	b = append(b, mem[0x1100+0x2dde:0x1100+0x32b4]...)
	b = append(b, mem[0x1100+0x1abe:0x1100+0x1daa]...)
	return nativeSHA(b)
}
func guardedFrame(s resumeImage) bool {
	m := s.M
	if len(m.Mem) != 1<<20 || m.R[4] > 65530 || m.R[5] > 65528 {
		return false
	}
	word := func(at uint16) uint16 { return binary.LittleEndian.Uint16(m.Mem[0x1e880+int(at):]) }
	return word(m.R[4]) == 0x309e && word(m.R[4]+2) == 0x110 && word(m.R[5]+2) == 0x25ee && word(m.R[5]+4) == 0x110 && word(0x8d6a) == 0 && guardedSignature(m.Mem) == guardedCodeSHA
}
func guardNPCAt(g, index int) int { return int(guardedBases[g]) + index*24 }
func guardSavedWord(native []byte, ds int) (uint16, error) {
	at := guardedSaveBase + ds - 0x365e
	if len(native) != 2987 || ds < 0x365e || ds >= 0x3a4e || ds%2 != 0 {
		return 0, errors.New("guard save offset")
	}
	return binary.LittleEndian.Uint16(native[at:]) - uint16(at+3), nil
}
func bindGuard(mem []byte, c ArmyCatalog, cc game.OwnedCombatCatalog) (*guardedBinding, error) {
	if len(mem) != 1<<20 || guardedSignature(mem) != guardedCodeSHA {
		return nil, errors.New("guard fixed PAM source")
	}
	word := func(at int) uint16 { return binary.LittleEndian.Uint16(mem[0x1e880+at:]) }
	region := int(word(0x56d6))
	if region > 7 {
		return nil, errors.New("guard region")
	}
	index := -1
	for i, p := range guardedCoordinates[region] {
		if word(0x8c30+i*4) != p[0] || word(0x8c32+i*4) != p[1] {
			return nil, errors.New("guard coordinates changed")
		}
		if word(0x8e12) == p[0] && word(0x8e44) == p[1] {
			if index != -1 {
				return nil, errors.New("duplicate guard coordinate")
			}
			index = i
		}
	}
	if index < 0 {
		return nil, errors.New("unidentified guard")
	}
	ctx := EncounterContext{Kind: "guarded", Region: uint16(region), Index: uint16(index), Legacy26AA: word(0x26aa)}
	ctx.Boss = word(0x8e12) == word(0x26bc+region*6) && word(0x8e44) == word(0x26be+region*6)
	for i := 0; i < 6; i++ {
		ctx.EndingGuardAlive = ctx.EndingGuardAlive || word(0x365e+24*4+i*4) > 0
	}
	for i := range ctx.Pieces {
		v := word(0x275a + i*2)
		if v > 1 {
			return nil, errors.New("guard sword flags")
		}
		ctx.Pieces[i] = v == 1
	}
	if ctx.Boss || region == 0 && index == 4 || !ctx.EndingGuardAlive {
		return nil, errors.New("boss or ending guard remains unsupported")
	}
	at := 0x1e880 + guardNPCAt(region, index)
	raw := mem[at : at+24]
	g := &guardedBinding{Context: ctx}
	if !bytes.Equal(raw, make([]byte, 24)) {
		rows, e := decodeRuntimeEnemy(raw, c, cc)
		if e != nil {
			return nil, e
		}
		g.Rows = rows
	}
	return g, nil
}
func guardNPCBinding(mem, native []byte, g *guardedBinding, skipTarget bool) error {
	start := guardNPCAt(int(g.Context.Region), int(g.Context.Index))
	for ds := 0x365e; ds < 0x3a4e; ds += 2 {
		if skipTarget && ds >= start && ds < start+24 {
			continue
		}
		v, e := guardSavedWord(native, ds)
		if e != nil || v != binary.LittleEndian.Uint16(mem[0x1e880+ds:]) {
			return errors.New("guard saved/live NPC mismatch")
		}
	}
	return nil
}
func guardSourceFromImage(im resumeImage, s *progressPairStore) (*guardedBinding, error) {
	if !guardedFrame(im) {
		return nil, nil
	}
	return bindGuard(im.M.Mem, s.Catalog, s.Combat)
}
func guardValidateResume(s *progressPairStore, p progressPairSnapshot, im resumeImage) error {
	g, e := bindGuard(im.M.Mem, s.Catalog, s.Combat)
	if e != nil {
		return e
	}
	ref, e := savedResume(p.Bytes.World)
	if e != nil {
		return e
	}
	if e = guardNPCBinding(im.M.Mem, p.Bytes.Native, g, ref.Phase == "return"); e != nil {
		return e
	}
	record, ok := p.World.Encounters[g.key()]
	if !ok {
		return errors.New("guard record missing")
	}
	if ref.Phase == "battle" {
		if p.World.Battle == nil || p.World.Battle.Encounter != g.key() || record.Cleared || record.Enemy != g.Rows {
			return errors.New("guard active identity")
		}
		for i, v := range g.Rows {
			r := p.World.Battle.State.Initial[1][i]
			if r.Unit != v.Unit || r.Count != v.Count {
				return errors.New("guard initial enemy binding")
			}
		}
	} else {
		if (ref.Result == 0) != record.Cleared {
			return errors.New("guard cleared result")
		}
		rows := record.Enemy
		if record.Cleared {
			rows = [6]ArmyStack{}
		}
		projected, e := projectGuardNPC(p.Bytes.Native, g, rows)
		if e != nil || !bytes.Equal(projected, p.Bytes.Native) {
			return errors.New("guard durable NPC result")
		}
	}
	return nil
}
func guardBeginWorld(before OwnedWorld, c ArmyCatalog, cc game.OwnedCombatCatalog, g *guardedBinding, rows [6]ArmyStack) (OwnedWorld, error) {
	w := cloneCampWorld(before)
	key := "random:runtime-r1"
	if g != nil {
		key = g.key()
		if old, ok := w.Encounters[key]; ok && old.Cleared {
			return w, errors.New("cleared guard cannot reopen")
		}
		if rows != g.Rows {
			return w, errors.New("guard imported rows differ")
		}
	} else {
		for k := range w.Encounters {
			if !guardedKey(k) {
				return w, errors.New("unfinished random encounter")
			}
		}
	}
	w.Encounters[key] = WorldEncounter{Enemy: rows}
	return w.begin(c, cc, key, game.OwnedCombatConfig{Rules: w.Army.Rules, Divisors: [2]uint32{5, 5}, Multipliers: [2]uint32{1, 1}})
}
func guardReturnIP(b *controlledBattle) uint16 {
	if b.Guard != nil {
		return 0x309e
	}
	return 0x171d
}
func guardEntryFrame(b *controlledBattle, m *dg.Machine) bool {
	ds := uint32(0x1e880)
	sp, bp := m.CPU.R[dg.SP], m.CPU.R[dg.BP]
	parent := uint16(0xbd3)
	if b.Guard != nil {
		parent = 0x25ee
	}
	return m.Read16(ds+uint32(sp)) == guardReturnIP(b) && m.Read16(ds+uint32(sp)+2) == 0x110 && m.Read16(ds+uint32(bp)+2) == parent && m.Read16(ds+uint32(bp)+4) == 0x110
}
func guardGeneratorFrame(x *runtimeEnemyBattle, m *dg.Machine, bp uint16) bool {
	return m.Read16(0x1e880+uint32(bp)+2) == guardReturnIP(x.controlledBattle) && m.Read16(0x1e880+uint32(bp)+4) == 0x110
}
func (b *controlledBattle) afterGuard(m *dg.Machine) (bool, error) {
	if b.Guard == nil || !b.Pending || !b.Settled || b.Returned || m.CPU.R[dg.SP] != b.SP+4 || m.CPU.R[dg.BP] != b.BP {
		return false, errors.New("guard return frame")
	}
	if e := b.check(m, 0x309e); e != nil {
		return false, e
	}
	start := guardNPCAt(int(b.Guard.Context.Region), int(b.Guard.Context.Index))
	for i := 0; i < 12; i++ {
		v, e := guardSavedWord(b.Current.Bytes.Native, start+i*2)
		if e != nil {
			return false, e
		}
		m.Write16(0x1e880+uint32(start+i*2), v)
	}
	if b.Result == 3 {
		if e := applyOriginReturn(m, b); e != nil {
			return false, e
		}
	}
	m.CPU.IP = 0x32ad
	m.CPU.Cycles++
	b.Returned = true
	return true, nil
}
func installGuardedBattle(e *game.Engine, p *worldArmyPort) error {
	x := encounterCurrent
	if x == nil {
		return errors.New("guard shared controller missing")
	}
	o := e.Oracle
	code, err := worldArmyCode(e.PAM)
	if err != nil {
		return err
	}
	o.OnCall(oracle.Far(0x110, 0x2dde), func(o *oracle.Oracle) {
		fail := func(s string) { panic(&worldArmyPortFault{s}) }
		r := o.Regs()
		if r.CS != 0x110 || r.DS != 0x1e88 || r.SS != 0x1e88 || r.SP > 65528 || o.Word(oracle.Far(r.SS, r.SP)) != 0x25ee || o.Word(oracle.Far(r.SS, r.SP+2)) != 0x110 {
			fail("guard entry caller")
		}
		s, er := p.snapshot()
		if er != nil {
			fail(er.Error())
		}
		g, er := bindGuard(o.Bytes(oracle.Far(0, 0), 1<<20), p.Store.Catalog, p.Store.Combat)
		if er != nil {
			fail(er.Error())
		}
		if er = guardNPCBinding(o.Bytes(oracle.Far(0, 0), 1<<20), s.Bytes.Native, g, false); er != nil {
			fail(er.Error())
		}
		if x.Opened && !x.Finished {
			fail("unfinished guard encounter")
		}
		b := x.Bridge
		*b = controlledBattle{Store: p.Store, Current: s, Code: code, Guard: g}
		*runtimeEnemyCurrent = runtimeEnemyBattle{controlledBattle: b}
		x.ColdResume = false
		x.Confirmed = false
		x.Opened = false
		x.Finished = false
		x.UI = nil
		x.Sequence++
		x.NativeRows = append([]byte{}, o.Bytes(oracle.Far(0x1e88, 0x54a), 24)...)
		x.Events = append(x.Events, map[string]any{"command": "guard-entry", "key": g.key(), "context": g.Context, "token": s.Token})
	})
	o.OnCall(oracle.Far(0x110, 0x2fc3), func(o *oracle.Oracle) {
		if x.Bridge.Guard != nil {
			x.Confirmed = o.Regs().AX == 1
		}
	})
	o.OnHostInstruction(oracle.Far(0x110, 0x3048), func(m *dg.Machine) (bool, error) {
		b := x.Bridge
		c := m.CPU
		if b.Guard == nil || c.Seg[dg.CS] != 0x110 || c.Seg[dg.DS] != 0x1e88 || c.Seg[dg.SS] != 0x1e88 || c.R[dg.BP] > 65528 || m.Read16(0x1e880+uint32(c.R[dg.BP])+2) != 0x25ee || guardedSignature(m.Mem) != guardedCodeSHA {
			return false, errors.New("guard party gate")
		}
		v := uint16(1)
		for _, s := range b.Current.World.Army.Slots {
			if s.Count > 0 {
				v = 0
			}
		}
		m.Write16(0x1e880+uint32(c.R[dg.BP])-4, v)
		c.IP = 0x3069
		c.Cycles++
		b.Guard.PresenceSkips++
		return true, nil
	})
	o.OnHostInstruction(oracle.Far(0x110, 0x309e), func(m *dg.Machine) (bool, error) { return x.Bridge.afterGuard(m) })
	o.OnCall(oracle.Far(0x110, 0x25ee), func(o *oracle.Oracle) {
		b := x.Bridge
		if b.Guard == nil || !x.Opened || !b.Returned || x.Finished {
			return
		}
		if !bytes.Equal(x.NativeRows, o.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
			panic(&worldArmyPortFault{"guard changed player shadow"})
		}
		s, er := p.snapshot()
		if er != nil || s.Token != b.Current.Token {
			panic(&worldArmyPortFault{"guard return pair"})
		}
		x.Finished = true
		x.ReturnSteps = o.Steps()
		x.Presence.Active = false
		x.Presence.Prompt = false
		x.Presence.Token = s.Token
		x.Events = append(x.Events, map[string]any{"command": "guard-return", "world": s.World, "key": b.Guard.key()})
	})
	return nil
}
func init() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		v, er := previous(e, p)
		if er != nil {
			return nil, er
		}
		er = installGuardedBattle(e, p)
		return v, er
	}
}
