package ownedworld

import (
	"fmt"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"image"
	"image/color"
)

func wideMonthlyVisible() bool {
	return monthlyCurrent != nil && monthlyCurrent.Active && monthlyCurrent.Committed
}

type wideMonthlyExtra struct{ Previous armyScreenExtra }

func (v *wideMonthlyExtra) IsActive() bool {
	return wideMonthlyVisible() || (v.Previous != nil && v.Previous.IsActive())
}
func (v *wideMonthlyExtra) NoteKey(scan byte, down bool) {
	if !wideMonthlyVisible() && v.Previous != nil {
		v.Previous.NoteKey(scan, down)
	}
}
func (v *wideMonthlyExtra) Click(x, y int) (byte, error) {
	if wideMonthlyVisible() {
		if image.Pt(x, y).In(reviewCloseRect) {
			return 1, nil
		}
		return 0, nil
	}
	if v.Previous != nil {
		return v.Previous.Click(x, y)
	}
	return 0, nil
}
func (v *wideMonthlyExtra) State() map[string]any {
	if v.Previous != nil {
		return v.Previous.State()
	}
	return map[string]any{}
}
func (v *wideMonthlyExtra) Paint(f *armyUIFonts, id string) (*image.RGBA, []armyUIText) {
	if wideMonthlyVisible() {
		return paintWideMonthly(monthlyCurrent.Budget, f, id)
	}
	return v.Previous.Paint(f, id)
}
func paintWideMonthly(b monthlyBudget, f *armyUIFonts, id string) (*image.RGBA, []armyUIText) {
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	uiFill(out, out.Bounds(), color.RGBA{8, 36, 25, 255})
	uiBorder(out, image.Rect(24, 20, 1896, 1180), uiGold)
	p := &armyUIPaint{Fonts: f, Canvas: out, Font: id}
	p.text("monthly-title", "神州八劍・每月收支統計", image.Rect(60, 32, 1080, 110), 44, uiGold, false)
	for _, v := range []struct{ ID, Label string }{{"noto", "Noto 900"}, {"lishu", "教育部隸書"}, {"caoshu", "草書"}} {
		p.button("font-"+v.ID, v.Label, uiFontRect(v.ID), id == v.ID, true)
	}
	for i, v := range []struct {
		Role, Label string
		Value       uint64
	}{{"before", "月初金錢", b.Before}, {"income", "月薪收入", b.Income}, {"due", "軍費應付", b.Due}, {"charged", "軍費實付", b.Charged}, {"after", "現金餘額", b.After}} {
		y := 200 + i*135
		uiFill(out, image.Rect(80, y, 1840, y+110), color.RGBA{20, 56, 41, 255})
		p.text("monthly-"+v.Role+"-label", v.Label, image.Rect(120, y+12, 650, y+98), 42, uiGold, false)
		p.number("monthly-"+v.Role, fmt.Sprintf("%d", v.Value), image.Rect(740, y+12, 1790, y+98), 46, 32, uiIvory)
	}
	if b.Disbanded {
		p.text("monthly-disband", "金錢不足 全軍離隊 本次軍費免收", image.Rect(100, 930, 1820, 1010), 36, uiGold, true)
	}
	p.button("monthly-return", "返回地圖", reviewCloseRect, false, true)
	return out, p.Texts
}
func initializeLayer39() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		v, err := previous(e, p)
		if err != nil {
			return nil, err
		}
		return &wideMonthlyExtra{v}, nil
	}
	armyReviewTitle = "神州八劍・軍隊試作・月結"
}
