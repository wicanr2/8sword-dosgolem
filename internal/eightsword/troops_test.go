package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/png"
	"maps"
	"math/bits"
	"os"
	"path/filepath"
	"reflect"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

func troopTestPaths(t *testing.T) (string, string, string, string) {
	t.Helper()
	dir, base, root, cache := os.Getenv("EIGHTSWORD_TEST_TROOPS_ASSETS"), os.Getenv("EIGHTSWORD_TEST_TROOPS_BASE"), os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_TROOPS_CACHE")
	if dir == "" || base == "" || root == "" || cache == "" {
		t.Skip("需要048本機候選、r48、原版及獨立快取")
	}
	return dir, base, root, cache
}

func troopEngine(t *testing.T, dir, root string) *Engine {
	t.Helper()
	e, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(e.Close)
	if e.BattleActorError != "" || e.GraphicsError != "" || e.AssetError != "" {
		t.Fatal(e.Status())
	}
	return e
}

func TestTroopsRealSourcesAndIndependentCaches(t *testing.T) {
	dir, base, root, cache := troopTestPaths(t)
	e, old := troopEngine(t, dir, root), troopEngine(t, base, root)
	a, b := e.Tracker.graphics.assets, old.Tracker.graphics.assets
	if len(a.Actors) != len(b.Actors)+320 || len(a.BattleActors) != len(b.BattleActors)+160 || len(a.BattleAliases) != 160 {
		t.Fatal("未完整載入兩向、軍隊及戰場別名")
	}
	if !reflect.DeepEqual(a.Materials, b.Materials) || !reflect.DeepEqual(a.Effects, b.Effects) || !reflect.DeepEqual(e.Assets, old.Assets) {
		t.Fatal("舊材質、效果或字型改變")
	}
	for id, m := range b.Actors {
		if a.ActorSHA[id] != b.ActorSHA[id] || !bytes.Equal(a.Actors[id].Tile.Pix, m.Tile.Pix) {
			t.Fatalf("舊角色%d改變", id)
		}
	}
	for key, id := range b.ByNative {
		if a.ByNative[key] != id {
			t.Fatal("舊來源對應改變")
		}
	}
	for gi, group := range troopGroups {
		stem := fmt.Sprintf("troop-man%s", group.Source[3:5])
		raw, err := os.ReadFile(filepath.Join(root, group.Source))
		if err != nil {
			t.Fatal(err)
		}
		for ri := 0; ri < 4; ri++ {
			record := raw[ri*3304 : (ri+1)*3304]
			mirrored := append([]byte(nil), record...)
			for row := 4; row < 3304; row += 11 {
				for x := 0; x < 11; x++ {
					mirrored[row+x] = bits.Reverse8(record[row+10-x])
				}
			}
			for di, source := range [][]byte{record, mirrored} {
				id := uint16(160 + gi*16 + ri*4 + di*2)
				m := a.Actors[id]
				if a.ByNative[hash(source[:2204])] != id || a.BattleAliases[id] != id+1 || a.Actors[id+1] != m || a.BattleActors[id] || !a.BattleActors[id+1] || !e.Tracker.graphics.heroRecordMatches(id, 6, source) || !e.Tracker.graphics.heroRecordMatches(id+1, 6, source) {
					t.Fatalf("來源／別名不符 %s/%d/%d", group.Source, ri, di)
				}
				want, err := os.ReadFile(filepath.Join(cache, fmt.Sprintf("%s-%d-%d.rgba", stem, ri, di)))
				if err != nil {
					t.Fatal(err)
				}
				if !bytes.Equal(want, m.Tile.Pix) {
					t.Fatalf("獨立取樣不符 %s/%d/%d", group.Source, ri, di)
				}
				bad := append([]byte(nil), source...)
				bad[3303] ^= 1
				if e.Tracker.graphics.heroRecordMatches(id, 6, bad) || e.Tracker.graphics.heroRecordMatches(id, 5, source) {
					t.Fatal("接受未知遮罩或錯誤平面")
				}
			}
		}
	}
}

