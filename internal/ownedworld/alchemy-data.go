package ownedworld

import (
	"bytes"
	"encoding/binary"
	"errors"
	"math"
)

const alchemyUsesOffset = 1254
const alchemyLearnedOffset = 1316
const alchemyBonusOffset = 1324

type alchemyAward struct {
	Roll       uint16
	Bonus      bool
	UsesBefore uint16
}

func buildAlchemyWorld(before progressPairSnapshot, a alchemyAward) (OwnedWorld, []byte, uint64, error) {
	w := cloneCampWorld(before.World)
	uses, e := alchemyWord(before.Bytes.Native, alchemyUsesOffset)
	learned, x := alchemyWord(before.Bytes.Native, alchemyLearnedOffset)
	bonus, y := alchemyWord(before.Bytes.Native, alchemyBonusOffset)
	if e != nil || x != nil || y != nil || learned != 1 || uses == 0 || uses > 32767 || uses != a.UsesBefore || (bonus == 1) != a.Bonus || a.Roll > 32767 || w.Battle != nil || w.Revision == math.MaxUint64 || w.Army.Gold > 30000 {
		return w, nil, 0, errors.New("alchemy source/uses/world")
	}
	amount := uint64(a.Roll / 260)
	if a.Bonus {
		amount += 40
	}
	w.Army.Gold += amount
	if w.Army.Gold > 30000 {
		w.Army.Gold = 30000
	}
	w.Revision++
	n := bytes.Clone(before.Bytes.Native)
	if e = setAlchemyWord(n, alchemyUsesOffset, uses-1); e != nil {
		return w, nil, 0, e
	}
	return w, n, amount, nil
}

func alchemyWord(n []byte, at int) (uint16, error) {
	if len(n) != 2987 || at < 0 || at+2 > len(n) || at%2 != 0 {
		return 0, errors.New("alchemy word bounds")
	}
	return binary.LittleEndian.Uint16(n[at:]) - uint16(at+3), nil
}
func setAlchemyWord(n []byte, at int, v uint16) error {
	if _, e := alchemyWord(n, at); e != nil {
		return e
	}
	binary.LittleEndian.PutUint16(n[at:], v+uint16(at+3))
	return nil
}
