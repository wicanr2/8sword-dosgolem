package eightsword

import (
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func battleAIFixture(t *testing.T, name string) battleAIView {
	t.Helper()
	root := os.Getenv("EIGHTSWORD_POLICY_TEST_BATCH")
	if root == "" {
		t.Skip("需要已驗候選資料")
	}
	dir := "ai-policy-r1"
	if name == "special5-empty-original" {
		dir = "ai-policy-extra-r2"
	}
	raw, e := os.ReadFile(filepath.Join(root, dir, name, "shadow/trace.json"))
	if e != nil {
		t.Fatal(e)
	}
	var trace struct{ View battleAIView }
	if e = json.Unmarshal(raw, &trace); e != nil {
		t.Fatal(e)
	}
	return trace.View
}
func TestBattleAIRealCandidateSets(t *testing.T) {
	fixtures := []struct {
		name   string
		slots  []uint16
		chosen uint16
	}{
		{"normal-locked", []uint16{0}, 0}, {"normal-choice", []uint16{0, 1}, 0},
		{"normal-rear-only", []uint16{3, 4}, 3}, {"front-ranged-mixed", []uint16{0, 3}, 0},
		{"rear-ranged-mixed", []uint16{0, 3}, 0}, {"special0-choice", []uint16{0, 1}, 0},
		{"special2-choice", []uint16{0, 1}, 0}, {"special5-empty-original", []uint16{0, 1}, 0},
	}
	for _, f := range fixtures {
		t.Run(f.name, func(t *testing.T) {
			v := battleAIFixture(t, f.name)
			copy := v
			d, e := evaluateBattleAI(v)
			if e != nil {
				t.Fatal(e)
			}
			slots := []uint16{}
			for _, c := range d.Candidates {
				slots = append(slots, c.Slot)
			}
			if !reflect.DeepEqual(slots, f.slots) || d.SuggestedSlot != f.chosen {
				t.Fatalf("unexpected candidates or choice: %+v", d)
			}
			if v != copy {
				t.Fatal("view mutated")
			}
		})
	}
}
func TestBattleAIRejectsUnsafeViews(t *testing.T) {
	base := battleAIFixture(t, "front-ranged-mixed")
	cases := []struct {
		name string
		edit func(*battleAIView)
	}{
		{"source-slot", func(v *battleAIView) { v.SourceSlot = 6 }},
		{"original-slot", func(v *battleAIView) { v.OriginalSlot = 6 }},
		{"mapping-range", func(v *battleAIView) { v.FriendlySlots[0] = 6 }},
		{"duplicate-live", func(v *battleAIView) { v.FriendlySlots[1] = v.FriendlySlots[0] }},
		{"empty-source", func(v *battleAIView) { v.Enemy[v.EnemySlots[v.SourceSlot]].Count = 0 }},
		{"route", func(v *battleAIView) { v.Route = "unknown" }},
		{"ranged-kind", func(v *battleAIView) { v.Enemy[v.EnemySlots[v.SourceSlot]].Kind = 6 }},
		{"zero-divisor", func(v *battleAIView) { v.Divisor = 65531 }},
		{"zero-target-factor", func(v *battleAIView) { v.Factors[v.Friendly[0].Kind*2+1] = 0 }},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			v := base
			c.edit(&v)
			copy := v
			if _, e := evaluateBattleAI(v); e == nil {
				t.Fatal("unsafe view accepted")
			}
			if v != copy {
				t.Fatal("rejected input mutated")
			}
		})
	}
	for _, selector := range []uint16{1, 3, 4, 6, 7, 65535} {
		v := battleAIFixture(t, "special2-choice")
		v.Selector = selector
		if _, e := evaluateBattleAI(v); e == nil {
			t.Fatalf("unsupported selector %d accepted", selector)
		}
	}
	v := battleAIFixture(t, "special2-choice")
	v.Friendly[0].Kind = 5
	v.Friendly[1].Kind = 16
	if _, e := evaluateBattleAI(v); e == nil {
		t.Fatal("ineligible type set accepted")
	}
}
func TestBattleAIStableTieRetainsOriginal(t *testing.T) {
	v := battleAIFixture(t, "front-ranged-mixed")
	v.Friendly[1] = v.Friendly[0]
	v.OriginalSlot = 3
	d, e := evaluateBattleAI(v)
	if e != nil {
		t.Fatal(e)
	}
	if d.SuggestedSlot != 3 {
		t.Fatal("equal score changed original target")
	}
}

