//go:build ignore

package main

import (
	"errors"
	"fmt"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
	"image"
	"image/color"
	"image/draw"
)

type reinforcementUI struct {
	Previous  armyScreenExtra
	Engine    *game.Engine
	Port      *worldArmyPort
	Active    bool
	Selected  int
	Count     uint32
	Message   string
	Blocked   map[byte]bool
	ExitPhase int
	Purchases uint64
	Events    []map[string]any
}

var reinforcementCurrent *reinforcementUI
var reinforceNativeTab = image.Rect(60, 30, 430, 100)
var reinforceNewTab = image.Rect(450, 30, 820, 100)
var reinforceBuy = image.Rect(1430, 900, 1850, 980)

func reinforcementCard(i int) image.Rectangle {
	x, y := 60+i%4*450, 260+i/4*290
	return image.Rect(x, y, x+410, y+270)
}
func (x *reinforcementUI) IsActive() bool {
	return x.Port.ShopOpen || x.Previous != nil && x.Previous.IsActive()
}
func (x *reinforcementUI) key() string {
	return reinforcementKey(x.Port.ShopGroup, x.Port.ShopRow, x.Port.ShopKind, openKBArtIDs[x.Selected])
}
func (x *reinforcementUI) ready() bool {
	return x.Port.ShopOpen && recruitIconsCurrent != nil && recruitIconsCurrent.Ready && x.ExitPhase == 0
}
func (x *reinforcementUI) open() error {
	if !x.ready() {
		return nil
	}
	s, e := x.Port.Store.BindReinforcements(x.Port.Current.Token, x.Port.ShopGroup, x.Port.ShopRow)
	if e != nil {
		return e
	}
	x.Port.Current = s
	x.Active = true
	x.Selected = 2
	x.Count = 1
	x.Message = ""
	x.Engine.ReleaseAll()
	x.Events = append(x.Events, map[string]any{"event": "open", "steps": x.Engine.Oracle.Steps(), "token": s.Token})
	return nil
}
func (x *reinforcementUI) buy() error {
	if !x.Active {
		return nil
	}
	if x.Port.Current.World.Army.Rules == "native" {
		x.Message = "請先選擇結陣試作或戰術試作"
		return nil
	}
	q, e := x.Port.Current.World.Army.quote(x.Port.Store.Catalog, x.key())
	if e != nil {
		return e
	}
	if x.Count == 0 || x.Count > q.Maximum {
		x.Message = "金錢 領導力 等級 庫存 或陣位不足"
		return nil
	}
	s, e := x.Port.Store.RecruitReinforcement(x.Port.Current.Token, x.key(), x.Count)
	if e != nil {
		return e
	}
	x.Port.Current = s
	for i, n := range pairWorldResources(s.World).words() {
		if n > 30000 {
			return errors.New("reinforcement native resource bound")
		}
		x.Engine.Oracle.WriteU16(oracle.Far(0x1e88, 0x4f2+uint16(i*2)), uint16(n))
	}
	x.Purchases++
	x.Active = false
	x.ExitPhase = 1
	x.Events = append(x.Events, map[string]any{"event": "purchase", "key": x.key(), "count": x.Count, "steps": x.Engine.Oracle.Steps(), "token": s.Token})
	return nil
}
func (x *reinforcementUI) NoteKey(k byte, down bool) {
	if !down {
		return
	}
	if x.Active {
		x.Blocked[k] = true
		switch k {
		case 1:
			x.Active = false
		case 0x4b:
			if x.Selected%4 > 0 {
				x.Selected--
			}
		case 0x4d:
			if x.Selected%4 < 3 {
				x.Selected++
			}
		case 0x48:
			if x.Selected >= 4 {
				x.Selected -= 4
			}
		case 0x50:
			if x.Selected < 4 {
				x.Selected += 4
			}
		case 0x1c:
			if e := x.buy(); e != nil {
				panic(&worldArmyPortFault{e.Error()})
			}
		}
		return
	}
	if x.Previous != nil {
		x.Previous.NoteKey(k, down)
	}
}
func (x *reinforcementUI) Click(px, py int) (byte, error) {
	pt := image.Pt(px, py)
	if x.Port.ShopOpen {
		if pt.In(reinforceNewTab) {
			return 0, x.open()
		}
		if pt.In(reinforceNativeTab) {
			x.Active = false
			return 0, nil
		}
		if !x.Active {
			return 0, nil
		}
		for i := range openKBArtIDs {
			if pt.In(reinforcementCard(i)) {
				x.Selected = i
				x.Count = 1
				x.Message = ""
				return 0, nil
			}
		}
		for i, id := range []string{"native", "formation", "tactics"} {
			if pt.In(image.Rect(1020+i*280, 150, 1280+i*280, 215)) {
				w := cloneCampWorld(x.Port.Current.World)
				w.Army.Rules = id
				if e := w.Army.validate(x.Port.Store.Catalog); e != nil {
					x.Message = "軍隊已有新增兵種 請保留試作規則"
					return 0, nil
				}
				if id == x.Port.Current.World.Army.Rules {
					return 0, nil
				}
				w.Revision++
				s, e := x.Port.Store.Commit(x.Port.Current.Token, w)
				if e != nil {
					return 0, e
				}
				x.Port.Current = s
				return 0, nil
			}
		}
		q, e := x.Port.Current.World.Army.quote(x.Port.Store.Catalog, x.key())
		if e != nil {
			return 0, e
		}
		if pt.In(image.Rect(60, 900, 220, 980)) && x.Count > 1 {
			x.Count--
		}
		if pt.In(image.Rect(450, 900, 610, 980)) && x.Count < q.Maximum {
			x.Count++
		}
		if pt.In(image.Rect(640, 900, 940, 980)) && q.Maximum > 0 {
			x.Count = q.Maximum
		}
		if pt.In(reinforceBuy) {
			return 0, x.buy()
		}
		return 0, nil
	}
	if x.Previous != nil {
		return x.Previous.Click(px, py)
	}
	return 0, nil
}
func (x *reinforcementUI) State() map[string]any {
	v := map[string]any{}
	if x.Previous != nil {
		v = x.Previous.State()
	}
	v["reinforcements"] = map[string]any{"active": x.Active, "shop_open": x.Port.ShopOpen, "selected": x.Selected, "count": x.Count, "message": x.Message, "purchases": x.Purchases, "exit_phase": x.ExitPhase, "events": x.Events, "offers": reinforcementOffers(x.Port.Current.World.Army), "native_stock": x.Port.ShopStock, "group": x.Port.ShopGroup, "row": x.Port.ShopRow}
	return v
}
func (x *reinforcementUI) Paint(f *armyUIFonts, font string) (*image.RGBA, []armyUIText) {
	if !x.Port.ShopOpen {
		return x.Previous.Paint(f, font)
	}
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	p := &armyUIPaint{Fonts: f, Canvas: out, Font: font}
	if !x.Active {
		base := composeRecruitIcons(x.Engine, x.Engine.Frame())
		draw.Draw(out, out.Bounds(), base, image.Point{}, draw.Src)
	} else {
		resetHDUnitArtwork("reinforcements")
		uiFill(out, out.Bounds(), color.RGBA{8, 36, 25, 255})
		uiBorder(out, image.Rect(24, 20, 1896, 1180), uiGold)
	}
	p.button("reinforce-native", "原版兵種", reinforceNativeTab, !x.Active, true)
	p.button("reinforce-new", "新增兵種", reinforceNewTab, x.Active, x.ready())
	if !x.Active {
		return out, p.Texts
	}
	for _, v := range []struct{ ID, Name string }{{"noto", "Noto 900"}, {"lishu", "教育部隸書"}, {"caoshu", "草書"}} {
		p.button("font-"+v.ID, v.Name, uiFontRect(v.ID), font == v.ID, true)
	}
	w := x.Port.Current.World
	idx, _ := x.Port.Store.Catalog.index()
	metrics, _ := measureWorldArmy(x.Port.Store.Catalog, w.Army)
	p.text("reinforce-title", "神州八劍・新增兵種", image.Rect(60, 105, 1080, 150), 36, uiGold, false)
	p.number("reinforce-resources", fmt.Sprintf("金錢 %d 領導力 %d/%d 等級 %d", w.Army.Gold, metrics.Used, w.Army.Leadership, w.Army.RecruitRank), image.Rect(60, 155, 1000, 215), 28, 25, uiIvory)
	for i, id := range []string{"native", "formation", "tactics"} {
		p.button("reinforce-rule-"+id, []string{"原版規則", "結陣試作", "戰術試作"}[i], image.Rect(1020+i*280, 150, 1280+i*280, 215), w.Army.Rules == id, true)
	}
	p.number("reinforce-source", fmt.Sprintf("原版兵種 %s 庫存 %d", idx[x.Port.ShopUnit].Name, x.Port.ShopStock), image.Rect(60, 215, 1800, 255), 28, 24, uiMuted)
	for i, id := range openKBArtIDs {
		r := reinforcementCard(i)
		uiFill(out, r, color.RGBA{20, 56, 41, 255})
		border := uiMuted
		if i == x.Selected {
			border = uiGold
		}
		uiBorder(out, r, border)
		drawHDUnitArtwork(out, id, image.Rect(r.Min.X+10, r.Min.Y+40, r.Min.X+165, r.Max.Y-15), false)
		u := idx[id]
		o := w.Army.Offers[reinforcementKey(x.Port.ShopGroup, x.Port.ShopRow, x.Port.ShopKind, id)]
		left := r.Min.X + 175
		p.text(fmt.Sprintf("reinforce-%d-name", i), u.Name, image.Rect(left, r.Min.Y+10, r.Max.X-8, r.Min.Y+65), 32, uiGold, false)
		for j, s := range []string{fmt.Sprintf("金錢 %d", u.Gold), fmt.Sprintf("領導力 %d", u.Command), fmt.Sprintf("等級 %d", u.Rank), fmt.Sprintf("庫存 %d", o.Stock)} {
			p.number(fmt.Sprintf("reinforce-%d-%d", i, j), s, image.Rect(left, r.Min.Y+70+j*43, r.Max.X-8, r.Min.Y+110+j*43), 24, 20, uiIvory)
		}
	}
	q, _ := w.Army.quote(x.Port.Store.Catalog, x.key())
	p.number("reinforce-maximum", fmt.Sprintf("%s 可招募 %d", idx[openKBArtIDs[x.Selected]].Name, q.Maximum), image.Rect(60, 850, 1850, 895), 32, 24, uiGold)
	p.button("reinforce-minus", "-", image.Rect(60, 900, 220, 980), false, x.Count > 1)
	p.number("reinforce-count", fmt.Sprintf("%d", x.Count), image.Rect(240, 900, 430, 980), 40, 12, uiIvory)
	p.button("reinforce-plus", "+", image.Rect(450, 900, 610, 980), false, x.Count < q.Maximum)
	p.button("reinforce-max", "最大", image.Rect(640, 900, 940, 980), false, q.Maximum > 0)
	p.button("reinforce-buy", "招募", reinforceBuy, false, q.Maximum > 0 && w.Army.Rules != "native")
	p.text("reinforce-message", x.Message, image.Rect(60, 1000, 1850, 1060), 28, uiGold, false)
	p.text("reinforce-help", "方向鍵選擇 Enter 招募 Esc 返回原版兵種 F10 字型", image.Rect(60, 1090, 1850, 1160), 28, uiIvory, false)
	return out, p.Texts
}
func reinforcementGuestKey(g *armyReviewApp, k byte, down bool) error {
	x := reinforcementCurrent
	if x != nil {
		if x.Blocked[k] {
			if !down {
				delete(x.Blocked, k)
			}
			return nil
		}
		if x.Active {
			return nil
		}
	}
	return encounterGuestKey(g, k, down)
}
func advanceReinforcementUI(g *armyReviewApp) error {
	x := reinforcementCurrent
	if x != nil {
		if x.Active {
			return nil
		}
		if x.ExitPhase == 1 {
			x.Engine.ReleaseAll()
			if e := encounterGuestKey(g, 1, true); e != nil {
				return e
			}
			x.ExitPhase = 2
		} else if x.ExitPhase == 2 {
			if e := encounterGuestKey(g, 1, false); e != nil {
				return e
			}
			x.ExitPhase = 0
		}
	}
	return advanceSummonUI(g)
}
func init() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		v, err := previous(e, p)
		if err != nil {
			return nil, err
		}
		x := &reinforcementUI{Previous: v, Engine: e, Port: p, Count: 1, Blocked: map[byte]bool{}}
		reinforcementCurrent = x
		return x, nil
	}
	armyReviewTitle = "神州八劍・軍隊試作・增援營地"
}
