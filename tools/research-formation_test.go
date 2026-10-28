package main

import "testing"

func TestFormationBoundariesAndSymmetry(t *testing.T) {
	v := formationInput{Side: "player", Route: "normal", Amount: 400, HP: 25, Slots: [6]formationUnit{{1, 31}, {21, 69}}}
	before := v
	got, err := formationProposal(v, 20)
	if err != nil || !got.Eligible || got.Amount != 320 || got.Loss != 12 || got.Remaining != 19 || v != before {
		t.Fatal(got, err)
	}
	v.Side = "enemy"
	other, err := formationProposal(v, 20)
	if err != nil || got.Amount != other.Amount || got.Loss != other.Loss {
		t.Fatal("side asymmetry", other, err)
	}
	for _, count := range []uint16{0, 1, 2, 31, 65535} {
		v.Slots[0].Count = count
		for amount := uint32(0); amount <= 65535; amount++ {
			v.Amount = uint16(amount)
			last := uint16(65535)
			for _, rate := range []uint16{0, 10, 20, 30} {
				r, e := formationProposal(v, rate)
				if e != nil || r.Loss > count || r.Remaining+r.Loss != count || r.Loss > last {
					t.Fatal("bounds", count, amount, rate, r, e)
				}
				last = r.Loss
			}
		}
	}
}
func TestFormationEligibilityAndOriginalThreshold(t *testing.T) {
	v := formationInput{Side: "player", Route: "normal", Amount: 400, HP: 25, Slots: [6]formationUnit{{1, 31}, {21, 69}}}
	for _, kind := range []string{"alone", "rear-only", "dead-support", "rear-target", "other-kind", "special", "two-supports"} {
		w := v
		switch kind {
		case "alone", "dead-support":
			w.Slots[1].Count = 0
		case "rear-only":
			w.Slots[3] = w.Slots[1]
			w.Slots[1].Count = 0
		case "rear-target":
			w.Target = 3
			w.Slots[3] = w.Slots[0]
		case "other-kind":
			w.Slots[0].Kind = 2
		case "special":
			w.Route = "special"
			w.Amount = 5
		case "two-supports":
			w.Slots[2] = formationUnit{2, 10}
		}
		r, e := formationProposal(w, 20)
		if e != nil {
			t.Fatal(e)
		}
		if r.Eligible != (kind == "two-supports") {
			t.Fatal(kind, r)
		}
		if kind == "two-supports" && r.Amount != 320 {
			t.Fatal("stacked mitigation", r)
		}
	}
	for _, v := range []struct{ a, h, c, w uint16 }{{0, 25, 31, 0}, {24, 25, 31, 0}, {25, 25, 31, 1}, {25, 25, 2, 2}, {65535, 1, 31, 0}} {
		got, e := originalFormationLoss(v.a, v.h, v.c)
		if e != nil || got != v.w {
			t.Fatal(v, got, e)
		}
	}
	if _, e := formationProposal(v, 31); e == nil {
		t.Fatal("invalid rate accepted")
	}
	v.Target = 6
	if _, e := formationProposal(v, 20); e == nil {
		t.Fatal("invalid slot accepted")
	}
}