func TestBattleAIFormationEstimate(t *testing.T) {
	v := battleAIFixture(t, "front-ranged-mixed")
	v.FriendlySlots = [6]uint16{0, 1, 5, 5, 5, 5}
	v.Friendly[0] = battleAIUnit{1, 15}
	v.Friendly[1] = battleAIUnit{21, 15}
	v.OriginalSlot = 0
	old, err := evaluateBattleAI(v)
	if err != nil || old.SuggestedSlot != 0 || old.Candidates[0].Loss != 15 {
		t.Fatal(old, err)
	}
	v.Formation = true
	before := v
	d, err := evaluateBattleAI(v)
	if err != nil || d.SuggestedSlot != 1 || !d.Formation || d.Candidates[0].Amount != 320 || d.Candidates[0].Loss != 12 || d.Candidates[1].Loss != 13 || v != before {
		t.Fatal(d, err)
	}
	v.FriendlySlots[2] = 2
	v.Friendly[2] = battleAIUnit{21, 100}
	d, err = evaluateBattleAI(v)
	if err != nil || d.Candidates[0].Amount != 320 {
		t.Fatal("formation stacked", d, err)
	}
	for _, rear := range []bool{false, true} {
		x := before
		if rear {
			x.FriendlySlots = [6]uint16{1, 5, 5, 0, 5, 5}
			x.OriginalSlot = 3
		} else {
			x.FriendlySlots = [6]uint16{0, 5, 5, 1, 5, 5}
		}
		on, e := evaluateBattleAI(x)
		x.Formation = false
		off, e2 := evaluateBattleAI(x)
		if e != nil || e2 != nil || !reflect.DeepEqual(on.Candidates, off.Candidates) || on.SuggestedSlot != off.SuggestedSlot {
			t.Fatal("rear/no-support changed", on, off, e, e2)
		}
	}
	for _, name := range []string{"special0-choice", "special2-choice", "special5-empty-original"} {
		x := battleAIFixture(t, name)
		off, e := evaluateBattleAI(x)
		x.Formation = true
		on, e2 := evaluateBattleAI(x)
		if e != nil || e2 != nil || !reflect.DeepEqual(on.Candidates, off.Candidates) || on.SuggestedSlot != off.SuggestedSlot {
			t.Fatal("special damage changed", name, e, e2)
		}
	}
}

func TestBattleAITacticsEstimate(t *testing.T) {
	v := battleAIFixture(t, "front-ranged-mixed")
	v.FriendlySlots = [6]uint16{0, 1, 5, 5, 5, 5}
	v.Friendly[0] = battleAIUnit{1, 20}
	v.Friendly[1] = battleAIUnit{21, 22}
	v.OriginalSlot = 0
	v.Formation = true
	old, err := evaluateBattleAI(v)
	if err != nil || old.SuggestedSlot != 0 || old.Candidates[0].Loss != 12 {
		t.Fatal(old, err)
	}
	v.ArcherPressure = true
	before := v
	d, err := evaluateBattleAI(v)
	if err != nil || !d.ArcherPressure || d.SuggestedSlot != 1 || d.Candidates[0].Amount != 240 || d.Candidates[0].Loss != 9 || d.Candidates[1].Amount != 300 || d.Candidates[1].Loss != 10 || v != before {
		t.Fatal(d, err)
	}
	for _, rear := range []bool{false, true} {
		x := before
		if rear {
			x.SourceSlot = 3
			x.EnemySlots = [6]uint16{3, 1, 2, 0, 4, 5}
		} else {
			x.Enemy[0].Kind = 24
		}
		on, e := evaluateBattleAI(x)
		x.ArcherPressure = false
		off, e2 := evaluateBattleAI(x)
		if e != nil || e2 != nil || !reflect.DeepEqual(on.Candidates, off.Candidates) || on.SuggestedSlot != off.SuggestedSlot {
			t.Fatal("rear/bird changed", on, off, e, e2)
		}
	}
	x := before
	x.FriendlySlots = [6]uint16{5, 0, 5, 1, 5, 5}
	x.OriginalSlot = 1
	d, err = evaluateBattleAI(x)
	if err != nil || d.Candidates[0].Amount != 400 {
		t.Fatal("open lane", d, err)
	}
	x = before
	x.Formation = false
	x.Enemy[0].Count = 4
	x.Friendly[0].Count = 2
	x.Friendly[1].Count = 0
	d, err = evaluateBattleAI(x)
	if err != nil || len(d.Candidates) != 1 || d.Candidates[0].Amount != 24 || d.Candidates[0].Loss != 0 {
		t.Fatal("small-army threshold", d, err)
	}
	for _, name := range []string{"special0-choice", "special2-choice", "special5-empty-original"} {
		x := battleAIFixture(t, name)
		off, e := evaluateBattleAI(x)
		x.Formation = true
		x.ArcherPressure = true
		on, e2 := evaluateBattleAI(x)
		if e != nil || e2 != nil || !reflect.DeepEqual(on.Candidates, off.Candidates) || on.SuggestedSlot != off.SuggestedSlot {
			t.Fatal("special changed", name, e, e2)
		}
	}
}
