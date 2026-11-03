package ownedworld

import (
	"bytes"
	"errors"
	"fmt"
	"image/png"
	"os"
	"path/filepath"
	"testing"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func actionFixture(t *testing.T, code []byte, catalog game.OwnedCombatCatalog, rows [2][6]ArmyStack) (*dg.Machine, *originalBattleActions) {
	t.Helper()
	m := dg.New()
	copy(m.Mem[0x1100:], code)
	c := m.CPU
	c.Seg[dg.CS], c.Seg[dg.DS], c.Seg[dg.SS] = 0xf67, 0x1e88, 0x1e88
	c.R[dg.SP], c.Flags = 0xef00, 0xad7
	c.R[dg.BP] = 0xee00
	m.Write16(0x1e880+0xedfc, 7)
	m.Write16(0x1e880+0xedfa, 0)
	p, err := planOriginalBattleSetup(catalog, rows)
	if err != nil {
		t.Fatal(err)
	}
	for side, base := range []uint32{0x56e8, 0x5700} {
		clear(m.Mem[0x1e880+base : 0x1e880+base+24])
		for i, s := range rows[side] {
			profile := catalog.Profiles[s.Unit]
			if profile.NativeKind != 0 {
				m.Write16(0x1e880+base+uint32(i*4), profile.NativeKind)
				m.Write16(0x1e880+base+uint32(i*4+2), uint16(s.Count))
			}
		}
	}
	for side, base := range []uint32{0x6fb6, 0x6fc2} {
		for i, raw := range p.Slots[side] {
			m.Write16(0x1e880+base+uint32(i*2), raw)
		}
	}
	override := rows[0]
	x := &originalBattleSetup{Code: code, Catalog: catalog, Override: &override, Plan: p, Phase: "ready"}
	return m, &originalBattleActions{Setup: x, Active: true}
}

func TestOriginalBattlePresenceControls(t *testing.T) {
	work, _, catalog := setupInputs(t)
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	if err != nil {
		t.Fatal(err)
	}
	code, err := worldArmyCode(pam)
	if err != nil {
		t.Fatal(err)
	}
	reports := []map[string]any{}
	for _, site := range originalBattlePresenceSites {
		for _, count := range []uint32{0, 1, 30, 32768, 65535} {
			var rows [2][6]ArmyStack
			if count != 0 {
				rows[site.Side][0] = ArmyStack{"native:01", count}
			}
			m, x := actionFixture(t, code, catalog, rows)
			m.CPU.IP = uint16(site.IDA - 0x1e570)
			before := bytes.Clone(m.Mem)
			if err := m.Step(); err != nil {
				t.Fatal(err)
			}
			flags, ip := m.CPU.Flags, m.CPU.IP
			m, x = actionFixture(t, code, catalog, rows)
			m.CPU.IP = uint16(site.IDA - 0x1e570)
			if handled, er := x.presence(m, site); er != nil || !handled {
				t.Fatal(er)
			}
			if m.CPU.Flags != flags || m.CPU.IP != ip || !bytes.Equal(before, m.Mem) {
				t.Fatal("native/Go comparison", site, count)
			}
			reports = append(reports, map[string]any{"ida": site.IDA, "side": site.Side, "count": count, "flags": flags, "next_ip": ip})
		}
	}
	extended := []map[string]any{}
	for _, id := range openKBArtIDs {
		for _, site := range originalBattlePresenceSites {
			rows := [2][6]ArmyStack{}
			rows[site.Side][0] = ArmyStack{id, 4294967295}
			m, x := actionFixture(t, code, catalog, rows)
			if site.Side == 1 {
				x.Setup.Override = nil // Enemy expanded rows are not admitted by the initial setup contract.
				continue
			}
			m.CPU.IP = uint16(site.IDA - 0x1e570)
			before := bytes.Clone(m.Mem)
			if _, er := x.presence(m, site); er != nil {
				t.Fatal(er)
			}
			if m.CPU.Flags&0x40 != 0 || x.ExtendedReads != 1 || !bytes.Equal(before, m.Mem) {
				t.Fatal("extension comparison", id)
			}
			extended = append(extended, map[string]any{"id": id, "ida": site.IDA, "count": uint32(4294967295)})
		}
	}
	refusals := []string{"source", "segment", "phase", "raw", "unaligned", "slot-map", "native-projection", "inactive", "target-held", "cycles"}
	for _, name := range refusals {
		rows := [2][6]ArmyStack{{{"openkb:wolf", 2}}}
		m, x := actionFixture(t, code, catalog, rows)
		site := originalBattlePresenceSites[1]
		m.CPU.IP = uint16(site.IDA - 0x1e570)
		switch name {
		case "source":
			m.Mem[0x1100+site.Start-0x10000] ^= 1
		case "segment":
			m.CPU.Seg[dg.DS]++
		case "phase":
			x.Setup.Phase = "formation"
		case "raw":
			m.CPU.R[dg.BX] = 24
		case "unaligned":
			m.CPU.R[dg.BX] = 1
		case "slot-map":
			m.Write16(0x1e880+0x6fb6, 7)
		case "native-projection":
			m.Write16(0x1e880+0x56e8, 1)
		case "inactive":
			x.Active = false
		case "target-held":
			x.Target = &originalEnemyTarget{}
		case "cycles":
			m.CPU.Cycles = ^uint64(0)
		}
		before := bytes.Clone(m.Mem)
		regs, flags, cycles, ip := m.CPU.R, m.CPU.Flags, m.CPU.Cycles, m.CPU.IP
		if _, er := x.presence(m, site); er == nil {
			t.Fatal("unsafe comparison admitted", name)
		}
		if !bytes.Equal(before, m.Mem) || regs != m.CPU.R || flags != m.CPU.Flags || cycles != m.CPU.Cycles || ip != m.CPU.IP || x.Comparisons != 0 {
			t.Fatal("refusal mutated state", name)
		}
	}
	aliases := []originalBattleAlias{}
	for _, value := range []uint16{0, 1} {
		makeAlias := func() (*dg.Machine, *originalBattleActions) {
			m, x := actionFixture(t, code, catalog, [2][6]ArmyStack{{{"openkb:wolf", 2}}, {{"native:06", 10}}})
			m.CPU.IP = 0x17d4
			m.CPU.R[dg.BX] = 0x9d94
			m.Write16(0x1e880+0xedfc, 0)
			m.Write16(0x1e880+0x6fa8, 0x2765)
			m.Write16(0x1e880+0xf47e, value)
			return m, x
		}
		m, _ := makeAlias()
		before := bytes.Clone(m.Mem)
		if er := m.Step(); er != nil {
			t.Fatal(er)
		}
		flags, ip := m.CPU.Flags, m.CPU.IP
		m, x := makeAlias()
		if _, er := x.presence(m, originalBattlePresenceSites[9]); er != nil {
			t.Fatal(er)
		}
		if flags != m.CPU.Flags || ip != m.CPU.IP || len(x.AliasReads) != 1 || !bytes.Equal(before, m.Mem) {
			t.Fatal("transient target alias differs")
		}
		aliases = append(aliases, x.AliasReads[0])
	}
	setupWrite(t, filepath.Join(work, "presence-controls.json"), map[string]any{"status": "passed-original-battle-presence-controls", "native_pairs": reports, "extension_reads": extended, "refusals": refusals, "original_RAM_unchanged": true, "transient_alias_pairs": aliases})
}

func TestOriginalBattlePresenceGuards(t *testing.T) {
	work, _, catalog := setupInputs(t)
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	if err != nil {
		t.Fatal(err)
	}
	code, err := worldArmyCode(pam)
	if err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"empty", "unknown", "zero", "duplicate", "native-wide"} {
		rows := [6]ArmyStack{{"openkb:wolf", 4294967295}}
		switch name {
		case "empty":
			rows = [6]ArmyStack{}
		case "unknown":
			rows[0].Unit = "openkb:missing"
		case "zero":
			rows[0].Count = 0
		case "duplicate":
			rows[1] = rows[0]
		case "native-wide":
			rows[0] = ArmyStack{"native:01", 32768}
		}
		if _, er := originalHeldProjectionBytes(rows, catalog); er == nil {
			t.Fatal("unsafe held projection", name)
		}
	}
	rows := [2][6]ArmyStack{{{"openkb:wolf", 2}}, {{"native:06", 10}}}
	for _, name := range []string{"caller", "source-slot", "target-slot", "phase", "source-bytes", "stack"} {
		m, x := actionFixture(t, code, catalog, rows)
		m.CPU.IP = 0x484c
		for i, v := range []uint16{0x1818, 0xf67, 0, 0} {
			m.Write16(0x1e880+0xef00+uint32(i*2), v)
		}
		switch name {
		case "caller":
			m.Write16(0x1e880+0xef00, 0x1718)
		case "source-slot":
			m.Write16(0x1e880+0xef04, 6)
		case "target-slot":
			m.Write16(0x1e880+0xef06, 6)
		case "phase":
			x.Active = false
		case "source-bytes":
			m.Mem[0xf670+0x484c] ^= 1
		case "stack":
			m.CPU.R[dg.SP] = 65528
		}
		before := bytes.Clone(m.Mem)
		regs, flags, cycles, ip := m.CPU.R, m.CPU.Flags, m.CPU.Cycles, m.CPU.IP
		if _, er := x.hold(m, 0x484c); er == nil || errors.Is(er, errOriginalBattleTargetHeld) {
			t.Fatal("unsafe target gate", name)
		}
		if !bytes.Equal(before, m.Mem) || regs != m.CPU.R || flags != m.CPU.Flags || cycles != m.CPU.Cycles || ip != m.CPU.IP || x.Target != nil {
			t.Fatal("target refusal mutated state", name)
		}
	}
	m, _ := actionFixture(t, code, catalog, rows)
	raw, err := originalHeldProjectionBytes(rows[0], catalog)
	if err != nil {
		t.Fatal(err)
	}
	x := &originalArmyProjection{Code: code, Catalog: catalog, Input: rows[0], Encoded: raw, HeldPreview: true, Phase: "projected", EntrySP: 0xef00, EntryBP: 0xf100, Shadow: bytes.Clone(m.Mem[0x1e880+0x54a : 0x1e880+0x562])}
	c := m.CPU
	c.Seg[dg.CS] = 0x110
	c.IP = 0x3745
	c.R[dg.BP] = 0xeefe
	c.R[dg.SP] = 0xeeec
	m.Write16(0x1e880+0xeefe, 0xf100)
	m.Write16(0x1e880+0xef00, 0x171d)
	m.Write16(0x1e880+0xef02, 0x110)
	before := bytes.Clone(m.Mem)
	regs, cycles, ip := c.R, c.Cycles, c.IP
	if _, er := x.execute(m, 0x3745); er == nil {
		t.Fatal("held projection committed")
	}
	if !bytes.Equal(before, m.Mem) || regs != c.R || cycles != c.Cycles || ip != c.IP || x.Captures != 0 || x.Phase != "projected" {
		t.Fatal("held capture refusal mutated state")
	}
	setupWrite(t, filepath.Join(work, "presence-guards.json"), map[string]any{"status": "passed-original-battle-presence-guards", "held_model_refusals": 5, "target_gate_refusals": 6, "held_capture_refusal": true, "state_unchanged": true})
}

