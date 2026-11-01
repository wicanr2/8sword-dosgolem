//go:build ignore

// Explicitly separate GUI fixture. Normal monthly-ui never resets the timer.
package main

import (
	"flag"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

var monthlyFixture = flag.Bool("controlled-monthly-boundary", false, "set verified source countdown to one after ordinary Continue")

func init() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		v, err := previous(e, p)
		if err != nil {
			return nil, err
		}
		if *monthlyFixture {
			e.Oracle.WriteU16(oracle.Far(0x1e88, 0x56da), 1)
		}
		return v, nil
	}
}
