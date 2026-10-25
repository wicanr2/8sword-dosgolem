package eightsword

import (
	"bytes"
	"encoding/json"
	"image"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func palacePaths(t *testing.T) (string, string, string, string) {
	t.Helper()
	dir, base := os.Getenv("EIGHTSWORD_TEST_PALACE_ASSETS"), os.Getenv("EIGHTSWORD_TEST_PALACE_BASE")
	root, cache := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_PALACE_CACHE")
	if dir == "" || base == "" || root == "" || cache == "" {
		t.Skip("需要046候選、r46、固定原版與獨立快取")
	}
	return dir, base, root, cache
}

func TestBattlePalaceSourceAndIndependentCache(t *testing.T) {
	dir, base, root, cache := palacePaths(t)
	old, err := Open(Options{Root: root, Assets: base, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer old.Close()
	good, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer good.Close()
	if good.BattleBackgroundError != "" || good.BattleActorError != "" || good.GraphicsError != "" || old.BattleBackgroundError != "" || !good.HD {
		t.Fatal(good.Status())
	}
	a, b := good.Tracker.graphics.assets, old.Tracker.graphics.assets
	if len(a.Materials) != len(b.Materials)+1 || len(a.ByNative) != len(b.ByNative)+1 || !reflect.DeepEqual(a.Native, b.Native) || !reflect.DeepEqual(a.Actors, b.Actors) || !reflect.DeepEqual(a.ActorSHA, b.ActorSHA) || !reflect.DeepEqual(a.BattleActors, b.BattleActors) || !reflect.DeepEqual(a.Effects, b.Effects) || !reflect.DeepEqual(a.EffectSHA, b.EffectSHA) || !reflect.DeepEqual(good.Assets, old.Assets) {
		t.Fatal("攻城背景改變既有圖像、字型或來源")
	}
	for id, entry := range b.Materials {
		if !reflect.DeepEqual(a.Materials[id], entry) {
			t.Fatalf("材質%d改變", id)
		}
	}
	for source, id := range b.ByNative {
		if a.ByNative[source] != id {
			t.Fatal("既有原生來源改變")
		}
	}
	expected, err := os.ReadFile(filepath.Join(cache, "palace-background.rgba"))
	if err != nil || hash(expected) != battlePalaceCacheSHA {
		t.Fatal("獨立攻城快取不符", err)
	}
	m := a.Materials[battlePalaceID]
	if m == nil || m.NativeWidth != 640 || m.NativeHeight != 200 || !bytes.Equal(m.Tile.Pix, expected) || a.ByNative[battlePalaceNativeSHA] != battlePalaceID || a.Actors[152] != nil {
		t.Fatal("攻城背景來源、完整快取或友軍組隔離不符")
	}
}

func TestBattlePalaceFaultsAreAtomic(t *testing.T) {
	dir, base, root, _ := palacePaths(t)
	e, err := Open(Options{Root: root, Assets: base, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	a := e.Tracker.graphics.assets
	manifest, err := os.ReadFile(filepath.Join(dir, "battle-palace-background.json"))
	if err != nil {
		t.Fatal(err)
	}
	pngBytes, err := os.ReadFile(filepath.Join(dir, "battle-palace-background-r1.png"))
	if err != nil {
		t.Fatal(err)
	}
	for _, kind := range []string{"missing", "malformed", "unknown-field", "trailing", "oversize", "source", "corrupt-source", "cache", "filename", "bad-image", "missing-image", "symlink-manifest", "symlink-image", "id-collision", "native-alias"} {
		t.Run(kind, func(t *testing.T) {
			out := t.TempDir()
			data := append([]byte(nil), manifest...)
			sourceRoot := root
			if kind == "malformed" {
				data = []byte("{")
			}
			if kind == "corrupt-source" {
				sourceRoot = t.TempDir()
				source, err := os.ReadFile(filepath.Join(root, "GRO01.EG"))
				if err != nil {
					t.Fatal(err)
				}
				source[len(source)/2] ^= 1
				if err = os.WriteFile(filepath.Join(sourceRoot, "GRO01.EG"), source, 0644); err != nil {
					t.Fatal(err)
				}
			}
			if kind == "unknown-field" || kind == "source" || kind == "cache" || kind == "filename" {
				var m map[string]any
				if err := json.Unmarshal(data, &m); err != nil {
					t.Fatal(err)
				}
				switch kind {
				case "unknown-field":
					m["unknown"] = true
				case "source":
					m["source_sha256"] = "wrong"
				case "cache":
					m["cache_sha256"] = "wrong"
				case "filename":
					m["image"].(map[string]any)["file"] = "../other.png"
				}
				data, err = json.Marshal(m)
				if err != nil {
					t.Fatal(err)
				}
			}
			if kind == "trailing" {
				data = append(data, []byte("{}")...)
			}
			if kind == "oversize" {
				data = append(data, bytes.Repeat([]byte(" "), 16384)...)
			}
			if kind != "missing" {
				path := filepath.Join(out, "battle-palace-background.json")
				if kind == "symlink-manifest" {
					err = os.Symlink(filepath.Join(dir, "battle-palace-background.json"), path)
				} else {
					err = os.WriteFile(path, data, 0644)
				}
				if err != nil {
					t.Fatal(err)
				}
			}
			if kind != "missing-image" {
				path := filepath.Join(out, "battle-palace-background-r1.png")
				imageData := append([]byte(nil), pngBytes...)
				if kind == "bad-image" {
					imageData[len(imageData)/2] ^= 1
				}
				if kind == "symlink-image" {
					err = os.Symlink(filepath.Join(dir, "battle-palace-background-r1.png"), path)
				} else {
					err = os.WriteFile(path, imageData, 0644)
				}
				if err != nil {
					t.Fatal(err)
				}
			}
			if kind == "id-collision" {
				a.Effects[battlePalaceID] = a.Effects[103]
				defer delete(a.Effects, battlePalaceID)
			}
			if kind == "native-alias" {
				a.ByNative["other-native"] = battlePalaceID
				defer delete(a.ByNative, "other-native")
			}
			before, err := json.Marshal(a)
			if err != nil {
				t.Fatal(err)
			}
			err = loadBattlePalaceBackground(out, sourceRoot, a)
			if (kind == "missing") != (err == nil) {
				t.Fatalf("預期回退不符：%v", err)
			}
			after, err := json.Marshal(a)
			if err != nil || !bytes.Equal(before, after) {
				t.Fatal("故障群改變既有素材", err)
			}
		})
	}
}

func TestBattlePalaceLoadsWhenGRO02Fails(t *testing.T) {
	dir, _, root, _ := palacePaths(t)
	out := t.TempDir()
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		data, err := os.ReadFile(filepath.Join(dir, entry.Name()))
		if err != nil {
			t.Fatal(err)
		}
		if entry.Name() == "battle-background-r1.png" {
			data[len(data)/2] ^= 1
		}
		if err = os.WriteFile(filepath.Join(out, entry.Name()), data, 0644); err != nil {
			t.Fatal(err)
		}
	}
	e, err := Open(Options{Root: root, Assets: out, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	if e.BattleBackgroundError == "" || e.GraphicsError != "" || !e.HD || e.Tracker.graphics.assets.Materials[battlePalaceID] == nil || e.Tracker.graphics.assets.Materials[battleBackgroundID] != nil {
		t.Fatal("GRO02故障阻擋獨立攻城背景", e.Status())
	}
}

// Diagnostic ownership failures; normal guest return evidence is separate.
func TestBattleBackgroundOwnershipRejectsMixedPages(t *testing.T) {
	assets := &GraphicsAssets{Materials: map[uint16]*graphicMaterial{}}
	tile := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	assets.Materials[battleBackgroundID] = &graphicMaterial{640, 200, tile}
	assets.Materials[battlePalaceID] = &graphicMaterial{640, 200, tile}
	g := &Graphics{assets: assets, owners: make([]graphicCell, 65536*8)}
	first := uint32(0x4000 + 100*80 + 23)
	for _, id := range []uint16{battleBackgroundID, battlePalaceID} {
		for y := 0; y < 50; y++ {
			for x := 0; x < 88; x++ {
				g.owners[(first+uint32(y*80+x/8))*8+uint32(x%8)] = graphicCell{id, uint32((100+y)*640 + 23*8 + x)}
			}
		}
		if !g.battleBackgroundKnown(first, 88, 50) {
			t.Fatal("完整已知背景被拒絕")
		}
		at := (first+uint32(49*80+10))*8 + 7
		original := g.owners[at]
		for _, bad := range []graphicCell{{}, {86 + 151 - id, original.Local}, {id, 128000}} {
			g.owners[at] = bad
			if g.battleBackgroundKnown(first, 88, 50) {
				t.Fatal("未知、混合或越界背景被接受")
			}
		}
		g.owners[at] = original
	}
	assets.Materials[battlePalaceID].Tile = nil
	if g.battleBackgroundKnown(first, 88, 50) || g.battleBackgroundKnown(65535, 88, 50) {
		t.Fatal("缺失快取或實體越界被接受")
	}
}
