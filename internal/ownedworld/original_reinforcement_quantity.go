package ownedworld

import (
	"errors"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"math"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

// Spec 030 READY. A selected extension offer uses the actual original editor;
// the native shop identity remains only the immutable camp binding.
type originalReinforcementQuantity struct {
	Owner                                    *originalRecruitQuantity
	UI                                       *reinforcementUI
	Key, Unit, Token, Phase                  string
	Ready, EscapeDown, EscapeSent, Committed bool
	Starts, Purchases                        uint64
	Events                                   []map[string]any
}

func originalReinforcementPlanFor(c ArmyCatalog, a OwnedArmy, key string) (originalRecruitPlan, error) {
	m, err := measureWorldArmy(c, a)
	if err != nil {
		return originalRecruitPlan{}, err
	}
	_, _, _, id, err := parseReinforcementKey(key)
	if err != nil {
		return originalRecruitPlan{}, err
	}
	o, ok := a.Offers[key]
	idx, err := c.index()
	if err != nil {
		return originalRecruitPlan{}, err
	}
	u, found := idx[id]
	if !ok || !found || o.Unit != id || !originalOpenKBID(id) || u.Origin == "native" || u.NativeKind != 0 || u.Gold == 0 || u.Command == 0 || a.Rules == "native" {
		return originalRecruitPlan{}, errors.New("original reinforcement offer/profile/rules")
	}
	p := originalRecruitPlan{Unit: id, Price: u.Gold, Command: u.Command, Used: m.Used, Limit: (a.Leadership - m.Used) / u.Command, Stock: o.Stock, Preflight: 0x55f0}
	capacity, err := worldArmyCapacity(c, a, id)
	if err != nil {
		return p, err
	}
	switch {
	case u.Rank > a.RecruitRank:
		p.Preflight = 0x5533
	case !capacity:
		p.Preflight = 0x5574
	case a.Gold < u.Gold:
		p.Preflight = 0x55a0
	case p.Limit == 0:
		p.Preflight = 0x5774
	}
	if p.Limit > 32767 {
		return p, errors.New("original reinforcement leadership display range")
	}
	return p, nil
}

func (x *originalReinforcementQuantity) active() bool { return x != nil && x.Phase != "" }

func (x *originalReinforcementQuantity) begin() error {
	q, p := x.Owner, x.Owner.Port
	if x.active() || !p.ShopOpen || p.ShopCommitted || !q.InputPending || q.Returned || q.InputParent+2 != p.ShopSP {
		return errors.New("original reinforcement editor is not waiting")
	}
	if err := q.source(); err != nil {
		return err
	}
	s, err := p.snapshot()
	if err != nil {
		return err
	}
	key := x.UI.key()
	plan, err := originalReinforcementPlanFor(p.Store.Catalog, s.World.Army, key)
	if err != nil {
		return err
	}
	quote, err := s.World.Army.quote(p.Store.Catalog, key)
	if err != nil {
		return err
	}
	if quote.Maximum == 0 || plan.Preflight != 0x55f0 {
		return errors.New("original reinforcement unavailable offer")
	}
	x.Key, x.Unit, x.Token, x.Phase = key, plan.Unit, s.Token, "switch"
	x.Ready, x.EscapeDown, x.EscapeSent, x.Committed = false, false, false, false
	x.Starts++
	x.UI.Active = false
	x.Events = append(x.Events, map[string]any{"event": "begin", "key": key, "token": s.Token})
	return nil
}

func (x *originalReinforcementQuantity) plan(s progressPairSnapshot) (originalRecruitPlan, error) {
	p := x.Owner.Port
	g, row, kind, id, err := parseReinforcementKey(x.Key)
	if err != nil || g != p.ShopGroup || row != p.ShopRow || kind != p.ShopKind || id != x.Unit || s.Token != x.Token || x.Committed {
		return originalRecruitPlan{}, errors.New("original reinforcement binding/token")
	}
	return originalReinforcementPlanFor(p.Store.Catalog, s.World.Army, x.Key)
}

func (x *originalReinforcementQuantity) result(m *dg.Machine, s progressPairSnapshot, count uint16) (uint16, error) {
	q, p := x.Owner, x.Owner.Port
	plan, err := x.plan(s)
	if err != nil {
		return 0, err
	}
	if x.Phase == "switch" {
		if count != 0 || q.ReturnIP != 0x50c9 {
			return 0, errors.New("original reinforcement switch requires original Escape")
		}
		x.Phase = "input"
		x.Events = append(x.Events, map[string]any{"event": "restart-preflight", "ip": 0x5523, "token": s.Token})
		return 0x5523, nil
	}
	if x.Phase != "input" {
		return 0, errors.New("original reinforcement result phase")
	}
	next, err := plan.result(uint32(count), s.World.Army.Gold)
	if err != nil {
		return 0, err
	}
	x.Phase = "closing"
	if next == 0x56ec {
		if x.Committed || s.World.Revision == math.MaxUint64 {
			return 0, errors.New("original reinforcement duplicate/revision")
		}
		updated, err := p.Store.RecruitReinforcement(s.Token, x.Key, uint32(count))
		if err != nil {
			return 0, err
		}
		for i, n := range pairWorldResources(updated.World).words() {
			if n > 30000 {
				return 0, errors.New("original reinforcement native resource bound")
			}
			m.Write16(0x1e880+0x4f2+uint32(i*2), uint16(n))
		}
		p.Current = updated
		x.Token, x.Committed = updated.Token, true
		x.Purchases++
		x.UI.Purchases++
		x.UI.Count = uint32(count)
		// AX zero from 555F makes the original wrapper leave native stock alone.
		next = 0x555f
	}
	x.Events = append(x.Events, map[string]any{"event": "result", "count": count, "next_ip": next, "committed": x.Committed, "token": x.Token})
	return next, nil
}

func (x *originalReinforcementQuantity) advance(g *armyReviewApp) error {
	if x == nil {
		return nil
	}
	if x.EscapeDown {
		if err := encounterGuestKey(g, 1, false); err != nil {
			return err
		}
		x.EscapeDown = false
	} else if x.Phase == "switch" && !x.EscapeSent {
		x.Owner.Engine.ReleaseAll()
		if err := encounterGuestKey(g, 1, true); err != nil {
			return err
		}
		x.EscapeDown = true
		x.EscapeSent = true
	}
	if x.active() && !x.Owner.Port.ShopOpen {
		x.Phase, x.Ready = "", false
	}
	return nil
}

func (x *originalReinforcementQuantity) paint(base *image.RGBA) (*image.RGBA, []armyUIText) {
	if !x.Ready {
		if x.UI.Held == nil {
			panic(&worldArmyPortFault{"original reinforcement missing complete selection frame"})
		}
		return x.UI.Held, x.UI.HeldTexts
	}
	p := x.Owner.Port
	if err := x.Owner.source(); err != nil {
		panic(&worldArmyPortFault{err.Error()})
	}
	s, err := p.snapshot()
	if err != nil || s.Token != x.Token {
		panic(&worldArmyPortFault{"original reinforcement presentation token"})
	}
	f := p.OriginalReview.Fields
	idx, _ := p.Store.Catalog.index()
	u := idx[x.Unit]
	rows := [6]originalReviewRow{{Host: true, Unit: x.Unit, Name: u.Name}}
	if err := f.validate(rows); err != nil {
		panic(&worldArmyPortFault{err.Error()})
	}
	if base == nil || base.Bounds() != image.Rect(0, 0, 1920, 1200) {
		panic("original reinforcement canvas shape")
	}
	out := image.NewRGBA(base.Bounds())
	draw.Draw(out, out.Bounds(), base, base.Bounds().Min, draw.Src)
	uiFill(out, recruitIconCard, color.RGBA{176, 150, 85, 255})
	uiFill(out, recruitIconCard.Inset(3), color.RGBA{7, 36, 26, 255})
	f.icon(out, x.Unit, recruitIconCard.Inset(21))
	// sub_15792 puts the three source lines at y=116/133/150. The numeric
	// prompt at y=167, its original text, digits and blinking cursor stay intact.
	f.Texts = nil
	for i, text := range []string{fmt.Sprintf("這裡住著 %d 名 %s", s.World.Army.Offers[x.Key].Stock, u.Name), fmt.Sprintf("每名月薪 %d", u.Gold), fmt.Sprintf("你有現金 %d", s.World.Army.Gold)} {
		r := image.Rect(48, (116+i*17)*6, 1344, (116+i*17)*6+90)
		uiFill(out, r, color.RGBA{85, 85, 85, 255})
		f.text(out, fmt.Sprintf("reinforcement-original:%d", i), text, r, [3]uint8{255, 241, 181})
	}
	return out, append([]armyUIText(nil), f.Texts...)
}

func installOriginalReinforcementQuantity(ui *reinforcementUI) {
	q := ui.Port.RecruitQuantity
	if q == nil {
		return
	}
	x := &originalReinforcementQuantity{Owner: q, UI: ui}
	q.Reinforcement = x
	swordOnCall(ui.Engine.Oracle, oracle.Far(0x110, 0x4ea6), func(*oracle.Oracle) {
		if x.Phase == "input" && q.InputPending && !q.Returned {
			x.Ready = true
		}
	})
}
