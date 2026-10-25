package eightsword

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func landmark52Paths(t *testing.T) (string, string, string, string) {
	t.Helper()
	dir, base := os.Getenv("EIGHTSWORD_TEST_LANDMARK52_ASSETS"), os.Getenv("EIGHTSWORD_TEST_LANDMARK52_BASE")
	root, cache := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_LANDMARK52_CACHE")
	if dir == "" || base == "" || root == "" || cache == "" {
		t.Skip("需要 045 候選、r44、原版及獨立快取")
	}
	return dir, base, root, cache
}

func TestMapLandmark52RealSourceAndIndependentCache(t *testing.T) {
	dir, base, root, cache := landmark52Paths(t)
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
	if good.MapLandmarkError != "" || old.MapLandmarkError != "" || good.MapCastleError != "" || good.GraphicsError != "" || !good.HD {
		t.Fatal(good.Status())
	}
	a, b := good.Tracker.graphics.assets, old.Tracker.graphics.assets
	if len(a.Materials) != len(b.Materials)+2 || !reflect.DeepEqual(a.Native, b.Native) || !reflect.DeepEqual(a.ByNative, b.ByNative) || !reflect.DeepEqual(a.Actors, b.Actors) || !reflect.DeepEqual(a.Effects, b.Effects) || !reflect.DeepEqual(a.ActorSHA, b.ActorSHA) || !reflect.DeepEqual(a.BattleActors, b.BattleActors) || !reflect.DeepEqual(good.Assets, old.Assets) {
		t.Fatal("地圖物件52改變既有來源、字型、角色或效果")
	}
	for id, entry := range b.Materials {
		if !reflect.DeepEqual(a.Materials[id], entry) {
			t.Fatalf("材質 %d 改變", id)
		}
	}
	expected, err := os.ReadFile(filepath.Join(cache, "landmark-52.rgba"))
	if err != nil || hash(expected) != mapLandmark52CacheSHA {
		t.Fatal("獨立快取", err)
	}
	entry := a.Materials[53]
	if entry == nil || entry.NativeWidth != 64 || entry.NativeHeight != 25 || !bytes.Equal(entry.Tile.Pix, expected) {
		t.Fatal("完整地圖物件52快取不符")
	}
	for id, other := range a.Materials {
		if id != 53 && &entry.Tile.Pix[0] == &other.Tile.Pix[0] {
			t.Fatal("地圖物件52快取可變別名")
		}
	}
}

func TestMapLandmark52FaultsLeaveExistingAssets(t *testing.T) {
	dir, base, root, _ := landmark52Paths(t)
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
	manifest, err := os.ReadFile(filepath.Join(dir, "map-landmark-52.json"))
	if err != nil {
		t.Fatal(err)
	}
	png, err := os.ReadFile(filepath.Join(dir, "map-landmark-52-r1.png"))
	if err != nil {
		t.Fatal(err)
	}
	for _, kind := range []string{"missing", "unknown-field", "trailing", "oversize", "record", "source", "bad-image", "missing-image", "id-collision", "missing-grass"} {
		t.Run(kind, func(t *testing.T) {
			out := t.TempDir()
			data, source := append([]byte(nil), manifest...), pmap
			if kind == "trailing" {
				data = append(data, []byte("{}")...)
			}
			if kind == "oversize" {
				data = append(data, bytes.Repeat([]byte(" "), 16384)...)
			}
			if kind == "unknown-field" || kind == "record" {
				var m map[string]any
				if err := json.Unmarshal(data, &m); err != nil {
					t.Fatal(err)
				}
				if kind == "unknown-field" {
					m["unknown"] = true
				} else {
					m["record_sha256"] = "wrong"
				}
				data, err = json.Marshal(m)
				if err != nil {
					t.Fatal(err)
				}
			}
			if kind != "missing" {
				if err := os.WriteFile(filepath.Join(out, "map-landmark-52.json"), data, 0644); err != nil {
					t.Fatal(err)
				}
			}
			if kind != "missing-image" {
				image := append([]byte(nil), png...)
				if kind == "bad-image" {
					image[len(image)-20] ^= 1
				}
				if err := os.WriteFile(filepath.Join(out, "map-landmark-52-r1.png"), image, 0644); err != nil {
					t.Fatal(err)
				}
			}
			if kind == "source" {
				source = append([]byte(nil), pmap...)
				source[52*1004+999] ^= 1
			}
			if kind == "id-collision" {
				a.Materials[53] = a.Materials[1]
				defer delete(a.Materials, 53)
			}
			if kind == "missing-grass" {
				grass := a.Materials[1]
				delete(a.Materials, 1)
				defer func() { a.Materials[1] = grass }()
			}
			before, marshalErr := json.Marshal(a)
			if marshalErr != nil {
				t.Fatal(marshalErr)
			}
			err := loadMapLandmark52(out, source, a)
			if (kind == "missing") != (err == nil) {
				t.Fatalf("預期錯誤不符 %v", err)
			}
			if kind == "missing-grass" && err.Error() != "地圖物件52缺少完整草地快取" {
				t.Fatalf("未驗到草地失敗分支：%v", err)
			}
			after, marshalErr := json.Marshal(a)
			if marshalErr != nil {
				t.Fatal(marshalErr)
			}
			if !bytes.Equal(before, after) {
				t.Fatal("失敗群改變既有資料")
			}
		})
	}
}
