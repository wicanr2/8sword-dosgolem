//go:build ignore

// 030 DRAFT: direct Go RGBA canvas. No emulator, VGA buffer or guest reference.
package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	_ "image/png"
	"io"
	"os"
	"path/filepath"
	"unicode/utf8"
)

const armyUIWidth, armyUIHeight = 1920, 1200

var uiGold = color.RGBA{226, 197, 128, 255}
var uiIvory = color.RGBA{246, 234, 202, 255}
var uiMuted = color.RGBA{142, 159, 141, 255}

type armyUIFonts struct {
	Atlases       map[string]image.Image
	Glyphs        map[rune]image.Rectangle
	Sources       map[string]string
	Fallbacks     map[string]int
	CatalogRawSHA string
}

func armyUIRead(path string, limit int64) ([]byte, error) {
	f, e := os.Open(path)
	if e != nil {
		return nil, e
	}
	defer f.Close()
	s, e := f.Stat()
	if e != nil {
		return nil, e
	}
	if !s.Mode().IsRegular() || s.Size() > limit {
		return nil, errors.New("軍隊介面檔案形狀不符")
	}
	raw, e := io.ReadAll(io.LimitReader(f, limit+1))
	if e != nil {
		return nil, e
	}
	if int64(len(raw)) > limit {
		return nil, errors.New("軍隊介面檔案過大")
	}
	return raw, nil
}
func loadArmyUIFonts(dir string) (*armyUIFonts, error) {
	raw, err := armyUIRead(filepath.Join(dir, "army-ui-fonts.json"), 1<<20)
	if err != nil {
		return nil, err
	}
	var m struct {
		Schema        int
		CatalogRawSHA string `json:"army_catalog_sha256"`
		Glyphs        []struct {
			Character string
			Cell      [4]int
		}
		Profiles []struct {
			ID, File, SHA string
			SourceSHA     string `json:"source_sha256"`
			Width, Height int
			Fallbacks     int
		}
	}
	if err = json.Unmarshal(raw, &m); err != nil {
		return nil, err
	}
	if m.Schema != 1 || len(m.Profiles) != 3 || len(m.Glyphs) < 95 || len(m.Glyphs) > 4096 {
		return nil, errors.New("軍隊字圖形狀不符")
	}
	f := &armyUIFonts{Atlases: map[string]image.Image{}, Glyphs: map[rune]image.Rectangle{}, Sources: map[string]string{}, Fallbacks: map[string]int{}, CatalogRawSHA: m.CatalogRawSHA}
	wanted := map[string]string{"noto": "3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151", "lishu": "f0ba5eda31727ad89cc0b1f6b9a7dfda02f061fa101c18548b6f8ea0145c108b", "caoshu": "cab396b91a5b7c0b4005a35891180d06e6751f5ac261fe680aec65c1ae209033"}
	for _, p := range m.Profiles {
		if wanted[p.ID] == "" || wanted[p.ID] != p.SourceSHA || p.File != "army-ui-"+p.ID+".png" || f.Atlases[p.ID] != nil || p.Width != 1024 || p.Height < 64 || p.Height > 16384 {
			return nil, errors.New("軍隊字圖來源不符")
		}
		raw, e := armyUIRead(filepath.Join(dir, p.File), 8<<20)
		if e != nil {
			return nil, e
		}
		if contentSHA(raw) != p.SHA {
			return nil, errors.New("軍隊字圖SHA不符")
		}
		cfg, _, e := image.DecodeConfig(bytes.NewReader(raw))
		if e != nil || cfg.Width != p.Width || cfg.Height != p.Height {
			return nil, errors.New("軍隊字圖尺寸不符")
		}
		im, _, e := image.Decode(bytes.NewReader(raw))
		if e != nil {
			return nil, e
		}
		if im.Bounds() != image.Rect(0, 0, p.Width, p.Height) {
			return nil, errors.New("軍隊字圖尺寸不符")
		}
		f.Atlases[p.ID] = im
		f.Sources[p.ID] = p.SourceSHA
		f.Fallbacks[p.ID] = p.Fallbacks
	}
	for _, g := range m.Glyphs {
		r, n := utf8.DecodeRuneInString(g.Character)
		box := image.Rect(g.Cell[0], g.Cell[1], g.Cell[0]+g.Cell[2], g.Cell[1]+g.Cell[3])
		if n != len(g.Character) || r == utf8.RuneError || f.Glyphs[r] != (image.Rectangle{}) || g.Cell[2] != 64 || g.Cell[3] != 64 {
			return nil, errors.New("軍隊字元形狀不符")
		}
		for _, im := range f.Atlases {
			if !box.In(im.Bounds()) {
				return nil, errors.New("軍隊字元越界")
			}
		}
		f.Glyphs[r] = box
	}
	return f, nil
}

