package eightsword

import (
	"bytes"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func TestRecruitmentBuildingFailureIsolation(t *testing.T) {
	dir, root := os.Getenv("EIGHTSWORD_TEST_RECRUITMENT_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ORIG")
	if dir == "" || root == "" {
		t.Skip("需要本機 034 素材與原版")
	}
	good, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer good.Close()
	if good.BattleBackgroundError != "" || good.BattleActorError != "" || good.BattleEffectError != "" || good.BattleMarkerError != "" {
		t.Fatalf("新建築影響既有群組：%v", good.Status())
	}
	if good.RecruitmentBuildingError != "" || good.Tracker == nil || good.Tracker.graphics == nil || good.Tracker.graphics.assets.Materials[recruitmentBuildingID] == nil {
		t.Fatalf("募兵建築未載入：%v", good.Status())
	}
	for _, mode := range []string{"missing-group", "broken-png", "trailing-json"} {
		t.Run(mode, func(t *testing.T) {
			copyDir := t.TempDir()
			entries, err := os.ReadDir(dir)
			if err != nil {
				t.Fatal(err)
			}
			for _, file := range entries {
				if mode == "missing-group" && file.Name() == "recruitment-building.json" {
					continue
				}
				data, err := os.ReadFile(filepath.Join(dir, file.Name()))
				if err != nil {
					t.Fatal(err)
				}
				if mode == "broken-png" && file.Name() == "recruitment-building-r1.png" {
					data = append(data, 0)
				}
				if mode == "trailing-json" && file.Name() == "recruitment-building.json" {
					data = append(data, []byte(" {}")...)
				}
				if err := os.WriteFile(filepath.Join(copyDir, file.Name()), data, 0644); err != nil {
					t.Fatal(err)
				}
			}
			bad, err := Open(Options{Root: root, Assets: copyDir, Saves: t.TempDir(), HD: true})
			if err != nil {
				t.Fatal(err)
			}
			defer bad.Close()
			if bad.BattleBackgroundError != "" || bad.BattleActorError != "" || bad.BattleEffectError != "" || bad.BattleMarkerError != "" {
				t.Fatalf("故障影響既有群組：%v", bad.Status())
			}
			if (bad.RecruitmentBuildingError != "") != (mode != "missing-group") || !bad.HD || bad.AssetError != "" || bad.GraphicsError != "" || bad.Tracker == nil || bad.Tracker.graphics == nil {
				t.Fatalf("局部故障影響其他 HD：%v", bad.Status())
			}
			a, b := good.Tracker.graphics.assets, bad.Tracker.graphics.assets
			if b.ByNative[recruitmentNativeSHA] != 0 || b.Materials[recruitmentBuildingID] != nil || len(a.Materials) != len(b.Materials)+1 || !reflect.DeepEqual(good.Assets, bad.Assets) {
				t.Fatal("故障群組部分載入或改變 Noto")
			}
			for id, m := range b.Materials {
				if !bytes.Equal(m.Tile.Pix, a.Materials[id].Tile.Pix) {
					t.Fatalf("材質 %d 改變", id)
				}
			}
			for id, m := range b.Actors {
				if !bytes.Equal(m.Tile.Pix, a.Actors[id].Tile.Pix) {
					t.Fatalf("人物 %d 改變", id)
				}
			}
			if len(a.Effects) != len(b.Effects) || len(a.BattleActors) != len(b.BattleActors) {
				t.Fatal("新建築改變既有特效或部隊數量")
			}
			for id, m := range b.Effects {
				if !bytes.Equal(m.Tile.Pix, a.Effects[id].Tile.Pix) {
					t.Fatalf("特效 %d 改變", id)
				}
			}
		})
	}
}
