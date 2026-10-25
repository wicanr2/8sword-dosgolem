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

func castlePaths(t *testing.T) (string, string, string, string) {
	t.Helper()
	dir, base := os.Getenv("EIGHTSWORD_TEST_CASTLE_ASSETS"), os.Getenv("EIGHTSWORD_TEST_CASTLE_BASE")
	root, cache := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_CASTLE_CACHE")
	if dir == "" || base == "" || root == "" || cache == "" {
		t.Skip("需要 043 候選、r40、原版及獨立快取")
	}
	return dir, base, root, cache
}

func castleCacheHashes(a *GraphicsAssets) map[string]string {
	out := map[string]string{}
	for kind, entries := range map[string]map[uint16]*graphicMaterial{"material": a.Materials, "actor": a.Actors, "effect": a.Effects} {
		for id, entry := range entries {
			out[fmt.Sprintf("%s/%d", kind, id)] = hash(entry.Tile.Pix)
		}
	}
	return out
}

func TestMapCastleRealSourcesAndIndependentCaches(t *testing.T) {
	dir, base, root, cache := castlePaths(t)
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
	if good.MapCastleError != "" || old.MapCastleError != "" || good.GraphicsError != "" || !good.HD {
		t.Fatal(good.Status(), old.Status())
	}
	a, b := good.Tracker.graphics.assets, old.Tracker.graphics.assets
	if len(a.Materials) != len(b.Materials)+6 || !reflect.DeepEqual(a.Native, b.Native) || !reflect.DeepEqual(a.ByNative, b.ByNative) || !reflect.DeepEqual(a.Actors, b.Actors) || !reflect.DeepEqual(a.Effects, b.Effects) || !reflect.DeepEqual(a.ActorSHA, b.ActorSHA) || !reflect.DeepEqual(a.BattleActors, b.BattleActors) || !reflect.DeepEqual(good.Assets, old.Assets) {
		t.Fatal("castle altered an existing source, actor, effect, or font")
	}
	for id, material := range b.Materials {
		if !reflect.DeepEqual(a.Materials[id], material) {
			t.Fatalf("old material %d changed", id)
		}
	}
	for _, source := range mapCastleRecords {
		id := uint16(source.Index + 1)
		expected, err := os.ReadFile(filepath.Join(cache, fmt.Sprintf("castle-%d.rgba", source.Index)))
		if err != nil || hash(expected) != source.CacheSHA {
			t.Fatal("independent cache", err)
		}
		entry := a.Materials[id]
		if entry == nil || entry.NativeWidth != 64 || entry.NativeHeight != 25 || !bytes.Equal(entry.Tile.Pix, expected) {
			t.Fatalf("source %d cache mismatch", source.Index)
		}
		for other, material := range a.Materials {
			if other != id && &entry.Tile.Pix[0] == &material.Tile.Pix[0] {
				t.Fatal("mutable cache alias")
			}
		}
	}
}

func TestMapCastleFaultsAreAtomic(t *testing.T) {
	dir, base, root, _ := castlePaths(t)
	old, err := Open(Options{Root: root, Assets: base, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer old.Close()
	a := old.Tracker.graphics.assets
	pmap, err := os.ReadFile(filepath.Join(root, "PMAP.AY"))
	if err != nil {
		t.Fatal(err)
	}
	manifest, err := os.ReadFile(filepath.Join(dir, "map-castle.json"))
	if err != nil {
		t.Fatal(err)
	}
	png, err := os.ReadFile(filepath.Join(dir, "map-castle-r2.png"))
	if err != nil {
		t.Fatal(err)
	}
	for _, kind := range []string{"missing", "unknown-field", "trailing", "oversize", "last-record", "source", "bad-image", "missing-image", "id-collision", "missing-grass"} {
		t.Run(kind, func(t *testing.T) {
			out := t.TempDir()
			data, source := append([]byte(nil), manifest...), pmap
			if kind == "trailing" {
				data = append(data, []byte("{}")...)
			}
			if kind == "oversize" {
				data = append(data, bytes.Repeat([]byte(" "), 65536)...)
			}
			if kind == "unknown-field" || kind == "last-record" {
				var m map[string]any
				if err = json.Unmarshal(data, &m); err != nil {
					t.Fatal(err)
				}
				if kind == "unknown-field" {
					m["unknown"] = true
				} else {
					m["records"].([]any)[5].(map[string]any)["record_sha256"] = "wrong"
				}
				data, err = json.Marshal(m)
				if err != nil {
					t.Fatal(err)
				}
			}
			if kind != "missing" {
				if err = os.WriteFile(filepath.Join(out, "map-castle.json"), data, 0644); err != nil {
					t.Fatal(err)
				}
			}
			if kind != "missing-image" {
				image := append([]byte(nil), png...)
				if kind == "bad-image" {
					image[len(image)-20] ^= 1
				}
				if err = os.WriteFile(filepath.Join(out, "map-castle-r2.png"), image, 0644); err != nil {
					t.Fatal(err)
				}
			}
			if kind == "source" {
				source = append([]byte(nil), pmap...)
				source[64*1004+999] ^= 1
			}
			if kind == "id-collision" {
				a.Materials[65] = a.Materials[1]
				defer delete(a.Materials, 65)
			}
			if kind == "missing-grass" {
				grass := a.Materials[1]
				delete(a.Materials, 1)
				defer func() { a.Materials[1] = grass }()
			}
			before := castleCacheHashes(a)
			native, _ := json.Marshal(a.ByNative)
			err = loadMapCastle(out, source, a)
			if (kind == "missing") != (err == nil) {
				t.Fatalf("unexpected result %v", err)
			}
			after, _ := json.Marshal(a.ByNative)
			if !reflect.DeepEqual(before, castleCacheHashes(a)) || !bytes.Equal(native, after) {
				t.Fatal("failed group left registrations or changed existing caches")
			}
		})
	}
}
