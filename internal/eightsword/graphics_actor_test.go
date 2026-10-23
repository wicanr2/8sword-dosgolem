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

func TestMilitiaSourceCacheAndLegacyPack(t *testing.T) {
	dir, original := os.Getenv("EIGHTSWORD_TEST_ARMY_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ORIG")
	if dir == "" || original == "" {
		t.Skip("需要本機 018 民兵及原版資料")
	}
	if _, err := os.Stat(filepath.Join(dir, "terrain.json")); os.IsNotExist(err) {
		t.Skip("本機尚未匯入 018 民兵素材")
	} else if err != nil {
		t.Fatal(err)
	}
	pmap, err := os.ReadFile(filepath.Join(original, "PMAP.AY"))
	if err != nil {
		t.Fatal(err)
	}
	a, err := loadGraphicsAssets(dir, pmap)
	if err != nil || a == nil || len(a.Native) != 85 || len(a.Actors) != 13 {
		t.Fatalf("militia catalogue: %v", err)
	}
	legacy, err := loadGraphicsAssets(os.Getenv("EIGHTSWORD_TEST_PUBLISHER_ASSETS"), pmap)
	if err != nil || legacy == nil || len(legacy.Native) != 84 || len(legacy.Actors) != 12 {
		t.Fatalf("legacy catalogue: %v", err)
	}
	for id, m := range legacy.Actors {
		if !bytes.Equal(m.Tile.Pix, a.Actors[id].Tile.Pix) || m.NativeWidth != a.Actors[id].NativeWidth || m.NativeHeight != a.Actors[id].NativeHeight {
			t.Fatalf("legacy actor cache changed: %d", id)
		}
	}
	for id, m := range legacy.Materials {
		if !bytes.Equal(m.Tile.Pix, a.Materials[id].Tile.Pix) {
			t.Fatalf("legacy material changed: %d", id)
		}
	}
	raw, err := os.ReadFile(filepath.Join(original, "MAN01.EGG"))
	if err != nil || hash(raw) != "a7e02cf495800fac19c293688043f3af6eb6deaec1a61a581ed3f9d5b8b3e5f1" {
		t.Fatalf("original militia source: %v", err)
	}
	mirrored := append([]byte(nil), raw[:3304]...)
	for plane := 0; plane < 6; plane++ {
		for y := 0; y < 50; y++ {
			for x := 0; x < 11; x++ {
				v, reversed := raw[4+plane*550+y*11+10-x], byte(0)
				for bit := 0; bit < 8; bit++ {
					reversed = reversed<<1 | v&1
					v >>= 1
				}
				mirrored[4+plane*550+y*11+x] = reversed
			}
		}
	}
	tracker, g := graphicsFixture()
	g.assets, g.actors, g.Stats.Bound = a, make([]graphicCell, 65536*8), true
	if hash(mirrored[:2204]) != militiaNativeSHA || !g.heroRecordMatches(85, 6, mirrored) || g.heroRecordMatches(85, 5, mirrored) {
		t.Fatal("militia source or plane kind not checked")
	}
	mirrored[3303] ^= 1
	if g.heroRecordMatches(85, 6, mirrored) {
		t.Fatal("changed sixth-plane mask accepted")
	}
	mirrored[3303] ^= 1
	const first = uint32(0x4413)
	paper := a.Materials[47]
	for y := 0; y < 50; y++ {
		for x := 0; x < 88; x++ {
			g.set((first+uint32(y*80+x/8))*8+uint32(x%8), graphicCell{47, uint32((y%paper.NativeHeight)*paper.NativeWidth + x%paper.NativeWidth)})
		}
	}
	if !g.actorBackgroundKnown(first, 88, 50) || g.actorBackgroundKnown(first, 88, 49) {
		t.Fatal("militia background geometry not checked")
	}
	saved := append([]graphicCell(nil), g.owners...)
	g.active = &bitmapCall{Kind: 6, Width: 11, Height: 50, First: first, Actor: 85, Mask: mirrored[2754:]}
	for plane := 0; plane < 4; plane++ {
		for y := 0; y < 50; y++ {
			for x := 0; x < 11; x++ {
				tracker.write(oracle.VideoWrite{CS: 0x14d2, IP: 0x57d, Offset: first + uint32(y*80+x), WriteMode: 0})
			}
		}
	}
	if !bytes.Equal(graphicBytes(saved), graphicBytes(g.owners)) || g.Stats.ActorCompletions != 1 {
		t.Fatal("militia transaction damaged paper or failed to finish")
	}
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	for at := 0; at < len(out.Pix); at += 4 {
		copy(out.Pix[at:at+4], []byte{255, 0, 255, 255})
	}
	g.paint(out, oracle.PlanarDisplay{Width: 640, Height: 200, Pitch: 80, LineCompare: 1023, Palette: canonicalEGA, Start: first})
	tile := a.Actors[85].Tile
	if tile.Bounds() != image.Rect(0, 0, 264, 300) || g.Stats.ActorPaintedPixels != 4400 {
		t.Fatal("militia cache truncated to hero dimensions")
	}
	transparent, opaque := 0, 0
	for y := 0; y < 300; y++ {
		for x := 0; x < 264; x++ {
			src, dst := y*tile.Stride+x*4, y*out.Stride+x*4
			alpha := uint32(tile.Pix[src+3])
			if alpha == 0 {
				transparent++
			}
			if alpha >= 250 {
				opaque++
			}
			px, py := (x/3%paper.NativeWidth)*3+x%3, (y/6%paper.NativeHeight)*6+y%6
			for c := 0; c < 3; c++ {
				want := uint8(min(255, uint32(tile.Pix[src+c])+(uint32(paper.Tile.Pix[py*paper.Tile.Stride+px*4+c])*(255-alpha)+127)/255))
				if out.Pix[dst+c] != want {
					t.Fatalf("militia/paper mismatch at %d,%d", x, y)
				}
			}
		}
	}
	if transparent == 0 || opaque == 0 {
		t.Fatal("militia transparency/body lost")
	}
	last := (first+49*80+10)*8 + 7
	g.set(last, graphicCell{})
	if g.actorBackgroundKnown(first, 88, 50) {
		t.Fatal("missing final background pixel accepted")
	}
	// A real last-PNG failure rejects the entire graphics group after all
	// twelve existing hero files have passed their own validation.
	bad := t.TempDir()
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		data, err := os.ReadFile(filepath.Join(dir, entry.Name()))
		if err != nil {
			t.Fatal(err)
		}
		if entry.Name() == "militia-painted-r1.png" {
			data[len(data)-1] ^= 1
		}
		if err := os.WriteFile(filepath.Join(bad, entry.Name()), data, 0600); err != nil {
			t.Fatal(err)
		}
	}
	if partial, err := loadGraphicsAssets(bad, pmap); err == nil || partial != nil {
		t.Fatal("late militia failure published partial graphics group")
	}
}
