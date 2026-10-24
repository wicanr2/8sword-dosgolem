package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"io"
	"math"
	"os"
	"path/filepath"
	"time"
)

const PosterWidth, PosterHeight = 2944, 1264
const posterFade = 400 * time.Millisecond

var PosterGameRect = image.Rect(512, 64, 2432, 1264)
var posterMatte = color.RGBA{8, 36, 23, 255}

type toolbarManifest struct {
	Schema    int    `json:"schema"`
	AtlasSHA  string `json:"atlas_sha256"`
	SourceSHA string `json:"source_sha256"`
	Glyphs    []struct {
		Character string `json:"character"`
		Ink       [4]int `json:"ink"`
	} `json:"glyphs"`
}

// PosterToolbar owns host presentation only. It has no guest or clock reference.
type PosterToolbar struct {
	Error                        string
	ID                           string
	Menu                         string
	Selected                     int
	panels                       map[string]*image.RGBA
	atlas                        image.Image
	glyphs                       map[rune][4]int
	from, target                 *image.RGBA
	started                      time.Time
	font                         string
	choices                      []FontChoice
	frame, lastGame              *image.RGBA
	dirty                        bool
	CachedPixels, RenderedFrames uint64
}

func posterID(id string) bool { return id == "wings" || id == "cover" || id == "off" }

func readPosterJSON(path string, out any) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()
	s, err := f.Stat()
	if err != nil {
		return err
	}
	if !s.Mode().IsRegular() || s.Size() > 32768 {
		return fmt.Errorf("海報清單形狀不符")
	}
	d := json.NewDecoder(io.LimitReader(f, 32769))
	d.DisallowUnknownFields()
	if err = d.Decode(out); err != nil {
		return err
	}
	var extra any
	if d.Decode(&extra) != io.EOF {
		return fmt.Errorf("海報清單有額外資料")
	}
	return nil
}

func readPosterImage(dir, file, sha string, w, h int) (image.Image, error) {
	p := filepath.Join(dir, file)
	s, err := os.Lstat(p)
	if err != nil {
		return nil, err
	}
	if !s.Mode().IsRegular() || s.Size() > 12<<20 {
		return nil, fmt.Errorf("海報圖片形狀不符")
	}
	b, err := os.ReadFile(p)
	if err != nil {
		return nil, err
	}
	if hash(b) != sha {
		return nil, fmt.Errorf("%s SHA-256 不符", file)
	}
	c, _, err := image.DecodeConfig(bytes.NewReader(b))
	if err != nil || c.Width != w || c.Height != h {
		return nil, fmt.Errorf("%s 尺寸不符", file)
	}
	im, _, err := image.Decode(bytes.NewReader(b))
	return im, err
}

