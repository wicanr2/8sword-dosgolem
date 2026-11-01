// Only UI wiring for the existing verified selectors. No new combat rules.
package ownedworld

import (
	"errors"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"image"
)

var rearButtons = []struct {
	ID, Text string
	Selector int
	Rect     image.Rectangle
}{
	{"rear:0", "定額打擊", 0, image.Rect(710, 190, 1050, 260)},
	{"rear:2", "剋制打擊", 2, image.Rect(1070, 190, 1410, 260)},
	{"rear:5", "比例打擊", 5, image.Rect(1430, 190, 1830, 260)},
}

func rearSpecialSource(s game.OwnedCombatState, c game.OwnedCombatCatalog, side, source int) bool {
	if side < 0 || side > 1 || source < 3 || source > 5 {
		return false
	}
	p := c.Profiles[s.Rows[side][source].Unit]
	return p.NativeKind == 10 || p.NativeKind == 12
}
func rearPlayerPlan(u *battleUI, selector int) (game.OwnedCombatOutcome, error) {
	s, ok := u.state()
	if !ok {
		return game.OwnedCombatOutcome{}, errors.New("尚未開戰")
	}
	return s.Plan(u.Combat, game.OwnedCombatAction{Side: 0, Source: u.Source, Target: u.Target, Kind: "special", Selector: selector})
}
func rearPlayerAction(u *battleUI, name string) error {
	for _, b := range rearButtons {
		if b.ID == name {
			p, e := rearPlayerPlan(u, b.Selector)
			if e != nil {
				return e
			}
			return u.apply(p)
		}
	}
	return errors.New("未知的戰鬥操作")
}
func rearEnemyPlan(u *battleUI) (game.OwnedCombatOutcome, error) {
	s, ok := u.state()
	if !ok {
		return game.OwnedCombatOutcome{}, errors.New("尚未開戰")
	}
	for i, row := range s.Rows[1] {
		if row.Count == 0 || s.Acted[1][i] {
			continue
		}
		if rearSpecialSource(s, u.Combat, 1, i) {
			return s.Choose(u.Combat, 1, i, "special", 0, -1)
		}
		if i >= 3 && !u.Combat.Profiles[row.Unit].Ranged {
			continue
		}
		return s.Choose(u.Combat, 1, i, u.kind(1, i), 0, -1)
	}
	return game.OwnedCombatOutcome{}, errors.New("敵軍已出手，或沒有可用的普通行動")
}
func rearEnemyPass(u *battleUI) (game.OwnedCombatState, error) {
	s, ok := u.state()
	if !ok {
		return s, errors.New("尚未開戰")
	}
	changed := false
	for i := 3; i < 6; i++ {
		row := s.Rows[1][i]
		p := u.Combat.Profiles[row.Unit]
		if row.Count == 0 || s.Acted[1][i] || p.Ranged || rearSpecialSource(s, u.Combat, 1, i) {
			continue
		}
		var e error
		s, e = s.PassRearMelee(u.Combat, 1, i)
		if e != nil {
			return s, e
		}
		changed = true
	}
	if !changed {
		return s, errors.New("敵軍已出手，或沒有可用的普通行動")
	}
	return s, nil
}
func rearEnemyPassAvailable(u *battleUI) bool { _, e := rearEnemyPass(u); return e == nil }
func rearEnemyAction(u *battleUI) error {
	p, e := u.enemyPlan()
	if e == nil {
		return u.apply(p)
	}
	s, x := rearEnemyPass(u)
	if x != nil {
		return e
	}
	if e = u.saveState(s); e != nil {
		return e
	}
	u.Message = "敵方後排略過。已儲存。"
	return nil
}
func paintRearButtons(u *battleUI, p *armyUIPaint) {
	for _, b := range rearButtons {
		_, e := rearPlayerPlan(u, b.Selector)
		p.button(b.ID, b.Text, b.Rect, false, e == nil)
	}
}
