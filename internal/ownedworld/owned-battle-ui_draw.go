package ownedworld

import (
	"fmt"
	"image"
	"image/color"
)

func battleCard(side, slot int) image.Rectangle {
	x := 60 + slot%3*290
	if side == 1 {
		x += 960
	}
	y := 300 + slot/3*260
	return image.Rect(x, y, x+270, y+235)
}

var battleButtons = []struct {
	ID, Text string
	Rect     image.Rectangle
}{
	{"recruit", "招募野狼30", image.Rect(60, 190, 350, 260)},
	{"begin", "進入戰場", image.Rect(370, 190, 650, 260)},
	{"attack", "我方出手", image.Rect(60, 860, 350, 940)},
	{"enemy", "敵方策略出手", image.Rect(380, 860, 720, 940)},
	{"pass", "後排略過", image.Rect(750, 860, 1030, 940)},
	{"round", "下一輪", image.Rect(1060, 860, 1340, 940)},
	{"settle", "領取勝利戰果", image.Rect(1370, 860, 1860, 940)},
}

func battleHit(u *battleUI, x, y int) string {
	pt := image.Pt(x, y)
	for _, id := range []string{"noto", "lishu", "caoshu"} {
		if pt.In(uiFontRect(id)) {
			return "font:" + id
		}
	}
	for side := 0; side < 2; side++ {
		for i := 0; i < 6; i++ {
			if pt.In(battleCard(side, i)) {
				return fmt.Sprintf("card:%d:%d", side, i)
			}
		}
	}
	for _, b := range rearButtons {
		if pt.In(b.Rect) {
			return b.ID
		}
	}
	for _, b := range battleButtons {
		if pt.In(b.Rect) {
			return b.ID
		}
	}
	return ""
}
func paintBattleUI(u *battleUI, f *armyUIFonts) (*image.RGBA, []armyUIText) {
	resetHDUnitArtwork("battle")
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	uiFill(out, out.Bounds(), color.RGBA{7, 36, 26, 255})
	uiBorder(out, image.Rect(24, 20, 1896, 1180), uiGold)
	p := armyUIPaint{Fonts: f, Canvas: out, Font: u.Font}
	p.text("title", "神州八劍・Go戰鬥試作", image.Rect(60, 40, 1100, 104), 48, uiGold, false)
	for _, v := range []struct{ ID, Text string }{{"noto", "Noto 900"}, {"lishu", "教育部隸書"}, {"caoshu", "草書"}} {
		p.button("font:"+v.ID, v.Text, uiFontRect(v.ID), v.ID == u.Font, true)
	}
	p.number("gold", fmt.Sprintf("金錢 %d", u.World.Army.Gold), image.Rect(60, 120, 450, 178), 34, 18, uiIvory)
	p.number("merit", fmt.Sprintf("戰績 %d", u.World.Progress.Merit), image.Rect(480, 120, 880, 178), 34, 18, uiIvory)
	p.number("rank", fmt.Sprintf("等級 %d", u.World.Progress.Rank), image.Rect(900, 120, 1200, 178), 34, 18, uiIvory)
	status := "戰前整備"
	s, active := u.state()
	if active {
		status = fmt.Sprintf("第%d輪", s.Round)
		if s.Result == "win" {
			status = "戰鬥勝利"
		}
		if s.Result == "loss" {
			status = "全軍覆沒，交接待完成"
		}
	}
	p.text("phase", status, image.Rect(1250, 120, 1860, 178), 34, uiGold, true)
	p.text("side0", "我方・前三隊為前排", image.Rect(60, 266, 900, 300), 26, uiGold, false)
	p.text("side1", "敵方・前三隊為前排", image.Rect(1020, 266, 1860, 300), 26, uiGold, false)
	names := map[string]string{}
	for _, v := range u.Catalog.Profiles {
		names[v.ID] = v.Name
	}
	for side := 0; side < 2; side++ {
		for i := 0; i < 6; i++ {
			rect := battleCard(side, i)
			uiFill(out, rect, color.RGBA{20, 57, 42, 255})
			stroke := uiMuted
			if side == 0 && i == u.Source || side == 1 && i == u.Target {
				stroke = uiGold
			}
			uiBorder(out, rect, stroke)
			var stack ArmyStack
			acted := false
			if active {
				v := s.Rows[side][i]
				stack = ArmyStack{Unit: v.Unit, Count: v.Count}
				acted = s.Acted[side][i]
			} else if side == 0 {
				stack = u.World.Army.Slots[i]
			} else {
				e := u.World.Encounters["skeleton-patrol"]
				if !e.Cleared {
					stack = e.Enemy[i]
				}
			}
			p.text(fmt.Sprintf("slot%d:%d", side, i), fmt.Sprintf("第%d隊", i+1), image.Rect(rect.Min.X+16, rect.Min.Y+12, rect.Max.X-16, rect.Min.Y+50), 28, uiMuted, false)
			name := names[stack.Unit]
			if name == "" {
				name = "空陣位"
			}
			p.text("unit", name, image.Rect(rect.Min.X+12, rect.Min.Y+54, rect.Max.X-12, rect.Min.Y+98), 30, uiGold, true)
			drawHDUnitArtwork(out, stack.Unit, image.Rect(rect.Min.X+12, rect.Min.Y+105, rect.Min.X+130, rect.Min.Y+220), side == 1)
			p.number("count", fmt.Sprintf("兵數 %d", stack.Count), image.Rect(rect.Min.X+138, rect.Min.Y+108, rect.Max.X-10, rect.Min.Y+164), 28, 10, uiIvory)
			label := "待命"
			if acted {
				label = "已行動"
			}
			if stack.Count == 0 {
				label = "無法行動"
			}
			p.text("acted", label, image.Rect(rect.Min.X+138, rect.Min.Y+178, rect.Max.X-10, rect.Min.Y+220), 24, uiMuted, true)
		}
	}
	for _, b := range battleButtons {
		enabled := true
		switch b.ID {
		case "recruit", "begin":
			enabled = !active
		case "attack":
			_, e := u.playerPlan()
			enabled = e == nil
		case "enemy":
			_, e := u.enemyPlan()
			enabled = e == nil || rearEnemyPassAvailable(u)
		case "settle":
			enabled = active && s.Result == "win"
		case "pass", "round":
			enabled = active && s.Result == ""
		}
		p.button(b.ID, b.Text, b.Rect, false, enabled)
	}
	paintRearButtons(u, &p)
	// Filesystem errors can contain user-defined path characters outside this
	// bounded UI pack. Keep the original error in status; render unknown runes
	// as an ASCII question mark rather than panicking while reporting a failure.
	message := []rune(u.Message)
	for i, ch := range message {
		if _, ok := f.Glyphs[ch]; !ok {
			message[i] = '?'
		}
	}
	p.text("message", string(message), image.Rect(60, 970, 1860, 1040), 32, uiIvory, false)
	p.text("scope", "獨立操作試作・資源與敵軍為測試資料・每個有效動作自動儲存", image.Rect(60, 1050, 1860, 1100), 28, uiMuted, false)
	p.text("keys", "點選部隊與指令・F10 字型・F12 擷取・Ctrl+Q 離開", image.Rect(60, 1110, 1860, 1160), 28, uiMuted, false)
	return out, p.Texts
}
