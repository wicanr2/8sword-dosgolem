package ownedworld

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"image"
	"image/draw"
	"image/png"
	"os"
	"path/filepath"
	"strings"
	"testing"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func TestOriginalBattleSetupRawArt(t *testing.T) {
	work, _, _ := setupInputs(t)
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	folder := filepath.Join(work, "raw-art-r1")
	must(os.Mkdir(folder, 0700))
	raw, err := os.ReadFile(filepath.Join(work, "ui-assets/unit-art.json"))
	must(err)
	var pack unitArtPack
	must(pairStrictJSON(raw, &pack))
	rows := []map[string]any{}
	for _, r := range pack.Rows {
		b, er := os.ReadFile(filepath.Join(work, "ui-assets", r.File))
		must(er)
		if contentSHA(b) != r.SHA {
			t.Fatal("raw source SHA")
		}
		im, er := png.Decode(bytes.NewReader(b))
		must(er)
		dst := image.NewRGBA(im.Bounds())
		draw.Draw(dst, dst.Bounds(), im, im.Bounds().Min, draw.Src)
		name := strings.ReplaceAll(r.ID, ":", "-") + ".rgba"
		must(os.WriteFile(filepath.Join(folder, name), dst.Pix, 0600))
		rows = append(rows, map[string]any{"id": r.ID, "file": name, "source_file": r.File, "source_sha256": r.SHA, "rgba_sha256": contentSHA(dst.Pix), "size": []int{dst.Rect.Dx(), dst.Rect.Dy()}})
	}
	setupWrite(t, filepath.Join(folder, "receipt.json"), map[string]any{"status": "decoded-raw-art-with-standard-image-libraries", "rows": rows, "game_renderer_used": false})
}

func TestOriginalBattleSetupRefusals(t *testing.T) {
	work, _, catalog := setupInputs(t)
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	must(err)
	code, err := worldArmyCode(pam)
	must(err)
	names := []string{"source", "caller", "segment", "stack", "cycles", "kind", "count", "phase", "HP-factor", "HP-before-formation", "HP-row-change", "extension-shadow"}
	for _, name := range names {
		m := dg.New()
		copy(m.Mem[0x1100:], code)
		c := m.CPU
		c.Seg[dg.CS] = 0xf67
		c.Seg[dg.DS] = 0x1e88
		c.Seg[dg.SS] = 0x1e88
		c.R[dg.SP] = 0xef00
		c.IP = 0x1daa
		m.Write16(0x1e880+0xef00, 0x1b)
		m.Write16(0x1e880+0xef02, 0xf67)
		clear(m.Mem[0x23f68:0x23f98])
		m.Write16(0x23f68, 1)
		m.Write16(0x23f6a, 30)
		m.Write16(0x1e880+0x70d4, uint16(catalog.Profiles["native:01"].HP))
		x := &originalBattleSetup{Code: code, Catalog: catalog}
		ip := uint16(0x1daa)
		switch name {
		case "source":
			m.Mem[0xf670+int(ip)] ^= 1
		case "caller":
			m.Write16(0x1e880+0xef00, 0x1234)
		case "segment":
			c.Seg[dg.DS]++
		case "stack":
			c.R[dg.SP] = 65532
		case "cycles":
			c.Cycles = ^uint64(0)
		case "kind":
			m.Write16(0x23f68, 26)
		case "count":
			m.Write16(0x23f6a, 0)
		case "phase":
			x.Phase = "ready"
		case "HP-factor":
			m.Write16(0x1e880+0x70d4, 26)
		case "extension-shadow":
			override := [6]ArmyStack{{"openkb:wolf", 2}}
			x.Override = &override
		case "HP-before-formation", "HP-row-change":
			ip = 0x14ba
			c.IP = ip
			m.Write16(0x1e880+0xef00, 0x35)
			if name == "HP-row-change" {
				rows, er := x.rows(m)
				must(er)
				x.Plan, err = planOriginalBattleSetup(catalog, rows)
				must(err)
				x.Phase = "formation"
				m.Write16(0x23f6a, 31)
			}
		}
		before := bytes.Clone(m.Mem)
		regs, at, cycles := c.R, c.IP, c.Cycles
		phase := x.Phase
		if _, er := x.execute(m, ip); er == nil {
			t.Fatal("unsafe setup admitted", name)
		}
		if !bytes.Equal(before, m.Mem) || regs != c.R || at != c.IP || cycles != c.Cycles || phase != x.Phase {
			t.Fatal("refusal mutated state", name)
		}
	}
	setupWrite(t, filepath.Join(work, "refusals-r1.json"), map[string]any{"status": "passed-original-battle-setup-refusals", "cases": names, "state_unchanged": true})
}

