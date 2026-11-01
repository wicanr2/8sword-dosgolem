package ownedworld

import (
	"fmt"
	"image"
	"image/color"
)

func paintArmyDismiss(d *armyDismiss, f *armyUIFonts, font string) (*image.RGBA, []armyUIText) {
	resetHDUnitArtwork("dismiss")
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	uiFill(out, out.Bounds(), color.RGBA{8, 36, 25, 255})
	p := &armyUIPaint{Fonts: f, Canvas: out, Font: font}
	uiBorder(out, image.Rect(24, 20, 1896, 1180), uiGold)
	p.text("dismiss-title", "神州八劍・解雇軍隊", image.Rect(60, 32, 1080, 104), 44, uiGold, false)
	for _, v := range []struct{ ID, Name string }{{"noto", "Noto 900"}, {"lishu", "教育部隸書"}, {"caoshu", "草書"}} {
		p.button("font-"+v.ID, v.Name, uiFontRect(v.ID), font == v.ID, true)
	}
	p.number("dismiss-gold", fmt.Sprintf("金錢 %d", d.Data.Gold), image.Rect(60, 130, 450, 205), 36, 24, uiIvory)
	p.number("dismiss-total", fmt.Sprintf("總兵數 %d", d.Data.Metrics.Total), image.Rect(480, 130, 960, 205), 36, 20, uiIvory)
	p.number("dismiss-used", fmt.Sprintf("領導力 %d / %d", d.Data.Metrics.Used, d.Data.Leadership), image.Rect(980, 130, 1850, 205), 36, 18, uiIvory)
	for i, r := range d.Data.Rows {
		card := dismissCard(i)
		x, y := card.Min.X, card.Min.Y
		uiFill(out, card, color.RGBA{20, 56, 41, 255})
		stroke := uiMuted
		if i == d.Selected {
			uiFill(out, card, color.RGBA{104, 47, 38, 255})
			stroke = uiGold
		}
		uiBorder(out, card, stroke)
		p.text(fmt.Sprintf("dismiss-%d-slot", i), fmt.Sprintf("第%d隊", i+1), image.Rect(x+20, y+10, x+200, y+60), 28, uiMuted, false)
		if r.Count == 0 {
			p.text(fmt.Sprintf("dismiss-%d-empty", i), "空陣位", image.Rect(x+220, y+70, x+850, y+155), 40, uiMuted, true)
			continue
		}
		drawHDUnitArtwork(out, r.ID, image.Rect(x+16, y+66, x+200, y+210), false)
		p.text(fmt.Sprintf("dismiss-%d-name", i), r.Name, image.Rect(x+220, y+10, x+850, y+75), 40, uiGold, false)
		p.number(fmt.Sprintf("dismiss-%d-count", i), fmt.Sprintf("兵數 %d", r.Count), image.Rect(x+220, y+85, x+850, y+145), 36, 22, uiIvory)
		p.number(fmt.Sprintf("dismiss-%d-used", i), fmt.Sprintf("領導力 %d", r.Used), image.Rect(x+220, y+155, x+850, y+210), 30, 18, uiIvory)
	}
	p.text("dismiss-help", "選擇部隊　Enter 解雇整隊　Esc 返回", image.Rect(60, 1070, 1080, 1145), 28, uiIvory, false)
	p.button("dismiss-commit", "解雇整隊", dismissCommitRect, false, d.Selected >= 0)
	p.button("dismiss-close", "返回地圖", reviewCloseRect, false, true)
	return out, p.Texts
}
