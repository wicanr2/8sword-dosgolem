//go:build ignore

// 030 DRAFT: real combat controls over the existing Go world/combat contracts.
package main

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

type battleUI struct {
	Catalog                               ArmyCatalog
	Combat                                game.OwnedCombatCatalog
	World                                 OwnedWorld
	Dir, BaseSHA, SavedSHA, Font, Message string
	Source, Target                        int
	Dirty, Locked                         bool
	Events                                []game.OwnedCombatOutcome
	CommitPair                            func(OwnedWorld) (string, string, error)
	ClosePair                             func()
}

// The default research UI keeps its existing storage. A separately compiled
// paired-save prototype supplies the alternative factory.
var battleUIOpener = openBattleUI

func openBattleUI(dir string, c ArmyCatalog, cc game.OwnedCombatCatalog, seed OwnedWorld) (*battleUI, error) {
	base, err := armyUIRead(filepath.Join(dir, "gamedata.ay"), 2987)
	if err != nil || len(base) != 2987 {
		return nil, errors.New("基底進度長度不符")
	}
	if err = os.Mkdir(filepath.Join(dir, ".owned-battle-ui.lock"), 0700); err != nil {
		return nil, errors.New("進度已被開啟，或留有未處理的鎖")
	}
	u := &battleUI{Catalog: c, Combat: cc, Dir: dir, BaseSHA: contentSHA(base), Font: "noto", Dirty: true, Locked: true, Message: "先招募野狼，再進入戰場。"}
	path := filepath.Join(dir, "gamedata.ay.army.json")
	if st, e := os.Lstat(path); e == nil {
		if !st.Mode().IsRegular() {
			err = errors.New("軍隊進度不是一般檔案")
		} else {
			u.World, err = loadWorld(dir, c, cc)
			if err == nil {
				var raw []byte
				raw, err = armyUIRead(path, 1<<20)
				u.SavedSHA = contentSHA(raw)
			}
		}
	} else if os.IsNotExist(e) {
		err = u.persist(seed)
	} else {
		err = e
	}
	if err != nil {
		u.Close()
		return nil, err
	}
	return u, nil
}
func (u *battleUI) Close() {
	if u != nil && u.Locked {
		if u.ClosePair != nil {
			u.ClosePair()
			u.ClosePair = nil
			u.Locked = false
			return
		}
		os.Remove(filepath.Join(u.Dir, ".owned-battle-ui.lock"))
		u.Locked = false
	}
}
func (u *battleUI) persist(next OwnedWorld) error {
	if !u.Locked {
		return errors.New("進度未鎖定")
	}
	if u.CommitPair != nil {
		base, saved, e := u.CommitPair(next)
		if e != nil {
			return e
		}
		u.BaseSHA, u.SavedSHA = base, saved
		u.World, u.Dirty = next, true
		return nil
	}
	base, e := armyUIRead(filepath.Join(u.Dir, "gamedata.ay"), 2987)
	if e != nil || len(base) != 2987 || contentSHA(base) != u.BaseSHA {
		return errors.New("基底進度已改變，請重新開啟")
	}
	path := filepath.Join(u.Dir, "gamedata.ay.army.json")
	if st, e := os.Lstat(path); e == nil && (!st.Mode().IsRegular() || st.Size() > 1<<20) {
		return errors.New("軍隊進度形狀不符")
	} else if e != nil && !os.IsNotExist(e) {
		return e
	}
	if e = saveWorld(u.Dir, u.Catalog, u.Combat, next, u.SavedSHA); e != nil {
		return e
	}
	raw, e := armyUIRead(path, 1<<20)
	if e != nil {
		return e
	}
	u.SavedSHA = contentSHA(raw)
	u.World = next
	u.Dirty = true
	return nil
}
func (u *battleUI) state() (game.OwnedCombatState, bool) {
	if u.World.Battle == nil {
		return game.OwnedCombatState{}, false
	}
	return u.World.Battle.State, true
}
func (u *battleUI) saveState(s game.OwnedCombatState) error {
	next := u.World
	b := *next.Battle
	b.State = s
	next.Battle = &b
	return u.persist(next)
}
func (u *battleUI) kind(side, source int) string {
	s, ok := u.state()
	if !ok || side < 0 || side > 1 || source < 0 || source >= 6 {
		return "normal"
	}
	if u.Combat.Profiles[s.Rows[side][source].Unit].Ranged {
		return "ranged"
	}
	return "normal"
}
func (u *battleUI) playerPlan() (game.OwnedCombatOutcome, error) {
	s, ok := u.state()
	if !ok {
		return game.OwnedCombatOutcome{}, errors.New("尚未開戰")
	}
	return s.Plan(u.Combat, game.OwnedCombatAction{Side: 0, Source: u.Source, Target: u.Target, Kind: u.kind(0, u.Source)})
}
func (u *battleUI) enemyPlan() (game.OwnedCombatOutcome, error) {
	s, ok := u.state()
	if !ok {
		return game.OwnedCombatOutcome{}, errors.New("尚未開戰")
	}
	for i, row := range s.Rows[1] {
		if row.Count == 0 || s.Acted[1][i] {
			continue
		}
		if i >= 3 && !u.Combat.Profiles[row.Unit].Ranged {
			continue
		}
		return s.Choose(u.Combat, 1, i, u.kind(1, i), 0, -1)
	}
	return game.OwnedCombatOutcome{}, errors.New("敵軍已出手，或沒有可用的普通行動")
}
func (u *battleUI) apply(plan game.OwnedCombatOutcome) error {
	s, _ := u.state()
	next, event, e := s.Apply(u.Combat, plan.Action)
	if e != nil {
		return e
	}
	if e = u.saveState(next); e != nil {
		return e
	}
	u.Events = append(u.Events, event)
	who := "我方"
	if event.Action.Side == 1 {
		who = "敵方"
	}
	u.Message = fmt.Sprintf("%s出手，傷害 %d，目標減員 %d。已儲存。", who, event.Damage, event.Loss)
	return nil
}
func (u *battleUI) action(name string) error {
	u.Dirty = true
	switch name {
	case "recruit":
		if u.World.Battle != nil {
			return errors.New("戰鬥中不能招募")
		}
		next := u.World
		a, _, e := next.Army.recruit(u.Catalog, "wolf-camp", 30)
		if e != nil {
			return e
		}
		next.Army = a
		next.Revision++
		if e = u.persist(next); e != nil {
			return e
		}
		u.Message = "已招募野狼30，花費1200。已儲存。"
	case "begin":
		next, e := u.World.begin(u.Catalog, u.Combat, "skeleton-patrol", game.OwnedCombatConfig{Rules: u.World.Army.Rules, Divisors: [2]uint32{5, 5}, Multipliers: [2]uint32{1, 1}})
		if e != nil {
			return e
		}
		if next.Battle.State.Result != "" {
			return errors.New("請先招募存活部隊")
		}
		if e = u.persist(next); e != nil {
			return e
		}
		u.Message = "戰鬥開始。點選我方與敵方部隊後出手。"
	case "attack":
		p, e := u.playerPlan()
		if e != nil {
			return e
		}
		return u.apply(p)
	case "enemy":
		p, e := u.enemyPlan()
		if e != nil {
			return e
		}
		return u.apply(p)
	case "round":
		s, ok := u.state()
		if !ok {
			return errors.New("尚未開戰")
		}
		n, e := s.NextRound(u.Combat)
		if e != nil {
			return e
		}
		if e = u.saveState(n); e != nil {
			return e
		}
		u.Message = "下一輪。雙方可再次出手。"
	case "pass":
		s, ok := u.state()
		if !ok {
			return errors.New("尚未開戰")
		}
		n, e := s.PassRearMelee(u.Combat, 0, u.Source)
		if e != nil {
			return e
		}
		if e = u.saveState(n); e != nil {
			return e
		}
		u.Message = "後排近戰部隊本輪略過。"
	case "settle":
		next, reward, e := u.World.settleVictory(u.Catalog, u.Combat)
		if e != nil {
			return e
		}
		if e = u.persist(next); e != nil {
			return e
		}
		u.Message = fmt.Sprintf("勝利戰果已儲存。金錢增加%d，戰績增加%d。", reward.Gold, reward.Merit)
	default:
		return errors.New("未知的戰鬥操作")
	}
	return nil
}
func (u *battleUI) handle(name string) {
	if e := u.action(name); e != nil {
		u.Message = e.Error()
		u.Dirty = true
	}
}
