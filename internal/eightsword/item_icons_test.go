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

func itemPaths(t *testing.T) (string, string, string, string) {
	t.Helper()
	dir, base, root, cache := os.Getenv("EIGHTSWORD_TEST_ITEMS_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ITEMS_BASE"), os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_ITEMS_CACHE")
	if dir == "" || base == "" || root == "" || cache == "" {
		t.Skip("需要052候選、r53、原版及獨立快取")
	}
	return dir, base, root, cache
}

func itemEngine(t *testing.T, dir, root string) *Engine {
	t.Helper()
	e, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(e.Close)
	if !e.sourceEnabled || e.AssetError != "" || e.GraphicsError != "" || e.ItemIconsError != "" || e.MapLandmarkError != "" || e.BuildingsError != "" || e.BattleActorError != "" || e.MapEncounterBatchError != "" || e.BattleBackgroundBatchError != "" {
		t.Fatal(e.Status())
	}
	return e
}

func itemManifest(t *testing.T, dir string) itemIconsManifest {
	t.Helper()
	raw, err := os.ReadFile(filepath.Join(dir, "man-items.json"))
	if err != nil {
		t.Fatal(err)
	}
	var m itemIconsManifest
	if err := json.Unmarshal(raw, &m); err != nil {
		t.Fatal(err)
	}
	return m
}

func TestItemsRealSourcesAndCaches(t *testing.T) {
	dir, base, root, cache := itemPaths(t)
	e, old := itemEngine(t, dir, root), itemEngine(t, base, root)
	a, b := e.Tracker.graphics.assets, old.Tracker.graphics.assets
	if len(a.Actors) != len(b.Actors)+16 || len(a.ActorSHA) != len(b.ActorSHA)+16 || len(a.ByNative) != len(b.ByNative)+16 || !reflect.DeepEqual(a.Materials, b.Materials) || !reflect.DeepEqual(a.Native, b.Native) || !reflect.DeepEqual(a.BattleActors, b.BattleActors) || !reflect.DeepEqual(a.BattleAliases, b.BattleAliases) || !reflect.DeepEqual(a.Effects, b.Effects) || !reflect.DeepEqual(a.EffectSHA, b.EffectSHA) || !reflect.DeepEqual(e.Assets, old.Assets) {
		t.Fatal("既有材質／角色／效果／字型改變")
	}
	for id, m := range b.Actors {
		if !reflect.DeepEqual(a.Actors[id], m) || a.ActorSHA[id] != b.ActorSHA[id] {
			t.Fatal("原角色改變", id)
		}
	}
	for key, id := range b.ByNative {
		if a.ByNative[key] != id {
			t.Fatal("原來源改變")
		}
	}
	m := itemManifest(t, dir)
	for slot, entry := range m.Entries {
		id := uint16(852 + slot)
		actor := a.Actors[id]
		data, err := os.ReadFile(filepath.Join(cache, fmt.Sprintf("man-%02d.rgba", entry.Index)))
		if err != nil {
			t.Fatal(err)
		}
		if actor == nil || actor.NativeWidth != 32 || actor.NativeHeight != 16 || actor.Tile.Bounds() != image.Rect(0, 0, 96, 96) || !bytes.Equal(actor.Tile.Pix, data) || a.ByNative[entry.NativeSHA] != id || a.ActorSHA[id] != entry.RecordSHA || a.BattleActors[id] || a.BattleAliases[id] != 0 {
			t.Fatal("器物完整快取不符", entry.Index)
		}
	}
}

func TestItemsFailureAtomic(t *testing.T) {
	dir, _, root, _ := itemPaths(t)
	e := itemEngine(t, dir, root)
	original := e.Tracker.graphics.assets
	m := itemManifest(t, dir)
	for _, kind := range []string{"missing", "manifest", "prompt", "image", "source", "source-missing", "collision", "native-alias"} {
		t.Run(kind, func(t *testing.T) {
			a := *original
			a.Actors = maps.Clone(original.Actors)
			a.ActorSHA = maps.Clone(original.ActorSHA)
			a.ByNative = maps.Clone(original.ByNative)
			for slot, entry := range m.Entries {
				id := uint16(852 + slot)
				delete(a.Actors, id)
				delete(a.ActorSHA, id)
				delete(a.ByNative, entry.NativeSHA)
			}
			if kind == "collision" {
				a.Actors[867] = original.Actors[852]
			}
			if kind == "native-alias" {
				a.ByNative["other-source"] = 867
			}
			before := a
			before.Actors = maps.Clone(a.Actors)
			before.ActorSHA = maps.Clone(a.ActorSHA)
			before.ByNative = maps.Clone(a.ByNative)
			assets := t.TempDir()
			if kind != "missing" {
				names := []string{"man-items.json"}
				for _, entry := range m.Entries {
					names = append(names, entry.Image.File, entry.Prompt)
				}
				for _, name := range names {
					corrupt := kind == "manifest" && name == "man-items.json" || kind == "image" && name == "man-28-r2.png" || kind == "prompt" && name == "man-28-r2.prompt.txt"
					if corrupt {
						raw, err := os.ReadFile(filepath.Join(dir, name))
						if err != nil {
							t.Fatal(err)
						}
						if err := os.WriteFile(filepath.Join(assets, name), append(raw, 0), 0644); err != nil {
							t.Fatal(err)
						}
					} else {
						raw, err := os.ReadFile(filepath.Join(dir, name))
						if err != nil {
							t.Fatal(err)
						}
						if err := os.WriteFile(filepath.Join(assets, name), raw, 0644); err != nil {
							t.Fatal(err)
						}
					}
				}
			}
			source := root
			if kind == "source" || kind == "source-missing" {
				source = t.TempDir()
				if kind == "source" {
					raw, err := os.ReadFile(filepath.Join(root, "MAN.AY"))
					if err != nil {
						t.Fatal(err)
					}
					raw[14448] ^= 1
					if err := os.WriteFile(filepath.Join(source, "MAN.AY"), raw, 0644); err != nil {
						t.Fatal(err)
					}
				}
			}
			err := loadItemIcons(assets, source, &a)
			if (err == nil) != (kind == "missing") || !reflect.DeepEqual(before, a) {
				t.Fatal("失敗組部分提交", kind, err)
			}
		})
	}
}

