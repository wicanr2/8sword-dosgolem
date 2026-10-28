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
