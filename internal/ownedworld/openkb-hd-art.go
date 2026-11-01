// Presentation-only, string-ID artwork for the isolated owned-army client.
package ownedworld

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"image"
	"image/draw"
	"image/png"
	"os"
	"path/filepath"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

type unitArtRow struct {
	ID   string `json:"id"`
	File string `json:"file"`
	SHA  string `json:"sha256"`
}
type unitArtPack struct {
	Schema  int          `json:"schema"`
	Catalog string       `json:"catalog_raw_sha256"`
	Rows    []unitArtRow `json:"rows"`
}
type unitArtStamp struct {
	ID          string `json:"id"`
	Area        [4]int `json:"area"`
	Destination [4]int `json:"destination"`
	Source      [2]int `json:"source"`
	SHA         string `json:"rgba_sha256"`
	Mirror      bool   `json:"mirror"`
}
type hdUnitArtwork struct {
	Images   map[string]*image.RGBA
	Failures map[string]string
	Stamps   []unitArtStamp
	View     string
}

func artBox(r image.Rectangle) [4]int { return [4]int{r.Min.X, r.Min.Y, r.Max.X, r.Max.Y} }

var hdUnitArt *hdUnitArtwork
var openKBArtIDs = []string{"openkb:arcr", "openkb:pike", "openkb:wolf", "openkb:skel", "openkb:troll", "openkb:drui", "openkb:vamp", "openkb:drag"}

func loadHDUnitArtwork(e *game.Engine, dir, catalog string) *hdUnitArtwork {
	v := &hdUnitArtwork{Images: map[string]*image.RGBA{}, Failures: map[string]string{}}
	if e != nil && e.HD {
		for k := uint16(1); k <= 25; k++ {
			if im := e.RecruitmentUnitIcon(k); im != nil {
				v.Images[fmt.Sprintf("native:%02d", k)] = im
			}
		}
	}
	raw, err := os.ReadFile(filepath.Join(dir, "unit-art.json"))
	if err != nil || len(raw) > 32768 {
		v.Failures["pack"] = "missing/size"
		return v
	}
	var pack unitArtPack
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if d.Decode(&pack) != nil || pack.Schema != 1 || pack.Catalog != catalog || len(pack.Rows) != 8 {
		v.Failures["pack"] = "schema/catalog/shape"
		return v
	}
	allowed := map[string]bool{}
	for _, id := range openKBArtIDs {
		allowed[id] = true
	}
	seen := map[string]bool{}
	for _, r := range pack.Rows {
		if !allowed[r.ID] || seen[r.ID] || filepath.Base(r.File) != r.File || r.File == "." || r.File == ".." {
			v.Failures["pack"] = "identity/path"
			return v
		}
		seen[r.ID] = true
	}
	// Publish only complete immutable images. A rejected unit keeps its text card.
	for _, r := range pack.Rows {
		raw, err := os.ReadFile(filepath.Join(dir, r.File))
		if err != nil || len(raw) > 4<<20 || fmt.Sprintf("%x", sha256.Sum256(raw)) != r.SHA {
			v.Failures[r.ID] = "missing/SHA"
			continue
		}
		cfg, err := png.DecodeConfig(bytes.NewReader(raw))
		if err != nil || cfg.Width != 512 || cfg.Height != 512 {
			v.Failures[r.ID] = "shape"
			continue
		}
		im, err := png.Decode(bytes.NewReader(raw))
		if err != nil {
			v.Failures[r.ID] = "PNG"
			continue
		}
		rgba := image.NewRGBA(image.Rect(0, 0, 512, 512))
		draw.Draw(rgba, rgba.Bounds(), im, im.Bounds().Min, draw.Src)
		v.Images[r.ID] = rgba
	}
	return v
}
func resetHDUnitArtwork(view string) {
	if hdUnitArt != nil {
		hdUnitArt.View = view
		hdUnitArt.Stamps = nil
	}
}
func drawHDUnitArtwork(out *image.RGBA, id string, area image.Rectangle, mirror bool) bool {
	if hdUnitArt == nil || !area.In(out.Bounds()) || area.Empty() {
		return false
	}
	im := hdUnitArt.Images[id]
	if im == nil {
		return false
	}
	box := image.Rectangle{}
	for y := im.Rect.Min.Y; y < im.Rect.Max.Y; y++ {
		for x := im.Rect.Min.X; x < im.Rect.Max.X; x++ {
			if im.RGBAAt(x, y).A != 0 {
				box = box.Union(image.Rect(x, y, x+1, y+1))
			}
		}
	}
	if box.Empty() {
		return false
	}
	w, h := area.Dx(), area.Dy()
	if w*box.Dy() > h*box.Dx() {
		w = h * box.Dx() / box.Dy()
	} else {
		h = w * box.Dy() / box.Dx()
	}
	if w < 1 || h < 1 {
		return false
	}
	dest := image.Rect(area.Min.X+(area.Dx()-w)/2, area.Min.Y+(area.Dy()-h)/2, area.Min.X+(area.Dx()-w)/2+w, area.Min.Y+(area.Dy()-h)/2+h)
	for y := 0; y < h; y++ {
		sy := box.Min.Y + y*box.Dy()/h
		for x := 0; x < w; x++ {
			sx := box.Min.X + x*box.Dx()/w
			if mirror {
				sx = box.Max.X - 1 - x*box.Dx()/w
			}
			c := im.RGBAAt(sx, sy)
			at := out.PixOffset(dest.Min.X+x, dest.Min.Y+y)
			a := uint32(c.A)
			for k, s := range []uint8{c.R, c.G, c.B} {
				out.Pix[at+k] = uint8(uint32(s) + (uint32(out.Pix[at+k])*(255-a)+127)/255)
			}
			out.Pix[at+3] = 255
		}
	}
	hdUnitArt.Stamps = append(hdUnitArt.Stamps, unitArtStamp{id, artBox(area), artBox(dest), [2]int{im.Rect.Dx(), im.Rect.Dy()}, fmt.Sprintf("%x", sha256.Sum256(im.Pix)), mirror})
	return true
}
func hdUnitArtworkStatus() map[string]any {
	if hdUnitArt == nil {
		return map[string]any{"loaded": 0}
	}
	return map[string]any{"loaded": len(hdUnitArt.Images), "failures": hdUnitArt.Failures, "view": hdUnitArt.View, "stamps": hdUnitArt.Stamps}
}
