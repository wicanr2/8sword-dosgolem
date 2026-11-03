package ownedworld

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

// Spec030 READY: bounded native-kind projection into the original battlefield.
// Expanded IDs remain outside this adapter; ordinary player startup is disabled.
type originalArmyProjection struct {
	Rounds                    *originalBattleRounds
	Code                      []byte
	Catalog                   game.OwnedCombatCatalog
	Input, Remaining          [6]ArmyStack
	Encoded                   [24]byte
	Shadow                    []byte
	Phase                     string
	EntrySP, EntryBP, Result  uint16
	Entries, Copies, Captures uint64
	HeldPreview               bool
}

// Expanded identities have no native representation. This opt-in encoder is
// restricted to held battle research, whose result path must never commit.
func originalHeldProjectionBytes(rows [6]ArmyStack, catalog game.OwnedCombatCatalog) ([24]byte, error) {
	var raw [24]byte
	if err := catalog.Validate(); err != nil {
		return raw, err
	}
	seen := map[string]bool{}
	for i, s := range rows {
		if s.Unit == "" && s.Count == 0 {
			continue
		}
		p, ok := catalog.Profiles[s.Unit]
		if !ok || s.Count == 0 || seen[s.Unit] {
			return raw, errors.New("held projection identity/count")
		}
		seen[s.Unit] = true
		if p.NativeKind == 0 {
			if !originalOpenKBID(s.Unit) {
				return raw, errors.New("held projection extension")
			}
			continue
		}
		if s.Unit != fmt.Sprintf("native:%02d", p.NativeKind) || p.NativeKind > 25 || s.Count > 32767 {
			return raw, errors.New("held projection native bounds")
		}
		binary.LittleEndian.PutUint16(raw[i*4:], p.NativeKind)
		binary.LittleEndian.PutUint16(raw[i*4+2:], uint16(s.Count))
	}
	if len(seen) == 0 {
		return raw, errors.New("held projection empty army")
	}
	return raw, nil
}

func originalArmyProjectionBytes(rows [6]ArmyStack, catalog game.OwnedCombatCatalog) ([24]byte, error) {
	var raw [24]byte
	if err := catalog.Validate(); err != nil {
		return raw, err
	}
	seen := map[string]bool{}
	alive := false
	for i, s := range rows {
		if s.Unit == "" && s.Count == 0 {
			continue
		}
		p, ok := catalog.Profiles[s.Unit]
		if !ok || p.NativeKind < 1 || p.NativeKind > 25 || s.Unit != fmt.Sprintf("native:%02d", p.NativeKind) || s.Count == 0 || s.Count > 32767 || seen[s.Unit] {
			return [24]byte{}, errors.New("original battle projection: native identity/count/duplicate")
		}
		binary.LittleEndian.PutUint16(raw[i*4:], p.NativeKind)
		binary.LittleEndian.PutUint16(raw[i*4+2:], uint16(s.Count))
		alive, seen[s.Unit] = true, true
	}
	if !alive {
		return [24]byte{}, errors.New("original battle projection: no army")
	}
	return raw, nil
}

func (x *originalArmyProjection) capture(raw []byte) ([6]ArmyStack, error) {
	var rows [6]ArmyStack
	if len(raw) != 24 {
		return rows, errors.New("original battle result shape")
	}
	before := map[string]uint32{}
	for _, s := range x.Input {
		if s.Unit != "" {
			before[s.Unit] = s.Count
		}
	}
	seen := map[string]bool{}
	empty := false
	for i := range rows {
		kind, count := binary.LittleEndian.Uint16(raw[i*4:]), binary.LittleEndian.Uint16(raw[i*4+2:])
		if kind == 0 && count == 0 {
			empty = true
			continue
		}
		id := fmt.Sprintf("native:%02d", kind)
		if empty || kind < 1 || kind > 25 || count == 0 || uint32(count) > before[id] || seen[id] {
			return [6]ArmyStack{}, errors.New("original battle result identity/count/compaction")
		}
		seen[id] = true
		rows[i] = ArmyStack{id, uint32(count)}
	}
	return rows, nil
}

