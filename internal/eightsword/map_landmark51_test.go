package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/draw"
	"image/png"
	"maps"
	"os"
	"path/filepath"
	"reflect"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

func map51Paths(t *testing.T) (string, string, string, string) {
	t.Helper()
	dir, base, root, cache := os.Getenv("EIGHTSWORD_TEST_MAP51_ASSETS"), os.Getenv("EIGHTSWORD_TEST_MAP51_BASE"), os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_MAP51_CACHE")
	if dir == "" || base == "" || root == "" || cache == "" {
		t.Skip("需要045候選、r52、原版及獨立快取")
	}
	return dir, base, root, cache
}

func map51Engine(t *testing.T, dir, root string) *Engine {
	t.Helper()
	e, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(e.Close)
	if !e.sourceEnabled || e.AssetError != "" || e.GraphicsError != "" || e.MapLandmarkError != "" || e.BuildingsError != "" || e.BattleActorError != "" || e.MapEncounterBatchError != "" || e.BattleBackgroundBatchError != "" {
		t.Fatal(e.Status())
	}
	return e
}

func TestMap51RealSourcesAndCaches(t *testing.T) {
	dir, base, root, cache := map51Paths(t)
	e, old := map51Engine(t, dir, root), map51Engine(t, base, root)
	a, b := e.Tracker.graphics.assets, old.Tracker.graphics.assets
	if len(a.Materials) != len(b.Materials)+1 || !reflect.DeepEqual(a.ByNative, b.ByNative) || !reflect.DeepEqual(a.Native, b.Native) || !reflect.DeepEqual(a.Actors, b.Actors) || !reflect.DeepEqual(a.ActorSHA, b.ActorSHA) || !reflect.DeepEqual(a.BattleActors, b.BattleActors) || !reflect.DeepEqual(a.BattleAliases, b.BattleAliases) || !reflect.DeepEqual(a.Effects, b.Effects) || !reflect.DeepEqual(a.EffectSHA, b.EffectSHA) || !reflect.DeepEqual(e.Assets, old.Assets) {
		t.Fatal("既有來源／角色／效果／字型改變")
	}
	for id, m := range b.Materials {
		if !reflect.DeepEqual(a.Materials[id], m) {
			t.Fatal("原材質改變", id)
		}
	}
	data, err := os.ReadFile(filepath.Join(cache, "map51.rgba"))
	if err != nil {
		t.Fatal(err)
	}
	if b.Materials[52] != nil || !bytes.Equal(a.Materials[52].Tile.Pix, data) {
		t.Fatal("第51筆完整快取不符")
	}
	export := os.Getenv("EIGHTSWORD_TEST_MAP51_EXPORT")
	if export == "" {
		t.Fatal("需要65筆快取輸出")
	}
	if err := os.Mkdir(export, 0755); err != nil {
		t.Fatal(err)
	}
	rows := []map[string]any{}
	for i := 0; i < 65; i++ {
		m := a.Materials[uint16(i+1)]
		if m == nil || m.NativeWidth != 64 || m.NativeHeight != 25 || m.Tile == nil || m.Tile.Bounds().Dx() != 192 || m.Tile.Bounds().Dy() != 150 {
			t.Fatal("主地圖快取缺失", i)
		}
		tile := image.NewRGBA(image.Rect(0, 0, 192, 150))
		draw.Draw(tile, tile.Bounds(), m.Tile, m.Tile.Bounds().Min, draw.Src)
		name := fmt.Sprintf("pmap-%02d.rgba", i)
		if err := os.WriteFile(filepath.Join(export, name), tile.Pix, 0644); err != nil {
			t.Fatal(err)
		}
		rows = append(rows, map[string]any{"index": i, "native_sha256": a.Native[i].NativeSHA, "cache_sha256": hash(tile.Pix), "file": name})
	}
	raw, err := json.MarshalIndent(rows, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(export, "caches.json"), append(raw, 10), 0644); err != nil {
		t.Fatal(err)
	}
}

func TestMap51FailureAtomic(t *testing.T) {
	dir, _, root, _ := map51Paths(t)
	e := map51Engine(t, dir, root)
	original := e.Tracker.graphics.assets
	for _, kind := range []string{"missing", "manifest", "prompt", "image", "source", "collision", "native-alias", "metadata"} {
		t.Run(kind, func(t *testing.T) {
			a := *original
			a.Materials = maps.Clone(original.Materials)
			a.ByNative = maps.Clone(original.ByNative)
			delete(a.Materials, 52)
			if kind == "collision" {
				a.Materials[52] = original.Materials[1]
			}
			if kind == "native-alias" {
				a.ByNative["other-source"] = 52
			}
			if kind == "metadata" {
				a.Native = append(a.Native[:0:0], a.Native...)
				a.Native[51].Height = 24
			}
			before := a
			before.Materials = maps.Clone(a.Materials)
			before.ByNative = maps.Clone(a.ByNative)
			assets := t.TempDir()
			if kind != "missing" {
				for _, name := range []string{"map-landmark-51.json", "map-landmark-51-r1.png", "map-landmark-51-r1.prompt.txt"} {
					data, err := os.ReadFile(filepath.Join(dir, name))
					if err != nil {
						t.Fatal(err)
					}
					if kind == "manifest" && name == "map-landmark-51.json" || kind == "prompt" && name == "map-landmark-51-r1.prompt.txt" || kind == "image" && name == "map-landmark-51-r1.png" {
						data = append(data, 0)
					}
					if err := os.WriteFile(filepath.Join(assets, name), data, 0644); err != nil {
						t.Fatal(err)
					}
				}
			}
			source, err := os.ReadFile(filepath.Join(root, "PMAP.AY"))
			if err != nil {
				t.Fatal(err)
			}
			if kind == "source" {
				source = append([]byte(nil), source...)
				source[51*1004] ^= 1
			}
			err = loadMapLandmark51(assets, source, &a)
			if (err == nil) != (kind == "missing") || !reflect.DeepEqual(before, a) {
				t.Fatal("失敗組部分提交", kind, err)
			}
		})
	}
}

