package main

import (
 "encoding/json"
 "os"
 "path/filepath"
 "reflect"
 "testing"
)
func policyFixture(t *testing.T,name string) policyView {
 t.Helper();root:=os.Getenv("EIGHTSWORD_POLICY_TEST_BATCH");if root=="" {t.Fatal("explicit verified research inputs required")}
 dir:="ai-policy-r1";if name=="special5-empty-original" {dir="ai-policy-extra-r2"}
 raw,e:=os.ReadFile(filepath.Join(root,dir,name,"shadow/trace.json"));if e!=nil {t.Fatal(e)}
 var trace struct{View policyView};if e=json.Unmarshal(raw,&trace);e!=nil {t.Fatal(e)};return trace.View
}
func TestPolicyRealCandidateSets(t *testing.T) {
 fixtures:=[]struct{name string;slots []uint16;chosen uint16}{
  {"normal-locked",[]uint16{0},0},{"normal-choice",[]uint16{0,1},0},
  {"normal-rear-only",[]uint16{3,4},3},{"front-ranged-mixed",[]uint16{0,3},0},
  {"rear-ranged-mixed",[]uint16{0,3},0},{"special0-choice",[]uint16{0,1},0},
  {"special2-choice",[]uint16{0,1},0},{"special5-empty-original",[]uint16{0,1},0},
 }
 for _,f:=range fixtures {t.Run(f.name,func(t *testing.T){v:=policyFixture(t,f.name);copy:=v;d,e:=evaluatePolicy(v);if e!=nil {t.Fatal(e)};slots:=[]uint16{};for _,c:=range d.Candidates {slots=append(slots,c.Slot)};if !reflect.DeepEqual(slots,f.slots)||d.SuggestedSlot!=f.chosen {t.Fatalf("unexpected candidates or choice: %+v",d)};if v!=copy {t.Fatal("view mutated")}})}
}
func TestPolicyRejectsUnsafeViews(t *testing.T) {
 base:=policyFixture(t,"front-ranged-mixed")
 cases:=[]struct{name string;edit func(*policyView)}{
  {"source-slot",func(v *policyView){v.SourceSlot=6}},
  {"original-slot",func(v *policyView){v.OriginalSlot=6}},
  {"mapping-range",func(v *policyView){v.FriendlySlots[0]=6}},
  {"duplicate-live",func(v *policyView){v.FriendlySlots[1]=v.FriendlySlots[0]}},
  {"empty-source",func(v *policyView){v.Enemy[v.EnemySlots[v.SourceSlot]].Count=0}},
  {"route",func(v *policyView){v.Route="unknown"}},
  {"ranged-kind",func(v *policyView){v.Enemy[v.EnemySlots[v.SourceSlot]].Kind=6}},
  {"zero-divisor",func(v *policyView){v.Divisor=65531}},
  {"zero-target-factor",func(v *policyView){v.Factors[v.Friendly[0].Kind*2+1]=0}},
 }
 for _,c:=range cases {t.Run(c.name,func(t *testing.T){v:=base;c.edit(&v);copy:=v;if _,e:=evaluatePolicy(v);e==nil {t.Fatal("unsafe view accepted")};if v!=copy {t.Fatal("rejected input mutated")}})}
 for _,selector:=range []uint16{1,3,4,6,7,65535} {v:=policyFixture(t,"special2-choice");v.Selector=selector;if _,e:=evaluatePolicy(v);e==nil {t.Fatalf("unsupported selector %d accepted",selector)}}
 v:=policyFixture(t,"special2-choice");v.Friendly[0].Kind=5;v.Friendly[1].Kind=16;if _,e:=evaluatePolicy(v);e==nil {t.Fatal("ineligible type set accepted")}
}
func TestPolicyStableTieRetainsOriginal(t *testing.T) {
 v:=policyFixture(t,"front-ranged-mixed");v.Friendly[1]=v.Friendly[0];v.OriginalSlot=3
 d,e:=evaluatePolicy(v);if e!=nil {t.Fatal(e)};if d.SuggestedSlot!=3 {t.Fatal("equal score changed original target")}
}
