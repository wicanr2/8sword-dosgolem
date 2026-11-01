//go:build ignore

// Only the starting position is controlled; guard troops and input stay native.
package main

import (
	"errors"
	"flag"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

var guardedFixture = flag.Bool("controlled-guard-position", false, "start one cell east of the first existing ordinary guard")

func init() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		v, err := previous(e, p)
		if err != nil {
			return nil, err
		}
		if *guardedFixture {
			o := e.Oracle
			if o.Word(oracle.Far(0x1e88, 0x56d6)) != 0 || o.Word(oracle.Far(0x1e88, 0x8c30)) != 5 || o.Word(oracle.Far(0x1e88, 0x8c32)) != 4 {
				return nil, errors.New("guard position fixture source")
			}
			o.WriteU16(oracle.Far(0x1e88, 0x8e12), 6)
			o.WriteU16(oracle.Far(0x1e88, 0x8e44), 4)
		}
		return v, nil
	}
}
