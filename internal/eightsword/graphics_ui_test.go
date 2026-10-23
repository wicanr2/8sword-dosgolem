package eightsword

import (
	"image"
	"image/color"
	"os"
	"path/filepath"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

func TestRealUISourcesAndContentRegions(t *testing.T) {
	a, _, _, root := realGraphics(t)
	for _, source := range []struct {
		file  string
		index int
	}{{"BUMBOO.AY", 69}, {"MSGBOX.AY", 70}} {
		raw, err := os.ReadFile(filepath.Join(root, source.file))
		if err != nil || hash(raw) != a.Native[source.index].NativeSHA {
			t.Fatalf("UI source mismatch: %s", source.file)
		}
	}
	frame := a.Materials[72].Tile
	if frame.Bounds() != image.Rect(0, 0, 1920, 1200) {
		t.Fatal("full frame size mismatch")
	}
	black := color.RGBA{0, 0, 0, 255}
	for _, r := range []image.Rectangle{image.Rect(8, 12, 456, 187), image.Rect(465, 9, 632, 29), image.Rect(14, 192, 450, 197)} {
		for y := r.Min.Y * 6; y < r.Max.Y*6; y++ {
			for x := r.Min.X * 3; x < r.Max.X*3; x++ {
				if frame.RGBAAt(x, y) != black {
					t.Fatalf("UI ornament crossed original content at %d,%d", x, y)
				}
			}
		}
	}
	message := a.Materials[71].Tile
	for y := 18; y < 432; y++ {
		for x := 18; x < 1326; x++ {
			if message.RGBAAt(x, y) != (color.RGBA{85, 85, 85, 255}) {
				t.Fatal("message opaque text background no longer matches original")
			}
		}
	}
}

func TestFullFrameCoordinatesSurviveWriteAndPageCopy(t *testing.T) {
	a, _, _, _ := realGraphics(t)
	tracker, g := graphicsFixture()
	g.assets = a
	g.Stats.Bound = true
	g.active = &bitmapCall{Kind: 4, Width: 80, Height: 200, First: 0, Material: 72}
	tracker.write(oracle.VideoWrite{CS: 0x14d2, IP: 0x9fc, Offset: 15999, WriteMode: 0})
	if g.owners[15999*8+7].Local != 127999 {
		t.Fatal("last full-frame coordinate truncated")
	}
	tracker.copyByte(0x4000+15999, 15999)
	if g.owners[(0x4000+15999)*8+7].Local != 127999 {
		t.Fatal("page copy truncated full-frame coordinate")
	}
	tracker.write(oracle.VideoWrite{CS: 0x14d2, IP: 0x9fc, Offset: 15840, WriteMode: 0})
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	g.paint(out, oracle.PlanarDisplay{Width: 640, Height: 200, Pitch: 80, LineCompare: 1023, Palette: canonicalEGA})
	got := out.RGBAAt(0, 1188)
	if got != a.Materials[72].Tile.RGBAAt(0, 1188) || got == (color.RGBA{0, 0, 0, 255}) {
		t.Fatal("bottom gold frame sampled a wrapped coordinate")
	}
}
