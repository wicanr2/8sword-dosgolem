//go:build ignore

package eightsword

import (
	"compress/gzip"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"image/png"
	"os"
	"path/filepath"
	"testing"
)

func researchExportActorMasks(e *Engine, scene *ownedScene, dir string, t *testing.T) {
	pixels := scene.Pixels[scene.Start : scene.Start+128000]
	grid := make([]byte, 128000*6)
	mask := make([]byte, 1920*1200)
	tiles := map[uint16]map[string]any{}
	materials := e.Tracker.graphics.assets.Actors
	if materials == nil {
		materials = map[uint16]*graphicMaterial{}
	}
	for i, p := range pixels {
		binary.LittleEndian.PutUint16(grid[i*6:], p.Actor.ID)
		binary.LittleEndian.PutUint32(grid[i*6+2:], p.Actor.Local)
		if p.Actor.ID != 0 {
			if _, ok := tiles[p.Actor.ID]; !ok {
				m := materials[p.Actor.ID]
				info := map[string]any{"missing": true}
				if m != nil && m.Tile != nil {
					name := fmt.Sprintf("actor-%d.png", p.Actor.ID)
					f, err := os.Create(filepath.Join(dir, name))
					if err != nil {
						t.Fatal(err)
					}
					if err = png.Encode(f, m.Tile); err != nil {
						t.Fatal(err)
					}
					f.Close()
					info = map[string]any{"file": name, "width": m.NativeWidth, "height": m.NativeHeight, "missing": false}
				}
				tiles[p.Actor.ID] = info
			}
		}
		for y := i / 640 * 6; y < i/640*6+6; y++ {
			for x := i % 640 * 3; x < i%640*3+3; x++ {
				if p.Text.ID != 0 || spellCueActorProtected(p, x, y, materials) {
					mask[y*1920+x] = 1
				}
			}
		}
	}
	for name, raw := range map[string][]byte{"mask-hd.gz": mask, "actor-grid.gz": grid} {
		f, err := os.Create(filepath.Join(dir, name))
		if err != nil {
			t.Fatal(err)
		}
		g := gzip.NewWriter(f)
		if _, err = g.Write(raw); err != nil {
			t.Fatal(err)
		}
		g.Close()
		f.Close()
	}
	raw, err := json.MarshalIndent(tiles, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(dir, "actor-tiles.json"), append(raw, '\n'), 0644); err != nil {
		t.Fatal(err)
	}
}
