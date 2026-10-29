//go:build ignore

// Pure Go replay on actual source frames. The prior renderer is copied from the
// frozen, accepted r2 source and renamed only in this private diagnostic module.
package eightsword

import (
	"compress/gzip"
	"encoding/json"
	"fmt"
	"image"
	"image/draw"
	"image/png"
	"io"
	"os"
	"path/filepath"
	"testing"
)

func TestResearchMapColorReplay(t *testing.T) {
	root := os.Getenv("EIGHTSWORD_COLOR_OUT")
	if root == "" {
		t.Fatal("missing color output")
	}
	readMask := func(path string) []byte {
		f, e := os.Open(path)
		if e != nil {
			t.Fatal(e)
		}
		defer f.Close()
		g, e := gzip.NewReader(f)
		if e != nil {
			t.Fatal(e)
		}
		defer g.Close()
		b, e := io.ReadAll(g)
		if e != nil || len(b) != 128000 {
			t.Fatal("bad mask", e)
		}
		return b
	}
	for kind := 0; kind < 8; kind++ {
		dir := filepath.Join(root, "normal-r2", fmt.Sprint(kind))
		raw, e := os.ReadFile(filepath.Join(dir, "receipt.json"))
		if e != nil {
			t.Fatal(e)
		}
		var m struct {
			Sample int
			Cue    struct{ Anchor [2]int }
		}
		if e = json.Unmarshal(raw, &m); e != nil {
			t.Fatal(e)
		}
		f, e := os.Open(filepath.Join(dir, "base.png"))
		if e != nil {
			t.Fatal(e)
		}
		decoded, e := png.Decode(f)
		f.Close()
		if e != nil {
			t.Fatal(e)
		}
		base := image.NewRGBA(decoded.Bounds())
		draw.Draw(base, base.Bounds(), decoded, decoded.Bounds().Min, draw.Src)
		text, mask := readMask(filepath.Join(dir, "text-mask.gz")), readMask(filepath.Join(dir, "mask.gz"))
		pixels := make([]ownedPixel, 128000)
		for i := range pixels {
			if text[i] != 0 {
				pixels[i].Text.ID = 1
			}
			if mask[i] != 0 && text[i] == 0 {
				pixels[i].Actor.ID = 1
			}
		}
		prior := drawPriorSpellCue(kind, float64(m.Sample)/120, m.Cue.Anchor)
		old := compositeSpellCue(base, prior, pixels)
		out, e := os.Create(filepath.Join(dir, "prior-replay.png"))
		if e != nil {
			t.Fatal(e)
		}
		if e = png.Encode(out, old); e != nil {
			t.Fatal(e)
		}
		out.Close()
	}
}