func (x *originalArmyProjection) execute(m *dg.Machine, ip uint16) (bool, error) {
	fail := func(s string) (bool, error) { return false, &worldArmyPortFault{"original army projection: " + s} }
	c := m.CPU
	ds := uint32(0x1e880)
	if c.IP != ip || c.Seg[dg.CS] != 0x110 || c.Seg[dg.DS] != 0x1e88 || c.Seg[dg.SS] != 0x1e88 || c.Cycles == ^uint64(0) || len(x.Code) < 0x380b {
		return fail("site/segments/source shape")
	}
	if !bytes.Equal(x.Code[0x32e0:0x380b], m.Mem[0x1100+0x32e0:0x1100+0x380b]) {
		return fail("wrapper/cleanup bytes")
	}
	encoded, err := originalArmyProjectionBytes(x.Input, x.Catalog)
	if x.HeldPreview {
		encoded, err = originalHeldProjectionBytes(x.Input, x.Catalog)
	}
	if err != nil || encoded != x.Encoded {
		return fail("typed army changed")
	}
	sp, bp := c.R[dg.SP], c.R[dg.BP]
	if ip == 0x32e0 {
		if x.Phase != "" || sp < 32 || sp > 65530 || bp > 65528 || m.Read16(ds+uint32(sp)) != 0x171d || m.Read16(ds+uint32(sp)+2) != 0x110 || m.Read16(ds+uint32(bp)+2) != 0xbd3 || m.Read16(ds+uint32(bp)+4) != 0x110 {
			return fail("entry phase/caller")
		}
		x.EntrySP, x.EntryBP = sp, bp
		x.Shadow = bytes.Clone(m.Mem[ds+0x54a : ds+0x562])
		x.Phase = "entered"
		x.Entries++
		return false, nil // Original prologue, terrain and enemy generation continue.
	}
	if bp != x.EntrySP-2 || sp != bp-0x12 || m.Read16(ds+uint32(bp)) != x.EntryBP || m.Read16(ds+uint32(bp)+2) != 0x171d || m.Read16(ds+uint32(bp)+4) != 0x110 || !bytes.Equal(x.Shadow, m.Mem[ds+0x54a:ds+0x562]) {
		return fail("frame/shadow")
	}
	switch ip {
	case 0x3365:
		if x.Phase != "entered" || x.Copies != 0 {
			return fail("copy phase")
		}
		copy(m.Mem[ds+0x56e8:ds+0x5700], x.Encoded[:])
		clear(m.Mem[ds+0x5700 : ds+0x5718])
		c.IP = 0x3396
		x.Phase = "projected"
		x.Copies++
	case 0x3745:
		if x.HeldPreview && (x.Rounds == nil || !x.Rounds.Done || !x.Rounds.Released) {
			return fail("held preview cannot capture or commit")
		}
		if x.Phase != "projected" || x.Captures != 0 {
			return fail("capture phase")
		}
		rows, err := x.capture(m.Mem[ds+0x56e8 : ds+0x5700])
		if x.HeldPreview {
			rows, err = x.captureRounds()
		}
		if err != nil {
			return fail(err.Error())
		}
		result := m.Read16(ds + uint32(bp) - 0xe)
		if result > 2 {
			return fail("unsupported result")
		}
		x.Remaining, x.Result = rows, result
		c.IP = 0x376a
		x.Phase = "captured"
		x.Captures++
	default:
		return fail("unknown gate")
	}
	c.Cycles++
	return true, nil
}

func (x *originalArmyProjection) captureRounds() ([6]ArmyStack, error) {
	var rows [6]ArmyStack
	if x.Rounds == nil || !x.Rounds.Done || !x.Rounds.Released {
		return rows, errors.New("Go battle result unbound")
	}
	before := map[string]uint32{}
	for _, s := range x.Input {
		if s.Unit != "" {
			before[s.Unit] = s.Count
		}
	}
	seen := map[string]bool{}
	at := 0
	for _, s := range x.Rounds.Rows[0] {
		if s.Count == 0 {
			continue
		}
		if s.Unit == "" || s.Count > before[s.Unit] || seen[s.Unit] || at >= 6 {
			return rows, errors.New("Go battle result identity/count")
		}
		rows[at] = s
		at++
		seen[s.Unit] = true
	}
	return rows, nil
}

func installOriginalArmyProjection(e *game.Engine, catalog game.OwnedCombatCatalog, rows [6]ArmyStack) (*originalArmyProjection, error) {
	return installOriginalArmyProjectionMode(e, catalog, rows, false)
}

func installOriginalArmyProjectionMode(e *game.Engine, catalog game.OwnedCombatCatalog, rows [6]ArmyStack, heldPreview bool) (*originalArmyProjection, error) {
	if !e.PAMLoaded || e.BattleRulesMode() != "native" {
		return nil, errors.New("original army projection requires loaded PAM/native rules")
	}
	raw, err := originalArmyProjectionBytes(rows, catalog)
	if heldPreview {
		raw, err = originalHeldProjectionBytes(rows, catalog)
	}
	if err != nil {
		return nil, err
	}
	code, err := worldArmyCode(e.PAM)
	if err != nil {
		return nil, err
	}
	x := &originalArmyProjection{Code: code, Catalog: catalog, Input: rows, Encoded: raw, HeldPreview: heldPreview}
	for _, ip := range []uint16{0x32e0, 0x3365, 0x3745} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0x110, ip), func(m *dg.Machine) (bool, error) { return x.execute(m, ip) })
	}
	for _, ip := range []uint16{0x3371, 0x3379, 0x3755, 0x375d} {
		ip := ip
		swordOnCall(e.Oracle, oracle.Far(0x110, ip), func(*oracle.Oracle) {
			panic(&worldArmyPortFault{fmt.Sprintf("native army copy escaped at 0110:%04X", ip)})
		})
	}
	return x, nil
}
