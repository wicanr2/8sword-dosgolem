package eightsword

import (
	"bytes"
	"image"
	"image/color"
	"os"
	"path/filepath"
	"testing"
)

func TestStaticObjectPremultipliedAlpha(t *testing.T) {
	background := image.NewRGBA(image.Rect(0, 0, 192, 150))
	for y := 0; y < 150; y++ {
		for x := 0; x < 192; x++ {
			background.SetRGBA(x, y, color.RGBA{50, 100, 150, 255})
		}
	}
	source := image.NewNRGBA(background.Bounds())
	source.SetNRGBA(50, 50, color.NRGBA{255, 0, 0, 128})
	source.SetNRGBA(80, 80, color.NRGBA{0, 0, 255, 255})
	source.SetNRGBA(1, 1, color.NRGBA{255, 0, 0, 1})
	out, err := compositeStaticObject(source, background)
	if err != nil {
		t.Fatal(err)
	}
	for _, p := range []image.Point{{0, 0}, {1, 1}} {
		if out.RGBAAt(p.X, p.Y) != (color.RGBA{50, 100, 150, 255}) {
			t.Fatal("transparent/noise pixel did not preserve grass")
		}
	}
	if out.RGBAAt(50, 50) != (color.RGBA{153, 50, 75, 255}) {
		t.Fatal("semi-transparent colour multiplied alpha twice")
	}
	if out.RGBAAt(80, 80) != (color.RGBA{0, 0, 255, 255}) {
		t.Fatal("opaque object pixel changed")
	}
}

func TestActualStaticEdgesAndSandSources(t *testing.T) {
	a, _, dir, _ := realGraphics(t)
	grass := a.Materials[1].Tile
	for _, index := range []int{50, 53, 57} {
		tile := a.Materials[uint16(index+1)].Tile
		changed := 0
		for y := 0; y < 150; y++ {
			for x := 0; x < 192; x++ {
				c := tile.RGBAAt(x, y)
				if c.A != 255 {
					t.Fatal("static cache was not flattened")
				}
				if c != grass.RGBAAt(x, y) {
					changed++
				}
				if (x == 0 || x == 191 || y == 0 || y == 149) && c != grass.RGBAAt(x, y) {
					t.Fatalf("static %d edge did not match grass", index)
				}
			}
		}
		if changed < 500 {
			t.Fatal("actual object disappeared into background")
		}
	}
	for i := 30; i <= 44; i++ {
		if a.Materials[uint16(i+1)] == nil {
			t.Fatalf("missing yellow-earth source %d", i)
		}
	}
	if a.Materials[46] != nil {
		t.Fatal("source 45 guessed into yellow-earth range")
	}
	// The original 30 has no green pixels; 31 is explicitly a mixed source.
	for _, c := range a.Native[30].Pixels {
		if c == 2 || c == 10 {
			t.Fatal("pure source 30 is not pure")
		}
	}
	if !bytes.Contains(a.Native[31].Pixels, []byte{2}) {
		t.Fatal("mixed source 31 lost its original grass")
	}
	// Validate a real transparent PNG rather than testing just synthetic alpha.
	raw, err := os.ReadFile(filepath.Join(dir, "pmap-57-house-r1.png"))
	if err != nil {
		t.Fatal(err)
	}
	decoded, _, err := image.Decode(bytes.NewReader(raw))
	if err != nil {
		t.Fatal(err)
	}
	if _, err = compositeStaticObject(decoded, grass); err != nil {
		t.Fatal(err)
	}
}
