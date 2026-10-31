//go:build ignore

package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"os"
	"path/filepath"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

func hdArtMust(e error) {
	if e != nil {
		panic(e)
	}
}
func hdArtWrite(p string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	hdArtMust(e)
	f, e := os.OpenFile(p, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	hdArtMust(e)
	_, e = f.Write(append(b, '\n'))
	hdArtMust(e)
	hdArtMust(f.Close())
}
func main() {
	input := flag.String("input", "", "fixed input")
	out := flag.String("out", "", "new output")
	pack := flag.String("pack", "", "UI artwork")
	mode := flag.String("mode", "probe", "probe/init")
	scenario := flag.String("scenario", "a", "a or b")
	session := flag.String("session", "", "new paired progress")
	flag.Parse()
	if os.Getuid() != 1000 {
		panic("UID1000")
	}
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	var w OwnedWorld
	for _, v := range []struct {
		name string
		dst  any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}, {"showcase-" + *scenario + ".json", &w}} {
		b, e := os.ReadFile(filepath.Join(*input, v.name))
		hdArtMust(e)
		hdArtMust(pairStrictJSON(b, v.dst))
	}
	base, e := os.ReadFile(filepath.Join(*input, "original-save.ay"))
	hdArtMust(e)
	if *mode == "init" {
		hdArtMust(initializeProgressPair(*session, base, c, cc, w))
		return
	}
	hdArtMust(os.Mkdir(*out, 0700))
	raw, e := os.ReadFile(filepath.Join(*input, "army-catalog.json"))
	hdArtMust(e)
	hdUnitArt = loadHDUnitArtwork(nil, *pack, contentSHA(raw))
	if len(hdUnitArt.Images) != 8 || len(hdUnitArt.Failures) != 0 {
		panic(hdUnitArt.Failures)
	}
	rows := []map[string]any{}
	canvas := image.NewRGBA(image.Rect(0, 0, 1280, 960))
	draw.Draw(canvas, canvas.Bounds(), image.NewUniform(color.RGBA{20, 56, 41, 255}), image.Point{}, draw.Src)
	for i, id := range openKBArtIDs {
		im := hdUnitArt.Images[id]
		before := append([]byte{}, im.Pix...)
		hdArtMust(os.WriteFile(filepath.Join(*out, fmt.Sprintf("unit%d.rgba", i)), im.Pix, 0600))
		area := image.Rect(i%4*320+16, i/4*480+16, i%4*320+304, i/4*480+464)
		if !drawHDUnitArtwork(canvas, id, area, i%2 == 1) {
			panic("known artwork missing")
		}
		if !bytes.Equal(before, im.Pix) {
			panic("cache mutated")
		}
		rows = append(rows, map[string]any{"id": id, "raw": fmt.Sprintf("unit%d.rgba", i), "sha256": contentSHA(im.Pix)})
	}
	if drawHDUnitArtwork(canvas, "openkb:missing", image.Rect(0, 0, 100, 100), false) || drawHDUnitArtwork(canvas, "native:01", image.Rect(0, 0, 100, 100), false) || drawHDUnitArtwork(canvas, "openkb:wolf", image.Rect(-1, 0, 100, 100), false) {
		panic("unsafe artwork draw")
	}
	f, e := os.Create(filepath.Join(*out, "drawn.png"))
	hdArtMust(e)
	hdArtMust(png.Encode(f, canvas))
	hdArtMust(f.Close())
	empty := loadHDUnitArtwork(nil, filepath.Join(*out, "missing"), contentSHA(raw))
	if len(empty.Images) != 0 || empty.Failures["pack"] == "" {
		panic("missing pack fallback")
	}
	wrong := loadHDUnitArtwork(nil, *pack, "wrong")
	if len(wrong.Images) != 0 || wrong.Failures["pack"] == "" {
		panic("catalog fallback")
	}
	// No game state is mutated by any artwork load or draw.
	hdArtWrite(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-eight-openkb-art-cache", "rows": rows, "stamps": hdUnitArt.Stamps, "canvas_rgba_sha256": contentSHA(canvas.Pix), "immutable": true, "unknown_and_missing_fallback": true, "catalog_mismatch_fallback": true, "world_digest": worldDigest(w)})
}