func LoadPosterToolbar(dir string, choices []FontChoice) (*PosterToolbar, error) {
	var m toolbarManifest
	if err := readPosterJSON(filepath.Join(dir, "poster-toolbar.json"), &m); err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}
	if m.Schema != 1 || m.SourceSHA != "3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151" || m.AtlasSHA != "34009f2ab958e1cf34436b8d10950cc173e834c8c18631e123b1b26601d32657" || len(m.Glyphs) != 123 {
		return nil, fmt.Errorf("工具列字集來源不符")
	}
	if len(choices) == 0 || len(choices) > 3 {
		return nil, fmt.Errorf("工具列字型選項缺失")
	}
	atlas, err := readPosterImage(dir, "poster-toolbar-font.png", m.AtlasSHA, 1024, 512)
	if err != nil {
		return nil, err
	}
	v := &PosterToolbar{ID: "wings", atlas: atlas, glyphs: map[rune][4]int{}, panels: map[string]*image.RGBA{}, choices: append([]FontChoice(nil), choices...), dirty: true}
	for _, g := range m.Glyphs {
		r := []rune(g.Character)
		box := image.Rect(g.Ink[0], g.Ink[1], g.Ink[0]+g.Ink[2], g.Ink[1]+g.Ink[3])
		if len(r) != 1 || g.Ink[2] < 0 || g.Ink[3] < 0 || !box.In(atlas.Bounds()) {
			return nil, fmt.Errorf("工具列字墨越界")
		}
		if _, ok := v.glyphs[r[0]]; ok {
			return nil, fmt.Errorf("工具列字元重複")
		}
		v.glyphs[r[0]] = g.Ink
	}
	for _, r := range "神州八劍字型海報Noto Black 900隸書風草書龍虎延展經典封面關閉" {
		if _, ok := v.glyphs[r]; !ok {
			return nil, fmt.Errorf("工具列缺字 %U", r)
		}
	}
	v.panels["off"] = image.NewRGBA(image.Rect(0, 0, 1024, 1200))
	draw.Draw(v.panels["off"], v.panels["off"].Bounds(), image.NewUniform(posterMatte), image.Point{}, draw.Src)
	for _, a := range []struct {
		id, file, sha string
		w, h          int
		roi           [2]image.Rectangle
	}{
		{"wings", "poster-wings.png", "f14552801e98d4171befeb1220a9626c9e2e7a25efdad011896d2d3abfcba341", 2172, 724, [2]image.Rectangle{image.Rect(160, 0, 469, 724), image.Rect(1640, 0, 1949, 724)}},
		{"cover", "poster-cover.png", "2d666efbb2b1fc714e92b82f078c3fd4139b7c690fce794b95c99c8b2725c55d", 1122, 1402, [2]image.Rectangle{image.Rect(0, 0, 600, 1402), image.Rect(522, 0, 1122, 1402)}},
	} {
		im, err := readPosterImage(dir, a.file, a.sha, a.w, a.h)
		if err != nil {
			v.Error += err.Error() + "; "
			continue
		}
		v.panels[a.id] = makePosterPanels(im, a.roi)
	}
	if v.Error != "" {
		delete(v.panels, "wings")
		delete(v.panels, "cover")
		v.ID = "off"
	}
	v.target = v.panels[v.ID]
	return v, nil
}

func makePosterPanels(im image.Image, rois [2]image.Rectangle) *image.RGBA {
	p := image.NewRGBA(image.Rect(0, 0, 1024, 1200))
	for side, r := range rois {
		for y := 0; y < 1200; y++ {
			for x := 0; x < 512; x++ {
				fx := float64(r.Min.X) + (float64(x)+.5)*float64(r.Dx())/512 - .5
				fy := float64(r.Min.Y) + (float64(y)+.5)*float64(r.Dy())/1200 - .5
				fx = math.Max(0, math.Min(float64(im.Bounds().Max.X-1), fx))
				fy = math.Max(0, math.Min(float64(im.Bounds().Max.Y-1), fy))
				x0, y0 := int(fx), int(fy)
				x1, y1 := min(x0+1, im.Bounds().Max.X-1), min(y0+1, im.Bounds().Max.Y-1)
				u, w := fx-float64(x0), fy-float64(y0)
				a := color.RGBAModel.Convert(im.At(x0, y0)).(color.RGBA)
				b := color.RGBAModel.Convert(im.At(x1, y0)).(color.RGBA)
				c := color.RGBAModel.Convert(im.At(x0, y1)).(color.RGBA)
				d := color.RGBAModel.Convert(im.At(x1, y1)).(color.RGBA)
				f := math.Min(1, math.Max(0, float64(512-x)/112))
				if side == 1 {
					f = math.Min(1, float64(x)/112)
				}
				f = f * f * (3 - 2*f)
				channel := func(i, j, k, l, base uint8) uint8 {
					sample := math.Round(float64(i)*(1-u)*(1-w) + float64(j)*u*(1-w) + float64(k)*(1-u)*w + float64(l)*u*w)
					return uint8(math.Round(sample*f + float64(base)*(1-f)))
				}
				p.SetRGBA(side*512+x, y, color.RGBA{channel(a.R, b.R, c.R, d.R, posterMatte.R), channel(a.G, b.G, c.G, d.G, posterMatte.G), channel(a.B, b.B, c.B, d.B, posterMatte.B), 255})
			}
		}
	}
	return p
}

