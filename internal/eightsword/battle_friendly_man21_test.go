package eightsword

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func friendlyMan21Paths(t *testing.T) (string, string, string, string) {
	t.Helper()
	dir, base, root, cache := os.Getenv("EIGHTSWORD_TEST_FRIENDLY_ASSETS"), os.Getenv("EIGHTSWORD_TEST_FRIENDLY_BASE"), os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_FRIENDLY_CACHE")
	if dir == "" || base == "" || root == "" || cache == "" {
		t.Skip("需要042候選、r47、固定原版與已驗鏡射快取")
	}
	return dir, base, root, cache
}

func TestFriendlyMan21SourceAndImmutableCaches(t *testing.T) {
	dir, base, root, cache := friendlyMan21Paths(t)
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
	if good.BattleActorError != "" || good.ArmyMan21Error != "" || good.BattleBackgroundError != "" {
		t.Fatal(good.Status())
	}
	a, b := good.Tracker.graphics.assets, old.Tracker.graphics.assets
	if !reflect.DeepEqual(a.Materials, b.Materials) || !reflect.DeepEqual(a.Effects, b.Effects) || !reflect.DeepEqual(a.Native, b.Native) || len(a.ByNative) != len(b.ByNative)+3 || len(a.Actors) != len(b.Actors)+4 {
		t.Fatal("既有圖像目錄改變")
	}
	for id, m := range b.Actors {
		if !reflect.DeepEqual(a.Actors[id], m) || a.ActorSHA[id] != b.ActorSHA[id] || a.BattleActors[id] != b.BattleActors[id] {
			t.Fatalf("既有部隊%d改變", id)
		}
	}
	for key, id := range b.ByNative {
		if a.ByNative[key] != id {
			t.Fatal("既有來源改變")
		}
	}
	for i := 0; i < 4; i++ {
		id := uint16(152 + i)
		data, err := os.ReadFile(filepath.Join(cache, "record-"+string(rune('0'+i))+"-mirror.rgba"))
		if err != nil {
			t.Fatal(err)
		}
		if hash(data) != friendlyMan21MirrorCaches[i] || !bytes.Equal(a.Actors[id].Tile.Pix, data) || a.ActorSHA[id] != friendlyMan21Sources[i].Record || !a.BattleActors[id] {
			t.Fatal("鏡射完整快取不符", i)
		}
		if a.Actors[id].Tile == a.Actors[uint16(99+i)].Tile || a.Actors[id].Tile == a.Actors[150].Tile {
			t.Fatal("鏡射共用可變快取", i)
		}
		if i > 0 && a.ByNative[friendlyMan21Sources[i].Native] != id {
			t.Fatal("新增來源未登錄")
		}
	}
	if a.ByNative[armyMan21NativeSHA] != 150 || a.BattleActors[150] {
		t.Fatal("F2分類改變")
	}
}

func TestFriendlyMan21FaultsAreAtomic(t *testing.T) {
	dir, base, root, _ := friendlyMan21Paths(t)
	e, err := Open(Options{Root: root, Assets: base, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	a := e.Tracker.graphics.assets
	raw, err := os.ReadFile(filepath.Join(dir, "battle-friendly-man21.json"))
	if err != nil {
		t.Fatal(err)
	}
	for _, kind := range []string{"missing", "malformed", "unknown-field", "trailing", "oversize", "symlink", "source", "last-cache", "missing-last", "reorder", "source-file", "last-id-collision", "native-alias", "native-collision", "missing-F2", "last-original-cache"} {
		t.Run(kind, func(t *testing.T) {
			out := t.TempDir()
			sourceRoot := root
			data := append([]byte(nil), raw...)
			var m map[string]any
			if err := json.Unmarshal(raw, &m); err != nil {
				t.Fatal(err)
			}
			switch kind {
			case "malformed":
				data = []byte("{")
			case "trailing":
				data = append(data, []byte("{}")...)
			case "oversize":
				data = append(data, bytes.Repeat([]byte(" "), 16384)...)
			case "unknown-field":
				m["unknown"] = true
			case "source":
				m["source_sha256"] = "wrong"
			case "last-cache":
				m["frames"].([]any)[3].(map[string]any)["cache_sha256"] = "wrong"
			case "missing-last":
				m["frames"] = m["frames"].([]any)[:3]
			case "reorder":
				v := m["frames"].([]any)
				v[2], v[3] = v[3], v[2]
			case "source-file":
				sourceRoot = t.TempDir()
				v, err := os.ReadFile(filepath.Join(root, "MAN21.EGG"))
				if err != nil {
					t.Fatal(err)
				}
				v[len(v)-1] ^= 1
				if err = os.WriteFile(filepath.Join(sourceRoot, "MAN21.EGG"), v, 0644); err != nil {
					t.Fatal(err)
				}
			case "last-id-collision":
				a.Effects[155] = a.Effects[103]
				defer delete(a.Effects, 155)
			case "native-alias":
				a.ByNative["other"] = 155
				defer delete(a.ByNative, "other")
			case "native-collision":
				a.ByNative[friendlyMan21Sources[3].Native] = 99
				defer delete(a.ByNative, friendlyMan21Sources[3].Native)
			case "missing-F2":
				v := a.Actors[150]
				delete(a.Actors, 150)
				defer func() { a.Actors[150] = v }()
			case "last-original-cache":
				v := a.Actors[102]
				bad := *v
				tile := *v.Tile
				tile.Pix = append([]byte(nil), tile.Pix...)
				tile.Pix[100] ^= 1
				bad.Tile = &tile
				a.Actors[102] = &bad
				defer func() { a.Actors[102] = v }()
			}
			if kind == "unknown-field" || kind == "source" || kind == "last-cache" || kind == "missing-last" || kind == "reorder" {
				data, err = json.Marshal(m)
				if err != nil {
					t.Fatal(err)
				}
			}
			path := filepath.Join(out, "battle-friendly-man21.json")
			if kind == "symlink" {
				err = os.Symlink(filepath.Join(dir, "battle-friendly-man21.json"), path)
			} else if kind != "missing" {
				err = os.WriteFile(path, data, 0644)
			}
			if err != nil {
				t.Fatal(err)
			}
			before, err := json.Marshal(a)
			if err != nil {
				t.Fatal(err)
			}
			err = loadFriendlyMan21(out, sourceRoot, a)
			if (kind == "missing") != (err == nil) {
				t.Fatal("回退結果不符", kind, err)
			}
			after, err := json.Marshal(a)
			if err != nil || !bytes.Equal(before, after) {
				t.Fatal("失敗群改變既有素材", kind, err)
			}
		})
	}
}
