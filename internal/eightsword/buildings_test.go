package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/png"
	"maps"
	"os"
	"path/filepath"
	"reflect"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

func buildingPaths(t *testing.T) (string, string, string, string) {
	t.Helper()
	dir, base, root, cache := os.Getenv("EIGHTSWORD_TEST_BUILDINGS_ASSETS"), os.Getenv("EIGHTSWORD_TEST_BUILDINGS_BASE"), os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_BUILDINGS_CACHE")
	if dir == "" || base == "" || root == "" || cache == "" {
		t.Skip("需要051候選、r51、原版及獨立快取")
	}
	return dir, base, root, cache
}

func buildingEngine(t *testing.T, dir, root string) *Engine {
	t.Helper()
	e, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(e.Close)
	if !e.sourceEnabled || e.AssetError != "" || e.GraphicsError != "" || e.BuildingsError != "" || e.BattleActorError != "" || e.MapEncounterBatchError != "" || e.BattleBackgroundBatchError != "" {
		t.Fatal(e.Status())
	}
	return e
}

func TestBuildingsRealSourcesAndCaches(t *testing.T) {
	dir, base, root, cache := buildingPaths(t)
	e, old := buildingEngine(t, dir, root), buildingEngine(t, base, root)
	a, b := e.Tracker.graphics.assets, old.Tracker.graphics.assets
	if len(a.Materials) != len(b.Materials)+3 || len(a.ByNative) != len(b.ByNative)+3 || !reflect.DeepEqual(a.Actors, b.Actors) || !reflect.DeepEqual(a.ActorSHA, b.ActorSHA) || !reflect.DeepEqual(a.BattleActors, b.BattleActors) || !reflect.DeepEqual(a.BattleAliases, b.BattleAliases) || !reflect.DeepEqual(a.Effects, b.Effects) || !reflect.DeepEqual(a.EffectSHA, b.EffectSHA) || !reflect.DeepEqual(e.Assets, old.Assets) {
		t.Fatal("建築改變既有角色／效果／字型")
	}
	for id, m := range b.Materials {
		if !reflect.DeepEqual(a.Materials[id], m) {
			t.Fatal("原材質改變", id)
		}
	}
	for key, id := range b.ByNative {
		if a.ByNative[key] != id {
			t.Fatal("原來源改變")
		}
	}
	for _, group := range buildingGroups {
		data, err := os.ReadFile(filepath.Join(cache, fmt.Sprintf("live%d-building.rgba", group.Number)))
		if err != nil {
			t.Fatal(err)
		}
		m := a.Materials[group.ID]
		if m == nil || m.NativeWidth != 448 || m.NativeHeight != 100 || m.Tile.Bounds() != image.Rect(0, 0, 1344, 600) || !bytes.Equal(data, m.Tile.Pix) || a.ByNative[group.NativeSHA] != group.ID {
			t.Fatal("完整建築快取不符", group.Number)
		}
	}
	if a.Materials[849] != nil || a.Materials[851] != nil || a.ByNative["c249b6f8707a004789b20b8fac594a0cceaaad2ab601e0ba8aa9440d5b384590"] != 0 || a.ByNative["4ef8db559801e29c0812f65a32a60067677ae5227bf2a9ca76d458d467d747d1"] != 0 {
		t.Fatal("未達READY的LIVE4／6被接入")
	}
}

func TestBuildingsFailureAtomic(t *testing.T) {
	dir, _, root, _ := buildingPaths(t)
	e := buildingEngine(t, dir, root)
	original := e.Tracker.graphics.assets
	for _, kind := range []string{"missing", "manifest", "prompt", "image", "source", "collision", "native-alias"} {
		t.Run(kind, func(t *testing.T) {
			a := *original
			a.Materials = maps.Clone(original.Materials)
			a.ByNative = maps.Clone(original.ByNative)
			delete(a.Materials, 848)
			delete(a.ByNative, buildingGroups[1].NativeSHA)
			if kind == "collision" {
				a.Materials[848] = original.Materials[847]
			}
			if kind == "native-alias" {
				a.ByNative["other-source"] = 848
			}
			before := a
			before.Materials = maps.Clone(a.Materials)
			before.ByNative = maps.Clone(a.ByNative)
			assets, source := t.TempDir(), root
			if kind != "missing" {
				for _, name := range []string{"building-live3.json", "live3-hd-r1.png", "live3-hd-r1.prompt.txt"} {
					data, err := os.ReadFile(filepath.Join(dir, name))
					if err != nil {
						t.Fatal(err)
					}
					if kind == "manifest" && name == "building-live3.json" || kind == "prompt" && name == "live3-hd-r1.prompt.txt" || kind == "image" && name == "live3-hd-r1.png" {
						data = append(data, 0)
					}
					if err := os.WriteFile(filepath.Join(assets, name), data, 0644); err != nil {
						t.Fatal(err)
					}
				}
			}
			if kind == "source" {
				source = t.TempDir()
				data, err := os.ReadFile(filepath.Join(root, "LIVE3.AY"))
				if err != nil {
					t.Fatal(err)
				}
				data[0] ^= 1
				if err := os.WriteFile(filepath.Join(source, "LIVE3.AY"), data, 0644); err != nil {
					t.Fatal(err)
				}
			}
			err := loadBuildingGroup(assets, source, &a, 1)
			if (err == nil) != (kind == "missing") || !reflect.DeepEqual(before, a) {
				t.Fatal("失敗組部分提交", kind, err)
			}
		})
	}
}