func (v *PosterToolbar) panel(now time.Time) *image.RGBA {
	if v.from == nil {
		return v.target
	}
	n := now.Sub(v.started)
	if n >= posterFade {
		v.from = nil
		return v.target
	}
	q := max(0, min(256, int(n*256/posterFade)))
	out := image.NewRGBA(v.target.Bounds())
	for i := range out.Pix {
		out.Pix[i] = uint8((int(v.from.Pix[i])*(256-q) + int(v.target.Pix[i])*q + 128) / 256)
	}
	return out
}

func (v *PosterToolbar) SetPoster(id string, now time.Time) error {
	if !posterID(id) || v.panels[id] == nil {
		return fmt.Errorf("海報選項不可用：%s", id)
	}
	if id == v.ID {
		return nil
	}
	v.from = v.panel(now)
	v.target = v.panels[id]
	v.ID = id
	v.started = now
	v.dirty = true
	return nil
}

func (v *PosterToolbar) SyncFont(id string) {
	if v.font != id {
		v.font = id
		v.dirty = true
	}
}
func (v *PosterToolbar) CloseMenu() {
	if v.Menu != "" {
		v.Menu = ""
		v.dirty = true
	}
}

type ToolbarAction struct {
	Font, Poster string
	Consumed     bool
}

// Input receives only edges, so held menu keys cannot become guest key-downs.
func (v *PosterToolbar) Input(x, y int, click bool, key string) ToolbarAction {
	a := ToolbarAction{Consumed: v.Menu != ""}
	old := v.Menu
	if click {
		if y >= 8 && y < 56 && x >= 596 && x < 1012 {
			v.Menu = "font"
		} else if y >= 8 && y < 56 && x >= 1194 && x < 1536 {
			v.Menu = "poster"
		} else if v.Menu != "" {
			x0, x1 := 596, 1012
			if v.Menu == "poster" {
				x0, x1 = 1194, 1536
			}
			n := v.menuLen()
			if x >= x0 && x < x1 && y >= 64 && y < 64+n*56 {
				v.Selected = (y - 64) / 56
				key = "enter"
			} else {
				v.CloseMenu()
			}
		}
		if y < 64 || old != "" {
			a.Consumed = true
		}
		if old != v.Menu && v.Menu != "" {
			v.Selected = 0
			v.dirty = true
		}
	}
	if v.Menu != "" {
		a.Consumed = true
		n := v.menuLen()
		switch key {
		case "up":
			v.Selected = (v.Selected + n - 1) % n
			v.dirty = true
		case "down":
			v.Selected = (v.Selected + 1) % n
			v.dirty = true
		case "escape":
			v.CloseMenu()
		case "enter":
			if v.Menu == "font" {
				a.Font = v.choices[v.Selected].ID
			} else {
				a.Poster = []string{"wings", "cover", "off"}[v.Selected]
			}
			v.CloseMenu()
		}
	}
	return a
}
func (v *PosterToolbar) menuLen() int {
	if v.Menu == "font" {
		return len(v.choices)
	}
	return 3
}
func (v *PosterToolbar) fontLabel(id string) string {
	if id == "lishu" {
		for _, c := range v.choices {
			if c.ID == id && c.Label == "教育部隸書" {
				return "教育部隸書"
			}
		}
		return "隸書風"
	}
	if id == "caoshu" {
		return "草書"
	}
	return "Noto Black 900"
}
func posterLabel(id string) string {
	switch id {
	case "cover":
		return "經典封面"
	case "off":
		return "關閉"
	}
	return "龍虎延展"
}