func TestTroopsGroupFailureIsAtomic(t *testing.T) {
	dir, _, root, _ := troopTestPaths(t)
	e := troopEngine(t, dir, root)
	original := e.Tracker.graphics.assets
	for _, kind := range []string{"manifest", "last-png", "source", "missing", "collision"} {
		t.Run(kind, func(t *testing.T) {
			a := *original
			a.ByNative = maps.Clone(original.ByNative)
			a.Actors = maps.Clone(original.Actors)
			a.ActorSHA = maps.Clone(original.ActorSHA)
			a.BattleActors = maps.Clone(original.BattleActors)
			a.BattleAliases = maps.Clone(original.BattleAliases)
			for k, id := range a.ByNative {
				if id >= 160 && id < 176 {
					delete(a.ByNative, k)
				}
			}
			for id := uint16(160); id < 176; id++ {
				delete(a.Actors, id)
				delete(a.ActorSHA, id)
				delete(a.BattleActors, id)
				delete(a.BattleAliases, id)
			}
			if kind == "collision" {
				a.Actors[175] = original.Actors[175]
			}
			before := a
			before.ByNative = maps.Clone(a.ByNative)
			before.Actors = maps.Clone(a.Actors)
			before.ActorSHA = maps.Clone(a.ActorSHA)
			before.BattleActors = maps.Clone(a.BattleActors)
			before.BattleAliases = maps.Clone(a.BattleAliases)
			assets, source := t.TempDir(), root
			if kind != "missing" {
				for _, name := range []string{"troop-man02.json", "troop-man02-0-r1.png", "troop-man02-1-r1.png", "troop-man02-2-r1.png", "troop-man02-3-r1.png"} {
					raw, err := os.ReadFile(filepath.Join(dir, name))
					if err != nil {
						t.Fatal(err)
					}
					if kind == "manifest" && name == "troop-man02.json" || kind == "last-png" && name == "troop-man02-3-r1.png" {
						raw = append(raw, 0)
					}
					if err := os.WriteFile(filepath.Join(assets, name), raw, 0644); err != nil {
						t.Fatal(err)
					}
				}
			}
			if kind == "source" {
				source = t.TempDir()
				raw, err := os.ReadFile(filepath.Join(root, "MAN02.EGG"))
				if err != nil {
					t.Fatal(err)
				}
				raw[3303] ^= 1
				if err := os.WriteFile(filepath.Join(source, "MAN02.EGG"), raw, 0644); err != nil {
					t.Fatal(err)
				}
			}
			err := loadTroopGroup(assets, source, &a, 0)
			if (err == nil) != (kind == "missing") {
				t.Fatalf("拒絕結果不符 %s: %v", kind, err)
			}
			if !reflect.DeepEqual(before, a) {
				t.Fatal("失敗組留下部分角色或影響其他組")
			}
		})
	}
}