func TestOriginalBattlePresenceCold(t *testing.T) {
	work, root, catalog := setupInputs(t)
	assets := os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if assets == "" {
		t.Skip("HD assets")
	}
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	folder := filepath.Join(work, "cold-r1")
	must(os.Mkdir(folder, 0700))
	reports := []map[string]any{}
	for _, hd := range []bool{false, true} {
		var refFrame, refUnits []byte
		var refSeed uint32
		var refTarget originalEnemyTarget
		for mode := 0; mode < 2; mode++ {
			dir := filepath.Join(folder, fmt.Sprintf("hd-%v-mode-%d", hd, mode))
			must(os.Mkdir(dir, 0700))
			e := setupCold(t, root, assets, dir, hd)
			x, err := installOriginalBattleSetup(e, catalog, nil)
			must(err)
			a, err := installOriginalBattleActions(e, x, mode == 1)
			must(err)
			err = setupEncounter(t, e, true)
			if !errors.Is(err, errOriginalBattleTargetHeld) || a.Target == nil {
				t.Fatal("enemy target not held", err)
			}
			im := e.Frame()
			units := e.Oracle.Bytes(oracle.Far(0x1e88, 0x56e8), 48)
			seed := originalSeed(e.Oracle)
			if mode == 0 {
				refFrame, refUnits, refSeed, refTarget = bytes.Clone(im.Pix), bytes.Clone(units), seed, *a.Target
			} else if !bytes.Equal(im.Pix, refFrame) || !bytes.Equal(units, refUnits) || seed != refSeed || *a.Target != refTarget || a.Comparisons == 0 {
				t.Fatal("original/Go cold selection differs", hd)
			}
			f, err := os.Create(filepath.Join(dir, "frame.png"))
			must(err)
			must(png.Encode(f, im))
			must(f.Close())
			must(e.Oracle.SaveStateFile(filepath.Join(dir, "held.state")))
			reports = append(reports, map[string]any{"hd": hd, "mode": mode, "target": a.Target, "comparisons": a.Comparisons, "sites": a.Sites, "units_hex": fmt.Sprintf("%x", units), "frame_rgba_sha256": contentSHA(im.Pix), "seed_after": seed, "transient_alias_reads": a.AliasReads})
			e.Close()
		}
	}
	setupWrite(t, filepath.Join(work, "cold-receipt.json"), map[string]any{"status": "passed-original-battle-presence-cold", "rows": reports, "normal_cold_start": true, "snapshot_loaded": false, "seed": uint32(0x12345678), "scope": "native army first enemy selection only; attack held"})
}

