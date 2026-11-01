//go:build ignore

package main

import (
	"bytes"
	"errors"
	"fmt"
	"math"
)

const summonUsesOffset = 1256
const summonBonusOffset = 1328

type summonAward struct {
	Roll       uint16
	Bonus      bool
	UsesBefore uint16
}

type summonResult struct {
	Kind   uint16
	Count  uint32
	Slot   int
	Joined bool
}

func summonPayload(rank uint32, a summonAward) (summonResult, error) {
	r := summonResult{Slot: -1}
	if rank < 1 || rank > 5 || a.Roll > 32767 {
		return r, errors.New("summon rank/roll")
	}
	r.Kind = uint16(uint32(a.Roll/6600)*5 + rank)
	r.Count = 24 - rank*4
	if a.Bonus {
		r.Count = r.Count * 3 / 2
	}
	return r, nil
}

func buildSummonWorld(before progressPairSnapshot, c ArmyCatalog, a summonAward) (OwnedWorld, []byte, summonResult, error) {
	w := cloneCampWorld(before.World)
	result, e := summonPayload(w.Progress.Rank, a)
	if e != nil {
		return w, nil, result, e
	}
	uses, x := alchemyWord(before.Bytes.Native, summonUsesOffset)
	access, y := alchemyWord(before.Bytes.Native, alchemyLearnedOffset)
	bonus, z := alchemyWord(before.Bytes.Native, summonBonusOffset)
	if x != nil || y != nil || z != nil || access != 1 || uses == 0 || uses > 32767 || uses != a.UsesBefore || (bonus == 1) != a.Bonus || w.Battle != nil || w.Revision == math.MaxUint64 {
		return w, nil, result, errors.New("summon source/uses/world")
	}
	id := fmt.Sprintf("native:%02d", result.Kind)
	idx, e := c.index()
	if e != nil {
		return w, nil, result, e
	}
	if u, ok := idx[id]; !ok || u.NativeKind != result.Kind {
		return w, nil, result, errors.New("summon catalog identity")
	}
	for i, s := range w.Army.Slots {
		if s.Unit == id {
			result.Slot = i
			break
		}
	}
	if result.Slot < 0 {
		for i, s := range w.Army.Slots {
			if s.Unit == "" {
				result.Slot = i
				break
			}
		}
	}
	if result.Slot >= 0 {
		s := &w.Army.Slots[result.Slot]
		if s.Count > math.MaxUint32-result.Count {
			return w, nil, result, errors.New("summon stack overflow")
		}
		s.Unit = id
		s.Count += result.Count
		result.Joined = true
	}
	if e = w.Army.validate(c); e != nil {
		return w, nil, result, e
	}
	w.Revision++
	n := bytes.Clone(before.Bytes.Native)
	if e = setAlchemyWord(n, summonUsesOffset, uses-1); e != nil {
		return w, nil, result, e
	}
	return w, n, result, nil
}
