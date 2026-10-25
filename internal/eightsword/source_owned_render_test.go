package eightsword

import (
	"bytes"
	"image"
	"testing"
)

func renderTestTile(w, h int, alpha bool) *image.RGBA {
	im := image.NewRGBA(image.Rect(0, 0, w*3, h*6))
	for y := 0; y < im.Bounds().Dy(); y++ {
		for x := 0; x < im.Bounds().Dx(); x++ {
			a := uint8(255)
			if alpha {
				a = []uint8{0, 64, 128, 255}[(x/3+y/6)%4]
			}
			at := y*im.Stride + x*4
			im.Pix[at] = uint8(uint32((x*7+y*11)&255) * uint32(a) / 255)
			im.Pix[at+1] = uint8(uint32((x*13+y*3)&255) * uint32(a) / 255)
			im.Pix[at+2] = uint8(uint32((x*2+y*17)&255) * uint32(a) / 255)
			im.Pix[at+3] = a
		}
	}
	return im
}

func TestSourceOwnedBatchMatchesFrozenLayers(t *testing.T) {
	for _, start := range []int{0, 0x4000 * 8} {
		s := &ownedScene{Pixels: make([]ownedPixel, 65536*8), Glyphs: map[uint32]*glyph{}, Effects: map[uint16]*image.RGBA{}, Start: start}
		art := &GraphicsAssets{Materials: map[uint16]*graphicMaterial{}, Actors: map[uint16]*graphicMaterial{}}
		art.Materials[1] = &graphicMaterial{NativeWidth: 64, NativeHeight: 25, Tile: renderTestTile(64, 25, false)}
		art.Actors[2] = &graphicMaterial{NativeWidth: 88, NativeHeight: 50, Tile: renderTestTile(88, 50, true)}
		s.Effects[3] = renderTestTile(88, 50, true)
		for y := 0; y < 200; y++ {
			for x := 0; x < 640; x++ {
				c := &s.Pixels[start+y*640+x]
				c.Color = uint8((x/3 + y/5) & 15)
				if x >= 20 && x < 340 && y >= 25 && y < 150 {
					c.Material = graphicCell{1, uint32(((y-25)%25)*64 + (x-20)%64)}
				}
				if x >= 104 && x < 192 && y >= 40 && y < 90 && (x+y)%11 != 0 {
					c.Actor = graphicCell{2, uint32((y-40)*88 + x - 104)}
				}
				if x >= 140 && x < 228 && y >= 50 && y < 100 {
					c.Effect = graphicCell{3, uint32((y-50)*88 + x - 140)}
					c.EffectBase = uint8((x + y) & 15)
				}
			}
		}
		old := renderOwnedSceneReference(s, &Assets{}, art, nil)
		modern, stats := renderOwnedSceneBatch(s, &Assets{}, art, nil)
		if !bytes.Equal(old.Pix, modern.Pix) {
			for at := range old.Pix {
				if old.Pix[at] != modern.Pix[at] {
					t.Fatalf("page=%d RGBA byte=%d old=%d batch=%d", start, at, old.Pix[at], modern.Pix[at])
				}
			}
		}
		if stats.NativeRGBPixels == 0 || stats.TextureCopyPixels == 0 || stats.BlendedPixels == 0 {
			t.Fatal("layer positive controls absent", stats)
		}
		if stats.CopyRectangles >= stats.TextureCopyPixels/18 {
			t.Fatal("texture cells were not batched", stats)
		}
	}
}

func TestSourceOwnedBatchRejectsBeforePainting(t *testing.T) {
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	for i := range out.Pix {
		out.Pix[i] = 0xa5
	}
	before := append([]byte(nil), out.Pix...)
	b := ownedRenderBatch{Operations: []ownedRenderOp{
		{Destination: image.Rect(0, 0, 30, 6), Color: [3]uint8{1, 2, 3}},
		{Texture: renderTestTile(1, 1, false), Destination: image.Rect(0, 0, 30, 6)},
	}}
	if submitOwnedBatch(out, &b) == nil || !bytes.Equal(before, out.Pix) {
		t.Fatal("invalid complete packet partly painted")
	}
}
