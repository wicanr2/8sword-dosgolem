//go:build ignore

package main

import "math"

func wideMonthlyRuleChecks(c ArmyCatalog) []map[string]any {
	cases := []struct {
		Name         string
		Gold, Income uint64
		Count        uint32
		After, Due   uint64
		Disband      bool
	}{
		{"word-boundary-32767", 30000, 2767, 819, 7, 32760, false},
		{"above-word-paid", 30000, 10000, 999, 40, 39960, false},
		{"above-word-exact", 30000, 10000, 1000, 0, 40000, false},
		{"above-word-short", 30000, 9999, 1000, 30000, 40000, true},
		{"income-sum-60000", 30000, 30000, 1, 30000, 40, false},
		{"max-uint32-stack", 500, 100, math.MaxUint32, 600, uint64(math.MaxUint32) * 40, true},
	}
	rows := []map[string]any{}
	for _, tc := range cases {
		a := OwnedArmy{Gold: tc.Gold, Leadership: math.MaxUint64, Rules: "tactics", Offers: map[string]ArmyOffer{}, Slots: [6]ArmyStack{{"openkb:wolf", tc.Count}}}
		b, e := planMonthlyBudget(c, a, tc.Income)
		if e != nil || b.After != tc.After || b.Due != tc.Due || b.Disbanded != tc.Disband {
			panic(tc.Name)
		}
		rows = append(rows, map[string]any{"name": tc.Name, "budget": b})
	}
	a := OwnedArmy{Gold: 30001, Leadership: math.MaxUint64, Rules: "tactics", Offers: map[string]ArmyOffer{}}
	if _, e := planMonthlyBudget(c, a, 0); e == nil {
		panic("wide report expanded native resources")
	}
	synthetic := c
	synthetic.Profiles = append([]UnitProfile{}, c.Profiles...)
	for i := range synthetic.Profiles {
		synthetic.Profiles[i].Gold = 1000000000
		synthetic.Profiles[i].Command = 1
	}
	a.Gold = 0
	for i := range a.Slots {
		a.Slots[i] = ArmyStack{synthetic.Profiles[i].ID, math.MaxUint32}
	}
	if _, e := planMonthlyBudget(synthetic, a, 0); e == nil {
		panic("uint64 sum overflow")
	}
	return rows
}
