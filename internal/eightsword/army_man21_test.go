package eightsword

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func army21Paths(t *testing.T) (string, string, string, string) {
	t.Helper()
	dir, base := os.Getenv("EIGHTSWORD_TEST_ARMY21_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ARMY21_BASE")
	root, cache := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_ARMY21_CACHE")
	if dir == "" || base == "" || root == "" || cache == "" {
		t.Skip("需要本機 041 候選、r39、原版與獨立快取")
	}
	return dir, base, root, cache
}

func TestArmy21RealSourceAndIndependentMirror(t *testing.T) {
	dir, base, root, cache := army21Paths(t)
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
	if good.ArmyMan21Error != "" || old.ArmyMan21Error != "" || good.GraphicsError != "" || good.BattleActorError != "" {
		t.Fatal(good.Status(), old.Status())
	}
	a, b := good.Tracker.graphics.assets, old.Tracker.graphics.assets
	if len(a.Actors) != len(b.Actors)+1 || len(a.ByNative) != len(b.ByNative)+1 || len(a.ActorSHA) != len(b.ActorSHA)+1 || !reflect.DeepEqual(a.Materials, b.Materials) || !reflect.DeepEqual(a.BattleActors, b.BattleActors) || !reflect.DeepEqual(a.Effects, b.Effects) || !reflect.DeepEqual(good.Assets, old.Assets) {
		t.Fatal("army alias changed another group or font")
	}
	for id, actor := range b.Actors {
		if !reflect.DeepEqual(a.Actors[id], actor) || a.ActorSHA[id] != b.ActorSHA[id] {
			t.Fatalf("existing actor %d changed", id)
		}
	}
	for key, id := range b.ByNative {
		if a.ByNative[key] != id {
			t.Fatal("existing native source changed")
		}
	}
	expected, err := os.ReadFile(filepath.Join(cache, "army21-mirror-cache-r1.rgba"))
	if err != nil || hash(expected) != armyMan21MirrorCacheSHA {
		t.Fatal("independent mirror missing", err)
	}
	actor := a.Actors[150]
	if actor == nil || actor.NativeWidth != 88 || actor.NativeHeight != 50 || !bytes.Equal(actor.Tile.Pix, expected) || &actor.Tile.Pix[0] == &a.Actors[99].Tile.Pix[0] || a.BattleActors[150] {
		t.Fatal("alias was resampled, shared mutable bytes, or registered as a battle actor")
	}
	for _, prefix := range []string{"unit21-01", "unit21-02", "unit21-03"} {
		raw, err := os.ReadFile(filepath.Join(cache, "army21-source-r1", prefix+"-source.bin"))
		if err != nil {
			t.Fatal(err)
		}
		if a.ByNative[hash(raw[:2204])] != 150 || !good.Tracker.graphics.heroRecordMatches(150, 6, raw) {
			t.Fatal("actual F2/F3 source not recognized")
		}
		raw[len(raw)-1] ^= 1
		if good.Tracker.graphics.heroRecordMatches(150, 6, raw) {
			t.Fatal("changed sixth-plane mask accepted")
		}
	}
}

func TestArmy21FaultsKeepOriginalCaches(t *testing.T) {
	dir, base, root, _ := army21Paths(t)
	old, err := Open(Options{Root: root, Assets: base, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer old.Close()
	a := old.Tracker.graphics.assets
	before, _ := json.Marshal(a.ByNative)
	count := len(a.Actors)
	original := append([]byte(nil), a.Actors[99].Tile.Pix...)
	for _, kind := range []string{"missing", "unknown-field", "trailing", "cache-sha", "source", "missing-original", "id-collision"} {
		t.Run(kind, func(t *testing.T) {
			out, sourceRoot := t.TempDir(), root
			if kind != "missing" {
				raw, err := os.ReadFile(filepath.Join(dir, "army-man21.json"))
				if err != nil {
					t.Fatal(err)
				}
				if kind == "trailing" {
					raw = append(raw, []byte("{}")...)
				}
				if kind == "unknown-field" || kind == "cache-sha" {
					var m map[string]any
					if err = json.Unmarshal(raw, &m); err != nil {
						t.Fatal(err)
					}
					if kind == "unknown-field" {
						m["unexpected"] = true
					} else {
						m["cache_sha256"] = "wrong"
					}
					raw, err = json.Marshal(m)
					if err != nil {
						t.Fatal(err)
					}
				}
				if err = os.WriteFile(filepath.Join(out, "army-man21.json"), raw, 0644); err != nil {
					t.Fatal(err)
				}
			}
			if kind == "source" {
				sourceRoot = t.TempDir()
				raw, err := os.ReadFile(filepath.Join(root, "MAN21.EGG"))
				if err != nil {
					t.Fatal(err)
				}
				raw[len(raw)-1] ^= 1
				if err = os.WriteFile(filepath.Join(sourceRoot, "MAN21.EGG"), raw, 0644); err != nil {
					t.Fatal(err)
				}
			}
			if kind == "missing-original" {
				saved := a.Actors[99]
				delete(a.Actors, 99)
				defer func() { a.Actors[99] = saved }()
			}
			if kind == "id-collision" {
				a.Actors[150] = a.Actors[85]
				defer delete(a.Actors, 150)
			}
			err = loadArmyMan21(out, sourceRoot, a)
			if (kind == "missing") != (err == nil) {
				t.Fatalf("unexpected load result %v", err)
			}
			after, _ := json.Marshal(a.ByNative)
			if !bytes.Equal(before, after) || a.ActorSHA[150] != "" {
				t.Fatal("failed group left registrations")
			}
			want := count
			if kind == "missing-original" {
				want--
			}
			if kind == "id-collision" {
				want++
			}
			if len(a.Actors) != want {
				t.Fatal("failed group left actors")
			}
		})
	}
	if !bytes.Equal(original, a.Actors[99].Tile.Pix) {
		t.Fatal("source cache was mutated")
	}
}
