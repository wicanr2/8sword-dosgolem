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

func backgroundBatchPaths(t *testing.T) (string, string, string, string) {
	t.Helper()
	dir, base, root, cache := os.Getenv("EIGHTSWORD_TEST_BACKGROUNDS_ASSETS"), os.Getenv("EIGHTSWORD_TEST_BACKGROUNDS_BASE"), os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_BACKGROUNDS_CACHE")
	if dir == "" || base == "" || root == "" || cache == "" {
		t.Skip("需要050候選、r50、原版及獨立快取")
	}
	return dir, base, root, cache
}

func backgroundBatchEngine(t *testing.T, dir, root string) *Engine {
	t.Helper()
	e, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(e.Close)
	if !e.sourceEnabled || e.AssetError != "" || e.GraphicsError != "" || e.BattleBackgroundError != "" || e.BattleBackgroundBatchError != "" || e.BattleActorError != "" || e.MapEncounterBatchError != "" {
		t.Fatal(e.Status())
	}
	return e
}

func TestBackgroundBatchRealSourcesAndCaches(t *testing.T) {
	dir, base, root, cache := backgroundBatchPaths(t)
	e, old := backgroundBatchEngine(t, dir, root), backgroundBatchEngine(t, base, root)
	a, b := e.Tracker.graphics.assets, old.Tracker.graphics.assets
	if len(a.Materials) != len(b.Materials)+3 || len(a.ByNative) != len(b.ByNative)+3 || !reflect.DeepEqual(a.Actors, b.Actors) || !reflect.DeepEqual(a.ActorSHA, b.ActorSHA) || !reflect.DeepEqual(a.BattleActors, b.BattleActors) || !reflect.DeepEqual(a.BattleAliases, b.BattleAliases) || !reflect.DeepEqual(a.Effects, b.Effects) || !reflect.DeepEqual(a.EffectSHA, b.EffectSHA) || !reflect.DeepEqual(e.Assets, old.Assets) {
		t.Fatal("背景更動原有角色／效果／字型")
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
	for i, group := range battleBackgroundGroups {
		data, err := os.ReadFile(filepath.Join(cache, fmt.Sprintf("gro%02d-background.rgba", i+3)))
		if err != nil {
			t.Fatal(err)
		}
		m := a.Materials[uint16(844+i)]
		if m == nil || m.NativeWidth != 640 || m.NativeHeight != 200 || m.Tile.Bounds() != image.Rect(0, 0, 1920, 1200) || !bytes.Equal(m.Tile.Pix, data) || a.ByNative[group.NativeSHA] != uint16(844+i) {
			t.Fatal("完整快取不符", group.Source)
		}
	}
}

func TestBackgroundBatchFailureAtomic(t *testing.T) {
	dir, _, root, _ := backgroundBatchPaths(t)
	e := backgroundBatchEngine(t, dir, root)
	original := e.Tracker.graphics.assets
	for _, kind := range []string{"missing", "manifest", "prompt", "image", "source", "collision", "native-alias"} {
		t.Run(kind, func(t *testing.T) {
			a := *original
			a.Materials = maps.Clone(original.Materials)
			a.ByNative = maps.Clone(original.ByNative)
			delete(a.Materials, 845)
			delete(a.ByNative, battleBackgroundGroups[1].NativeSHA)
			if kind == "collision" {
				a.Materials[845] = original.Materials[844]
			}
			if kind == "native-alias" {
				a.ByNative["other-source"] = 845
			}
			before := a
			before.Materials = maps.Clone(a.Materials)
			before.ByNative = maps.Clone(a.ByNative)
			assets, source := t.TempDir(), root
			if kind != "missing" {
				for _, name := range []string{"battle-gro04.json", "gro04-hd-r1.png", "gro04-hd-r1.prompt.txt"} {
					data, err := os.ReadFile(filepath.Join(dir, name))
					if err != nil {
						t.Fatal(err)
					}
					if kind == "manifest" && name == "battle-gro04.json" || kind == "prompt" && name == "gro04-hd-r1.prompt.txt" || kind == "image" && name == "gro04-hd-r1.png" {
						data = append(data, 0)
					}
					if err := os.WriteFile(filepath.Join(assets, name), data, 0644); err != nil {
						t.Fatal(err)
					}
				}
			}
			if kind == "source" {
				source = t.TempDir()
				data, err := os.ReadFile(filepath.Join(root, "GRO04.EG"))
				if err != nil {
					t.Fatal(err)
				}
				data[0] ^= 1
				if err := os.WriteFile(filepath.Join(source, "GRO04.EG"), data, 0644); err != nil {
					t.Fatal(err)
				}
			}
			err := loadBattleBackgroundGroup(assets, source, &a, 1)
			if (err == nil) != (kind == "missing") || !reflect.DeepEqual(before, a) {
				t.Fatal("失敗組部分提交", kind, err)
			}
		})
	}
}

func TestBackgroundBatchOwnershipQualification(t *testing.T) {
	assets := &GraphicsAssets{Materials: map[uint16]*graphicMaterial{}}
	tile := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	for id := uint16(844); id <= 846; id++ {
		assets.Materials[id] = &graphicMaterial{640, 200, tile}
	}
	g := &Graphics{assets: assets, owners: make([]graphicCell, 65536*8)}
	first := uint32(0x4000 + 60*80 + 20)
	for id := uint16(844); id <= 846; id++ {
		for y := 0; y < 50; y++ {
			for x := 0; x < 88; x++ {
				g.owners[(first+uint32(y*80+x/8))*8+uint32(x%8)] = graphicCell{id, uint32((60+y)*640 + 160 + x)}
			}
		}
		if !g.battleBackgroundKnown(first, 88, 50) {
			t.Fatal("已核對背景被拒絕", id)
		}
		at := (first+uint32(49*80+10))*8 + 7
		original := g.owners[at]
		for _, bad := range []graphicCell{{}, {uint16(844 + (int(id)-843)%3), original.Local}, {id, 128000}} {
			g.owners[at] = bad
			if g.battleBackgroundKnown(first, 88, 50) {
				t.Fatal("混合／未知／越界背景被接受")
			}
		}
		g.owners[at] = original
	}
	if isBattleBackgroundMaterial(843) || isBattleBackgroundMaterial(847) {
		t.Fatal("接受非固定背景識別")
	}
	assets.Materials[846].Tile = nil
	if g.battleBackgroundKnown(first, 88, 50) || g.battleBackgroundKnown(65535, 88, 50) {
		t.Fatal("接受缺圖或越界")
	}
}

// Controlled memory presentation, never a natural combat or terrain-rule claim.
func TestBackgroundBatchControlledSourceDraw(t *testing.T) {
	dir, base, root, cache := backgroundBatchPaths(t)
	out := os.Getenv("EIGHTSWORD_TEST_BACKGROUNDS_OUT")
	if out == "" {
		t.Skip("需要全新受控輸出")
	}
	if err := os.Mkdir(out, 0755); err != nil {
		t.Fatal(err)
	}
	e, control := backgroundBatchEngine(t, dir, root), backgroundBatchEngine(t, base, root)
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
			t.Fatal("受控繪圖客體改變")
		}
	}
	actor, err := os.ReadFile(filepath.Join(root, "MAN02.EGG"))
	if err != nil {
		t.Fatal(err)
	}
	actor = actor[:3304]
	actorCache, err := os.ReadFile(filepath.Join(cache, "man02-0.rgba"))
	if err != nil || len(actorCache) != 264*300*4 {
		t.Fatal("缺少獨立角色快取", err)
	}
	rows := []map[string]any{}
	for i, group := range battleBackgroundGroups {
		bg, err := os.ReadFile(filepath.Join(cache, fmt.Sprintf("gro%02d-native.bin", i+3)))
		if err != nil || hash(bg) != group.NativeSHA {
			t.Fatal("原生背景不符", err)
		}
		bgCache, err := os.ReadFile(filepath.Join(cache, fmt.Sprintf("gro%02d-background.rgba", i+3)))
		if err != nil {
			t.Fatal(err)
		}
		for _, page := range []uint16{0xa400, 0xa000} {
			for _, engine := range engines {
				engine.Oracle.WriteU16(dest, page)
			}
			call(0x99c, bg, 0, 0)
		}
		for _, stage := range []string{"background", "actor", "restored"} {
			if stage == "actor" {
				call(0x626, actor, 20, 60)
			}
			if stage == "restored" {
				call(0x423, actor, 20, 60)
			}
			before := observerGuestState(t, e)
			frame := e.Frame()
			if !bytes.Equal(before, observerGuestState(t, e)) || e.renderFault != nil {
				t.Fatal("來源Frame非純讀或故障", e.Status())
			}
			want := image.NewRGBA(frame.Bounds())
			copy(want.Pix, bgCache)
			if stage == "actor" {
				for y := 0; y < 300; y++ {
					for x := 0; x < 264; x++ {
						src := (y*264 + x) * 4
						at := (360+y)*want.Stride + (480+x)*4
						alpha := uint32(actorCache[src+3])
						for c := 0; c < 3; c++ {
							want.Pix[at+c] = uint8(min(255, uint32(actorCache[src+c])+(uint32(want.Pix[at+c])*(255-alpha)+127)/255))
						}
					}
				}
			}
			if !bytes.Equal(frame.Pix, want.Pix) {
				t.Fatalf("完整背景／角色／還原不符 %s/%s", group.Source, stage)
			}
			name := fmt.Sprintf("gro%02d-%s.png", i+3, stage)
			f, err := os.OpenFile(filepath.Join(out, name), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
			if err != nil {
				t.Fatal(err)
			}
			err = png.Encode(f, frame)
			closeErr := f.Close()
			if err != nil || closeErr != nil {
				t.Fatal(err, closeErr)
			}
			rows = append(rows, map[string]any{"source": group.Source, "stage": stage, "png": name, "pixels": 2304000, "frame_sha256": hash(frame.Pix), "guest_state_sha256": hash(before), "frame_pure": true, "paired_guest_equal": true})
		}
	}
	for _, restore := range restores {
		restore()
	}
	if e.Tracker.Stats.ComposedFrames != 0 {
		t.Fatal("使用舊合成器")
	}
	report := map[string]any{"status": "PASS-controlled-background-source-render-not-natural-combat", "cases": rows, "ordinary_prefix": "boot/new game/map/F1/back/F2/back", "source_renderer": true, "source_direct_calls": e.sourceDirectCalls, "old_overlay_compositions": e.Tracker.Stats.ComposedFrames, "gameplay_changed": false, "controlled_memory": map[string]any{"buffer": "8000:0000", "bytes": 64004, "DS": "0AA8", "mode": "DS:7484=1", "destination": "DS:748A=A400/A000", "background": "14D2:0196=A400", "original_values": originals, "restored_and_verified": true}}
	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(out, "receipt.json"), append(data, 10), 0644); err != nil {
		t.Fatal(err)
	}
}