// Explicit controlled-memory presentation checks, not natural encounters or rule parity.
// Boot and menu inputs are ordinary; only the following local draw fixture writes RAM.
func TestTroopsControlledOriginalDraw(t *testing.T) {
	dir, _, root, cache := troopTestPaths(t)
	out := os.Getenv("EIGHTSWORD_TEST_TROOPS_OUT")
	if out == "" {
		t.Skip("需要獨立的受控繪圖收據目錄")
	}
	if err := os.Mkdir(out, 0755); err != nil {
		t.Fatal(err)
	}
	e := storyEngine(t, dir)
	e.Oracle.SetClock(12, 0, 0, 0)
	advance := func(ms int) { storyAdvance(t, e, ms); e.Frame() }
	press := func(scan byte) { storyPress(t, e, scan); e.Frame() }
	wait := func(scene string) {
		t.Helper()
		for n := 0; n < 300 && e.Tracker.VisibleScene != scene; n++ {
			advance(100)
		}
		if e.Tracker.VisibleScene != scene {
			t.Fatalf("普通選單未到%s: %v", scene, e.Status())
		}
	}
	advance(1000)
	press(2)
	press(2)
	advance(1000)
	press(1)
	wait("main-menu")
	press(0x50)
	press(0x1c)
	wait("new-game-confirm")
	press(0x1c)
	wait("map")
	press(0x3b)
	wait("character")
	press(1)
	wait("map")
	press(0x3c)
	advance(300)
	press(1)
	wait("map")
	if e.BattleActorError != "" || len(e.Oracle.Unimplemented()) != 0 {
		t.Fatal(e.Status())
	}
	g := e.Tracker.graphics
	bg, err := os.ReadFile(filepath.Join(cache, "gro02-native.bin"))
	if err != nil {
		t.Fatal(err)
	}
	if len(bg) != 64004 || hash(bg) != battleBackgroundNativeSHA {
		t.Fatal("GRO02原始繪圖資料不符")
	}
	buffer := oracle.Addr{Seg: 0x8000, Off: 0}
	saved := append([]byte(nil), e.Oracle.Bytes(buffer, len(bg))...)
	savedDS := e.Oracle.Regs().DS
	e.Oracle.SetRegs(oracle.CallRegs{DS: 0x0aa8, SetDS: true})
	mode, dest := oracle.Addr{Seg: 0x0aa8, Off: 0x7484}, oracle.Addr{Seg: 0x0aa8, Off: 0x748a}
	oldMode, oldDest := e.Oracle.Word(mode), e.Oracle.Word(dest)
	oldBack := e.Oracle.Word(oracle.Addr{Seg: e.Tracker.stringSeg, Off: 0x196})
	defer func() {
		e.Oracle.WriteBytes(buffer, saved)
		e.Oracle.WriteU16(mode, oldMode)
		e.Oracle.WriteU16(dest, oldDest)
		e.Oracle.WriteU16(oracle.Addr{Seg: e.Tracker.stringSeg, Off: 0x196}, oldBack)
		e.Oracle.SetRegs(oracle.CallRegs{DS: savedDS, SetDS: true})
	}()
	e.Oracle.WriteU16(mode, 1)
	e.Oracle.WriteU16(oracle.Addr{Seg: e.Tracker.stringSeg, Off: 0x196}, 0xa400)
	call := func(entry uint16, raw []byte, x, y uint16) {
		t.Helper()
		e.Oracle.WriteBytes(buffer, raw)
		if _, err := e.Oracle.CallBudget(500000, oracle.Addr{Seg: e.Tracker.stringSeg, Off: entry}, buffer.Off, buffer.Seg, x, y); err != nil {
			t.Fatal(err)
		}
	}
	drawBackground := func() {
		t.Helper()
		for _, page := range []uint16{0xa400, 0xa000} {
			e.Oracle.WriteU16(dest, page)
			call(0x99c, bg, 0, 0)
		}
	}
	rows := []map[string]any{}
	for _, gi := range []int{0, 5, 15} { // MAN02 infantry, MAN08 ghost and MAN20 dragon.
		raw, err := os.ReadFile(filepath.Join(root, troopGroups[gi].Source))
		if err != nil {
			t.Fatal(err)
		}
		for di := 0; di < 2; di++ {
			for _, battle := range []bool{false, true} {
				drawBackground()
				record := append([]byte(nil), raw[:3304]...)
				if di == 1 {
					for row := 4; row < 3304; row += 11 {
						for x := 0; x < 11; x++ {
							record[row+x] = bits.Reverse8(raw[row+10-x])
						}
					}
				}
				id, entry := uint16(160+gi*16+di*2), uint16(0x4f2)
				if battle {
					id++
					entry = 0x626
				}
				beforeCalls := g.Stats.ActorCompletions + g.Stats.BattleActorCompletions
				call(entry, record, 20, 60)
				before := observerGuestState(t, e)
				actual := e.Frame()
				if !bytes.Equal(before, observerGuestState(t, e)) {
					t.Fatal("Frame改變客體")
				}
				if g.Stats.ActorCompletions+g.Stats.BattleActorCompletions != beforeCalls+1 {
					t.Fatalf("原版繪圖未提交HD角色%d: %+v", id, g.Stats)
				}
				want := image.NewRGBA(actual.Bounds())
				copy(want.Pix, g.assets.Materials[battleBackgroundID].Tile.Pix)
				tile := g.assets.Actors[id].Tile
				for y := 0; y < 300; y++ {
					for x := 0; x < 264; x++ {
						src := (y*264 + x) * 4
						at := ((360 + y) * want.Stride) + (480+x)*4
						alpha := uint32(tile.Pix[src+3])
						for c := 0; c < 3; c++ {
							want.Pix[at+c] = uint8(min(255, uint32(tile.Pix[src+c])+(uint32(want.Pix[at+c])*(255-alpha)+127)/255))
						}
					}
				}
				if !bytes.Equal(actual.Pix, want.Pix) {
					t.Fatalf("受控完整畫面與獨立背景／角色模型不符 %d", id)
				}
				name := fmt.Sprintf("%s-%d-%t.png", troopGroups[gi].Source, di, battle)
				f, err := os.OpenFile(filepath.Join(out, name), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
				if err != nil {
					t.Fatal(err)
				}
				err = png.Encode(f, actual)
				closeErr := f.Close()
				if err != nil || closeErr != nil {
					t.Fatal(err, closeErr)
				}
				rows = append(rows, map[string]any{"resource": troopGroups[gi].Source, "record": 0, "mirrored": di == 1, "battle": battle, "id": id, "entry": fmt.Sprintf("%04X:%04X", e.Tracker.stringSeg, entry), "frame_sha256": hash(actual.Pix), "pixels": actual.Bounds().Dx() * actual.Bounds().Dy(), "frame_pure": true, "png": name})
			}
		}
	}
	report := map[string]any{"status": "PASS-controlled-original-draw-not-natural-encounter", "cases": rows, "controlled_memory": map[string]any{"source_buffer": "8000:0000", "bytes": len(bg), "original_buffer_sha256": hash(saved), "DS": "0AA8", "mode": "DS:7484=1", "destination": "DS:748A=A400/A000", "background_page": "14D2:0196=A400"}, "ordinary_prefix": "boot/menu/new game/map/F1/back/F2/back", "rules_changed": false, "source_files_unchanged": true}
	r, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(out, "receipt.json"), append(r, 10), 0644); err != nil {
		t.Fatal(err)
	}
}
