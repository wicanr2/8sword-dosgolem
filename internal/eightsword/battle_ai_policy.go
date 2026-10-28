// 030 READY: bounded target battleAI; no DOS API, RNG, clock or guest writes.
package eightsword

import "fmt"

type battleAIUnit struct{ Kind, Count uint16 }
type battleAIView struct {
	Route                              string
	SourceSlot, OriginalSlot, Selector uint16
	Friendly, Enemy                    [6]battleAIUnit
	FriendlySlots, EnemySlots          [6]uint16
	ShiftedSlotZero                    uint16
	Factors                            [52]uint16
	Divisor                            uint16
}
type battleAICandidate struct {
	Slot, Unit, Count, Amount, Loss uint16
	Eliminates                      bool
}
type battleAIDecision struct {
	SourceSlot, OriginalSlot, SuggestedSlot uint16
	Route                                   string
	Selector                                uint16
	OriginalEligible                        bool
	Candidates                              []battleAICandidate
	Reason                                  string
}

func battleAIPredict(v battleAIView, slot uint16) (battleAICandidate, error) {
	if slot >= 6 {
		return battleAICandidate{}, fmt.Errorf("target slot out of range")
	}
	unit := v.FriendlySlots[slot]
	u := v.Friendly[unit]
	source := v.Enemy[v.EnemySlots[v.SourceSlot]]
	c := battleAICandidate{Slot: slot, Unit: unit, Count: u.Count}
	if u.Count == 0 {
		return c, nil
	}
	switch v.Route {
	case "normal", "ranged":
		if source.Kind >= 26 || u.Kind >= 26 {
			return c, fmt.Errorf("factor index")
		}
		divisor, hp := uint16(v.Divisor+5), v.Factors[u.Kind*2+1]
		if divisor == 0 || hp == 0 {
			return c, fmt.Errorf("zero divisor")
		}
		c.Amount = uint16(uint32(v.Factors[source.Kind*2])*uint32(source.Count)) / divisor
		encoded := uint16(c.Amount/hp + 1)
		if encoded > 1 {
			c.Loss = encoded - 1
			if encoded >= u.Count {
				c.Loss = u.Count
			}
		}
	case "special":
		switch v.Selector {
		case 0:
			c.Amount = 5
			if source.Kind == 12 {
				c.Amount = 2
			}
		case 2:
			c.Amount = 15
			if source.Kind == 12 {
				c.Amount = 6
			}
		case 5:
			divisor := uint16(2)
			if source.Kind == 12 {
				divisor = 3
			}
			c.Amount = u.Count/divisor + 1
		default:
			return c, fmt.Errorf("unsupported special selector")
		}
		c.Loss = min(c.Amount, u.Count)
	default:
		return c, fmt.Errorf("unsupported route")
	}
	c.Eliminates = c.Loss == c.Count
	return c, nil
}
func battleAIBetter(a, b battleAICandidate) bool {
	if a.Eliminates != b.Eliminates {
		return a.Eliminates
	}
	return uint64(a.Loss)*uint64(b.Count) > uint64(b.Loss)*uint64(a.Count)
}
func evaluateBattleAI(v battleAIView) (battleAIDecision, error) {
	d := battleAIDecision{SourceSlot: v.SourceSlot, OriginalSlot: v.OriginalSlot, SuggestedSlot: v.OriginalSlot, Route: v.Route, Selector: v.Selector, Candidates: []battleAICandidate{}, Reason: "先全滅，再比較減員比例；同分保留原目標，原目標無效時依陣位排序"}
	if v.SourceSlot >= 6 || v.OriginalSlot >= 6 {
		return d, fmt.Errorf("slot out of range")
	}
	for _, slots := range [][6]uint16{v.FriendlySlots, v.EnemySlots} {
		for _, unit := range slots {
			if unit >= 6 {
				return d, fmt.Errorf("unit mapping out of range")
			}
		}
	}
	// Dead placeholders may repeat; a living unit cannot occupy two slots.
	for side, slots := range [][6]uint16{v.FriendlySlots, v.EnemySlots} {
		seen := [6]bool{}
		units := v.Friendly
		if side == 1 {
			units = v.Enemy
		}
		for _, id := range slots {
			if units[id].Count > 0 {
				if seen[id] {
					return d, fmt.Errorf("duplicate live mapping")
				}
				seen[id] = true
			}
		}
	}
	source := v.Enemy[v.EnemySlots[v.SourceSlot]]
	if source.Count == 0 {
		return d, fmt.Errorf("empty source")
	}
	ranged := source.Kind == 3 || source.Kind == 24
	if v.Route == "normal" && (v.SourceSlot >= 3 || ranged) {
		return d, fmt.Errorf("normal route mismatch")
	}
	if v.Route == "ranged" && !ranged {
		return d, fmt.Errorf("ranged route mismatch")
	}
	if v.Route == "special" && (v.SourceSlot < 3 || (source.Kind != 10 && source.Kind != 12) || (v.Selector != 0 && v.Selector != 2 && v.Selector != 5)) {
		return d, fmt.Errorf("special route outside sampled contract")
	}
	first, last := uint16(0), uint16(6)
	locked := false
	if v.Route == "normal" {
		last = 3
		alive := false
		for s := uint16(0); s < 3; s++ {
			if v.Friendly[v.FriendlySlots[s]].Count > 0 {
				alive = true
			}
		}
		if !alive {
			first, last = 3, 6
		} else if v.Friendly[v.FriendlySlots[v.SourceSlot]].Count > 0 {
			first, last = v.SourceSlot, v.SourceSlot+1
			locked = true
		}
	}
	for slot := first; slot < last; slot++ {
		u := v.Friendly[v.FriendlySlots[slot]]
		if u.Count == 0 {
			continue
		}
		if v.Route == "special" {
			if v.Selector == 2 && (u.Kind < 6 || u.Kind > 15) {
				continue
			}
			if v.Selector == 5 {
				guard := v.ShiftedSlotZero
				if slot > 0 {
					guard = v.FriendlySlots[slot-1]
				}
				if guard >= 6 {
					return d, fmt.Errorf("shifted mapping out of range")
				}
				if v.Friendly[guard].Count == 0 {
					continue
				}
			}
		}
		c, e := battleAIPredict(v, slot)
		if e != nil {
			return d, e
		}
		d.Candidates = append(d.Candidates, c)
	}
	if len(d.Candidates) == 0 {
		return d, errBattleAINoTarget
	}
	best := d.Candidates[0]
	for _, c := range d.Candidates {
		if c.Slot == v.OriginalSlot {
			best = c
			d.OriginalEligible = true
		}
	}
	if !d.OriginalEligible && !(v.Route == "special" && v.Selector == 5) {
		return d, fmt.Errorf("original target contradicts supported legality")
	}
	for _, c := range d.Candidates {
		if battleAIBetter(c, best) {
			best = c
		}
	}
	d.SuggestedSlot = best.Slot
	if locked {
		d.Reason = "原版普通前排鎖定正對陣位，保留該目標"
	}
	return d, nil
}