type armyUIText struct {
	Role, Text string
	Rect, Ink  [4]int
	Size       int
	Ellipsized bool
}
type armyUIPaint struct {
	Fonts  *armyUIFonts
	Canvas *image.RGBA
	Texts  []armyUIText
	Font   string
}

func uiBox(r image.Rectangle) [4]int { return [4]int{r.Min.X, r.Min.Y, r.Max.X, r.Max.Y} }
func uiFill(out *image.RGBA, r image.Rectangle, c color.RGBA) {
	draw.Draw(out, r, image.NewUniform(c), image.Point{}, draw.Src)
}
func uiBorder(out *image.RGBA, r image.Rectangle, c color.RGBA) {
	uiFill(out, image.Rect(r.Min.X, r.Min.Y, r.Max.X, r.Min.Y+2), c)
	uiFill(out, image.Rect(r.Min.X, r.Max.Y-2, r.Max.X, r.Max.Y), c)
	uiFill(out, image.Rect(r.Min.X, r.Min.Y, r.Min.X+2, r.Max.Y), c)
	uiFill(out, image.Rect(r.Max.X-2, r.Min.Y, r.Max.X, r.Max.Y), c)
}
func uiAdvance(r rune, size int) int {
	if r < 128 {
		return size * 2 / 3
	}
	return size
}
func uiTextWidth(text string, size int) int {
	n := 0
	for _, r := range text {
		n += uiAdvance(r, size)
	}
	return n
}
func uiFit(text string, width, size int) (string, bool) {
	if uiTextWidth(text, size) <= width {
		return text, false
	}
	r := []rune(text)
	for len(r) > 0 && uiTextWidth(string(r)+"…", size) > width {
		r = r[:len(r)-1]
	}
	if uiTextWidth("…", size) > width {
		return "", true
	}
	return string(r) + "…", true
}
func (p *armyUIPaint) text(role, text string, r image.Rectangle, size int, c color.RGBA, center bool) {
	if !r.In(p.Canvas.Bounds()) || r.Dy() < size || size < 1 {
		panic("text-safe rectangle")
	}
	rendered, truncated := uiFit(text, r.Dx(), size)
	x := r.Min.X
	if center {
		x += (r.Dx() - uiTextWidth(rendered, size)) / 2
	}
	y := r.Min.Y + (r.Dy()-size)/2
	ink := image.Rectangle{}
	atlas := p.Fonts.Atlases[p.Font]
	for _, ch := range rendered {
		adv := uiAdvance(ch, size)
		cell, ok := p.Fonts.Glyphs[ch]
		if !ok {
			panic(fmt.Sprintf("missing UI glyph %U", ch))
		}
		if ch != ' ' {
			for py := 0; py < size; py++ {
				for px := 0; px < adv; px++ {
					_, _, _, a := atlas.At(cell.Min.X+px*64/adv, cell.Min.Y+py*64/size).RGBA()
					v := uint32(a >> 8)
					if v == 0 {
						continue
					}
					ox, oy := x+px, y+py
					ink = ink.Union(image.Rect(ox, oy, ox+1, oy+1))
					at := oy*p.Canvas.Stride + ox*4
					for k, value := range []uint8{c.R, c.G, c.B} {
						p.Canvas.Pix[at+k] = uint8((uint32(value)*v + uint32(p.Canvas.Pix[at+k])*(255-v) + 127) / 255)
					}
				}
			}
		}
		x += adv
	}
	if !ink.Empty() && !ink.In(r) {
		panic("glyph ink escaped text-safe rectangle")
	}
	p.Texts = append(p.Texts, armyUIText{Role: role, Text: rendered, Rect: uiBox(r), Ink: uiBox(ink), Size: size, Ellipsized: truncated})
}
func (p *armyUIPaint) number(role, text string, r image.Rectangle, size, minimum int, c color.RGBA) {
	for size > minimum && uiTextWidth(text, size) > r.Dx() {
		size--
	}
	if uiTextWidth(text, size) > r.Dx() {
		panic("numeric field exceeded its full-value size contract")
	}
	p.text(role, text, r, size, c, false)
}
func uiFontRect(id string) image.Rectangle {
	switch id {
	case "noto":
		return image.Rect(1140, 40, 1370, 104)
	case "lishu":
		return image.Rect(1390, 40, 1620, 104)
	default:
		return image.Rect(1640, 40, 1860, 104)
	}
}
func uiRuleRect(id string) image.Rectangle {
	switch id {
	case "native":
		return image.Rect(1280, 125, 1460, 205)
	case "formation":
		return image.Rect(1480, 125, 1660, 205)
	default:
		return image.Rect(1680, 125, 1860, 205)
	}
}
func uiOfferRect(i int) image.Rectangle { return image.Rect(1190, 320+i*65, 1860, 378+i*65) }