func setupWrite(t *testing.T, path string, v any) {
	t.Helper()
	b, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(path, append(b, '\n'), 0600); err != nil {
		t.Fatal(err)
	}
}
func setupInputs(t *testing.T) (string, string, game.OwnedCombatCatalog) {
	t.Helper()
	return originalBattleInputs(t)
}
func setupData(o *oracle.Oracle) []byte {
	var b []byte
	for _, p := range []struct {
		at uint16
		n  int
	}{{0x6fb6, 24}, {0x8cb4, 6}, {0x8e6e, 6}, {0x8ca4, 12}, {0x8e60, 12}} {
		b = append(b, o.Bytes(oracle.Far(0x1e88, p.at), p.n)...)
	}
	return b
}

func TestOriginalBattleSetupControls(t *testing.T) {
	work, root, catalog := setupInputs(t)
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	folder := filepath.Join(work, "controls-r1")
	must(os.Mkdir(folder, 0700))
	reports := []map[string]any{}
	cases := [][6]ArmyStack{{}, {{"native:01", 30}}, {{"native:03", 7}, {"native:10", 2}, {"native:01", 9}, {"native:12", 3}, {"native:24", 2}}, {{}, {"native:24", 4}, {}, {"native:06", 11}}, {{"native:01", 2}, {"native:03", 3}, {"native:10", 1}, {"native:12", 1}, {"native:24", 4}, {"native:06", 7}}, {{"native:25", 4000}, {"native:10", 3000}}}
	for n, player := range cases {
		rows := [2][6]ArmyStack{player, cases[len(cases)-1-n]}
		plan, err := planOriginalBattleSetup(catalog, rows)
		must(err)
		for _, ip := range []uint16{0x1daa, 0x14ba} {
			var reference []byte
			for mode := 0; mode < 2; mode++ {
				dir := filepath.Join(folder, fmt.Sprintf("%d-%04x-%d", n, ip, mode))
				must(os.Mkdir(dir, 0700))
				e, err := game.Open(game.Options{Root: root, Saves: filepath.Join(dir, "scratch")})
				must(err)
				must(e.Oracle.LoadStateFile(filepath.Join(work, "inputs/start.state")))
				writeOriginalSeed(e.Oracle, 0x12345678)
				code, err := worldArmyCode(e.PAM)
				must(err)
				x := &originalBattleSetup{Code: code, Catalog: catalog}
				if ip == 0x14ba {
					x.Plan = plan
					x.Phase = "formation"
				}
				ret := uint16(0x1b)
				if ip == 0x14ba {
					ret = 0x35
				}
				set := false
				entry := e.Oracle.IP()
				swordOnHostInstruction(e.Oracle, entry, func(m *dg.Machine) (bool, error) {
					if set {
						return false, errors.New("setup fixture repeated")
					}
					set = true
					c := m.CPU
					c.Seg[dg.CS] = 0xf67
					c.Seg[dg.DS] = 0x1e88
					c.Seg[dg.SS] = 0x1e88
					c.R[dg.SP] = 0xef00
					c.IP = ip
					m.Write16(0x1e880+0xef00, ret)
					m.Write16(0x1e880+0xef02, 0xf67)
					for side, base := range []uint32{0x56e8, 0x5700} {
						clear(m.Mem[0x1e880+base : 0x1e880+base+24])
						for i, s := range rows[side] {
							if s.Unit != "" {
								m.Write16(0x1e880+base+uint32(i*4), catalog.Profiles[s.Unit].NativeKind)
								m.Write16(0x1e880+base+uint32(i*4+2), uint16(s.Count))
							}
						}
					}
					c.Cycles++
					return true, nil
				})
				if mode == 1 {
					swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return x.execute(m, ip) })
				}
				must(e.Oracle.RunUntil(oracle.NewCond("setup helper returned", func(o *oracle.Oracle) bool {
					r := o.Regs()
					return set && r.CS == 0xf67 && r.IP == ret && r.SP == 0xef04
				}), oracle.Budget(20000)))
				data := setupData(e.Oracle)
				if mode == 0 {
					reference = bytes.Clone(data)
				} else if !bytes.Equal(reference, data) {
					t.Fatal("original/Go setup differs", n, ip, fmt.Sprintf("%x", reference), fmt.Sprintf("%x", data))
				}
				if originalSeed(e.Oracle) != 0x12345678 {
					t.Fatal("setup changed RNG")
				}
				must(e.Oracle.SaveStateFile(filepath.Join(dir, "after.state")))
				e.Close()
			}
			reports = append(reports, map[string]any{"case": n, "ip": ip, "rows": rows, "plan": plan, "native_and_go_hex": fmt.Sprintf("%x", reference)})
		}
	}
	extensions := []map[string]any{}
	for _, id := range openKBArtIDs {
		rows := [2][6]ArmyStack{{{id, 4294967295}}}
		p, err := planOriginalBattleSetup(catalog, rows)
		must(err)
		if p.HP[0][0] != catalog.Profiles[id].HP*4294967295 || p.NativeHP[0][0] != 0 || !p.Extended {
			t.Fatal("extension HP escaped into original word")
		}
		extensions = append(extensions, map[string]any{"id": id, "plan": p})
	}
	for _, name := range []string{"unknown", "zero", "duplicate"} {
		rows := [2][6]ArmyStack{{{"native:01", 1}}}
		switch name {
		case "unknown":
			rows[0][0].Unit = "openkb:missing"
		case "zero":
			rows[0][0].Count = 0
		case "duplicate":
			rows[0][1] = rows[0][0]
		}
		if _, err := planOriginalBattleSetup(catalog, rows); err == nil {
			t.Fatal("unsafe setup model", name)
		}
	}
	setupWrite(t, filepath.Join(folder, "receipt.json"), map[string]any{"status": "passed-original-battle-setup-controls", "helper_pairs": reports, "extension_models": extensions, "model_refusals": []string{"unknown", "zero", "duplicate"}, "seed": uint32(0x12345678)})
}

