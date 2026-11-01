//go:build ignore

// Added only to the explicit GUI fixture. The normal binary has no injection.
package main

import (
	"errors"
	"flag"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

var rearEnemyFixture = flag.Bool("controlled-rear-enemy", false, "explicit enemy rows fixture")

func init() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		old, x := previous(e, p)
		if x != nil || !*rearEnemyFixture {
			return old, x
		}
		done := false
		e.Oracle.OnCall(oracle.Far(0x110, 0x36b4), func(o *oracle.Oracle) {
			if done {
				return
			}
			if runtimeEnemyCurrent == nil || runtimeEnemyCurrent.Stage != "generating" || o.Regs().DS != 0x1e88 {
				panic(&worldArmyPortFault{"rear fixture phase"})
			}
			rows := [12]uint16{6, 200, 0, 0, 0, 0, 12, 20, 0, 0, 2, 5}
			for i, n := range rows {
				o.WriteU16(oracle.Far(0x1e88, 0x5700+uint16(i*2)), n)
			}
			done = true
			encounterCurrent.Events = append(encounterCurrent.Events, map[string]any{"command": "controlled-rear-enemy", "rows": rows, "no_native_player_write": true})
		})
		if encounterCurrent == nil {
			return nil, errors.New("rear fixture missing encounter")
		}
		return old, nil
	}
}
