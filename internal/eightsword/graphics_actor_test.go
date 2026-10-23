package eightsword

import (
	"bytes"
	"image"
	"image/color"
	"os"
	"path/filepath"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

func actorFixture(t *testing.T) (*Tracker, *Graphics, []byte) {
	t.Helper()
	a, _, _, root := realGraphics(t)
	man, err := os.ReadFile(filepath.Join(root, "MAN.AY"))
	if err != nil {
		t.Fatal(err)
	}
	tracker, g := graphicsFixture()
	g.assets = a
	g.actors = make([]graphicCell, 65536*8)
	g.Stats.Bound = true
	return tracker, g, man
}

func TestActualActorRecordsAndAlpha(t *testing.T) {
	_, g, man := actorFixture(t)
	seen := map[string]bool{}
	for frame, source := range heroSources {
		raw := man[frame*1204 : (frame+1)*1204]
		if hash(raw) != source.RecordSHA || hash(raw[:804]) != source.NativeSHA {
			t.Fatalf("wrong original record %d", frame)
		}
		id := uint16(73 + frame)
		m := g.assets.Actors[id]
		if m == nil {
			continue
		}
		if !g.heroRecordMatches(id, 6, raw) || g.heroRecordMatches(id, 5, raw) {
			t.Fatal("masked source kind not checked")
		}
		changed := append([]byte(nil), raw...)
		changed[len(changed)-1] ^= 1
		if g.heroRecordMatches(id, 6, changed) {
			t.Fatal("changed native mask accepted")
		}
		sha := hash(m.Tile.Pix)
		if seen[sha] {
			t.Fatal("standing pose reused as another gait")
		}
		seen[sha] = true
		transparent, opaque := 0, 0
		for at := 0; at < len(m.Tile.Pix); at += 4 {
			p := m.Tile.Pix[at : at+4]
			if p[3] == 0 {
				transparent++
			}
			// Real PNGs have opaque source pixels, but bilinear downsampling
			// need not land on one exactly. Require a clearly visible body.
			if p[3] >= 250 {
				opaque++
			}
			if p[0] > p[3] || p[1] > p[3] || p[2] > p[3] {
				t.Fatal("actor cache is not premultiplied")
			}
		}
		if transparent == 0 || opaque == 0 {
			t.Fatalf("actor %d lost transparent canvas or opaque body: transparent=%d opaque=%d", frame, transparent, opaque)
		}
	}
	if len(seen) != 12 {
		t.Fatal("actual twelve actor frames missing")
	}
	source := image.NewNRGBA(image.Rect(0, 0, 192, 150))
	source.SetNRGBA(0, 0, color.NRGBA{255, 0, 0, 128})
	source.SetNRGBA(1, 0, color.NRGBA{0, 0, 255, 255})
	sampled, err := sampleActor(source)
	if err != nil {
		t.Fatal(err)
	}
	if sampled.RGBAAt(0, 0) != (color.RGBA{128, 0, 0, 128}) {
		t.Fatal("semi-transparent red was not premultiplied exactly once")
	}
}

func TestActorRestoresBackgroundAndSurvivesPageCopy(t *testing.T) {
	tracker, g, man := actorFixture(t)
	const first = uint32(0x500)
	const actorID = uint16(79) // MAN frame 6, standing left.
	for y := 0; y < 25; y++ {
		for x := 0; x < 64; x++ {
			g.set((first+uint32(y*80+x/8))*8+uint32(x%8), graphicCell{1, uint32(y*64 + x)})
		}
	}
	if !g.actorBackgroundKnown(first, 64, 25) {
		t.Fatal("actual complete background rejected")
	}
	saved := append([]graphicCell(nil), g.owners...)
	raw := man[6*1204 : 7*1204]
	g.active = &bitmapCall{Kind: 6, Width: 8, Height: 25, First: first, Actor: actorID, Mask: raw[1004:]}
	for y := 0; y < 25; y++ {
		for x := 0; x < 8; x++ {
			tracker.write(oracle.VideoWrite{CS: 0x14d2, IP: 0x57d, Offset: first + uint32(y*80+x), WriteMode: 0})
		}
	}
	if !bytes.Equal(graphicBytes(saved), graphicBytes(g.owners)) {
		t.Fatal("painted actor erased underlying HD ownership")
	}
	tracker.copyByte(first+0x4000, first)
	tracker.copyByte(first, first)
	for bit := 0; bit < 8; bit++ {
		if g.actors[(first+0x4000)*8+uint32(bit)] != g.actors[first*8+uint32(bit)] {
			t.Fatal("actor page copy lost local coordinates")
		}
	}
	// The original framebuffer may still contain the old magenta silhouette.
	// Every transparent new pixel must restore HD grass, not retain that ink.
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	for at := 0; at < len(out.Pix); at += 4 {
		copy(out.Pix[at:at+4], []byte{255, 0, 255, 255})
	}
	display := oracle.PlanarDisplay{Width: 640, Height: 200, Pitch: 80, LineCompare: 1023, Palette: canonicalEGA, Start: first}
	g.paint(out, display)
	tile, grass := g.assets.Actors[actorID].Tile, g.assets.Materials[1].Tile
	newOutsideMask := 0
	for y := 0; y < 150; y++ {
		for x := 0; x < 192; x++ {
			src := y*tile.Stride + x*4
			a := uint32(tile.Pix[src+3])
			dst := y*out.Stride + x*4
			for c := 0; c < 3; c++ {
				want := uint8(min(255, uint32(tile.Pix[src+c])+(uint32(grass.Pix[src+c])*(255-a)+127)/255))
				if out.Pix[dst+c] != want {
					t.Fatalf("native ink/background mismatch at %d,%d", x, y)
				}
			}
			if a > 0 && raw[1004+(y/6)*8+(x/3)/8]&(128>>uint((x/3)%8)) == 0 {
				newOutsideMask++
			}
		}
	}
	if newOutsideMask == 0 || g.Stats.ActorPaintedPixels < 1600 {
		t.Fatal("new contour did not extend outside original native mask")
	}
	// Same-value generic writes and opaque UI both invalidate actor ownership.
	tracker.write(oracle.VideoWrite{Offset: first, Value: 0})
	for bit := 0; bit < 8; bit++ {
		if g.actors[first*8+uint32(bit)].ID != 0 {
			t.Fatal("same-value write left actor ink")
		}
	}
	if g.actorBackgroundKnown(first, 64, 25) {
		t.Fatal("missing background accepted")
	}
	g.clear()
	for _, c := range g.actors {
		if c.ID != 0 {
			t.Fatal("mode clear retained actor")
		}
	}
}