func setupCold(t *testing.T, root, assets, dir string, hd bool) *game.Engine {
	t.Helper()
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	e, err := game.Open(game.Options{Root: root, Assets: assets, Saves: filepath.Join(dir, "scratch"), HD: hd})
	must(err)
	e.Oracle.SetClock(12, 0, 0, 0)
	e.EnableLiveClock(3000)
	ready, mapped := false, false
	e.Oracle.OnCall(oracle.Far(0x110, 0x55a), func(*oracle.Oracle) { ready = e.PAMLoaded })
	e.Oracle.OnCall(oracle.Far(0x110, 0xb62), func(*oracle.Oracle) { mapped = e.PAMLoaded })
	setupAdvance(t, e, 1000)
	setupPress(t, e, 2)
	setupPress(t, e, 2)
	setupAdvance(t, e, 1000)
	setupPress(t, e, 1)
	for n := 0; !ready && n < 2000; n++ {
		setupAdvance(t, e, 10)
	}
	if !ready {
		t.Fatal("setup cold menu")
	}
	setupPress(t, e, 0x1c)
	for n := 0; !mapped && n < 2000; n++ {
		setupAdvance(t, e, 10)
	}
	if !mapped {
		t.Fatal("setup Continue map")
	}
	writeOriginalSeed(e.Oracle, 0x12345678)
	return e
}
func setupAdvance(t *testing.T, e *game.Engine, ms int) {
	t.Helper()
	for n := 0; n < ms; n += 10 {
		if err := e.AdvanceCycles(30000); err != nil {
			t.Fatal(err)
		}
		e.RenderAudio()
	}
}
func setupPress(t *testing.T, e *game.Engine, key byte) {
	t.Helper()
	if err := e.Key(key, true); err != nil {
		t.Fatal(err)
	}
	setupAdvance(t, e, 100)
	if err := e.Key(key, false); err != nil {
		t.Fatal(err)
	}
	setupAdvance(t, e, 300)
}
func setupEncounter(t *testing.T, e *game.Engine, preview bool) error {
	t.Helper()
	prompt := false
	e.Oracle.OnCall(oracle.Far(0x110, 0x16e0), func(*oracle.Oracle) {
		if e.PAMLoaded {
			prompt = true
		}
	})
	setupPress(t, e, 0x50)
	setupPress(t, e, 0x50)
	for n := 0; !prompt && n < 128; n++ {
		k := byte(0x4d)
		if n%2 != 0 {
			k = 0x4b
		}
		setupPress(t, e, k)
	}
	if !prompt {
		t.Fatal("setup encounter prompt")
	}
	setupAdvance(t, e, 500)
	im := e.Frame()
	red := 0
	for y := 798; y < 888; y++ {
		for x := 624; x < 720; x++ {
			c := im.RGBAAt(x, y)
			if c.R > 180 && c.G < 120 && c.B < 130 {
				red++
			}
		}
	}
	if red > 1000 {
		setupPress(t, e, 0x4b)
	}
	entered := false
	var ret oracle.Regs
	stop := errors.New("setup first action returned")
	if !preview {
		e.Oracle.OnCall(oracle.Far(0xf67, 0x4626), func(o *oracle.Oracle) {
			if entered {
				return
			}
			entered = true
			ret = o.Regs()
			ret.IP = o.Word(oracle.Far(ret.SS, ret.SP))
			ret.CS = o.Word(oracle.Far(ret.SS, ret.SP+2))
			ret.SP += 4
		})
	}
	start := e.Oracle.Steps()
	keys := 0
	released := false
	e.Oracle.SetStepGuard(func(o *oracle.Oracle) error {
		r := o.Regs()
		if entered && r.CS == ret.CS && r.IP == ret.IP && r.SS == ret.SS && r.SP == ret.SP {
			return stop
		}
		if !released && o.Steps() > start+100000 {
			if err := e.Key(0x1c, false); err != nil {
				return err
			}
			released = true
		}
		if keys < 6 && o.Steps() > start+uint64(keys+1)*2000000 {
			o.PressScan(" ")
			keys++
		}
		if o.Steps() > start+60000000 {
			return errors.New("setup encounter budget")
		}
		return nil
	})
	if err := e.Key(0x1c, true); err != nil {
		t.Fatal(err)
	}
	var err error
	for err == nil {
		err = e.AdvanceCycles(100000)
		e.RenderAudio()
	}
	e.Oracle.SetStepGuard(nil)
	if !preview && errors.Is(err, stop) {
		return nil
	}
	return err
}

