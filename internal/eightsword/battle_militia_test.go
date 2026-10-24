package eightsword

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func TestBattleMilitiaSharesVerifiedF2Cache(t *testing.T) {
	dir, root := os.Getenv("EIGHTSWORD_TEST_BATTLE_MILITIA_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ORIG")
	if dir == "" || root == "" {
		t.Skip("需要 028 本機素材與原版")
	}
	e, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	if e.BattleActorError != "" || e.GraphicsError != "" || e.BattleEffectError != "" || e.Tracker == nil || e.Tracker.graphics == nil {
		t.Fatal(e.Status())
	}
	a := e.Tracker.graphics.assets
	if len(a.BattleActors) != 17 || len(a.Effects) != 4 || a.Actors[107] != a.Actors[85] || a.ByNative[militiaNativeSHA] != 85 || a.BattleActors[85] || !a.BattleActors[107] {
		t.Fatal("battle alias changed F2 or other groups")
	}
	raw, err := os.ReadFile(filepath.Join(root, "MAN01.EGG"))
	if err != nil {
		t.Fatal(err)
	}
	mirrored := append([]byte(nil), raw[:3304]...)
	for row := 4; row < 3304; row += 11 {
		for x := 0; x < 11; x++ {
			v := raw[row+10-x]
			var reversed byte
			for bit := 0; bit < 8; bit++ {
				reversed = reversed<<1 | v&1
				v >>= 1
			}
			mirrored[row+x] = reversed
		}
	}
	if hash(mirrored) != militiaRecordSHA || hash(mirrored[:2204]) != militiaNativeSHA || !e.Tracker.graphics.heroRecordMatches(85, 6, mirrored) || !e.Tracker.graphics.heroRecordMatches(107, 6, mirrored) {
		t.Fatal("original mirrored source mismatch")
	}
	mirrored[len(mirrored)-1] ^= 1
	if e.Tracker.graphics.heroRecordMatches(107, 6, mirrored) {
		t.Fatal("changed sixth mask accepted")
	}
	if hash(a.Actors[107].Tile.Pix) != militiaCacheSHA {
		t.Fatal("018 independent cache mismatch")
	}
}

func TestBadBattleMilitiaManifestPreservesF2AndOtherHD(t *testing.T) {
	dir, root := os.Getenv("EIGHTSWORD_TEST_BATTLE_MILITIA_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ORIG")
	if dir == "" || root == "" {
		t.Skip("需要 028 本機素材與原版")
	}
	good, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer good.Close()
	broken := t.TempDir()
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		b, err := os.ReadFile(filepath.Join(dir, entry.Name()))
		if err != nil {
			t.Fatal(err)
		}
		if entry.Name() == "battle-militia.json" {
			var m map[string]any
			if err = json.Unmarshal(b, &m); err != nil {
				t.Fatal(err)
			}
			m["record_sha256"] = "wrong-six-plane-source"
			b, err = json.Marshal(m)
			if err != nil {
				t.Fatal(err)
			}
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
	if bad.BattleActorError == "" || bad.AssetError != "" || bad.GraphicsError != "" || bad.BattleEffectError != "" || !bad.HD || bad.Tracker == nil || bad.Tracker.graphics == nil {
		t.Fatal(bad.Status())
	}
	a, b := good.Tracker.graphics.assets, bad.Tracker.graphics.assets
	if len(b.BattleActors) != 16 || len(b.Effects) != 4 || b.Actors[107] != nil || b.ActorSHA[107] != "" || b.ByNative[militiaNativeSHA] != 85 || b.BattleActors[85] || len(a.Actors) != len(b.Actors)+1 {
		t.Fatal("partial alias or broken existing groups")
	}
	for id, actor := range b.Actors {
		if !bytes.Equal(actor.Tile.Pix, a.Actors[id].Tile.Pix) {
			t.Fatalf("actor %d changed", id)
		}
	}
	if !reflect.DeepEqual(good.Assets, bad.Assets) || !reflect.DeepEqual(a.Materials, b.Materials) || !reflect.DeepEqual(a.Effects, b.Effects) {
		t.Fatal("unrelated Noto/background/PON changed")
	}
}
