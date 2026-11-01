package ownedworld

import (
	"errors"
	"flag"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

var monthlyEvidence = flag.String("monthly-evidence", "", "optional bounded monthly evidence folder")

func advanceMonthlyUI(g *armyReviewApp) error {
	err := advanceEncounterUI(g)
	if !errors.Is(err, errMonthlyYield) {
		return err
	}
	if monthlyCurrent == nil {
		return errors.New("monthly yield without controller")
	}
	return monthlyCurrent.Complete(flag.Lookup("root").Value.String(), flag.Lookup("input").Value.String(), flag.Lookup("scratch").Value.String(), *monthlyEvidence)
}
func monthlyStatus() map[string]any {
	if monthlyCurrent == nil {
		return map[string]any{"active": false}
	}
	p := monthlyCurrent
	return map[string]any{"active": p.Active, "pending": p.Pending, "committed": p.Committed, "saves": p.Saves, "budget": p.Budget, "events": p.Events}
}
func initializeLayer38() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		v, err := previous(e, p)
		if err != nil {
			return nil, err
		}
		_, err = installMonthlyPort(e, p)
		return v, err
	}
	armyReviewTitle = "神州八劍・軍隊試作・月度交接"
}
