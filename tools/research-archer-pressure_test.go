package main

import (
	"testing"
)

func baseScenario() scenario {
	return scenario{ID: "test", Side: "enemy", Route: "ranged", SourceKind: 3, SourceSlot: 0, SourceCount: 50, Front: [3]uint16{31, 0, 0}, TargetKind: 1, TargetSlot: 0, TargetCount: 31, HP: 25, RawAmount: 400}
}
func TestCandidatePressureAndThresholds(t *testing.T) {
	s := baseScenario()
	for i, want := range []uint16{16, 16, 12, 8} {
		r, e := calculate(s, modes[i])
		if e != nil || r.Loss != want {
			t.Fatal(r, e)
		}
	}
	s.Front[1] = 50
	r, e := calculate(s, modes[2])
	if e != nil || r.AfterPressure != 300 || r.Amount != 240 || r.Loss != 9 {
		t.Fatal(r, e)
	}
	s = baseScenario()
	s.TargetCount = 2
	s.Front[0] = 2
	s.RawAmount = 25
	r, e = calculate(s, modes[0])
	if e != nil || r.Loss != 2 {
		t.Fatal(r, e)
	}
	r, e = calculate(s, modes[2])
	if e != nil || r.Loss != 0 {
		t.Fatal(r, e)
	}
}
func TestCandidateBoundariesAndSymmetry(t *testing.T) {
	base := baseScenario()
	for _, edit := range []func(*scenario){func(s *scenario) { s.SourceSlot = 3 }, func(s *scenario) { s.Front[0] = 0; s.TargetSlot = 1; s.Front[1] = 31 }, func(s *scenario) { s.SourceKind = 24 }, func(s *scenario) { s.Route = "special"; s.RawAmount = 2 }} {
		s := base
		edit(&s)
		before := s
		a, e := calculate(s, modes[0])
		b, e2 := calculate(s, modes[2])
		if e != nil || e2 != nil || a.Loss != b.Loss || b.PressureApplied || s != before {
			t.Fatal(s, a, b, e, e2)
		}
	}
	a, e := calculate(base, modes[2])
	base.Side = "player"
	b, e2 := calculate(base, modes[2])
	if e != nil || e2 != nil || a != b {
		t.Fatal("side asymmetry")
	}
	base.Front = [3]uint16{31, 50, 50}
	a, e = calculate(base, modes[2])
	if e != nil || a.AfterPressure != 300 {
		t.Fatal("stacked pressure")
	}
	base.RawAmount = 7
	base.HP = 1
	a, e = calculate(base, modes[2])
	if e != nil || a.AfterPressure != 5 || a.Amount != 4 {
		t.Fatal("rounding order", a, e)
	}
	for _, edit := range []func(*scenario){func(s *scenario) { s.SourceSlot = 6 }, func(s *scenario) { s.SourceCount = 0 }, func(s *scenario) { s.HP = 0 }, func(s *scenario) { s.TargetKind = 26 }, func(s *scenario) { s.Route = "unknown" }} {
		s := base
		edit(&s)
		if _, e := calculate(s, modes[2]); e == nil {
			t.Fatal("invalid candidate accepted")
		}
	}
	if _, e := calculate(base, mode{Pressure: 30}); e == nil {
		t.Fatal("unknown percentage accepted")
	}
}
