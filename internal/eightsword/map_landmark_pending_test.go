package eightsword

import (
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

func TestMapPendingLandmarksIndependentFailures(t *testing.T) {
	dir, base, root, _ := landmark52Paths(t)
	old, err := Open(Options{Root: root, Assets: base, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer old.Close()
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatal(err)
	}
	for _, broken := range [][]int{{52}, {56}, {52, 56}, {55, 52}} {
		t.Run(fmt.Sprint(broken), func(t *testing.T) {
			out := t.TempDir()
			for _, entry := range entries {
				raw, err := os.ReadFile(filepath.Join(dir, entry.Name()))
				if err != nil {
					t.Fatal(err)
				}
				for _, index := range broken {
					if entry.Name() == fmt.Sprintf("map-landmark-%d-r1.png", index) {
						raw[len(raw)-20] ^= 1
					}
				}
				if err := os.WriteFile(filepath.Join(out, entry.Name()), raw, 0644); err != nil {
					t.Fatal(err)
				}
			}
			e, err := Open(Options{Root: root, Assets: out, Saves: t.TempDir(), HD: true})
			if err != nil {
				t.Fatal(err)
			}
			defer e.Close()
			if !e.HD || e.GraphicsError != "" || e.AssetError != "" || strings.Count(e.MapLandmarkError, "SHA-256") != len(broken) {
				t.Fatal(e.Status())
			}
			a, b := e.Tracker.graphics.assets, old.Tracker.graphics.assets
			if len(a.Materials) != len(b.Materials)+2-len(broken) {
				t.Fatal("群組數量不符")
			}
			for _, index := range []int{52, 56, 55} {
				bad := false
				for _, candidate := range broken {
					bad = bad || candidate == index
				}
				if (a.Materials[uint16(index+1)] == nil) != bad {
					t.Fatalf("物件 %d 未獨立回退", index)
				}
			}
			for id, entry := range b.Materials {
				skip := false
				for _, index := range broken {
					skip = skip || id == uint16(index+1)
				}
				if skip {
					continue
				}
				if !reflect.DeepEqual(a.Materials[id], entry) {
					t.Fatalf("舊材質 %d 改變", id)
				}
			}
			if !reflect.DeepEqual(e.Assets, old.Assets) || !reflect.DeepEqual(a.Actors, b.Actors) || !reflect.DeepEqual(a.Effects, b.Effects) {
				t.Fatal("獨立回退改變字型、角色或效果")
			}
		})
	}
}
