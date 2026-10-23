package eightsword

import (
	"bytes"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func TestCorruptBattleBackgroundKeepsOtherHD(t *testing.T) {
	dir, root := os.Getenv("EIGHTSWORD_TEST_BATTLE_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ORIG")
	if dir == "" || root == "" {
		t.Skip("需要本機 021 戰場素材與原版")
	}
	if _, err := os.Stat(filepath.Join(dir, "battle-background.json")); os.IsNotExist(err) {
		t.Skip("本機尚未匯入 021 戰場素材")
	} else if err != nil {
		t.Fatal(err)
	}
	good, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer good.Close()
	if good.Tracker == nil || good.Tracker.graphics == nil || good.BattleBackgroundError != "" || good.Tracker.graphics.assets.Materials[battleBackgroundID] == nil {
		t.Fatal("real battle group did not load")
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
		data, err := os.ReadFile(filepath.Join(dir, entry.Name()))
		if err != nil {
			t.Fatal(err)
		}
		if entry.Name() == "battle-background-r1.png" {
			data = append([]byte(nil), data...)
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
	if bad.BattleBackgroundError == "" || !bad.HD || bad.AssetError != "" || bad.GraphicsError != "" || bad.Tracker == nil || bad.Tracker.graphics == nil {
		t.Fatalf("battle failure disabled unrelated HD: %+v", bad.Status())
	}
	a, b := good.Tracker.graphics.assets, bad.Tracker.graphics.assets
	if b.Materials[battleBackgroundID] != nil || b.ByNative[battleBackgroundNativeSHA] != 0 || len(a.Materials) != len(b.Materials)+1 || len(a.Actors) != len(b.Actors) {
		t.Fatal("corrupt group partially loaded or changed other groups")
	}
	for id, m := range b.Materials {
		if !bytes.Equal(m.Tile.Pix, a.Materials[id].Tile.Pix) {
			t.Fatalf("material %d changed", id)
		}
	}
	for id, m := range b.Actors {
		if !bytes.Equal(m.Tile.Pix, a.Actors[id].Tile.Pix) {
			t.Fatalf("actor %d changed", id)
		}
	}
	if !reflect.DeepEqual(good.Assets, bad.Assets) {
		t.Fatal("battle failure changed Noto")
	}
}
