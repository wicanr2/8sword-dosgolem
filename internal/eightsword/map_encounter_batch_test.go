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

func encounterBatchPaths(t *testing.T) (string, string, string, string) {
	t.Helper()
	dir, base, root, cache := os.Getenv("EIGHTSWORD_TEST_ENCOUNTERS_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ENCOUNTERS_BASE"), os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_ENCOUNTERS_CACHE")
	if dir == "" || base == "" || root == "" || cache == "" {
		t.Skip("需要049本機候選、r49、原版及獨立快取")
	}
	return dir, base, root, cache
}

func encounterBatchEngine(t *testing.T, dir, root string) *Engine {
	t.Helper()
	e, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(e.Close)
	if !e.sourceEnabled || e.AssetError != "" || e.GraphicsError != "" || e.MapEncounterBatchError != "" || e.BattleActorError != "" {
		t.Fatal(e.Status())
	}
	return e
}

func TestEncounterBatchRealSourcesAndCaches(t *testing.T) {
	dir, base, root, cache := encounterBatchPaths(t)
	e, old := encounterBatchEngine(t, dir, root), encounterBatchEngine(t, base, root)
	a, b := e.Tracker.graphics.assets, old.Tracker.graphics.assets
	if len(a.Actors) != len(b.Actors)+321 || len(a.ByNative) != len(b.ByNative)+321 || !reflect.DeepEqual(a.Materials, b.Materials) || !reflect.DeepEqual(a.BattleActors, b.BattleActors) || !reflect.DeepEqual(a.BattleAliases, b.BattleAliases) || !reflect.DeepEqual(a.Effects, b.Effects) || !reflect.DeepEqual(e.Assets, old.Assets) {
		t.Fatal("新登錄數量或舊材質／效果／字型不符")
	}
	for id, actor := range b.Actors {
		if a.ActorSHA[id] != b.ActorSHA[id] || !reflect.DeepEqual(a.Actors[id], actor) {
			t.Fatalf("舊角色%d改變", id)
		}
	}
	for key, id := range b.ByNative {
		if a.ByNative[key] != id {
			t.Fatal("舊原生來源對應改變")
		}
	}
	source, err := os.ReadFile(filepath.Join(root, "ENEMY.AY"))
	if err != nil {
		t.Fatal(err)
	}
	frequency := map[string]int{}
	for record := 0; record < 14; record++ {
		for direction := 0; direction < 2; direction++ {
			for height := 1; height <= 25; height += 2 {
				p := encounterBatchPrefix(source[record*1204:(record+1)*1204], direction, height)
				frequency[hash(p[:4+32*height])]++
			}
		}
	}
	count := 0
	for record := 0; record < 14; record++ {
		data, err := os.ReadFile(filepath.Join(dir, fmt.Sprintf("encounter-batch-%02d.json", record)))
		if err != nil {
			t.Fatal(err)
		}
		var m encounterBatchManifest
		if err := json.Unmarshal(data, &m); err != nil {
			t.Fatal(err)
		}
		var expected [2][]byte
		for direction := range expected {
			expected[direction], err = os.ReadFile(filepath.Join(cache, fmt.Sprintf("encounter-%02d-%d.rgba", record, direction)))
			if err != nil || len(expected[direction]) != 192*150*4 || hash(expected[direction]) != m.Caches[direction] {
				t.Fatal("缺少獨立快取", err)
			}
		}
		for _, alias := range m.Aliases {
			count++
			id := encounterBatchID(record, alias.Direction, alias.Height)
			p := encounterBatchPrefix(source[record*1204:(record+1)*1204], alias.Direction, alias.Height)
			if frequency[alias.Native] != 1 || a.ByNative[hash(p[:4+32*alias.Height])] != id || a.ActorSHA[id] != hash(p) || !e.Tracker.graphics.heroRecordMatches(id, 6, p) {
				t.Fatalf("來源／唯一前綴不符 %d/%d/%d", record, alias.Direction, alias.Height)
			}
			tile := a.Actors[id].Tile
			if tile.Bounds() != image.Rect(0, 0, 192, alias.Height*6) || !bytes.Equal(tile.Pix[:alias.Height*6*tile.Stride], expected[alias.Direction][:alias.Height*6*192*4]) {
				t.Fatal("快取與獨立取樣不符", id)
			}
			p[len(p)-1] ^= 1
			if e.Tracker.graphics.heroRecordMatches(id, 6, p) {
				t.Fatal("接受損壞遮罩")
			}
		}
	}
	if count != 321 {
		t.Fatal(count)
	}
}

