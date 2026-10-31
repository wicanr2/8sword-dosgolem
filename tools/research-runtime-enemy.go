//go:build ignore

// DRAFT: retain the original random-enemy generator, isolate all player tables.
package main

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func decodeRuntimeEnemy(raw []byte, c ArmyCatalog, cc game.OwnedCombatCatalog) ([6]ArmyStack, error) {
	var rows [6]ArmyStack
	if len(raw) != 24 {
		return rows, errors.New("enemy six-row byte shape")
	}
	idx, e := c.index()
	if e != nil {
		return rows, e
	}
	if e = cc.Validate(); e != nil {
		return rows, e
	}
	seen := map[uint16]bool{}
	alive := false
	for i := 0; i < 6; i++ {
		kind := binary.LittleEndian.Uint16(raw[i*4:])
		count := binary.LittleEndian.Uint16(raw[i*4+2:])
		if kind == 0 && count == 0 {
			continue
		}
		if kind < 1 || kind > 25 || count < 1 || count > 32767 || seen[kind] {
			return [6]ArmyStack{}, errors.New("enemy kind/count/duplicate")
		}
		id := fmt.Sprintf("native:%02d", kind)
		p, ok := idx[id]
		v, ok2 := cc.Profiles[id]
		if !ok || !ok2 || p.NativeKind != kind || v.NativeKind != kind {
			return [6]ArmyStack{}, errors.New("enemy catalog binding")
		}
		rows[i] = ArmyStack{id, uint32(count)}
		seen[kind] = true
		alive = true
	}
	if !alive {
		return [6]ArmyStack{}, errors.New("empty runtime enemy")
	}
	return rows, nil
}

type runtimeEnemyBattle struct {
	*controlledBattle
	Stage                    string
	EntrySP, EntryBP         uint16
	CopySkipped              uint64
	EnemyBytes               []byte
	Rows                     [6]ArmyStack
	PlayerBytes, FriendBytes []byte
	Events                   []map[string]any
}

var runtimeEnemyCurrent *runtimeEnemyBattle

func runtimeEnemyState(v map[string]any) {
	if x := runtimeEnemyCurrent; x != nil {
		v["runtime_enemy_stage"] = x.Stage
		v["runtime_enemy_rows"] = x.Rows
		v["runtime_enemy_copy_skipped"] = x.CopySkipped
		v["runtime_enemy_hex"] = fmt.Sprintf("%x", x.EnemyBytes)
		v["runtime_enemy_events"] = x.Events
	}
}

