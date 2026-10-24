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

func encounterTestPaths(t *testing.T) (string, string, string, string) {
	t.Helper()
	dir, base := os.Getenv("EIGHTSWORD_TEST_ENCOUNTER_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ENCOUNTER_BASE")
	root, cache := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_ENCOUNTER_CACHE")
	if dir == "" || base == "" || root == "" || cache == "" {
		t.Skip("需要本機 037 素材、r37、原版與獨立快取")
	}
	return dir, base, root, cache
}

func TestMapEncounterRealPrefixesAndIndependentCache(t *testing.T) {
	dir, base, root, cache := encounterTestPaths(t)
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
	if good.MapEncounterError != "" || good.GraphicsError != "" || old.MapEncounterError != "" {
		t.Fatal(good.Status(), old.Status())
	}
	a, b := good.Tracker.graphics.assets, old.Tracker.graphics.assets
	if len(a.Actors) != len(b.Actors)+10 || len(a.ByNative) != len(b.ByNative)+10 || !reflect.DeepEqual(a.Materials, b.Materials) || !reflect.DeepEqual(a.BattleActors, b.BattleActors) || !reflect.DeepEqual(a.Effects, b.Effects) || !reflect.DeepEqual(good.Assets, old.Assets) {
		t.Fatal("new prefixes changed another group or font")
	}
	for id, actor := range b.Actors {
		if !reflect.DeepEqual(a.Actors[id], actor) || a.ActorSHA[id] != b.ActorSHA[id] {
			t.Fatalf("existing actor %d changed", id)
		}
	}
	expected, err := os.ReadFile(filepath.Join(cache, "encounter-13-cache-r1.rgba"))
	if err != nil || hash(expected) != "da28fb22a5c5b6c6e40dbaf0e3e59d9d7b283d7f61064d0710b9d7f2c015ab97" {
		t.Fatal("independent cache missing or changed", err)
	}
	for i := 0; i < 10; i++ {
		height, id := 7+i*2, encounterFirstID+uint16(i)
		raw, err := os.ReadFile(filepath.Join(cache, "encounter-source-r2", fmt.Sprintf("encounter-first-%02d-h%02d-source.bin", (height+1)/2, height)))
		if err != nil {
			t.Fatal(err)
		}
		actor := a.Actors[id]
		if actor == nil || actor.NativeWidth != 64 || actor.NativeHeight != height || actor.Tile.Bounds().Dx() != 192 || actor.Tile.Bounds().Dy() != height*6 || a.BattleActors[id] || a.ByNative[hash(raw[:4+32*height])] != id || !good.Tracker.graphics.heroRecordMatches(id, 6, raw) {
			t.Fatalf("actual source height %d not registered", height)
		}
		if !bytes.Equal(actor.Tile.Pix[:192*height*6*4], expected[:192*height*6*4]) || &actor.Tile.Pix[0] != &a.Actors[encounterFirstID].Tile.Pix[0] {
			t.Fatalf("prefix %d was rescaled or copied from another cache", height)
		}
		raw[len(raw)-1] ^= 1
		if good.Tracker.graphics.heroRecordMatches(id, 6, raw) {
			t.Fatal("changed sixth-plane mask accepted")
		}
	}
	for _, height := range []int{1, 3, 5} {
		raw, err := os.ReadFile(filepath.Join(cache, "encounter-source-r2", fmt.Sprintf("encounter-first-%02d-h%02d-source.bin", (height+1)/2, height)))
		if err != nil || a.ByNative[hash(raw[:4+32*height])] != b.ByNative[hash(raw[:4+32*height])] {
			t.Fatal("shared empty prefix changed", height, err)
		}
	}
}

func TestMapEncounterFaultsKeepExistingGroups(t *testing.T) {
	dir, base, root, _ := encounterTestPaths(t)
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
			for _, name := range []string{"map-encounter.json", "map-encounter-13-r1.png", "map-encounter-13-r1.prompt.txt"} {
				if kind == "missing" && name == "map-encounter.json" {
					continue
				}
				data, err := os.ReadFile(filepath.Join(dir, name))
				if err != nil {
					t.Fatal(err)
				}
				if (kind == "png" && name == "map-encounter-13-r1.png") || (kind == "prompt" && name == "map-encounter-13-r1.prompt.txt") || (kind == "trailing" && name == "map-encounter.json") {
					data = append(data, 0)
				}
				if kind == "unknown-field" && name == "map-encounter.json" {
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
				assets.Actors[125] = assets.Actors[85]
				defer delete(assets.Actors, 125)
			}
			err := loadMapEncounter(out, root, assets)
			if (kind == "missing") != (err == nil) {
				t.Fatalf("unexpected failure result: %v", err)
			}
			after, err := json.Marshal(assets.ByNative)
			if err != nil || !bytes.Equal(before, after) {
				t.Fatal("failed group left source registrations", err)
			}
			want := count
			if kind == "late-id" {
				want++
			}
			if len(assets.Actors) != want {
				t.Fatal("failed group left partial actors")
			}
		})
	}
}