// Shared presentation test after ordinary menus; no natural map reachability claim.
func TestMap51ControlledSourceDraw(t *testing.T) {
	dir, base, root, cache := map51Paths(t)
	out := os.Getenv("EIGHTSWORD_TEST_MAP51_OUT")
	if out == "" {
		t.Skip("需要全新受控輸出")
	}
	if err := os.Mkdir(out, 0755); err != nil {
		t.Fatal(err)
	}
	e, control := map51Engine(t, dir, root), map51Engine(t, base, root)
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
	for _, page := range []uint16{0xa400, 0xa000} {
		for _, engine := range engines {
			engine.Oracle.WriteU16(dest, page)
		}
		call(0x99c, bg, 0, 0)
	}
	background := append([]byte(nil), e.Frame().Pix...)
	raw, err := os.ReadFile(filepath.Join(cache, "pmap51-native.bin"))
	if err != nil || len(raw) != 1004 || hash(raw) != mapLandmark51RecordSHA {
		t.Fatal("五平面fixture不符", err)
	}
	cacheData, err := os.ReadFile(filepath.Join(cache, "map51.rgba"))
	if err != nil {
		t.Fatal(err)
	}
	rows := []map[string]any{}
	for _, stage := range []string{"back-hidden", "back-copied", "front-drawn", "restored"} {
		if stage == "back-hidden" {
			for _, engine := range engines {
				engine.Oracle.WriteU16(dest, 0xa400)
			}
			call(0x76f, raw, 12, 60)
		}
		if stage == "back-copied" {
			for _, engine := range engines {
				engine.Oracle.WriteU16(dest, 0xa000)
			}
			call(0x423, raw, 12, 60)
		}
		if stage == "front-drawn" {
			call(0x99c, bg, 0, 0)
			call(0x76f, raw, 12, 60)
		}
		if stage == "restored" {
			for _, engine := range engines {
				engine.Oracle.WriteU16(dest, 0xa400)
			}
			call(0x99c, bg, 0, 0)
			for _, engine := range engines {
				engine.Oracle.WriteU16(dest, 0xa000)
			}
			call(0x423, raw, 12, 60)
		}
		before := observerGuestState(t, e)
		frame := e.Frame()
		if !bytes.Equal(before, observerGuestState(t, e)) || e.renderFault != nil {
			t.Fatal("Frame非純讀或故障", e.Status())
		}
		want := image.NewRGBA(frame.Bounds())
		copy(want.Pix, background)
		if stage == "back-copied" || stage == "front-drawn" {
			for y := 0; y < 150; y++ {
				copy(want.Pix[(360+y)*want.Stride+288*4:(360+y)*want.Stride+480*4], cacheData[y*192*4:(y+1)*192*4])
			}
		}
		if !bytes.Equal(frame.Pix, want.Pix) {
			t.Fatal("完整前後頁／還原不符", stage)
		}
		name := "map51-" + stage + ".png"
		f, err := os.OpenFile(filepath.Join(out, name), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
		if err != nil {
			t.Fatal(err)
		}
		err = png.Encode(f, frame)
		closeErr := f.Close()
		if err != nil || closeErr != nil {
			t.Fatal(err, closeErr)
		}
		rows = append(rows, map[string]any{"stage": stage, "png": name, "rect": []int{288, 360, 192, 150}, "pixels": 2304000, "frame_sha256": hash(frame.Pix), "guest_state_sha256": hash(before), "frame_pure": true, "paired_guest_equal": true})
	}

	for _, restore := range restores {
		restore()
	}
	if e.Tracker.Stats.ComposedFrames != 0 {
		t.Fatal("使用舊合成器")
	}
	report := map[string]any{"status": "PASS-controlled-map51-source-render-not-natural-reachability", "cases": rows, "ordinary_prefix": "boot/new game/map/F1/back/F2/back", "source_renderer": true, "source_direct_calls": e.sourceDirectCalls, "old_overlay_compositions": e.Tracker.Stats.ComposedFrames, "gameplay_changed": false, "controlled_memory": map[string]any{"buffer": "8000:0000", "bytes": 64004, "DS": "0AA8", "mode": "DS:7484=1", "destination": "DS:748A=A400/A000", "background": "14D2:0196=A400", "original_values": originals, "restored_and_verified": true}}
	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(out, "receipt.json"), append(data, 10), 0644); err != nil {
		t.Fatal(err)
	}
}
