package eightsword

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"github.com/wicanr2/dosgolem/oracle"
	"image"
	"math/bits"
	"os"
	"path/filepath"
	"testing"
)

func graphicsFixture() (*Tracker, *Graphics) {
	t := &Tracker{loadSegment: 0x110, stringSeg: 0x14d2, fontSeg: 0xaa8, owners: make([]cell, 65536*8), glyphs: map[uint32]*glyph{1: {ID: 1, Width: 16}}}
	g := newGraphics(t, &GraphicsAssets{})
	t.graphics = g
	return t, g
}

func TestBitmapSourceNeverReadsVideoMemoryOrCrossesSegment(t *testing.T) {
	for _, test := range []struct {
		ptr    oracle.Addr
		length int
		valid  bool
	}{{oracle.Addr{Seg: 0x8000, Off: 0x20ec}, 1204, true},
		{oracle.Addr{Seg: 0x9fff, Off: 0xf}, 1, true},
		{oracle.Addr{Seg: 0x9fff, Off: 0xf}, 2, false},
		{oracle.Addr{Seg: 0xa000}, 4, false},
		{oracle.Addr{Seg: 0x7000, Off: 0xfffd}, 4, false}} {
		if bitmapSourceInRAM(test.ptr, test.length) != test.valid {
			t.Fatalf("unsafe source boundary %v length %d", test.ptr, test.length)
		}
	}
}
func TestRealSpriteMaskPreservesTransparentImageAndText(t *testing.T) {
	root := os.Getenv("EIGHTSWORD_TEST_ORIG")
	if root == "" {
		t.Skip("requires real original sprite")
	}
	raw, err := os.ReadFile(filepath.Join(root, "MAN.AY"))
	if err != nil {
		t.Fatal(err)
	}
	sprite := raw[8428 : 8428+1204]
	if hash(sprite) != "550add966262b8c457200f91759cf97fadb3808f70b8e4e7a862bfc7b0f46436" {
		t.Fatal("runtime-proven sprite corpus changed")
	}
	width, height := int(binary.LittleEndian.Uint16(sprite)), int(binary.LittleEndian.Uint16(sprite[2:]))
	area := width * height
	mask := sprite[4+5*area : 4+6*area]
	column := -1
	for i, b := range mask {
		if b != 0 && b != 255 {
			column = i
			break
		}
	}
	if column < 0 {
		t.Fatal("real sprite has no mixed transparent/opaque byte")
	}
	tracker, g := graphicsFixture()
	first := uint32(0x500)
	off := first + uint32(column/width*80+column%width)
	g.active = &bitmapCall{Kind: 6, Width: width, Height: height, First: first, Mask: mask}
	for bit := 0; bit < 8; bit++ {
		at := off*8 + uint32(bit)
		g.set(at, graphicCell{1, uint16(bit)})
		tracker.set(at, cell{ID: 1, Local: uint16(bit), Ink: true})
	}
	tracker.write(oracle.VideoWrite{CS: 0x14d2, IP: 0x57d, Offset: off, Value: 0, WriteMode: 0})
	for bit := 0; bit < 8; bit++ {
		opaque := mask[column]&(0x80>>uint(bit)) != 0
		at := off*8 + uint32(bit)
		if (g.owners[at].ID == 0) != opaque || (tracker.owners[at].ID == 0) != opaque {
			t.Fatalf("wrong sprite coverage for bit %d, mask %08b", bit, mask[column])
		}
	}
	if tracker.glyphs[1].Refs != 8-bits.OnesCount8(mask[column]) {
		t.Fatal("transparent sprite bits lost text references")
	}
}
func TestImagePageCopyAndSameValueWrite(t *testing.T) {
	tracker, g := graphicsFixture()
	const source = uint32(11)
	const dest = uint32(0x400b)
	for bit := 0; bit < 8; bit++ {
		g.set(source*8+uint32(bit), graphicCell{1, uint16(320 + bit)})
	}
	tracker.copyByte(dest, source)
	if !bytes.Equal(graphicBytes(g.owners[source*8:source*8+8]), graphicBytes(g.owners[dest*8:dest*8+8])) {
		t.Fatal("page copy lost image coordinates")
	}
	before := tracker.revision
	tracker.copyByte(source, source)
	if tracker.revision != before {
		t.Fatal("same-location copy invalidated image")
	}
	tracker.write(oracle.VideoWrite{Offset: source, Value: 0})
	for bit := 0; bit < 8; bit++ {
		if g.owners[source*8+uint32(bit)].ID != 0 || g.owners[dest*8+uint32(bit)].ID != 1 {
			t.Fatal("same-value write failed to invalidate just its destination")
		}
	}
}
func graphicBytes(cells []graphicCell) []byte {
	out := make([]byte, len(cells)*4)
	for i, c := range cells {
		binary.LittleEndian.PutUint16(out[i*4:], c.ID)
		binary.LittleEndian.PutUint16(out[i*4+2:], c.Local)
	}
	return out
}