func installRuntimeEnemyBattle(o *oracle.Oracle, store *progressPairStore, s progressPairSnapshot, code []byte) *runtimeEnemyBattle {
	x := &runtimeEnemyBattle{controlledBattle: installControlledBattle(o, store, s, code)}
	o.OnHostInstruction(oracle.Far(0x110, 0x32e0), x.entry)
	o.OnHostInstruction(oracle.Far(0x110, 0x3365), x.skipPlayerCopy)
	o.OnHostInstruction(oracle.Far(0x110, 0x36b4), x.importEnemy)
	return x
}
func (x *runtimeEnemyBattle) entry(m *dg.Machine) (bool, error) {
	if x.Stage == "held" {
		return x.controlledBattle.enter(m)
	}
	if x.Stage != "" && x.Stage != "generating" {
		return false, errors.New("runtime enemy entry phase")
	}
	if e := x.check(m, 0x32e0); e != nil {
		return false, e
	}
	if m.Read16(0x1e880+0x8d6a) != 0 {
		return false, errors.New("ordinary random caller modifier")
	}
	if x.Stage == "generating" {
		if m.CPU.R[dg.SP] != x.EntrySP || m.CPU.R[dg.BP] != x.EntryBP {
			return false, errors.New("repeated generation entry frame")
		}
		return false, nil
	}
	x.EntrySP = m.CPU.R[dg.SP]
	x.EntryBP = m.CPU.R[dg.BP]
	x.SP = x.EntrySP
	x.BP = x.EntryBP
	for i, n := range pairWorldResources(x.Current.World).words() {
		x.BeforeResources[i] = uint16(n)
	}
	x.PlayerBytes = append([]byte(nil), m.Mem[0x1edca:0x1ede2]...)
	x.FriendBytes = append([]byte(nil), m.Mem[0x23f68:0x23f80]...)
	x.Stage = "generating"
	x.Events = append(x.Events, map[string]any{"event": "generation-entry", "steps_not_replayed": true})
	return false, nil // Execute the actual original prologue and terrain lookup.
}
func (x *runtimeEnemyBattle) generatorCheck(m *dg.Machine, ip uint16) error {
	c := m.CPU
	ds := uint32(0x1e880)
	bp := c.R[dg.BP]
	if x.Stage != "generating" || c.IP != ip || c.Seg[dg.CS] != 0x110 || c.Seg[dg.DS] != 0x1e88 || c.Seg[dg.SS] != 0x1e88 || c.Cycles == ^uint64(0) || x.EntrySP < 32 || bp != x.EntrySP-2 || c.R[dg.SP] != bp-0x12 || m.Read16(ds+uint32(bp)) != x.EntryBP || m.Read16(ds+uint32(bp)+2) != 0x171d || m.Read16(ds+uint32(bp)+4) != 0x110 {
		return errors.New("enemy generator frame")
	}
	if !bytes.Equal(x.Code[0x32e0:0x3774], m.Mem[0x1100+0x32e0:0x1100+0x3774]) || !bytes.Equal(x.Code[0x151c:0x1796], m.Mem[0x1100+0x151c:0x1100+0x1796]) {
		return errors.New("enemy generator source")
	}
	if m.Read16(ds+uint32(bp)-0xc) == 65 || m.Read16(ds+0x56d6) > 7 || m.Read16(ds+0x8d6a) != 0 {
		return errors.New("guarded or unsupported encounter")
	}
	if !bytes.Equal(x.PlayerBytes, m.Mem[ds+0x54a:ds+0x562]) || !bytes.Equal(x.FriendBytes, m.Mem[ds+0x56e8:ds+0x5700]) {
		return errors.New("original player tables changed")
	}
	s, e := x.Store.Recover()
	if e != nil {
		return e
	}
	if s.Token != x.Current.Token {
		return errors.New("enemy generation stale pair")
	}
	for i, n := range pairWorldResources(s.World).words() {
		if uint64(m.Read16(ds+0x4f2+uint32(i*2))) != n {
			return errors.New("enemy generation resources")
		}
	}
	return nil
}
func (x *runtimeEnemyBattle) skipPlayerCopy(m *dg.Machine) (bool, error) {
	if e := x.generatorCheck(m, 0x3365); e != nil {
		return false, e
	}
	if x.CopySkipped != 0 {
		return false, errors.New("repeated player copy")
	}
	clear(m.Mem[0x23f80:0x23f98]) // Enemy output only. No reads of native player rows.
	m.CPU.IP = 0x3396
	m.CPU.Cycles++
	x.CopySkipped++
	return true, nil
}
func (x *runtimeEnemyBattle) importEnemy(m *dg.Machine) (bool, error) {
	if e := x.generatorCheck(m, 0x36b4); e != nil {
		return false, e
	}
	if x.CopySkipped != 1 {
		return false, errors.New("enemy copy gate missing")
	}
	raw := append([]byte(nil), m.Mem[0x23f80:0x23f98]...)
	rows, e := decodeRuntimeEnemy(raw, x.Store.Catalog, x.Store.Combat)
	if e != nil {
		return false, e
	}
	w := x.Current.World
	if w.Battle != nil || len(w.Encounters) != 0 {
		return false, errors.New("runtime encounter collision")
	}
	w.Encounters = map[string]WorldEncounter{"random:runtime-r1": {Enemy: rows}}
	w, e = w.begin(x.Store.Catalog, x.Store.Combat, "random:runtime-r1", game.OwnedCombatConfig{Rules: w.Army.Rules, Divisors: [2]uint32{5, 5}, Multipliers: [2]uint32{1, 1}})
	if e != nil {
		return false, e
	}
	if e = x.commit(w); e != nil {
		return false, e
	}
	x.EnemyBytes = raw
	x.Rows = rows
	x.Pending = true
	x.Stage = "held"
	bp := m.CPU.R[dg.BP]
	ds := uint32(0x1e880)
	m.CPU.R[dg.SI] = m.Read16(ds + uint32(bp) - 0x12)
	m.CPU.R[dg.DI] = m.Read16(ds + uint32(bp) - 0x10)
	m.CPU.R[dg.SP] = bp + 2
	m.CPU.R[dg.BP] = m.Read16(ds + uint32(bp))
	m.CPU.IP = 0x32e0
	m.CPU.Cycles++
	x.Events = append(x.Events, map[string]any{"event": "imported", "rows": rows, "raw_hex": fmt.Sprintf("%x", raw), "region": m.Read16(ds + 0x56d6)})
	return true, nil // Retry only the host bridge; never regenerate the enemy.
}
