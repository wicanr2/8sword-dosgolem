package ownedworld

import (
	"errors"
	"flag"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

var summonEvidence = flag.String("summon-evidence", "", "optional bounded cast evidence")

func advanceSummonUI(g *armyReviewApp) error {
	e := advanceAlchemyUI(g)
	if !errors.Is(e, errSummonYield) {
		return e
	}
	if summonCurrent == nil {
		return errors.New("summon yield without controller")
	}
	return summonCurrent.Complete(flag.Lookup("root").Value.String(), flag.Lookup("input").Value.String(), flag.Lookup("scratch").Value.String(), *summonEvidence)
}
func summonStatus() map[string]any {
	if summonCurrent == nil {
		return map[string]any{"active": false}
	}
	p := summonCurrent
	return map[string]any{"active": p.Active, "waiting": p.Waiting, "pending": p.Pending, "committed": p.Committed, "casts": p.Casts, "result": p.Result, "award": p.Award, "uses": p.Engine.Oracle.Word(oracle.Far(0x1e88, 0x2b2c)), "cue_active": p.Engine.SpellCueStatus().Active}
}
func initializeLayer54() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		v, x := previous(e, p)
		if x != nil {
			return nil, x
		}
		_, x = installSummonPort(e, p)
		return v, x
	}
	armyReviewTitle = "神州八劍・軍隊試作・召兵術"
}
