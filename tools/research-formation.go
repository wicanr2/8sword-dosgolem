//go:build ignore

// 030 DRAFT: offline formation proposal, never imported by the game.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
)

type formationUnit struct{ Kind, Count uint16 }
type formationInput struct {
	Name, Label, Route, Side, Provenance string
	Target                               uint16
	Slots                                [6]formationUnit
	Amount, HP                           uint16
}
type formationResult struct {
	Input                   formationInput
	Rate                    uint16
	Eligible                bool
	Amount, Loss, Remaining uint16
}

func originalFormationLoss(amount, hp, count uint16) (uint16, error) {
	if hp == 0 {
		return 0, fmt.Errorf("zero HP")
	}
	encoded := uint16(amount/hp + 1)
	if encoded <= 1 {
		return 0, nil
	}
	if encoded >= count {
		return count, nil
	}
	return encoded - 1, nil
}
func formationProposal(v formationInput, rate uint16) (formationResult, error) {
	r := formationResult{Input: v, Rate: rate, Amount: v.Amount}
	if v.Target >= 6 || rate > 30 || (v.Side != "player" && v.Side != "enemy") || v.HP == 0 {
		return r, fmt.Errorf("invalid proposal input")
	}
	if v.Route != "normal" && v.Route != "ranged" && v.Route != "special" {
		return r, fmt.Errorf("unsupported route")
	}
	u := v.Slots[v.Target]
	if u.Count == 0 {
		return r, nil
	}
	if v.Target < 3 && u.Kind == 1 && v.Route != "special" {
		for slot := 0; slot < 3; slot++ {
			if uint16(slot) != v.Target && v.Slots[slot].Count > 0 {
				r.Eligible = true
			}
		}
	}
	if r.Eligible {
		r.Amount = uint16(uint32(v.Amount) * uint32(100-rate) / 100)
	}
	if v.Route == "special" {
		r.Loss = min(v.Amount, u.Count)
	} else {
		var err error
		r.Loss, err = originalFormationLoss(r.Amount, v.HP, u.Count)
		if err != nil {
			return r, err
		}
	}
	r.Remaining = u.Count - r.Loss
	return r, nil
}
func main() {
	in := flag.String("input", "", "prepared offline input JSON")
	out := flag.String("out", "", "new proposal JSON")
	flag.Parse()
	raw, err := os.ReadFile(*in)
	mustFormation(err)
	var inputs []formationInput
	mustFormation(json.Unmarshal(raw, &inputs))
	results := []formationResult{}
	for _, v := range inputs {
		for _, rate := range []uint16{0, 10, 20, 30} {
			r, err := formationProposal(v, rate)
			mustFormation(err)
			results = append(results, r)
		}
	}
	data, err := json.MarshalIndent(results, "", "  ")
	mustFormation(err)
	f, err := os.OpenFile(*out, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
	mustFormation(err)
	mustFormation(json.NewEncoder(f).Encode(json.RawMessage(data)))
	mustFormation(f.Close())
	fmt.Printf("DRAFT offline proposal: %d cases, %d results\n", len(inputs), len(results))
}
func mustFormation(err error) {
	if err != nil {
		panic(err)
	}
}
