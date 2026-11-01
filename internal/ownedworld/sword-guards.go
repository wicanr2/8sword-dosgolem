package ownedworld

import (
	"encoding/binary"
	"errors"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

var swordBossIndex = [8]uint16{1, 3, 3, 3, 2, 3, 2, 10}
var swordBossCoordinates = [8][2]uint16{{48, 5}, {27, 69}, {29, 77}, {32, 62}, {53, 54}, {35, 72}, {18, 58}, {61, 76}}

func swordSource(mem []byte, ctx EncounterContext) error {
	if len(mem) != 1<<20 || ctx.Region > 7 {
		return errors.New("sword source bounds")
	}
	for i, p := range swordBossCoordinates {
		at := 0x1e880 + 0x26bc + i*6
		if binary.LittleEndian.Uint16(mem[at:]) != p[0] || binary.LittleEndian.Uint16(mem[at+2:]) != p[1] {
			return errors.New("sword boss source table")
		}
	}
	if ctx.Boss != (ctx.Index == swordBossIndex[ctx.Region]) {
		return errors.New("sword boss identity")
	}
	return nil
}
func savedSwords(raw []byte) ([8]bool, error) {
	var v [8]bool
	if len(raw) != 2987 {
		return v, errors.New("sword save size")
	}
	for i := range v {
		at := 1318 + i*4
		n := binary.LittleEndian.Uint16(raw[at:]) - uint16(at+3)
		if n > 1 {
			return v, errors.New("sword flag domain")
		}
		v[i] = n == 1
	}
	return v, nil
}
func projectSwords(raw []byte, region, index int, result uint16) ([]byte, error) {
	v, e := savedSwords(raw)
	if e != nil {
		return nil, e
	}
	if region < 0 || region > 7 || index < 0 || index >= len(guardedCoordinates[region]) || result > 3 {
		return nil, errors.New("sword result identity")
	}
	out := append([]byte{}, raw...)
	if result == 0 && uint16(index) == swordBossIndex[region] {
		v[region] = true
	}
	for i, x := range v {
		n := uint16(0)
		if x {
			n = 1
		}
		at := 1318 + i*4
		binary.LittleEndian.PutUint16(out[at:], n+uint16(at+3))
	}
	return out, nil
}
func swordNativeBinding(mem, native []byte, g *guardedBinding, returned bool) error {
	v, e := savedSwords(native)
	if e != nil {
		return e
	}
	expected := g.Context.Pieces
	if returned && g.Context.Boss {
		at := guardNPCAt(int(g.Context.Region), int(g.Context.Index))
		empty := true
		for i := 0; i < 6; i++ {
			kind, e := guardSavedWord(native, at+i*4)
			if e != nil {
				return e
			}
			if kind > 0 {
				empty = false
			}
		}
		if empty {
			expected[g.Context.Region] = true
		}
	}
	if v != expected {
		return errors.New("sword saved/source flags differ")
	}
	return nil
}
func swordEnding(b *controlledBattle) bool {
	return b.Guard != nil && b.Guard.Context.Region == 0 && b.Guard.Context.Index == 4 && b.Result == 0 && b.Settled
}
func swordApply(m *dg.Machine, b *controlledBattle) error {
	flags, e := savedSwords(b.Current.Bytes.Native)
	if e != nil {
		return e
	}
	for i, v := range flags {
		n := uint16(0)
		if v {
			n = 1
		}
		m.Write16(0x1e880+0x275a+uint32(i*2), n)
	}
	if swordEnding(b) {
		for i := 0; i < 6; i++ {
			if m.Read16(0x1e880+0x36be+uint32(i*4)) != 0 {
				return errors.New("final guard still alive")
			}
		}
		m.Write16(0x1e880+0x56e2, 1)
	}
	return nil
}
func swordState(v map[string]any, x *encounterExtra) {
	if flags, e := savedSwords(x.Port.Current.Bytes.Native); e == nil {
		v["swords"] = flags
	}
	v["ending"] = x.Engine.EndingStatus()
	v["engine_exited"] = x.Engine.Exited
	v["engine_exit_code"] = x.Engine.ExitCode
}
func initializeLayer62() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		v, err := previous(e, p)
		if err != nil {
			return nil, err
		}
		x := encounterCurrent
		swordOnCall(e.Oracle, oracle.Far(0x110, 0x20e), func(o *oracle.Oracle) {
			b := x.Bridge
			if !swordEnding(b) {
				return
			}
			if !b.Returned || o.Word(oracle.Far(0x1e88, 0x56e2)) != 1 || o.Word(oracle.Far(0x1e88, o.Regs().SP)) != 0x329f {
				panic(&worldArmyPortFault{"ending guard handoff frame"})
			}
			x.Finished = true
			x.UI = nil
			x.Presence.Active = false
			x.Presence.Prompt = false
			swordGameplayEnded = true
			x.Events = append(x.Events, map[string]any{"command": "go-final-guard-handoff", "token": b.Current.Token, "steps": o.Steps()})
		})
		return v, nil
	}
}