func (v *PosterToolbar) Frame(game *image.RGBA, now time.Time) *image.RGBA {
	if v.frame != nil && !v.dirty && v.from == nil {
		if v.lastGame == game {
			return v.frame
		}
		if v.lastGame != nil && v.lastGame.Bounds() == game.Bounds() && v.lastGame.Stride == game.Stride && bytes.Equal(v.lastGame.Pix, game.Pix) {
			v.CachedPixels++
			v.lastGame = game
			return v.frame
		}
	}
	out := image.NewRGBA(image.Rect(0, 0, PosterWidth, PosterHeight))
	draw.Draw(out, out.Bounds(), image.NewUniform(posterMatte), image.Point{}, draw.Src)
	p := v.panel(now)
	draw.Draw(out, image.Rect(0, 64, 512, 1264), p, image.Point{}, draw.Src)
	draw.Draw(out, image.Rect(2432, 64, 2944, 1264), p, image.Pt(512, 0), draw.Src)
	draw.Draw(out, PosterGameRect, game, game.Bounds().Min, draw.Src)
	fill := func(r image.Rectangle, c color.RGBA) { draw.Draw(out, r, image.NewUniform(c), image.Point{}, draw.Src) }
	gold := color.RGBA{216, 174, 78, 255}
	fill(image.Rect(0, 0, 2944, 63), color.RGBA{13, 43, 29, 255})
	fill(image.Rect(0, 63, 2944, 64), gold)
	button := func(r image.Rectangle) { fill(r, gold); fill(r.Inset(1), color.RGBA{17, 46, 31, 255}) }
	v.text(out, "神州八劍", 28, 12)
	v.text(out, "字型", 512, 12)
	button(image.Rect(596, 8, 1012, 56))
	v.text(out, v.fontLabel(v.font)+"  v", 616, 12)
	v.text(out, "海報", 1110, 12)
	button(image.Rect(1194, 8, 1536, 56))
	v.text(out, posterLabel(v.ID)+"  v", 1220, 12)
	if v.Menu != "" {
		x, w := 596, 416
		if v.Menu == "poster" {
			x, w = 1194, 342
		}
		for i := 0; i < v.menuLen(); i++ {
			r := image.Rect(x, 64+i*56, x+w, 120+i*56)
			button(r)
			if i == v.Selected {
				fill(r.Inset(2), color.RGBA{70, 74, 38, 255})
			}
			label := ""
			if v.Menu == "font" {
				label = v.fontLabel(v.choices[i].ID)
			} else {
				label = posterLabel([]string{"wings", "cover", "off"}[i])
			}
			v.text(out, label, x+20, r.Min.Y+8)
		}
	}
	v.frame, v.lastGame, v.dirty = out, game, false
	v.RenderedFrames++
	return out
}

func (v *PosterToolbar) text(out *image.RGBA, s string, x, y int) {
	for _, r := range s {
		g, ok := v.glyphs[r]
		if !ok {
			continue
		}
		advance := 34
		if r < 128 {
			advance = 20
		}
		dw, dh := g[2]*2/3, g[3]*2/3
		for yy := 0; yy < dh; yy++ {
			for xx := 0; xx < dw; xx++ {
				_, _, _, alpha := v.atlas.At(g[0]+xx*3/2, g[1]+yy*3/2).RGBA()
				a := uint32(alpha >> 8)
				ox, oy := x+(advance-dw)/2+xx, y+(40-dh)/2+yy
				if a == 0 || !image.Pt(ox, oy).In(out.Bounds()) {
					continue
				}
				old := out.RGBAAt(ox, oy)
				out.SetRGBA(ox, oy, color.RGBA{uint8((255*a + uint32(old.R)*(255-a) + 127) / 255), uint8((241*a + uint32(old.G)*(255-a) + 127) / 255), uint8((181*a + uint32(old.B)*(255-a) + 127) / 255), 255})
			}
		}
		x += advance
	}
}

func LoadPosterPreference(path string) (string, error) {
	var p struct {
		Schema int    `json:"schema"`
		Poster string `json:"poster"`
	}
	if err := readPosterJSON(path, &p); err != nil {
		if os.IsNotExist(err) {
			return "wings", nil
		}
		return "wings", err
	}
	if p.Schema != 1 || !posterID(p.Poster) {
		return "wings", fmt.Errorf("海報設定無效")
	}
	return p.Poster, nil
}
func SavePosterPreference(path, id string) error {
	if !posterID(id) {
		return fmt.Errorf("海報設定值無效")
	}
	if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		return err
	}
	f, err := os.CreateTemp(filepath.Dir(path), ".poster-settings-*")
	if err != nil {
		return err
	}
	name := f.Name()
	defer os.Remove(name)
	err = json.NewEncoder(f).Encode(struct {
		Schema int    `json:"schema"`
		Poster string `json:"poster"`
	}{1, id})
	closed := f.Close()
	if err != nil {
		return err
	}
	if closed != nil {
		return closed
	}
	return os.Rename(name, path)
}