func TestOriginalBattleSetupAction(t *testing.T) {
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
	folder := filepath.Join(work, "action-r1")
	must(os.Mkdir(folder, 0700))
	reports := []map[string]any{}
	for _, hd := range []bool{false, true} {
		var referenceFrame, referenceInitial, referenceUnits, referenceHP []byte
		var referenceSeed uint32
		for mode := 0; mode < 2; mode++ {
			dir := filepath.Join(folder, fmt.Sprintf("hd-%v-mode-%d", hd, mode))
			must(os.Mkdir(dir, 0700))
			e := setupCold(t, root, assets, dir, hd)
			var x *originalBattleSetup
			if mode == 1 {
				var err error
				x, err = installOriginalBattleSetup(e, catalog, nil)
				must(err)
			}
			var initial []byte
			e.Oracle.OnCall(oracle.Far(0xf67, 0x35), func(o *oracle.Oracle) { initial = setupData(o) })
			must(setupEncounter(t, e, false))
			im := e.Frame()
			units := e.Oracle.Bytes(oracle.Far(0x1e88, 0x56e8), 48)
			hp := append(e.Oracle.Bytes(oracle.Far(0x1e88, 0x8ca4), 12), e.Oracle.Bytes(oracle.Far(0x1e88, 0x8e60), 12)...)
			seed := originalSeed(e.Oracle)
			if mode == 0 {
				referenceFrame, referenceInitial, referenceUnits, referenceHP = bytes.Clone(im.Pix), bytes.Clone(initial), bytes.Clone(units), bytes.Clone(hp)
				referenceSeed = seed
			} else if !bytes.Equal(referenceFrame, im.Pix) || !bytes.Equal(referenceInitial, initial) || !bytes.Equal(referenceUnits, units) || !bytes.Equal(referenceHP, hp) || referenceSeed != seed || x.HPCalls != 1 || x.FormationCalls != 1 {
				t.Fatal("setup cold action differs", hd)
			}
			f, err := os.Create(filepath.Join(dir, "frame.png"))
			must(err)
			must(png.Encode(f, im))
			must(f.Close())
			must(e.Oracle.SaveStateFile(filepath.Join(dir, "after.state")))
			reports = append(reports, map[string]any{"hd": hd, "mode": mode, "initial_hex": fmt.Sprintf("%x", initial), "units_hex": fmt.Sprintf("%x", units), "pending_hp_hex": fmt.Sprintf("%x", hp), "frame_rgba_sha256": contentSHA(im.Pix), "seed_after": seed})
			e.Close()
		}
	}
	setupWrite(t, filepath.Join(folder, "receipt.json"), map[string]any{"status": "passed-original-battle-setup-action", "rows": reports, "normal_cold_start": true, "snapshot_loaded": false, "seed": uint32(0x12345678)})
}

