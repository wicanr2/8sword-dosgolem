//go:build ignore

// Bounded monthly rules for the isolated Go world. No guest indices for new units.
package main

import (
	"bytes"
	"encoding/binary"
	"errors"
	"math"
)

type monthlyBudget struct {
	Before, Income, Due, Charged, After uint64
	Disbanded                           bool
}

func planMonthlyBudget(c ArmyCatalog, a OwnedArmy, income uint64) (monthlyBudget, error) {
	v := monthlyBudget{Before: a.Gold, Income: income}
	if e := a.validate(c); e != nil {
		return v, e
	}
	idx, _ := c.index()
	for _, row := range a.Slots {
		if row.Count == 0 {
			continue
		}
		fee := idx[row.Unit].Gold
		if fee > math.MaxUint64/uint64(row.Count) || v.Due > math.MaxUint64-fee*uint64(row.Count) {
			return v, errors.New("monthly expense overflow")
		}
		v.Due += fee * uint64(row.Count)
	}
	// This first source-UI slice never wraps an expense into the native signed
	// word field. Larger budgets need an explicitly wider presentation contract.
	if a.Gold > 30000 || income > 30000 || v.Due > 32767 || a.Gold+income > 32767 {
		return v, errors.New("monthly budget exceeds admitted signed-word UI domain")
	}
	v.Charged = v.Due
	total := a.Gold + income
	if v.Due > total {
		v.Disbanded = true
		v.Charged = 0
		v.After = total
	} else {
		v.After = total - v.Due
	}
	if v.After > 30000 {
		v.After = 30000
	}
	return v, nil
}
func monthlyCaps(pam []byte) ([120]uint16, error) {
	var caps [120]uint16
	code, e := worldArmyCode(pam)
	if e != nil {
		return caps, e
	}
	for g := 0; g < 5; g++ {
		for row := 0; row < 24; row++ {
			at := 0x1d780 + 0x3a56 + g*240 + row*10
			if at+2 > len(code) {
				return caps, errors.New("monthly cap source")
			}
			v := binary.LittleEndian.Uint16(code[at:])
			if v > 30000 {
				return caps, errors.New("monthly cap domain")
			}
			caps[g*24+row] = v
		}
	}
	return caps, nil
}
func refillMonthlyCamps(native, pam []byte) ([]byte, error) {
	caps, e := monthlyCaps(pam)
	if e != nil {
		return nil, e
	}
	out := bytes.Clone(native)
	for g := 0; g < 5; g++ {
		for row := 0; row < 24; row++ {
			rec, e := decodeCampRecord(native, g, row)
			if e != nil {
				return nil, e
			}
			if rec.Words[3] == 0 {
				continue
			}
			stock := uint32(rec.Words[4])
			add := stock / 10
			if add < 10 {
				add = 10
			}
			value := stock + add
			if value > 32767 {
				return nil, errors.New("monthly stock addition outside source domain")
			}
			if value > uint32(caps[g*24+row]) {
				value = uint32(caps[g*24+row])
			}
			at := campOffset(g, row, 4)
			binary.LittleEndian.PutUint16(out[at:], uint16(value)+uint16(at+3))
		}
	}
	return out, nil
}
func buildMonthlyWorld(before progressPairSnapshot, c ArmyCatalog, pam []byte) (OwnedWorld, monthlyBudget, []byte, error) {
	w := cloneCampWorld(before.World)
	budget, e := planMonthlyBudget(c, w.Army, w.Progress.Legacy04F6)
	if e != nil {
		return w, budget, nil, e
	}
	if w.Battle != nil || w.Revision == math.MaxUint64 {
		return w, budget, nil, errors.New("monthly pending battle/revision")
	}
	refreshed, e := refillMonthlyCamps(before.Bytes.Native, pam)
	if e != nil {
		return w, budget, nil, e
	}
	offers, e := campOffers(w.Army)
	if e != nil {
		return w, budget, nil, e
	}
	for key, offer := range offers {
		g, row, _ := parseCampKey(key)
		rec, e := decodeCampRecord(refreshed, g, row)
		if e != nil || rec.unit() != offer.Unit {
			return w, budget, nil, errors.New("monthly camp identity changed")
		}
		offer.Stock = uint32(rec.Words[4])
		w.Army.Offers[key] = offer
	}
	w.Army.Gold = budget.After
	if budget.Disbanded {
		w.Army.Slots = [6]ArmyStack{}
	}
	w.Revision++
	return w, budget, refreshed, nil
}