// Controlled source rectangle after ordinary menus; not a natural recruitment claim.
func TestBuildingsControlledSourceDraw(t *testing.T) {
	dir, base, root, cache := buildingPaths(t)
	out := os.Getenv("EIGHTSWORD_TEST_BUILDINGS_OUT")
	if out == "" {
		t.Skip("需要全新受控輸出")
	}
	if err := os.Mkdir(out, 0755); err != nil {
		t.Fatal(err)
	}
	e, control := buildingEngine(t, dir, root), buildingEngine(t, base, root)
	engines := []*Engine{e, control}
	advance := func(ms int) {
		t.Helper()
		for elapsed := 0; elapsed < ms; elapsed += 10 {
			for _, engine := range engines {
				if err := engine.AdvanceCycles(30000); err != nil {
					t.Fatal(err)
				}
			}
			if !bytes.Equal(int16Bytes(e.RenderAudio()), int16Bytes(control.RenderAudio())) {
				t.Fatal("普通路徑PCM改變")
			}
		}
		for _, engine := range engines {
			engine.Frame()
		}
		if !bytes.Equal(observerGuestState(t, e), observerGuestState(t, control)) {
			t.Fatal("普通路徑客體改變")
		}
	}
	press := func(scan byte) {
		t.Helper()
		for _, engine := range engines {
			if err := engine.Key(scan, true); err != nil {
				t.Fatal(err)
			}
		}
		advance(100)
		for _, engine := range engines {
			if err := engine.Key(scan, false); err != nil {
				t.Fatal(err)
			}
		}
		advance(100)
	}
	for _, engine := range engines {
		engine.Oracle.SetClock(12, 0, 0, 0)
		engine.EnableLiveClock(3000)
	}
	advance(1000)
	press(2)
	press(2)
	advance(1000)
	press(1)
	for n := 0; n < 300 && e.Tracker.VisibleScene != "main-menu"; n++ {
		advance(100)
	}
	if e.Tracker.VisibleScene != "main-menu" {
		t.Fatal(e.Status())
	}
	press(0x50)
	press(0x1c)
	press(0x1c)
	advance(1400)
	press(0x3b)
	advance(700)
	press(1)
	press(0x3c)
	advance(700)
	press(1)
	if e.Tracker.VisibleScene != "map" || e.sourceDirectCalls == 0 {
		t.Fatal(e.Status())
	}
	bg, err := os.ReadFile(filepath.Join(cache, "gro02-native.bin"))
	if err != nil || len(bg) != 64004 || hash(bg) != battleBackgroundNativeSHA {
		t.Fatal("背景fixture不符", err)
	}
	buffer := oracle.Addr{Seg: 0x8000}
	mode, dest := oracle.Addr{Seg: 0x0aa8, Off: 0x7484}, oracle.Addr{Seg: 0x0aa8, Off: 0x748a}
	var restores []func()
	var originals []map[string]any
	for _, engine := range engines {
		engine := engine
		saved := append([]byte(nil), engine.Oracle.Bytes(buffer, 64004)...)
		ds := engine.Oracle.Regs().DS
		m, d := engine.Oracle.Word(mode), engine.Oracle.Word(dest)
		back := oracle.Addr{Seg: engine.Tracker.stringSeg, Off: 0x196}
		b := engine.Oracle.Word(back)
		restore := func() {
			engine.Oracle.WriteBytes(buffer, saved)
			engine.Oracle.WriteU16(mode, m)
			engine.Oracle.WriteU16(dest, d)
			engine.Oracle.WriteU16(back, b)
			engine.Oracle.SetRegs(oracle.CallRegs{DS: ds, SetDS: true})
			if !bytes.Equal(engine.Oracle.Bytes(buffer, len(saved)), saved) || engine.Oracle.Regs().DS != ds || engine.Oracle.Word(mode) != m || engine.Oracle.Word(dest) != d || engine.Oracle.Word(back) != b {
				t.Fatal("受控RAM恢復失敗")
			}
		}
		defer restore()
		restores = append(restores, restore)
		originals = append(originals, map[string]any{"buffer_sha256": hash(saved), "DS": ds, "mode": m, "destination": d, "background_page": b})
		engine.Oracle.SetRegs(oracle.CallRegs{DS: 0x0aa8, SetDS: true})
		engine.Oracle.WriteU16(mode, 1)
		engine.Oracle.WriteU16(back, 0xa400)
	}
	call := func(entry uint16, raw []byte, x, y uint16) {
		t.Helper()
		for _, engine := range engines {
			engine.Oracle.WriteBytes(buffer, raw)
			if _, err := engine.Oracle.CallBudget(500000, oracle.Addr{Seg: engine.Tracker.stringSeg, Off: entry}, 0, 0x8000, x, y); err != nil {
				t.Fatal(err)
			}
		}
		if !bytes.Equal(observerGuestState(t, e), observerGuestState(t, control)) {
			t.Fatal("受控客體改變")
		}
	}
	rows := []map[string]any{}
	for _, group := range buildingGroups {
		for _, page := range []uint16{0xa400, 0xa000} {
			for _, engine := range engines {
				engine.Oracle.WriteU16(dest, page)
			}
			call(0x99c, bg, 0, 0)
		}
		background := append([]byte(nil), e.Frame().Pix...)
		raw, err := os.ReadFile(filepath.Join(cache, fmt.Sprintf("live%d-native.bin", group.Number)))
		if err != nil || len(raw) != 22404 || hash(raw) != group.NativeSHA {
			t.Fatal("建築來源不符", err)
		}
		cacheData, err := os.ReadFile(filepath.Join(cache, fmt.Sprintf("live%d-building.rgba", group.Number)))
		if err != nil {
			t.Fatal(err)
		}
		for _, stage := range []string{"building", "restored"} {
			entry := uint16(0x99c)
			if stage == "restored" {
				entry = 0x423
			}
			call(entry, raw, 1, 12)
			before := observerGuestState(t, e)
			frame := e.Frame()
			if !bytes.Equal(before, observerGuestState(t, e)) || e.renderFault != nil {
				t.Fatal("Frame非純讀或故障", e.Status())
			}
			want := image.NewRGBA(frame.Bounds())
			copy(want.Pix, background)
			if stage == "building" {
				for y := 0; y < 600; y++ {
					copy(want.Pix[(72+y)*want.Stride+24*4:(72+y)*want.Stride+(24+1344)*4], cacheData[y*1344*4:(y+1)*1344*4])
				}
			}
			if !bytes.Equal(frame.Pix, want.Pix) {
				t.Fatalf("完整建築／還原不符 LIVE%d/%s", group.Number, stage)
			}
			name := fmt.Sprintf("live%d-%s.png", group.Number, stage)
			f, err := os.OpenFile(filepath.Join(out, name), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
			if err != nil {
				t.Fatal(err)
			}
			err = png.Encode(f, frame)
			closeErr := f.Close()
			if err != nil || closeErr != nil {
				t.Fatal(err, closeErr)
			}
			rows = append(rows, map[string]any{"source": fmt.Sprintf("LIVE%d.AY", group.Number), "stage": stage, "png": name, "rect": []int{24, 72, 1344, 600}, "pixels": 2304000, "frame_sha256": hash(frame.Pix), "guest_state_sha256": hash(before), "frame_pure": true, "paired_guest_equal": true})
		}
	}
	for _, restore := range restores {
		restore()
	}
	if e.Tracker.Stats.ComposedFrames != 0 {
		t.Fatal("使用舊合成器")
	}
	report := map[string]any{"status": "PASS-controlled-building-source-render-not-natural-recruitment", "cases": rows, "ordinary_prefix": "boot/new game/map/F1/back/F2/back", "source_renderer": true, "source_direct_calls": e.sourceDirectCalls, "old_overlay_compositions": e.Tracker.Stats.ComposedFrames, "gameplay_changed": false, "controlled_memory": map[string]any{"buffer": "8000:0000", "bytes": 64004, "DS": "0AA8", "mode": "DS:7484=1", "destination": "DS:748A=A400/A000", "background": "14D2:0196=A400", "original_values": originals, "restored_and_verified": true}}
	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(out, "receipt.json"), append(data, 10), 0644); err != nil {
		t.Fatal(err)
	}
}
