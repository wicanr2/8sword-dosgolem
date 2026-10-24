package eightsword

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

func TestMan11RealSourcesAndLegacyCache(t *testing.T) {
	dir, base, root, cache := os.Getenv("EIGHTSWORD_TEST_MAN11_ASSETS"), os.Getenv("EIGHTSWORD_TEST_MAN06_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_MAN11_CACHE")
	if dir == "" || base == "" || root == "" || cache == "" {
		t.Skip("需要本機 025／024 素材、原版與獨立取樣")
	}
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
	if len(a.BattleActors) != 12 || len(b.BattleActors) != 8 || len(a.Actors) != len(b.Actors)+4 {
		t.Fatal("three complete groups not loaded")
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
	if !reflect.DeepEqual(good.Assets, old.Assets) {
		t.Fatal("Noto changed")
	}
	raw, err := os.ReadFile(filepath.Join(root, "MAN11.EGG"))
	if err != nil {
		t.Fatal(err)
	}
	for i, want := range man11Sources {
		id := uint16(95 + i)
		record := raw[i*3304 : (i+1)*3304]
		if hash(record) != want.Record || hash(record[:2204]) != want.Native || a.ByNative[want.Native] != id || !good.Tracker.graphics.heroRecordMatches(id, 6, record) {
			t.Fatalf("source %d mismatch", i)
		}
		bad := append([]byte(nil), record...)
		bad[len(bad)-1] ^= 1
		if good.Tracker.graphics.heroRecordMatches(id, 6, bad) {
			t.Fatal("mask mismatch accepted")
		}
		expected, err := os.ReadFile(filepath.Join(cache, fmt.Sprintf("cache-frame-%d.rgba", i)))
		if err != nil {
			t.Fatal(err)
		}
		if len(expected) != 264*300*4 || !bytes.Equal(expected, a.Actors[id].Tile.Pix) {
			t.Fatalf("independent frame %d mismatch", i)
		}
	}
}

func TestThreeBattleActorGroupsFailIndependently(t *testing.T) {
	dir, root := os.Getenv("EIGHTSWORD_TEST_MAN11_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ORIG")
	if dir == "" || root == "" {
		t.Skip("需要本機三組部隊素材與原版")
	}
	good, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer good.Close()
	if good.BattleActorError != "" {
		t.Fatal(good.BattleActorError)
	}
	for _, which := range []struct {
		name, source string
		missing      uint16
	}{{"battle-man11-3-r1.png", "MAN11.EGG", 95}, {"battle-man06-3-r1.png", "MAN06.EGG", 91}, {"battle-man16-3-r1.png", "MAN16.EGG", 87}} {
		t.Run(which.source, func(t *testing.T) {
			broken := t.TempDir()
			entries, err := os.ReadDir(dir)
			if err != nil {
				t.Fatal(err)
			}
			for _, entry := range entries {
				if entry.IsDir() {
					t.Fatal("unexpected nested asset")
				}
				data, err := os.ReadFile(filepath.Join(dir, entry.Name()))
				if err != nil {
					t.Fatal(err)
				}
				if entry.Name() == which.name {
					data[len(data)/2] ^= 1
				}
				if err = os.WriteFile(filepath.Join(broken, entry.Name()), data, 0644); err != nil {
					t.Fatal(err)
				}
			}
			bad, err := Open(Options{Root: root, Assets: broken, Saves: t.TempDir(), HD: true})
			if err != nil {
				t.Fatal(err)
			}
			defer bad.Close()
			if !strings.Contains(bad.BattleActorError, which.source) || !bad.HD || bad.AssetError != "" || bad.GraphicsError != "" || bad.BattleBackgroundError != "" {
				t.Fatal(bad.Status())
			}
			a, b := good.Tracker.graphics.assets, bad.Tracker.graphics.assets
			if len(b.BattleActors) != 8 || len(a.Actors) != len(b.Actors)+4 {
				t.Fatal("partial group or unrelated group lost")
			}
			for id := uint16(87); id < 99; id++ {
				rejected := id >= which.missing && id < which.missing+4
				if rejected == (b.Actors[id] != nil) {
					t.Fatalf("incorrect group membership for %d", id)
				}
			}
			for id, m := range b.Actors {
				if !bytes.Equal(m.Tile.Pix, a.Actors[id].Tile.Pix) {
					t.Fatalf("retained actor %d changed", id)
				}
			}
			for id, m := range b.Materials {
				if !bytes.Equal(m.Tile.Pix, a.Materials[id].Tile.Pix) {
					t.Fatalf("material %d changed", id)
				}
			}
			if !reflect.DeepEqual(good.Assets, bad.Assets) {
				t.Fatal("Noto changed")
			}
		})
	}
}
