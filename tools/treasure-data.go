//go:build ignore

package main

import (
	"bytes"
	"encoding/binary"
	"errors"
	"math"
)

type treasureAward struct {
	Region, Row, Choice int
	Amount              uint16
}

func buildTreasureWorld(before progressPairSnapshot, a treasureAward) (OwnedWorld, []byte, error) {
	w := cloneCampWorld(before.World)
	n, e := treasureAmount(before.Bytes.Native, a.Region, a.Row)
	if e != nil || a.Amount == 0 || n != a.Amount || (a.Choice != 1 && a.Choice != 2) || w.Battle != nil || w.Revision == math.MaxUint64 {
		return w, nil, errors.New("treasure identity/value/world")
	}
	if a.Choice == 1 {
		w.Army.Gold += uint64(a.Amount)
		if w.Army.Gold > 30000 {
			w.Army.Gold = 30000
		}
	} else {
		w.Army.Leadership += uint64(a.Amount / 10)
		if w.Army.Leadership > 30000 {
			w.Army.Leadership = 30000
		}
	}
	w.Revision++
	native := bytes.Clone(before.Bytes.Native)
	if e = writeTreasureAmount(native, a.Region, a.Row, 0); e != nil {
		return w, nil, e
	}
	return w, native, nil
}

func treasureOffset(region, row int) (int, error) {
	if region < 0 || region >= 8 || row < 0 || row >= 10 {
		return 0, errors.New("treasure identity bounds")
	}
	return 1348 + region*20 + row*2, nil
}
func treasureAmount(native []byte, region, row int) (uint16, error) {
	at, e := treasureOffset(region, row)
	if e != nil || len(native) != 2987 {
		return 0, errors.New("treasure progress bounds")
	}
	v := binary.LittleEndian.Uint16(native[at:]) - uint16(at+3)
	if v > 30000 {
		return 0, errors.New("treasure amount domain")
	}
	return v, nil
}
func writeTreasureAmount(native []byte, region, row int, value uint16) error {
	at, e := treasureOffset(region, row)
	if e != nil || len(native) != 2987 || value > 30000 {
		return errors.New("treasure projection bounds")
	}
	binary.LittleEndian.PutUint16(native[at:], value+uint16(at+3))
	return nil
}
