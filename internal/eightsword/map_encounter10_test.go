package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func encounter10TestPaths(t *testing.T) (string, string, string, string) {
	t.Helper()
	dir, base := os.Getenv("EIGHTSWORD_TEST_ENCOUNTER10_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ENCOUNTER10_BASE")
	root, cache := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_ENCOUNTER10_CACHE")
	if dir == "" || base == "" || root == "" || cache == "" {
		t.Skip("需要本機 038 素材、r38、原版與獨立快取")
	}
	return dir, base, root, cache
}

func TestMapEncounter10RealPrefixesAndIndependentCache(t *testing.T) {
	dir, base, root, cache := encounter10TestPaths(t)
	good, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer good.Close()
	old, err := Open(Options{Root: root, Assets: base, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer old.Close()
	if good.MapEncounter10Error != "" || good.MapEncounterError != "" || good.GraphicsError != "" || good.BattleActorError != "" || old.MapEncounter10Error != "" {
		t.Fatal(good.Status(), old.Status())
	}
	a, b := good.Tracker.graphics.assets, old.Tracker.graphics.assets
	if len(a.Actors) != len(b.Actors)+13 || len(a.ByNative) != len(b.ByNative)+13 || !reflect.DeepEqual(a.Materials, b.Materials) || !reflect.DeepEqual(a.BattleActors, b.BattleActors) || !reflect.DeepEqual(a.Effects, b.Effects) || !reflect.DeepEqual(good.Assets, old.Assets) {
		t.Fatal("new prefixes changed another group or font")
	}
	for id, actor := range b.Actors {
		if !reflect.DeepEqual(a.Actors[id], actor) || a.ActorSHA[id] != b.ActorSHA[id] {
			t.Fatalf("existing actor %d changed", id)
		}
	}
	expected, err := os.ReadFile(filepath.Join(cache, "encounter-10-art-r1", "encounter-10-cache-r1.rgba"))
	if err != nil || hash(expected) != "314e66eae62475a9076a3ea996885013dddb1f698d01c6466fd0a2bad27d4f74" {
		t.Fatal("independent cache missing or changed", err)
	}
	for i := 0; i < 13; i++ {
		height, id := 1+i*2, uint16(126+i)
		raw, err := os.ReadFile(filepath.Join(cache, "encounter-10-source-r1", fmt.Sprintf("encounter-first-%02d-h%02d-source.bin", i+1, height)))
		if err != nil {
			t.Fatal(err)
		}
		actor := a.Actors[id]
		if actor == nil || actor.NativeWidth != 64 || actor.NativeHeight != height || actor.Tile.Bounds().Dx() != 192 || actor.Tile.Bounds().Dy() != height*6 || a.BattleActors[id] || a.ByNative[hash(raw[:4+32*height])] != id || !good.Tracker.graphics.heroRecordMatches(id, 6, raw) {
			t.Fatalf("source height %d not registered", height)
		}
		if !bytes.Equal(actor.Tile.Pix[:192*height*6*4], expected[:192*height*6*4]) || &actor.Tile.Pix[0] != &a.Actors[126].Tile.Pix[0] {
			t.Fatalf("prefix %d rescaled or copied", height)
		}
		raw[len(raw)-1] ^= 1
		if good.Tracker.graphics.heroRecordMatches(id, 6, raw) {
			t.Fatal("changed sixth-plane mask accepted")
		}
	}
}

func TestMapEncounter10FaultsKeepExistingGroups(t *testing.T) {
	dir, base, root, _ := encounter10TestPaths(t)
	old, err := Open(Options{Root: root, Assets: base, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer old.Close()
	assets := old.Tracker.graphics.assets
	before, err := json.Marshal(assets.ByNative)
	if err != nil {
		t.Fatal(err)
	}
	count := len(assets.Actors)
	for _, kind := range []string{"missing", "png", "prompt", "unknown-field", "trailing", "late-id"} {
		t.Run(kind, func(t *testing.T) {
			out := t.TempDir()
			for _, name := range []string{"map-encounter-10.json", "battle-man16-0-r1.png", "battle-actors-prompts.txt"} {
				if kind == "missing" && name == "map-encounter-10.json" {
					continue
				}
				data, err := os.ReadFile(filepath.Join(dir, name))
				if err != nil {
					t.Fatal(err)
				}
				if (kind == "png" && name == "battle-man16-0-r1.png") || (kind == "prompt" && name == "battle-actors-prompts.txt") || (kind == "trailing" && name == "map-encounter-10.json") {
					data = append(data, 0)
				}
				if kind == "unknown-field" && name == "map-encounter-10.json" {
					var m map[string]any
					if err := json.Unmarshal(data, &m); err != nil {
						t.Fatal(err)
					}
					m["unexpected"] = true
					data, err = json.Marshal(m)
					if err != nil {
						t.Fatal(err)
					}
				}
				if err := os.WriteFile(filepath.Join(out, name), data, 0644); err != nil {
					t.Fatal(err)
				}
			}
			if kind == "late-id" {
				assets.Actors[138] = assets.Actors[85]
				defer delete(assets.Actors, 138)
			}
			err := loadMapEncounter10(out, root, assets)
			if (kind == "missing") != (err == nil) {
				t.Fatalf("unexpected result: %v", err)
			}
			after, err := json.Marshal(assets.ByNative)
			if err != nil || !bytes.Equal(before, after) {
				t.Fatal("failed group left registrations", err)
			}
			want := count
			if kind == "late-id" {
				want++
			}
			if len(assets.Actors) != want {
				t.Fatal("failed group left actors")
			}
		})
	}
}
