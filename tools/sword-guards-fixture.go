//go:build ignore

package main

import (
	"errors"
	"flag"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

var swordFixture = flag.String("controlled-sword-position", "", "boss or final starting position only")

func init() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		v, err := previous(e, p)
		if err != nil {
			return nil, err
		}
		if *swordFixture != "" {
			o := e.Oracle
			if o.Word(oracle.Far(0x1e88, 0x56d6)) != 0 {
				return nil, errors.New("sword position source")
			}
			x, y := uint16(49), uint16(5)
			if *swordFixture == "final" {
				x, y = 59, 52
			} else if *swordFixture != "boss" {
				return nil, errors.New("position mode")
			}
			o.WriteU16(oracle.Far(0x1e88, 0x8e12), x)
			o.WriteU16(oracle.Far(0x1e88, 0x8e44), y)
		}
		return v, nil
	}
}
