//go:build ignore

package main

import (
	"errors"
	"flag"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

var alchemyEvidence = flag.String("alchemy-evidence", "", "optional bounded cast evidence")

func advanceAlchemyUI(g *armyReviewApp) error {
	e := advanceTreasureUI(g)
	if !errors.Is(e, errAlchemyYield) {
		return e
	}
	if alchemyCurrent == nil {
		return errors.New("alchemy yield without controller")
	}
	return alchemyCurrent.Complete(flag.Lookup("root").Value.String(), flag.Lookup("input").Value.String(), flag.Lookup("scratch").Value.String(), *alchemyEvidence)
}
func alchemyStatus() map[string]any {
	if alchemyCurrent == nil {
		return map[string]any{"active": false}
	}
	p := alchemyCurrent
	return map[string]any{"active": p.Active, "waiting": p.Waiting, "pending": p.Pending, "committed": p.Committed, "casts": p.Casts, "menu_visits": p.MenuVisits, "menu_cursor": p.MenuCursor, "amount": p.Amount, "award": p.Award, "uses": p.Engine.Oracle.Word(oracle.Far(0x1e88, 0x2b2a)), "cue_active": p.Engine.SpellCueStatus().Active}
}
func init() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		v, x := previous(e, p)
		if x != nil {
			return nil, x
		}
		_, x = installAlchemyPort(e, p)
		return v, x
	}
	armyReviewTitle = "神州八劍・軍隊試作・煉金術"
}
