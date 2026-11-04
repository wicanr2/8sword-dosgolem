package eightsword

import (
	"fmt"
	"image"
	"testing"
)

// The optional package must commit atomically, keep caller-owned pixels
// immutable and release its per-engine registry on close.
func TestOwnedBattleArtPackage(t *testing.T) {
	e := &Engine{HD: true, sourceEnabled: true}
	p := &sourceAdapter{e: e, bound: true, sourceOnlyArt: GraphicsAssets{Actors: map[uint16]*graphicMaterial{}, Materials: map[uint16]*graphicMaterial{}}}
	tiles := map[string]*image.RGBA{}
	for i := 0; i < 8; i++ {
		im := image.NewRGBA(image.Rect(0, 0, 264, 300))
		im.Pix[3] = 255
		tiles[fmt.Sprint(i)] = im
	}
	resolve := func(OwnedBattleArtRequest) (OwnedBattleArtSelection, error) { return OwnedBattleArtSelection{}, nil }
	if e.SetOwnedBattleArt(tiles, resolve) == nil {
		t.Fatal("formal backend accepted optional art")
	}
	p.bindOwnedBattleArt()
	defer p.closeOwnedBattleArt()
	bad := tiles["7"]
	tiles["7"] = image.NewRGBA(image.Rect(0, 0, 2, 2))
	if e.SetOwnedBattleArt(tiles, resolve) == nil || len(p.sourceOnlyArt.Actors) != 0 {
		t.Fatal("partial package committed")
	}
	tiles["7"] = bad
	bad.Pix = bad.Pix[:1]
	if e.SetOwnedBattleArt(tiles, resolve) == nil || len(p.sourceOnlyArt.Actors) != 0 {
		t.Fatal("bad storage accepted")
	}
	bad.Pix = make([]byte, 264*300*4)
	bad.Pix[3] = 255
	bad.Pix[0] = 255
	bad.Pix[3] = 1
	if e.SetOwnedBattleArt(tiles, resolve) == nil || len(p.sourceOnlyArt.Actors) != 0 {
		t.Fatal("straight alpha accepted")
	}
	bad.Pix[0] = 0
	bad.Pix[3] = 255
	if err := e.SetOwnedBattleArt(tiles, resolve); err != nil {
		t.Fatal(err)
	}
	tiles["0"].Pix[3] = 0
	if len(p.sourceOnlyArt.Actors) != 8 || p.sourceOnlyArt.Actors[60000].Tile.Pix[3] != 255 {
		t.Fatal("package retained mutable input")
	}
	if e.SetOwnedBattleArt(tiles, resolve) == nil {
		t.Fatal("duplicate install")
	}
	p.scene = &ownedScene{Pixels: []ownedPixel{{Color: 5, Material: graphicCell{ID: 1}, Actor: graphicCell{ID: 60000}, Effect: graphicCell{ID: 2}, Text: cell{ID: 3}}, {Actor: graphicCell{ID: 17}}, {Actor: graphicCell{ID: 60000}}}}
	state, _ := ownedBattleArtEngines.Load(e)
	s := state.(*ownedBattleArtState)
	before := p.scene.Pixels[0]
	for _, selection := range []OwnedBattleArtSelection{{Retire: []string{"missing"}}, {Retire: []string{"0", "0"}}, {Unit: "0", Retire: []string{"0"}}} {
		if p.retireOwnedBattleArt(s, selection) == nil || p.scene.Revision != 0 {
			t.Fatal("invalid retirement committed")
		}
	}
	if err := p.retireOwnedBattleArt(s, OwnedBattleArtSelection{Retire: []string{"0"}}); err != nil {
		t.Fatal(err)
	}
	before.Actor = graphicCell{}
	if p.scene.Pixels[0] != before || p.scene.Pixels[1].Actor.ID != 17 || p.scene.Pixels[2].Actor.ID != 0 || s.retiredPixels != 2 || s.retirements != 1 {
		t.Fatal("retirement changed another layer")
	}
	revision := p.scene.Revision
	if err := p.retireOwnedBattleArt(s, OwnedBattleArtSelection{Retire: []string{"0"}}); err != nil || p.scene.Revision != revision {
		t.Fatal("retirement was not idempotent")
	}
	p.closeOwnedBattleArt()
	if e.OwnedBattleArtAvailable() {
		t.Fatal("closed adapter retained")
	}
	e.HD = false
	p.bindOwnedBattleArt()
	if e.SetOwnedBattleArt(tiles, resolve) == nil {
		t.Fatal("original mode accepted HD art")
	}
}
