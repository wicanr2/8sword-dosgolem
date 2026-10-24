package eightsword

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

func TestPresentationPaletteRealManifestAndAtomicFallback(t *testing.T) {
	dir := os.Getenv("EIGHTSWORD_TEST_PALETTE_ASSETS")
	if dir == "" {
		t.Skip("本機配色素材未提供")
	}
	a, _, _, _ := realGraphics(t)
	g := &Graphics{assets: a}
	raw, err := os.ReadFile(filepath.Join(dir, "presentation-palette.json"))
	if err != nil {
		t.Fatal(err)
	}
	profile, err := loadPresentationPalette(dir, g)
	if err != nil || profile == nil {
		t.Fatalf("real palette rejected: %v", err)
	}
	original := a.Materials[72]
	if p, err := loadPresentationPalette(t.TempDir(), nil); err != nil || p != nil {
		t.Fatal("old asset groups must keep their original colors")
	}
	var valid map[string]any
	if err := json.Unmarshal(raw, &valid); err != nil {
		t.Fatal(err)
	}
	for _, key := range []string{"schema", "source_sha256", "style", "style_reference_sha256", "approved_sample_sha256", "unknown"} {
		bad := make(map[string]any)
		for k, v := range valid {
			bad[k] = v
		}
		bad[key] = "invalid"
		data, _ := json.Marshal(bad)
		path := t.TempDir()
		if err := os.WriteFile(filepath.Join(path, "presentation-palette.json"), data, 0600); err != nil {
			t.Fatal(err)
		}
		if p, err := loadPresentationPalette(path, g); err == nil || p != nil {
			t.Fatalf("invalid %s accepted", key)
		}
	}
	for _, data := range [][]byte{append(append([]byte(nil), raw...), []byte("{}")...), make([]byte, 4097), []byte("{")} {
		path := t.TempDir()
		if err := os.WriteFile(filepath.Join(path, "presentation-palette.json"), data, 0600); err != nil {
			t.Fatal(err)
		}
		if p, err := loadPresentationPalette(path, g); err == nil || p != nil {
			t.Fatal("corrupted palette accepted")
		}
	}
	link := t.TempDir()
	if err := os.Symlink(filepath.Join(dir, "presentation-palette.json"), filepath.Join(link, "presentation-palette.json")); err != nil {
		t.Fatal(err)
	}
	if p, err := loadPresentationPalette(link, g); err == nil || p != nil {
		t.Fatal("symbolic palette accepted")
	}
	if p, err := loadPresentationPalette(dir, nil); err == nil || p != nil {
		t.Fatal("palette without verified UI accepted")
	}
	if a.Materials[72] != original {
		t.Fatal("palette loader changed an existing UI material")
	}
}

func paletteTrackerFixture() (*Tracker, oracle.PlanarDisplay) {
	p := oracle.PlanarDisplay{Width: 640, Height: 200, Pitch: 80, LineCompare: 1023, Palette: canonicalEGA}
	tr := &Tracker{owners: make([]cell, 65536*8), glyphs: map[uint32]*glyph{}, loadSegment: 0x110, palette: &presentationPalette{}}
	tr.graphics = newGraphics(tr, &GraphicsAssets{})
	tr.graphics.Stats.Bound = true
	for row := 0; row < 7; row++ {
		id := uint32(row + 1)
		tr.glyphs[id] = &glyph{ID: id, Rune: '檢', Width: 16, Source: uint16(990 + row*20), BG: 12, Refs: 1}
		tr.owners[((12+row*27)*80+488/8)*8] = cell{ID: id}
	}
	return tr, p
}

func TestPresentationPaletteCurrentPageAndSourceGuards(t *testing.T) {
	tr, p := paletteTrackerFixture()
	if !tr.paletteEnabled(p) || !tr.paletteSidebarVisible(p) {
		t.Fatal("verified current sidebar rejected")
	}
	tr.glyphs[4].Source++
	if tr.paletteSidebarVisible(p) {
		t.Fatal("historical sidebar source accepted")
	}
	tr.glyphs[4].Source--
	tr.glyphs[4].Rune = ' '
	if tr.paletteSidebarVisible(p) {
		t.Fatal("blank glyph treated as visible menu")
	}
	tr.glyphs[4].Rune = '檢'
	for row := 0; row < 7; row++ {
		source := uint32((12+row*27)*80 + 488/8)
		tr.copyByte(source+0x4000, source)
	}
	p.Start = 0x4000
	if !tr.paletteSidebarVisible(p) {
		t.Fatal("page copy lost sidebar source")
	}
	p.Start = 0x8000
	if tr.paletteSidebarVisible(p) {
		t.Fatal("offscreen menu enabled current-page colors")
	}
	p.Start = 0
	base := p
	p.Palette[10][0] ^= 1
	if tr.paletteEnabled(p) {
		t.Fatal("nonstandard palette was recolored")
	}
	p = base
	p.Pitch = 40
	if tr.paletteEnabled(p) {
		t.Fatal("unverified display geometry was recolored")
	}
	tr.palette = nil
	if tr.paletteEnabled(base) {
		t.Fatal("old assets enabled new palette")
	}
}

func TestPresentationPaletteSelectionIsNotRedArtwork(t *testing.T) {
	profile := &presentationPalette{}
	g := &glyph{ID: 1, Source: 990, BG: 12, Width: 16}
	c := cell{ID: 1}
	if rgb, ok := profile.backdrop(12, 488, 12, c, g, true); !ok || rgb != [3]uint8{128, 45, 39} {
		t.Fatal("selected text background did not use cinnabar")
	}
	if _, ok := profile.backdrop(12, 488, 12, cell{}, nil, true); ok {
		t.Fatal("red artwork was recolored")
	}
	if _, ok := profile.backdrop(12, 488, 12, c, g, false); ok {
		t.Fatal("battlefield was treated as sidebar")
	}
	g.BG = 255
	if _, ok := profile.backdrop(12, 488, 12, c, g, true); ok {
		t.Fatal("transparent glyph claimed a red background")
	}
	g.BG = 12
	for _, pos := range [][2]int{{471, 12}, {624, 12}, {488, 27}, {488, 39}} {
		if _, ok := profile.backdrop(12, pos[0], pos[1], c, g, true); ok {
			t.Fatalf("unverified source position accepted: %v", pos)
		}
	}
	if rgb, ok := profile.backdrop(10, 16, 193, cell{}, nil, true); !ok || rgb != [3]uint8{110, 167, 92} {
		t.Fatal("indicator refinement missing")
	}
	if _, ok := profile.backdrop(10, 16, 193, cell{}, nil, false); ok {
		t.Fatal("battlefield green was recolored")
	}
}
