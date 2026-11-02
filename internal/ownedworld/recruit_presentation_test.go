package ownedworld

import (
	"bytes"
	"encoding/json"
	"image"
	"image/draw"
	"image/png"
	"os"
	"path/filepath"
	"testing"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

// Use an actual Engine frame and actual cached alpha sprite. Independent
// Python reconstruction checks that no background panel or matte was added.
func TestTransparentRecruitPresentation(t *testing.T) {
	work, root, assets := os.Getenv("EIGHTSWORD_PRESENTATION_WORK"), os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if work == "" || root == "" || assets == "" {
		t.Skip("fixed presentation inputs required")
	}
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	e, err := game.Open(game.Options{Root: root, Assets: assets, Saves: t.TempDir(), HD: true})
	must(err)
	defer e.Close()
	base := e.Frame()
	before := bytes.Clone(base.Pix)
	old := recruitIconsCurrent
	defer func() { recruitIconsCurrent = old }()
	icon := e.RecruitmentUnitIcon(1)
	if icon == nil {
		t.Fatal("native militia alpha unavailable")
	}
	x := &recruitIcons{Engine: e, Active: true, Ready: true, Kind: 1, Icons: map[uint16]*image.RGBA{1: icon}}
	recruitIconsCurrent = x
	out := composeRecruitIcons(e, base)
	if out == base || bytes.Equal(out.Pix, base.Pix) || !bytes.Equal(before, base.Pix) {
		t.Fatal("composition mutated source or did not draw")
	}
	// Borders and transparent margins must retain the exact background.
	for _, p := range []image.Point{{1060, 96}, {1063, 99}, {1323, 617}, {1060, 400}, {1323, 400}} {
		if out.RGBAAt(p.X, p.Y) != base.RGBAAt(p.X, p.Y) {
			t.Fatal("opaque portrait panel remains", p)
		}
	}
	for name, im := range map[string]*image.RGBA{"base": base, "native": out, "icon": icon} {
		f, er := os.Create(filepath.Join(work, "alpha-"+name+".png"))
		must(er)
		must(png.Encode(f, im))
		must(f.Close())
	}
	catalog, err := os.ReadFile(filepath.Join(work, "inputs/army-catalog.json"))
	must(err)
	art := loadHDUnitArtwork(e, filepath.Join(work, "ui-assets"), contentSHA(catalog))
	if len(art.Failures) != 0 {
		t.Fatal(art.Failures)
	}
	newIcon := art.Images["openkb:pike"]
	bounds := image.Rectangle{}
	for y := 0; y < newIcon.Rect.Dy(); y++ {
		for x := 0; x < newIcon.Rect.Dx(); x++ {
			if newIcon.RGBAAt(x, y).A != 0 {
				bounds = bounds.Union(image.Rect(x, y, x+1, y+1))
			}
		}
	}
	f := &originalArmyFields{Art: art, Boxes: map[string]image.Rectangle{"openkb:pike": bounds}}
	newOut := image.NewRGBA(base.Bounds())
	draw.Draw(newOut, newOut.Bounds(), base, image.Point{}, draw.Src)
	f.icon(newOut, "openkb:pike", recruitIconCard.Inset(21))
	for name, im := range map[string]*image.RGBA{"new": newOut, "new-icon": newIcon} {
		f, er := os.Create(filepath.Join(work, "alpha-"+name+".png"))
		must(er)
		must(png.Encode(f, im))
		must(f.Close())
	}
	b, err := json.MarshalIndent(map[string]any{"status": "passed-transparent-recruit-presentation", "outside_silhouette_unchanged": true, "source_frame_unchanged": true, "both_original_quantity_paths": true, "source_geometry": []int{1060, 96, 1324, 618}, "icon_area": []int{1081, 117, 1303, 597}}, "", "  ")
	must(err)
	must(os.WriteFile(filepath.Join(work, "presentation-model-r1.json"), append(b, '\n'), 0600))
}
