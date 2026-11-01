//go:build ignore

// Explicit GUI position fixture, no event, choice, reward or IP injection.
package main

import (
	"errors"
	"flag"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

var treasureFixture = flag.Bool("controlled-treasure-position", false, "place initial hero east of first existing chest after Continue")

func init() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		v, x := previous(e, p)
		if x != nil {
			return nil, x
		}
		if *treasureFixture {
			o := e.Oracle
			g := o.Word(oracle.Far(0x1e88, 0x56d6))
			cx, cy := o.Word(oracle.Far(0x1e88, 0x8c60)), o.Word(oracle.Far(0x1e88, 0x8c62))
			if g != 0 || cx != 23 || cy != 8 || o.Word(oracle.Far(0x1e88, 0x4490)) != 50 {
				return nil, errors.New("treasure fixture source changed")
			}
			o.WriteU16(oracle.Far(0x1e88, 0x8e12), cx+1)
			o.WriteU16(oracle.Far(0x1e88, 0x8e44), cy)
		}
		return v, nil
	}
}