func TestOriginalBattlePresenceExpanded(t *testing.T) {
	work, root, catalog := setupInputs(t)
	assets := os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if assets == "" {
		t.Skip("HD assets")
	}
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	folder := filepath.Join(work, "expanded-r1")
	must(os.Mkdir(folder, 0700))
	reports := []map[string]any{}
	for i, player := range [][6]ArmyStack{{{"openkb:wolf", 2}, {"native:01", 30}}, {{"openkb:pike", 3}, {"openkb:arcr", 2}, {"openkb:wolf", 2}}} {
		dir := filepath.Join(folder, fmt.Sprint(i))
		must(os.Mkdir(dir, 0700))
		e := setupCold(t, root, assets, dir, true)
		shadow := e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)
		projection, err := installOriginalArmyProjectionMode(e, catalog, player, true)
		must(err)
		x, err := installOriginalBattleSetup(e, catalog, &player)
		must(err)
		a, err := installOriginalBattleActions(e, x, true)
		must(err)
		// Isolate enemy targeting without admitting an unimplemented player
		// half-turn. This controlled original argument is never a player option.
		firstSideSet := false
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x2076), func(m *dg.Machine) (bool, error) {
			if er := a.check(m, 0x2076, 0x205e6, 0x20689); er != nil {
				return false, er
			}
			sp := uint32(m.CPU.R[dg.SP])
			if !a.Active || sp > 65529 || m.Read16(0x1e880+sp) != 0x3c || m.Read16(0x1e880+sp+2) != 0xf67 {
				return false, errors.New("controlled enemy-first caller")
			}
			if !firstSideSet {
				if m.Read16(0x1e880+sp+4) != 0 {
					return false, errors.New("controlled first-side input")
				}
				m.Write16(0x1e880+sp+4, 1)
				firstSideSet = true
			}
			return false, nil
		})
		err = setupEncounter(t, e, true)
		if !errors.Is(err, errOriginalBattleTargetHeld) || !firstSideSet || a.Target == nil || catalog.Profiles[a.Target.Target.Unit].NativeKind != 0 || a.ExtendedReads == 0 || projection.Phase != "projected" || projection.Captures != 0 {
			t.Fatal("expanded target not selected", err, a.Target, a.ExtendedReads)
		}
		mem := e.Oracle.Bytes(oracle.Far(0, 0), 1<<20)
		cycles := e.Oracle.Cycles()
		target := *a.Target
		comparisons := a.Comparisons
		seed := originalSeed(e.Oracle)
		for j := 0; j < 5; j++ {
			if er := e.AdvanceCycles(100000); !errors.Is(er, errOriginalBattleTargetHeld) {
				t.Fatal("target gate escaped", er)
			}
		}
		if cycles != e.Oracle.Cycles() || !bytes.Equal(mem, e.Oracle.Bytes(oracle.Far(0, 0), 1<<20)) || *a.Target != target || comparisons != a.Comparisons || seed != originalSeed(e.Oracle) || !bytes.Equal(shadow, e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
			t.Fatal("held selection mutated state")
		}
		raw, err := os.ReadFile(filepath.Join(work, "inputs/army-catalog.json"))
		must(err)
		art := loadHDUnitArtwork(e, filepath.Join(work, "ui-assets"), contentSHA(raw))
		if len(art.Failures) > 0 {
			t.Fatal(art.Failures)
		}
		for _, name := range []string{"source", "frame"} {
			im := e.Frame()
			if name == "frame" {
				im, err = composeOriginalBattleSetup(e, x, art)
				must(err)
			}
			f, er := os.Create(filepath.Join(dir, name+".png"))
			must(er)
			must(png.Encode(f, im))
			must(f.Close())
		}
		must(e.Oracle.SaveStateFile(filepath.Join(dir, "held.state")))
		reports = append(reports, map[string]any{"case": i, "plan": x.Plan, "target": a.Target, "comparisons": a.Comparisons, "extended_reads": a.ExtendedReads, "sites": a.Sites, "native_rows_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x56e8), 48)), "shadow_hex": fmt.Sprintf("%x", shadow), "seed_after": seed, "held_retries": 5, "projection_captures": projection.Captures, "controlled_typed_override": true, "controlled_enemy_first_argument": true, "transient_alias_reads": a.AliasReads})
		e.Close()
	}
	setupWrite(t, filepath.Join(work, "expanded-receipt.json"), map[string]any{"status": "passed-original-battle-presence-expanded", "rows": reports, "playable": false, "actual_window_verified": false, "scope": "original HD enemy selection reaches expanded targets; held before damage"})
}