func realGraphics(t *testing.T) (*GraphicsAssets, []byte, string, string) {
	t.Helper()
	root := os.Getenv("EIGHTSWORD_TEST_ORIG")
	dir := os.Getenv("EIGHTSWORD_TEST_GRAPHICS_ASSETS")
	if root == "" || dir == "" {
		t.Skip("requires real PMAP and prepared generated graphics")
	}
	raw, err := os.ReadFile(filepath.Join(root, "PMAP.AY"))
	if err != nil {
		t.Fatal(err)
	}
	assets, err := loadGraphicsAssets(dir, raw)
	if err != nil {
		t.Fatal(err)
	}
	if assets == nil {
		t.Fatal("missing actual art assets")
	}
	return assets, raw, dir, root
}
func TestActualMaterialSeamsAndPixelContainment(t *testing.T) {
	assets, _, _, _ := realGraphics(t)
	if len(assets.Native) != 68 || len(assets.Materials) != 14 {
		t.Fatal("wrong actual asset shape")
	}
	tile := assets.Materials[1].Tile
	w, h := tile.Bounds().Dx(), tile.Bounds().Dy()
	if w != 192 || h != 150 {
		t.Fatal("wrong physical pixel aspect")
	}
	for y := 0; y < h; y++ {
		at := y * tile.Stride
		if !bytes.Equal(tile.Pix[at:at+4], tile.Pix[at+(w-1)*4:at+w*4]) {
			t.Fatal("horizontal tile seam")
		}
	}
	for x := 0; x < w; x++ {
		at := x * 4
		if !bytes.Equal(tile.Pix[at:at+4], tile.Pix[(h-1)*tile.Stride+at:(h-1)*tile.Stride+at+4]) {
			t.Fatal("vertical tile seam")
		}
	}
	tracker, g := graphicsFixture()
	g.assets = assets
	g.Stats.Bound = true
	g.set(0, graphicCell{1, 0})
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	for i := range out.Pix {
		out.Pix[i] = 31
	}
	g.paint(out, oracle.PlanarDisplay{Width: 640, Height: 200, Pitch: 80, LineCompare: 1023, Palette: canonicalEGA})
	for y := 0; y < 1200; y++ {
		for x := 0; x < 1920; x++ {
			at := y*out.Stride + x*4
			if x < 3 && y < 6 {
				src := y*tile.Stride + x*4
				if !bytes.Equal(out.Pix[at:at+4], tile.Pix[src:src+4]) {
					t.Fatal("material did not use original image-local coordinates")
				}
			} else if !bytes.Equal(out.Pix[at:at+4], []byte{31, 31, 31, 31}) {
				t.Fatal("material painted outside owned native pixel")
			}
		}
	}
	if g.Stats.LastPaintedPixels != 1 || tracker.revision == 0 {
		t.Fatal("missing real material paint")
	}
}

func TestRealShorelineUsesBothHDMaterials(t *testing.T) {
	assets, _, _, _ := realGraphics(t)
	// PMAP 3 is grass across its north edge and water across its south edge.
	shore := assets.Materials[4].Tile
	land, water := assets.Materials[1].Tile, assets.Materials[2].Tile
	for _, p := range []image.Point{{96, 0}, {96, 149}} {
		expected := land
		if p.Y == 149 {
			expected = water
		}
		if shore.RGBAAt(p.X, p.Y) != expected.RGBAAt(p.X, p.Y) {
			t.Fatalf("shoreline lost original north/south topology at %v", p)
		}
	}
	for i := 2; i <= 13; i++ {
		if assets.Materials[uint16(i+1)] == nil {
			t.Fatalf("missing real shoreline %d", i)
		}
	}
	bad := assets.Native[3]
	bad.Pixels = append([]uint8(nil), bad.Pixels...)
	bad.Pixels[0] = 15
	if _, err := shoreMaterial(bad, land, water); err == nil {
		t.Fatal("unrecognized shoreline palette accepted")
	}
}

func TestActualMaterialRejectsInvalidSamplingAndComposite(t *testing.T) {
	_, pmap, dir, _ := realGraphics(t)
	raw, err := os.ReadFile(filepath.Join(dir, "terrain.json"))
	if err != nil {
		t.Fatal(err)
	}
	var original terrainManifest
	if err := json.Unmarshal(raw, &original); err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"crop-overflow", "unknown-sampling", "duplicate-composite", "wrong-dependency"} {
		t.Run(name, func(t *testing.T) {
			temp := t.TempDir()
			for _, file := range original.Materials {
				if err := os.Symlink(filepath.Join(dir, file.File), filepath.Join(temp, file.File)); err != nil {
					t.Fatal(err)
				}
			}
			var m terrainManifest
			if err := json.Unmarshal(raw, &m); err != nil {
				t.Fatal(err)
			}
			switch name {
			case "crop-overflow":
				m.Materials[0].SourceRect = []int{m.Materials[0].Width, 0, 256, 200}
			case "unknown-sampling":
				m.Materials[0].Sampling = "unrecognized"
			case "duplicate-composite":
				m.Composites[1].Index = m.Composites[0].Index
			case "wrong-dependency":
				m.Composites[0].Land = 2
			}
			changed, err := json.Marshal(m)
			if err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(filepath.Join(temp, "terrain.json"), changed, 0600); err != nil {
				t.Fatal(err)
			}
			if a, err := loadGraphicsAssets(temp, pmap); err == nil || a != nil {
				t.Fatal("invalid group was accepted")
			}
		})
	}
}
func TestGraphicsCorruptionKeepsNotoAndRejectsWholeGroup(t *testing.T) {
	_, pmap, dir, root := realGraphics(t)
	temp := t.TempDir()
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		name := entry.Name()
		data, err := os.ReadFile(filepath.Join(dir, name))
		if err != nil {
			t.Fatal(err)
		}
		if name == "grass-painted-r1.png" {
			data = append(data, 1)
		}
		if err = os.WriteFile(filepath.Join(temp, name), data, 0600); err != nil {
			t.Fatal(err)
		}
	}
	if a, err := loadGraphicsAssets(temp, pmap); err == nil || a != nil {
		t.Fatal("corrupted group accepted")
	}
	engine, err := Open(Options{Root: root, Assets: temp, Saves: filepath.Join(t.TempDir(), "save"), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer engine.Close()
	if !engine.HD || engine.AssetError != "" || engine.GraphicsError == "" || engine.Tracker == nil || engine.Tracker.graphics != nil {
		t.Fatal("art failure disabled Noto or leaked partial group")
	}
}
