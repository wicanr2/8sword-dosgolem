package ownedworld

import (
	"errors"
	"flag"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

var treasureEvidence = flag.String("treasure-evidence", "", "optional chest evidence directory")

func advanceTreasureUI(g *armyReviewApp) error {
	e := advanceMonthlyUI(g)
	if !errors.Is(e, errTreasureYield) {
		return e
	}
	if treasureCurrent == nil {
		return errors.New("treasure yield without controller")
	}
	return treasureCurrent.Complete(flag.Lookup("root").Value.String(), flag.Lookup("input").Value.String(), flag.Lookup("scratch").Value.String(), *treasureEvidence)
}
func treasureStatus() map[string]any {
	if treasureCurrent == nil {
		return map[string]any{"active": false}
	}
	p := treasureCurrent
	values := [80]uint16{}
	for i := range values {
		values[i] = p.Engine.Oracle.Word(oracle.Far(0x1e88, uint16(0x4490+i*2)))
	}
	return map[string]any{"active": p.Active, "waiting": p.Waiting, "values": values, "pending": p.Pending, "committed": p.Committed, "awards": p.Awards, "opens": p.Opens, "closes": p.Closes, "award": p.Award, "events": p.Events}
}
func initializeLayer44() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		v, x := previous(e, p)
		if x != nil {
			return nil, x
		}
		_, x = installTreasurePort(e, p)
		return v, x
	}
	armyReviewTitle = "神州八劍・軍隊試作・寶箱資源"
}
