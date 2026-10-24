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

func TestMan06RealSourcesAndLegacyCache(t *testing.T) {
	dir, base, root, cache := os.Getenv("EIGHTSWORD_TEST_MAN06_ASSETS"), os.Getenv("EIGHTSWORD_TEST_BATTLE_ACTOR_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_MAN06_CACHE")
	if dir == "" || base == "" || root == "" || cache == "" {
		t.Skip("需要本機 024／023 素材、原版與獨立取樣")
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
	if len(a.BattleActors) != 8 || len(b.BattleActors) != 4 || len(a.Actors) != len(b.Actors)+4 {
		t.Fatal("two complete groups not loaded")
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
	raw, err := os.ReadFile(filepath.Join(root, "MAN06.EGG"))
	if err != nil {
		t.Fatal(err)
	}
	for i, want := range man06Sources {
		id := uint16(91 + i)
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

func TestBattleActorGroupsFailIndependently(t *testing.T) {
	dir, root := os.Getenv("EIGHTSWORD_TEST_MAN06_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ORIG")
	if dir == "" || root == "" {
		t.Skip("需要本機兩組部隊素材與原版")
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
		name, source      string
		missing, retained uint16
	}{{"battle-man06-3-r1.png", "MAN06.EGG", 91, 87}, {"battle-man16-3-r1.png", "MAN16.EGG", 87, 91}} {
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
			if len(b.BattleActors) != 4 || len(a.Actors) != len(b.Actors)+4 {
				t.Fatal("partial group or unrelated group lost")
			}
			for i := uint16(0); i < 4; i++ {
				if b.Actors[which.missing+i] != nil || b.Actors[which.retained+i] == nil {
					t.Fatal("incorrect rejected group")
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