func TestEncounterBatchFailureAtomic(t *testing.T) {
	dir, _, root, _ := encounterBatchPaths(t)
	e := encounterBatchEngine(t, dir, root)
	original := e.Tracker.graphics.assets
	for _, kind := range []string{"manifest", "image", "prompt", "source", "missing", "collision"} {
		t.Run(kind, func(t *testing.T) {
			a := *original
			a.ByNative, a.Actors, a.ActorSHA = maps.Clone(original.ByNative), maps.Clone(original.Actors), maps.Clone(original.ActorSHA)
			for key, id := range a.ByNative {
				if id >= 610 && id < 636 {
					delete(a.ByNative, key)
					delete(a.Actors, id)
					delete(a.ActorSHA, id)
				}
			}
			if kind == "collision" {
				a.Actors[635] = original.Actors[635]
			}
			before := a
			before.ByNative, before.Actors, before.ActorSHA = maps.Clone(a.ByNative), maps.Clone(a.Actors), maps.Clone(a.ActorSHA)
			assets, source := t.TempDir(), root
			if kind != "missing" {
				for _, name := range []string{"encounter-batch-05.json", "encounter-05-hd-r1.png", "encounter-05-hd-r1.prompt.txt"} {
					raw, err := os.ReadFile(filepath.Join(dir, name))
					if err != nil {
						t.Fatal(err)
					}
					if kind == "manifest" && name == "encounter-batch-05.json" || kind == "image" && name == "encounter-05-hd-r1.png" || kind == "prompt" && name == "encounter-05-hd-r1.prompt.txt" {
						raw = append(raw, 0)
					}
					if err := os.WriteFile(filepath.Join(assets, name), raw, 0644); err != nil {
						t.Fatal(err)
					}
				}
			}
			if kind == "source" {
				source = t.TempDir()
				raw, err := os.ReadFile(filepath.Join(root, "ENEMY.AY"))
				if err != nil {
					t.Fatal(err)
				}
				raw[0] ^= 1
				if err := os.WriteFile(filepath.Join(source, "ENEMY.AY"), raw, 0644); err != nil {
					t.Fatal(err)
				}
			}
			err := loadEncounterBatchGroup(assets, source, &a, 5)
			if (err == nil) != (kind == "missing") || !reflect.DeepEqual(before, a) {
				t.Fatal("失敗組部分提交或回退錯誤", kind, err)
			}
		})
	}
}