func TestOriginalBattleSetupPreview(t *testing.T) {
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
	folder := filepath.Join(work, "preview-r1")
	must(os.Mkdir(folder, 0700))
	reports := []map[string]any{}
	var saved checkpointSave
	raw, err := os.ReadFile(filepath.Join(work, "inputs/setup-world.json"))
	must(err)
	must(pairStrictJSON(raw, &saved))
	rows := [][6]ArmyStack{saved.World.Army.Slots, {{"native:01", 30}, {"openkb:arcr", 2}, {"openkb:pike", 1}, {"openkb:wolf", 2}, {"openkb:drui", 1}, {"openkb:drag", 1}}}
	for i, player := range rows {
		dir := filepath.Join(folder, fmt.Sprint(i))
		must(os.Mkdir(dir, 0700))
		e := setupCold(t, root, assets, dir, true)
		before := e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)
		x, err := installOriginalBattleSetup(e, catalog, &player)
		must(err)
		rounds := 0
		e.Oracle.OnCall(oracle.Far(0xf67, 0x2076), func(*oracle.Oracle) { rounds++ })
		err = setupEncounter(t, e, true)
		if !errors.Is(err, errOriginalBattleSetupHeld) {
			t.Fatal("preview did not hold", err)
		}
		cycles := e.Oracle.Cycles()
		mem := e.Oracle.Bytes(oracle.Far(0, 0), 1<<20)
		for j := 0; j < 5; j++ {
			if er := e.AdvanceCycles(100000); !errors.Is(er, errOriginalBattleSetupHeld) {
				t.Fatal("preview fell through", er)
			}
		}
		if rounds != 0 || e.Oracle.Cycles() != cycles || !bytes.Equal(mem, e.Oracle.Bytes(oracle.Far(0, 0), 1<<20)) || !bytes.Equal(before, e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
			t.Fatal("held preview changed original state")
		}
		for n, s := range player {
			if s.Unit != "" && catalog.Profiles[s.Unit].NativeKind == 0 {
				if !bytes.Equal(e.Oracle.Bytes(oracle.Far(0x1e88, uint16(0x56e8+n*4)), 4), make([]byte, 4)) || x.Plan.HP[0][n] == 0 {
					t.Fatal("extension escaped into original rows")
				}
			}
		}
		catalogRaw, err := os.ReadFile(filepath.Join(work, "inputs/army-catalog.json"))
		must(err)
		art := loadHDUnitArtwork(e, filepath.Join(work, "ui-assets"), contentSHA(catalogRaw))
		if len(art.Failures) != 0 {
			t.Fatal(art.Failures)
		}
		base := e.Frame()
		f, err := os.Create(filepath.Join(dir, "source.png"))
		must(err)
		must(png.Encode(f, base))
		must(f.Close())
		im, err := composeOriginalBattleSetup(e, x, art)
		must(err)
		f, err = os.Create(filepath.Join(dir, "frame.png"))
		must(err)
		must(png.Encode(f, im))
		must(f.Close())
		must(e.Oracle.SaveStateFile(filepath.Join(dir, "held.state")))
		reports = append(reports, map[string]any{"case": i, "plan": x.Plan, "native_rows_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x56e8), 48)), "coords_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x703c), 12)), "shadow_hex": fmt.Sprintf("%x", before), "round_entries": rounds, "held_retries": 5, "cycles": cycles, "seed": originalSeed(e.Oracle), "frame_rgba_sha256": contentSHA(im.Pix), "controlled_typed_override": true})
		e.Close()
	}
	setupWrite(t, filepath.Join(folder, "receipt.json"), map[string]any{"status": "passed-original-battle-setup-preview", "rows": reports, "playable": false, "actual_window_verified": false, "scope": "Original HD initial battlefield; host holds before all rounds, only Go owns extended identities and HP."})
}