// Shared presentation test after ordinary menus; no natural map reachability claim.
func TestItemsControlledSourceDraw(t *testing.T) {
	dir, base, root, cache := itemPaths(t)
	out := os.Getenv("EIGHTSWORD_TEST_ITEMS_OUT")
	if out == "" {
		t.Skip("需要全新受控輸出")
	}
	if err := os.Mkdir(out, 0755); err != nil {
		t.Fatal(err)
	}
	e, control := itemEngine(t, dir, root), itemEngine(t, base, root)
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
	mfest := itemManifest(t, dir)
	rows := []map[string]any{}
	for _, index := range []int{15, 27} {
		var entryIndex int
		for slot, entry := range mfest.Entries {
			if entry.Index == index {
				entryIndex = slot
			}
		}
		entry := mfest.Entries[entryIndex]
		for _, page := range []uint16{0xa400, 0xa000} {
			for _, engine := range engines {
				engine.Oracle.WriteU16(dest, page)
			}
			call(0x99c, bg, 0, 0)
		}
		background := append([]byte(nil), e.Frame().Pix...)
		raw, err := os.ReadFile(filepath.Join(cache, fmt.Sprintf("man-%02d-native.bin", index)))
		if err != nil || len(raw) != 388 || hash(raw) != entry.RecordSHA {
			t.Fatal("器物六平面fixture不符", err)
		}
		cacheData, err := os.ReadFile(filepath.Join(cache, fmt.Sprintf("man-%02d.rgba", index)))
		if err != nil {
			t.Fatal(err)
		}
		for _, stage := range []string{"material-draw", "restored", "color-draw", "color-restored"} {
			if stage == "color-draw" {
				black := make([]byte, 260)
				black[0] = 4
				black[2] = 16
				call(0x99c, black, 12, 60)
			}
			if stage == "material-draw" || stage == "color-draw" {
				call(0x4f2, raw, 12, 60)
			} else {
				call(0x423, raw, 12, 60)
			}
			before := observerGuestState(t, e)
			frame := e.Frame()
			if !bytes.Equal(before, observerGuestState(t, e)) || e.renderFault != nil {
				t.Fatal("Frame非純讀或故障", e.Status())
			}
			want := image.NewRGBA(frame.Bounds())
			copy(want.Pix, background)
			if stage == "material-draw" || stage == "color-draw" {
				for y := 0; y < 96; y++ {
					for x := 0; x < 96; x++ {
						src := (y*96 + x) * 4
						dst := (360+y)*want.Stride + (288+x)*4
						alpha := uint32(cacheData[src+3])
						for c := 0; c < 3; c++ {
							base := uint32(want.Pix[dst+c])
							if stage == "color-draw" {
								base = 0
							}
							want.Pix[dst+c] = uint8(min(255, uint32(cacheData[src+c])+(base*(255-alpha)+127)/255))
						}
					}
				}
			}
			if !bytes.Equal(frame.Pix, want.Pix) {
				t.Fatal("完整材質／純色／還原不符", index, stage)
			}
			name := fmt.Sprintf("man-%02d-%s.png", index, stage)
			f, err := os.OpenFile(filepath.Join(out, name), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
			if err != nil {
				t.Fatal(err)
			}
			err = png.Encode(f, frame)
			closeErr := f.Close()
			if err != nil || closeErr != nil {
				t.Fatal(err, closeErr)
			}
			rows = append(rows, map[string]any{"index": index, "stage": stage, "png": name, "rect": []int{288, 360, 96, 96}, "pixels": 2304000, "frame_sha256": hash(frame.Pix), "guest_state_sha256": hash(before), "frame_pure": true, "paired_guest_equal": true})
		}
	}

	for _, restore := range restores {
		restore()
	}
	if e.Tracker.Stats.ComposedFrames != 0 {
		t.Fatal("使用舊合成器")
	}
	report := map[string]any{"status": "PASS-controlled-item-source-render-not-natural-acquisition", "cases": rows, "ordinary_prefix": "boot/new game/map/F1/back/F2/back", "source_renderer": true, "source_direct_calls": e.sourceDirectCalls, "old_overlay_compositions": e.Tracker.Stats.ComposedFrames, "gameplay_changed": false, "controlled_memory": map[string]any{"buffer": "8000:0000", "bytes": 64004, "DS": "0AA8", "mode": "DS:7484=1", "destination": "DS:748A=A400/A000", "background": "14D2:0196=A400", "original_values": originals, "restored_and_verified": true}}
	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(out, "receipt.json"), append(data, 10), 0644); err != nil {
		t.Fatal(err)
	}
}