// Explicit RAM draw fixture after ordinary menus. This uses formal source Open,
// never the legacy storyEngine overlay reference and never a natural encounter claim.
func TestEncounterBatchControlledSourceDraw(t *testing.T) {
	dir, base, root, cache := encounterBatchPaths(t)
	out := os.Getenv("EIGHTSWORD_TEST_ENCOUNTERS_OUT")
	if out == "" {
		t.Skip("需要全新受控繪圖輸出")
	}
	if err := os.Mkdir(out, 0755); err != nil {
		t.Fatal(err)
	}
	e, control := encounterBatchEngine(t, dir, root), encounterBatchEngine(t, base, root)
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
				t.Fatal("配對PCM改變")
			}
		}
		for _, engine := range engines {
			engine.Frame()
		}
		if !bytes.Equal(observerGuestState(t, e), observerGuestState(t, control)) {
			t.Fatal("普通路徑配對完整客體改變")
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
	source, err := os.ReadFile(filepath.Join(root, "ENEMY.AY"))
	if err != nil {
		t.Fatal(err)
	}
	buffer := oracle.Addr{Seg: 0x8000}
	mode, dest := oracle.Addr{Seg: 0x0aa8, Off: 0x7484}, oracle.Addr{Seg: 0x0aa8, Off: 0x748a}
	var restores []func()
	var originalMemory []map[string]any
	for _, engine := range engines {
		engine := engine
		saved := append([]byte(nil), engine.Oracle.Bytes(buffer, len(bg))...)
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
				t.Fatal("受控RAM未完整恢復")
			}
		}
		defer restore()
		restores = append(restores, restore)
		originalMemory = append(originalMemory, map[string]any{"buffer_sha256": hash(saved), "DS": ds, "mode": m, "destination": d, "background_page": b})
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
			t.Fatal("受控原版繪圖改變客體")
		}
	}
	rows := []map[string]any{}
	for _, record := range []int{5, 8, 9} {
		for direction := 0; direction < 2; direction++ {
			for _, height := range []int{13, 25} {
				for _, page := range []uint16{0xa400, 0xa000} {
					for _, engine := range engines {
						engine.Oracle.WriteU16(dest, page)
					}
					call(0x99c, bg, 0, 0)
				}
				prefix := encounterBatchPrefix(source[record*1204:(record+1)*1204], direction, height)
				call(0x4f2, prefix, 20, uint16(112-height))
				before := observerGuestState(t, e)
				actual := e.Frame()
				if !bytes.Equal(before, observerGuestState(t, e)) || e.renderFault != nil {
					t.Fatal("Frame非純讀或來源故障", e.Status())
				}
				data, err := os.ReadFile(filepath.Join(cache, fmt.Sprintf("encounter-%02d-%d.rgba", record, direction)))
				if err != nil {
					t.Fatal(err)
				}
				want := image.NewRGBA(actual.Bounds())
				copy(want.Pix, e.Tracker.graphics.assets.Materials[battleBackgroundID].Tile.Pix)
				for y := 0; y < height*6; y++ {
					for x := 0; x < 192; x++ {
						src := (y*192 + x) * 4
						at := ((112-height)*6+y)*want.Stride + (480+x)*4
						alpha := uint32(data[src+3])
						for c := 0; c < 3; c++ {
							want.Pix[at+c] = uint8(min(255, uint32(data[src+c])+(uint32(want.Pix[at+c])*(255-alpha)+127)/255))
						}
					}
				}
				if !bytes.Equal(actual.Pix, want.Pix) {
					t.Fatalf("完整來源Frame不符 %d/%d/%d", record, direction, height)
				}
				name := fmt.Sprintf("encounter-%02d-%d-%02d.png", record, direction, height)
				f, err := os.OpenFile(filepath.Join(out, name), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
				if err != nil {
					t.Fatal(err)
				}
				err = png.Encode(f, actual)
				closeErr := f.Close()
				if err != nil || closeErr != nil {
					t.Fatal(err, closeErr)
				}
				rows = append(rows, map[string]any{"record": record, "direction": direction, "height": height, "id": encounterBatchID(record, direction, height), "png": name, "frame_sha256": hash(actual.Pix), "guest_state_sha256": hash(before), "pixels": actual.Bounds().Dx() * actual.Bounds().Dy(), "frame_pure": true, "paired_guest_equal": true})
			}
		}
	}
	for _, restore := range restores {
		restore()
	}
	report := map[string]any{"status": "PASS-controlled-source-render-not-natural-encounter", "cases": rows, "ordinary_prefix": "boot/new game/map/F1/back/F2/back", "source_renderer": true, "source_direct_calls": e.sourceDirectCalls, "old_overlay_compositions": e.Tracker.Stats.ComposedFrames, "controlled_memory": map[string]any{"buffer": "8000:0000", "bytes": len(bg), "DS": "0AA8", "mode": "DS:7484=1", "destination": "DS:748A=A400/A000", "background": "14D2:0196=A400", "original_values": originalMemory, "restored_and_verified": true}, "gameplay_changed": false}
	raw, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(out, "receipt.json"), append(raw, 10), 0644); err != nil {
		t.Fatal(err)
	}
}
