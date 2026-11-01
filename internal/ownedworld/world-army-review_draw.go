package ownedworld

import (
	"fmt"
	"image"
	"image/color"
)

var reviewCloseRect = image.Rect(1510, 1070, 1850, 1145)

func paintArmyReview(v armyReviewData, fonts *armyUIFonts, font string) (*image.RGBA, []armyUIText) {
	resetHDUnitArtwork("review")
	if fonts.Atlases[font] == nil {
		panic("unavailable army review font")
	}
	out := image.NewRGBA(image.Rect(0, 0, armyUIWidth, armyUIHeight))
	uiFill(out, out.Bounds(), color.RGBA{8, 36, 25, 255})
	for y := 0; y < armyUIHeight; y += 12 {
		uiFill(out, image.Rect(0, y, armyUIWidth, y+1), color.RGBA{10, 40, 27, 255})
	}
	p := &armyUIPaint{Fonts: fonts, Canvas: out, Font: font}
	uiBorder(out, image.Rect(24, 20, 1896, 1180), uiGold)
	p.text("review-title", "神州八劍・我的軍隊", image.Rect(60, 32, 1080, 104), 44, uiGold, false)
	for _, b := range []struct{ ID, Name string }{{"noto", "Noto 900"}, {"lishu", "教育部隸書"}, {"caoshu", "草書"}} {
		p.button("font-"+b.ID, b.Name, uiFontRect(b.ID), font == b.ID, true)
	}
	p.number("review-gold", fmt.Sprintf("金錢 %d", v.Gold), image.Rect(60, 130, 450, 205), 36, 24, uiIvory)
	p.number("review-total", fmt.Sprintf("總兵數 %d", v.Metrics.Total), image.Rect(480, 130, 960, 205), 36, 20, uiIvory)
	p.number("review-command", fmt.Sprintf("領導力 %d / %d", v.Metrics.Used, v.Leadership), image.Rect(980, 130, 1850, 205), 36, 18, uiIvory)
	for i, r := range v.Rows {
		x, y := 60+i%3*600, 245+i/3*375
		card := image.Rect(x, y, x+570, y+345)
		uiFill(out, card, color.RGBA{20, 56, 41, 255})
		uiBorder(out, card, color.RGBA{113, 126, 79, 255})
		p.text(fmt.Sprintf("review-%d-slot", i), fmt.Sprintf("第%d隊", i+1), image.Rect(x+22, y+16, x+548, y+70), 30, uiMuted, false)
		if r.Count == 0 {
			p.text(fmt.Sprintf("review-%d-empty", i), "空陣位", image.Rect(x+24, y+110, x+546, y+210), 44, uiMuted, true)
			continue
		}
		drawHDUnitArtwork(out, r.ID, image.Rect(x+18, y+75, x+220, y+320), false)
		p.text(fmt.Sprintf("review-%d-name", i), r.Name, image.Rect(x+240, y+78, x+546, y+150), 44, uiGold, false)
		p.number(fmt.Sprintf("review-%d-count", i), fmt.Sprintf("兵數 %d", r.Count), image.Rect(x+240, y+158, x+546, y+218), 36, 22, uiIvory)
		p.number(fmt.Sprintf("review-%d-used", i), fmt.Sprintf("領導力 %d", r.Used), image.Rect(x+240, y+225, x+546, y+280), 32, 18, uiIvory)
		origin := "神州兵種"
		if !r.Native {
			origin = "新增兵種"
		}
		p.text(fmt.Sprintf("review-%d-origin", i), origin, image.Rect(x+240, y+285, x+546, y+328), 26, uiMuted, false)
	}
	name := map[string]string{"native": "原版規則", "formation": "結陣試作", "tactics": "戰術試作"}[v.Rules]
	p.text("review-rules", name, image.Rect(60, 1020, 650, 1070), 30, uiGold, false)
	p.text("review-help", "按鍵返回地圖　F10 字型", image.Rect(60, 1080, 1430, 1140), 30, uiIvory, false)
	p.button("review-close", "返回地圖", reviewCloseRect, false, true)
	return out, p.Texts
}