var uiQuantityRect = image.Rect(1300, 910, 1550, 978)
var uiRecruitRect = image.Rect(1190, 1000, 1860, 1070)

func uiHit(u *armyUI, x, y int) string {
	pt := image.Pt(x, y)
	for _, id := range []string{"noto", "lishu", "caoshu"} {
		if pt.In(uiFontRect(id)) {
			return "font:" + id
		}
	}
	for _, id := range []string{"native", "formation", "tactics"} {
		if pt.In(uiRuleRect(id)) {
			return "rules:" + id
		}
	}
	for i, id := range u.pageOffers() {
		if pt.In(uiOfferRect(i)) {
			return "select:" + id
		}
	}
	for _, v := range []struct {
		Name string
		Rect image.Rectangle
	}{{"all", image.Rect(1190, 240, 1500, 300)}, {"new", image.Rect(1520, 240, 1860, 300)}, {"prev", image.Rect(1190, 730, 1350, 790)}, {"next", image.Rect(1700, 730, 1860, 790)}, {"minus", image.Rect(1190, 910, 1280, 978)}, {"quantity", uiQuantityRect}, {"plus", image.Rect(1570, 910, 1660, 978)}, {"max", image.Rect(1680, 910, 1860, 978)}, {"recruit", uiRecruitRect}} {
		if pt.In(v.Rect) {
			return v.Name
		}
	}
	return ""
}
func (p *armyUIPaint) button(role, label string, r image.Rectangle, selected, enabled bool) {
	c := color.RGBA{23, 64, 48, 255}
	stroke := color.RGBA{100, 126, 91, 255}
	text := uiIvory
	if selected {
		c = color.RGBA{104, 47, 38, 255}
		stroke = uiGold
	}
	if !enabled {
		text = uiMuted
		c = color.RGBA{24, 43, 35, 255}
	}
	uiFill(p.Canvas, r, c)
	uiBorder(p.Canvas, r, stroke)
	p.text(role, label, r.Inset(10), 28, text, true)
}
func paintArmyUI(u *armyUI, fonts *armyUIFonts) (*image.RGBA, []armyUIText) {
	if fonts.Atlases[u.Font] == nil {
		panic("unavailable UI font")
	}
	out := image.NewRGBA(image.Rect(0, 0, armyUIWidth, armyUIHeight))
	uiFill(out, out.Bounds(), color.RGBA{8, 36, 25, 255})
	for y := 0; y < armyUIHeight; y += 12 {
		uiFill(out, image.Rect(0, y, armyUIWidth, y+1), color.RGBA{10, 40, 27, 255})
	}
	p := &armyUIPaint{Fonts: fonts, Canvas: out, Font: u.Font}
	uiBorder(out, image.Rect(24, 20, 1896, 1180), uiGold)
	p.text("title", "神州八劍・軍隊招募試作", image.Rect(60, 32, 1080, 104), 44, uiGold, false)
	for _, v := range []struct{ ID, Label string }{{"noto", "Noto 900"}, {"lishu", "教育部隸書"}, {"caoshu", "草書"}} {
		p.button("font-"+v.ID, v.Label, uiFontRect(v.ID), u.Font == v.ID, true)
	}
	p.number("gold", fmt.Sprintf("金錢 %d", u.Army.Gold), image.Rect(60, 125, 450, 205), 34, 24, uiIvory)
	p.number("leadership", fmt.Sprintf("領導力 %d / %d", u.usage(), u.Army.Leadership), image.Rect(480, 125, 1020, 205), 32, 16, uiIvory)
	p.text("rank", fmt.Sprintf("等級 %d", u.Army.RecruitRank), image.Rect(1040, 125, 1260, 205), 32, uiGold, false)
	for _, v := range []struct{ ID, Label string }{{"native", "原版規則"}, {"formation", "結陣試作"}, {"tactics", "戰術試作"}} {
		p.button("rules-"+v.ID, v.Label, uiRuleRect(v.ID), u.Army.Rules == v.ID, true)
	}
	p.text("roster-title", "我的軍隊", image.Rect(60, 230, 1120, 285), 34, uiGold, false)
	idx, _ := u.Catalog.index()
	for i, s := range u.Army.Slots {
		x, y := 60+i%3*360, 300+i/3*340
		card := image.Rect(x, y, x+340, y+310)
		uiFill(out, card, color.RGBA{20, 56, 41, 255})
		uiBorder(out, card, color.RGBA{113, 126, 79, 255})
		p.text(fmt.Sprintf("slot-%d-number", i), fmt.Sprintf("第%d隊", i+1), image.Rect(x+20, y+16, x+320, y+60), 28, uiMuted, false)
		if s.Count == 0 {
			p.text(fmt.Sprintf("slot-%d-empty", i), "空陣位", image.Rect(x+20, y+110, x+320, y+180), 40, uiMuted, true)
			continue
		}
		profile := idx[s.Unit]
		name := []rune(profile.Name)
		emblem := image.Rect(x+20, y+78, x+112, y+174)
		uiBorder(out, emblem, uiGold)
		p.text(fmt.Sprintf("slot-%d-emblem", i), string(name[0]), emblem.Inset(8), 56, uiGold, true)
		p.text(fmt.Sprintf("slot-%d-name", i), profile.Name, image.Rect(x+130, y+72, x+320, y+126), 32, uiGold, false)
		p.number(fmt.Sprintf("slot-%d-count", i), fmt.Sprintf("兵數 %d", s.Count), image.Rect(x+20, y+178, x+320, y+222), 28, 24, uiIvory)
		p.number(fmt.Sprintf("slot-%d-leadership", i), fmt.Sprintf("領導力 %d", uint64(s.Count)*profile.Command), image.Rect(x+20, y+222, x+320, y+260), 28, 17, uiIvory)
		badge := "神州兵種"
		if profile.NativeKind == 0 {
			badge = "新增兵種・試作"
		}
		p.text(fmt.Sprintf("slot-%d-origin", i), badge, image.Rect(x+20, y+258, x+320, y+298), 24, uiMuted, false)
	}
	p.button("filter-all", "全部兵種", image.Rect(1190, 240, 1500, 300), !u.NewOnly, true)
	p.button("filter-new", "新增兵種", image.Rect(1520, 240, 1860, 300), u.NewOnly, true)
	for i, id := range u.pageOffers() {
		r := uiOfferRect(i)
		profile := u.profile(id)
		selected := id == u.Selected
		uiFill(out, r, color.RGBA{20, 56, 42, 255})
		if selected {
			uiFill(out, r, color.RGBA{103, 45, 37, 255})
		}
		uiBorder(out, r, color.RGBA{107, 119, 78, 255})
		c := uiIvory
		if profile.Rank > u.Army.RecruitRank {
			c = uiMuted
		}
		p.text("offer-name-"+id, profile.Name, image.Rect(r.Min.X+16, r.Min.Y+5, r.Min.X+230, r.Max.Y-5), 30, c, false)
		origin := "神州"
		if profile.NativeKind == 0 {
			origin = "新增"
		}
		p.text("offer-origin-"+id, origin, image.Rect(r.Min.X+250, r.Min.Y+5, r.Min.X+342, r.Max.Y-5), 22, uiMuted, false)
		p.text("offer-price-"+id, fmt.Sprintf("%d 金", profile.Gold), image.Rect(r.Min.X+350, r.Min.Y+5, r.Max.X-16, r.Max.Y-5), 28, uiGold, false)
	}
	rows := u.visibleOffers()
	p.button("page-prev", "上一頁", image.Rect(1190, 730, 1350, 790), false, u.Page > 0)
	p.button("page-next", "下一頁", image.Rect(1700, 730, 1860, 790), false, (u.Page+1)*6 < len(rows))
	p.text("page", fmt.Sprintf("第 %d / %d 頁", u.Page+1, max(1, (len(rows)+5)/6)), image.Rect(1360, 730, 1690, 790), 28, uiMuted, true)
	profile := u.profile(u.Selected)
	q, err := u.quote()
	if err != nil {
		panic(err)
	}
	p.number("offer-details", fmt.Sprintf("單價 %d　領導 %d　庫存 %d", profile.Gold, profile.Command, u.Army.Offers[u.Selected].Stock), image.Rect(1190, 810, 1860, 856), 28, 20, uiIvory)
	limit := fmt.Sprintf("可招募 %d", q.Maximum)
	if profile.Rank > u.Army.RecruitRank {
		limit = fmt.Sprintf("需要等級 %d", profile.Rank)
	}
	if q.Reason == "rules" {
		limit = "新增兵種需增強規則"
	}
	p.text("offer-limit", limit, image.Rect(1190, 860, 1860, 900), 28, uiGold, false)
	p.button("quantity-minus", "－", image.Rect(1190, 910, 1280, 978), false, true)
	p.button("quantity-plus", "＋", image.Rect(1570, 910, 1660, 978), false, true)
	p.button("quantity-max", "最大", image.Rect(1680, 910, 1860, 978), false, true)
	uiFill(out, uiQuantityRect, color.RGBA{9, 28, 21, 255})
	stroke := uiMuted
	if u.QtyFocused {
		stroke = uiGold
	}
	uiBorder(out, uiQuantityRect, stroke)
	p.text("quantity", u.Quantity, uiQuantityRect.Inset(10), 32, uiIvory, true)
	p.button("recruit", "招募", uiRecruitRect, false, u.canRecruit())
	p.text("message", u.Message, image.Rect(60, 1010, 1140, 1080), 27, uiIvory, false)
	p.text("help", "滑鼠選兵・輸入數量・Enter 招募・F10 字型・Ctrl+Q 離開", image.Rect(60, 1110, 1860, 1160), 26, uiMuted, false)
	return out, p.Texts
}
