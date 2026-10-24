package eightsword

import (
	"bytes"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func TestBattleActorsRealSourcesAndCache(t *testing.T) {
	dir, root, cache := os.Getenv("EIGHTSWORD_TEST_BATTLE_ACTOR_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_BATTLE_ACTOR_CACHE")
	if dir == "" || root == "" || cache == "" {
		t.Skip("需要 023 本機四筆素材、原版及獨立取樣快取")
	}
	e, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	if e.BattleActorError != "" || e.Tracker == nil || e.Tracker.graphics == nil {
		t.Fatal(e.Status())
	}
	g := e.Tracker.graphics
	if len(g.assets.BattleActors) != 4 {
		t.Fatal("four-frame group not loaded")
	}
	raw, err := os.ReadFile(filepath.Join(root, "MAN16.EGG"))
	if err != nil {
		t.Fatal(err)
	}
	for i, want := range man16Sources {
		id := uint16(87 + i)
		record := raw[i*3304 : (i+1)*3304]
		if hash(record) != want.Record || hash(record[:2204]) != want.Native || g.assets.ByNative[want.Native] != id || !g.heroRecordMatches(id, 6, record) {
			t.Fatalf("record %d mismatch", i)
		}
		bad := append([]byte(nil), record...)
		bad[len(bad)-1] ^= 1
		if g.heroRecordMatches(id, 6, bad) || g.heroRecordMatches(id, 5, record) {
			t.Fatal("mask or kind mismatch accepted")
		}
		expected, err := os.ReadFile(filepath.Join(cache, []string{"cache-frame-0.rgba", "cache-frame-1.rgba", "cache-frame-2.rgba", "cache-frame-3.rgba"}[i]))
		if err != nil {
			t.Fatal(err)
		}
		if len(expected) != 264*300*4 || !bytes.Equal(g.assets.Actors[id].Tile.Pix, expected) {
			t.Fatalf("record %d differs from independent registered cache", i)
		}
	}
	if g.Stats.ActorCompletions != 0 || g.Stats.BattleActorCompletions != 0 {
		t.Fatal("loading executed a guest drawing")
	}
}

func TestCorruptLastBattleActorKeepsOtherHD(t *testing.T) {
	dir, root := os.Getenv("EIGHTSWORD_TEST_BATTLE_ACTOR_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ORIG")
	if dir == "" || root == "" {
		t.Skip("需要 023 本機四筆素材與原版")
	}
	good, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer good.Close()
	if good.BattleActorError != "" {
		t.Fatal(good.BattleActorError)
	}
	broken := t.TempDir()
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		if entry.IsDir() {
			t.Fatal("unexpected nested asset")
		}
		b, err := os.ReadFile(filepath.Join(dir, entry.Name()))
		if err != nil {
			t.Fatal(err)
		}
		if entry.Name() == "battle-man16-3-r1.png" {
			b[len(b)/2] ^= 1
		}
		if err = os.WriteFile(filepath.Join(broken, entry.Name()), b, 0644); err != nil {
			t.Fatal(err)
		}
	}
	bad, err := Open(Options{Root: root, Assets: broken, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer bad.Close()
	if bad.BattleActorError == "" || !bad.HD || bad.AssetError != "" || bad.GraphicsError != "" || bad.BattleBackgroundError != "" || bad.Tracker == nil || bad.Tracker.graphics == nil {
		t.Fatal("unrelated HD failed", bad.Status())
	}
	a, b := good.Tracker.graphics.assets, bad.Tracker.graphics.assets
	if len(b.BattleActors) != 0 || len(a.Actors) != len(b.Actors)+4 || len(a.Materials) != len(b.Materials) {
		t.Fatal("partially committed group")
	}
	for _, s := range man16Sources {
		if b.ByNative[s.Native] != 0 {
			t.Fatal("stale rejected source")
		}
	}
	for id, m := range b.Materials {
		if !bytes.Equal(m.Tile.Pix, a.Materials[id].Tile.Pix) {
			t.Fatalf("material %d changed", id)
		}
	}
	for id, m := range b.Actors {
		if !bytes.Equal(m.Tile.Pix, a.Actors[id].Tile.Pix) {
			t.Fatalf("old actor %d changed", id)
		}
	}
	if !reflect.DeepEqual(good.Assets, bad.Assets) {
		t.Fatal("Noto changed")
	}
}
