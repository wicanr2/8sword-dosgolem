package eightsword

// Spec 054: install only in a private source copy. Export loaded art, no game run.
import (
	"encoding/json"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestExportHDLibrary(t *testing.T) {
	project, out := os.Getenv("HD_LIBRARY_PROJECT"), os.Getenv("HD_LIBRARY_OUT")
	if project == "" || out == "" {
		t.Skip("private artwork export only")
	}
	root := filepath.Join(project, "workplace/intake-20261023/sources/game/8sword")
	assets := filepath.Join(project, "workplace/player/assets-painted-r64")
	e, err := Open(Options{Root: root, Assets: assets, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	for k, v := range e.Status() {
		if strings.HasSuffix(k, "error") && v != "" && v != nil {
			t.Fatalf("%s: %v", k, v)
		}
	}
	var ledger struct {
		Records []struct {
			File        string `json:"source_file"`
			Record      int    `json:"record"`
			Fingerprint string `json:"native_fingerprint"`
			Mirrored    string `json:"mirrored_fingerprint"`
			SHA         string `json:"record_sha256"`
		} `json:"records"`
	}
	raw, err := os.ReadFile(filepath.Join(project, "artwork/all-graphics-sources-r1.json"))
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(raw, &ledger); err != nil {
		t.Fatal(err)
	}
	result := []map[string]any{}
	write := func(name string, im image.Image) string {
		if im == nil {
			return ""
		}
		p := filepath.Join(out, name+".png")
		f, er := os.Create(p)
		if er != nil {
			t.Fatal(er)
		}
		if er = png.Encode(f, im); er != nil {
			t.Fatal(er)
		}
		if er = f.Close(); er != nil {
			t.Fatal(er)
		}
		return filepath.Base(p)
	}
	g := e.Tracker.graphics.assets
	for _, r := range ledger.Records {
		var im image.Image
		method := ""
		if id, ok := g.ByNative[r.Fingerprint]; ok {
			for _, q := range []struct {
				name  string
				items map[uint16]*graphicMaterial
			}{{"go-actor", g.Actors}, {"go-material", g.Materials}, {"go-effect", g.Effects}} {
				if v := q.items[id]; v != nil {
					im = v.Tile
					method = q.name
					break
				}
			}
		}
		if im == nil && r.File == "MAN01.EGG" {
			if id, ok := g.ByNative[r.Mirrored]; ok {
				if a := g.Actors[id]; a != nil {
					b := a.Tile.Bounds()
					v := image.NewRGBA(b)
					for y := 0; y < b.Dy(); y++ {
						for x := 0; x < b.Dx(); x++ {
							v.Set(x, y, a.Tile.At(b.Dx()-1-x, y))
						}
					}
					im = v
					method = "go-actor-reverse-mirror-to-file-orientation"
				}
			}
		}
		if a := e.endingAssets; a != nil {
			for _, q := range []struct {
				name  string
				items map[string]image.Image
			}{{"ending-portrait", a.art.portraits}, {"ending-effect", a.art.effects}, {"ending-pair", a.art.pair}} {
				if v := q.items[r.SHA]; v != nil {
					im = v
					method = q.name
				}
			}
			if r.SHA == endingDuelSource {
				im = a.art.duel
				method = "ending-duel"
			}
			if r.SHA == endingSwordsSource {
				im = a.art.swords
				method = "ending-swords"
			}
			if r.SHA == endingRingSource {
				im = a.art.ring
				method = "ending-ring"
			}
			if r.File == "END7.AY" {
				im = a.art.end7
				method = "ending-landscape"
			}
			if r.File == "END8.AY" || r.File == "TIT2.AY" {
				im = a.art.titles["noto"]
				method = "title-font-noto"
			}
		}
		if m := e.Museum; m != nil {
			if v := m.actorSprites[r.SHA]; v != nil {
				im = v
				method = "museum-actor"
			}
			if v := m.records[r.SHA]; v != nil {
				switch v.role {
				case "left":
					im = m.art
					method = "museum-left"
				case "right":
					im = m.sceneArts["right:"+m.variant]
					method = "museum-right"
				case "portrait":
					im = m.sceneArts["portrait:all"]
					method = "heroine-portrait"
				}
			}
		}
		if im != nil {
			name := fmt.Sprintf("%s-%02d", strings.ReplaceAll(strings.ToLower(r.File), ".", "-"), r.Record)
			file := write(name, im)
			result = append(result, map[string]any{"source_file": r.File, "record": r.Record, "file": file, "method": method, "width": im.Bounds().Dx(), "height": im.Bounds().Dy()})
		}
	}
	raw, err = json.MarshalIndent(result, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(out, "export.json"), append(raw, '\n'), 0644); err != nil {
		t.Fatal(err)
	}
	t.Logf("exported %d of %d original records", len(result), len(ledger.Records))
}
