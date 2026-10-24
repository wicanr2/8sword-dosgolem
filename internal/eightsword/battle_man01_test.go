package eightsword

import (
	"bytes"
	"encoding/json"
	"math/bits"
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
	"testing"
)

func man01TestPaths(t *testing.T) (string, string, string, string) {
	t.Helper()
	dir, base := os.Getenv("EIGHTSWORD_TEST_MAN01_ASSETS"), os.Getenv("EIGHTSWORD_TEST_MAN01_BASE")
	root, cache := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_MAN01_CACHE")
	if dir == "" || base == "" || root == "" || cache == "" {
		t.Skip("需要本機 036／r36 素材、原版與獨立取樣")
	}
	return dir, base, root, cache
}

func TestMan01PosesRealSourcesAndLegacyCache(t *testing.T) {
	dir, base, root, cache := man01TestPaths(t)
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
	if good.BattleActorError != "" || old.BattleActorError != "" {
		t.Fatal(good.BattleActorError, old.BattleActorError)
	}
	a, b := good.Tracker.graphics.assets, old.Tracker.graphics.assets
	if len(a.BattleActors) != len(b.BattleActors)+3 || len(a.Actors) != len(b.Actors)+3 {
		t.Fatal("three complete poses not loaded")
	}
	for id, m := range b.Actors {
		if a.ActorSHA[id] != b.ActorSHA[id] || !bytes.Equal(m.Tile.Pix, a.Actors[id].Tile.Pix) {
			t.Fatalf("legacy actor %d changed", id)
		}
	}
	for id, m := range b.Materials {
		if !bytes.Equal(m.Tile.Pix, a.Materials[id].Tile.Pix) {
			t.Fatalf("material %d changed", id)
		}
	}
	if !reflect.DeepEqual(good.Assets, old.Assets) || !reflect.DeepEqual(a.Effects, b.Effects) {
		t.Fatal("font or effects changed")
	}
	if a.ByNative[militiaNativeSHA] != 85 || a.BattleActors[85] || a.Actors[107] != a.Actors[85] {
		t.Fatal("shared first pose or F2 classification changed")
	}
	raw, err := os.ReadFile(filepath.Join(root, "MAN01.EGG"))
	if err != nil {
		t.Fatal(err)
	}
	for i, want := range man01PoseSources[:3] {
		original := raw[(i+1)*3304 : (i+2)*3304]
		mirrored := append([]byte(nil), original...)
		for row := 4; row < 3304; row += 11 {
			for x := 0; x < 11; x++ {
				mirrored[row+x] = bits.Reverse8(original[row+10-x])
			}
		}
		id := uint16(113 + i)
		if hash(mirrored) != want.Record || hash(mirrored[:2204]) != want.Native || a.ByNative[want.Native] != id || !a.BattleActors[id] || !good.Tracker.graphics.heroRecordMatches(id, 6, mirrored) {
			t.Fatalf("mirrored source %d mismatch", i+1)
		}
		mirrored[len(mirrored)-1] ^= 1
		if good.Tracker.graphics.heroRecordMatches(id, 6, mirrored) {
			t.Fatal("changed mask accepted")
		}
		expected, err := os.ReadFile(filepath.Join(cache, "man01-mirror-"+strconv.Itoa(i+1)+"-cache-r1.rgba"))
		if err != nil || !bytes.Equal(expected, a.Actors[id].Tile.Pix) {
			t.Fatalf("independent cache %d mismatch: %v", i+1, err)
		}
	}
}

func TestMan01PosesRejectWholeNewGroup(t *testing.T) {
	dir, base, root, _ := man01TestPaths(t)
	old, err := Open(Options{Root: root, Assets: base, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer old.Close()
	for _, kind := range []string{"last-png", "transform", "count"} {
		t.Run(kind, func(t *testing.T) {
			broken := t.TempDir()
			entries, err := os.ReadDir(dir)
			if err != nil {
				t.Fatal(err)
			}
			for _, entry := range entries {
				data, err := os.ReadFile(filepath.Join(dir, entry.Name()))
				if err != nil {
					t.Fatal(err)
				}
				if entry.Name() == "battle-man01-3-r1.png" && kind == "last-png" {
					data = append(data, 0)
				}
				if entry.Name() == "battle-man01.json" && kind != "last-png" {
					var m map[string]any
					if err := json.Unmarshal(data, &m); err != nil {
						t.Fatal(err)
					}
					if kind == "transform" {
						m["transform"] = "identity"
					} else {
						m["frames"] = m["frames"].([]any)[:2]
					}
					data, err = json.Marshal(m)
					if err != nil {
						t.Fatal(err)
					}
				}
				if err := os.WriteFile(filepath.Join(broken, entry.Name()), data, 0644); err != nil {
					t.Fatal(err)
				}
			}
			bad, err := Open(Options{Root: root, Assets: broken, Saves: t.TempDir(), HD: true})
			if err != nil {
				t.Fatal(err)
			}
			defer bad.Close()
			if !strings.Contains(bad.BattleActorError, "MAN01.EGG") || bad.GraphicsError != "" || bad.AssetError != "" || bad.BattleEffectError != "" || bad.BattleMarkerError != "" {
				t.Fatal("new failure affected another group", bad.Status())
			}
			a, b := bad.Tracker.graphics.assets, old.Tracker.graphics.assets
			if !reflect.DeepEqual(a.Actors, b.Actors) || !reflect.DeepEqual(a.ByNative, b.ByNative) || !reflect.DeepEqual(a.BattleActors, b.BattleActors) || !reflect.DeepEqual(bad.Assets, old.Assets) {
				t.Fatal("failed group left partial actors or changed existing data")
			}
		})
	}
}
