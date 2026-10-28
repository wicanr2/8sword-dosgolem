// 030 DRAFT: offline prediction of sampled selectors 2/3/4/5/7, never guest writes.
package main

import (
 "crypto/sha256"
 "encoding/json"
 "flag"
 "fmt"
 "os"
 "path/filepath"
 "slices"
)

type event struct {
 Name string `json:"name"`
 Step uint64 `json:"step"`
 Stack []uint16 `json:"stack_words"`
 Wide []uint16 `json:"bp_minus_2_through_24"`
 Units []uint16 `json:"ds_56e8_words"`
 Mapping []uint16 `json:"ds_6fa8_words"`
 Flags []uint16 `json:"ds_8e78_words"`
 Special []uint16 `json:"ds_8cb0_words"`
 Gate uint16 `json:"ds_26ae_word"`
}
func must(e error) { if e!=nil { panic(e) } }
func hash(b []byte) string { return fmt.Sprintf("%x",sha256.Sum256(b)) }
func main() {
 batch:=flag.String("batch","","battle study root");out:=flag.String("out","","new JSON");flag.Parse()
 if _,e:=os.Stat(*out);!os.IsNotExist(e){panic("output exists")}
 names:=[]string{"special-12-case2-kind6","special-10-case2-kind15","special-12-case2-none","special-12-case3-gate0","special-12-case3-gate4","special-10-case3-gate4","special-12-case4","special-12-case5","special-10-case5","special-12-case7","special-10-case7","special-12-case5-live","special-10-case5-live"}
 rows:=[]map[string]any{};predictions:=0
 for _,name:=range names {
  dir:="ai-specials-r1"
  if slices.Contains([]string{"special-12-case2-kind6","special-10-case2-kind15","special-12-case2-none","special-12-case4","special-12-case5-live","special-10-case5-live"},name){dir="ai-specials-extra-r2"}
  raw,e:=os.ReadFile(filepath.Join(*batch,dir,name,"observed/trace.json"));must(e)
  var t struct {Events []event `json:"events"`;Scenario struct {Kind uint16;Variant int} `json:"scenario"`;Summary struct {Stop string `json:"stop"`} `json:"summary"`}
  must(json.Unmarshal(raw,&t));if t.Summary.Stop!="special-return" {panic("incomplete original action")}
  var entry,dispatch,gate,shifted,finish *event;effects:=[]map[string]any{};var pending *event
  for i:=range t.Events {v:=&t.Events[i];switch v.Name {
  case "sub_1F266":entry=v
  case "special-dispatch":dispatch=v
  case "case3-gate":gate=v
  case "case5-shifted-check":shifted=v
  case "sub_1F266:return":finish=v
  case "sub_21C36","sub_21E3C":
   if entry==nil||dispatch==nil||pending!=nil {panic("unmatched effect entry")};pending=v
  case "sub_21C36:return","sub_21E3C:return":
   if pending==nil {panic("unmatched effect return")};p:=pending
   slot:=p.Stack[3];if slot>=6 {panic("target slot")};unit:=p.Mapping[7+slot];q:=p.Units[unit*2+1];amount:=uint16(0)
   switch t.Scenario.Variant {
   case 2:
    kind:=p.Units[unit*2];if q==0||kind<6||kind>15 {panic("ineligible type target")};amount=15;if t.Scenario.Kind==12 {amount=6}
   case 3:
    if gate==nil||uint16(uint32(gate.Gate)*10+10)<=gate.Wide[4] {panic("failed success gate executed")};amount=q
   case 5:
    if shifted==nil||shifted.Wide[3]!=slot {panic("missing shifted guard")};guardUnit:=shifted.Mapping[6+slot]
    if shifted.Units[guardUnit*2+1]==0 {panic("empty shifted guard")}
    divisor:=uint16(2);if t.Scenario.Kind==12 {divisor=3};amount=q/divisor+1
   case 7:
    if p.Name!="sub_21E3C" {panic("wrong final executor")};amount=q
    if q>=50 {divisor:=uint16(10);if t.Scenario.Kind==12 {divisor=20};amount=uint16(uint32(q)*6)/divisor+1}
   default:panic("unsupported selector")
   }
   loss:=min(q,amount);expected:=slices.Clone(p.Units);expected[unit*2+1]-=loss
   if loss==q {expected[unit*2]=0}
   if amount!=p.Special[1]||!slices.Equal(expected,v.Units) {panic("effect prediction differs from original")}
   effect:=map[string]any{"step":p.Step,"executor":p.Name,"slot":slot,"unit":unit,"before":q,"amount":amount,"predicted_after":q-loss,"actual_after":v.Units[unit*2+1]}
   if t.Scenario.Variant==5 {effect["guard_unit"]=shifted.Mapping[6+slot];effect["guard_count"]=shifted.Units[shifted.Mapping[6+slot]*2+1]}
   effects=append(effects,effect);predictions++;pending=nil
  }}
  if entry==nil||dispatch==nil||finish==nil||pending!=nil||int(dispatch.Wide[1])!=t.Scenario.Variant {panic("incomplete dispatch")}
  expectedFlags:=slices.Clone(entry.Flags);result:=map[string]any{"name":name,"directory":dir,"trace_sha256":hash(raw),"selector":t.Scenario.Variant,"effects":effects}
  switch t.Scenario.Variant {
  case 2:
   eligible:=false;for slot:=0;slot<6;slot++ {kind:=entry.Units[entry.Mapping[7+slot]*2];if kind>=6&&kind<=15 {eligible=true}}
   if eligible!=(len(effects)==1) {panic("eligibility outcome")};result["eligible_type_exists"]=eligible
  case 3:
   if gate==nil {panic("missing gate")};threshold:=uint16(uint32(gate.Gate)*10+10);success:=threshold>gate.Wide[4]
   if success!=(len(effects)==1) {panic("gate outcome")};result["gate"]=map[string]any{"field":gate.Gate,"threshold":threshold,"recorded_random_remainder":gate.Wide[4],"success":success}
  case 4:
   if len(effects)!=0 {panic("flag selector damaged units")};for slot:=0;slot<6;slot++ {unit:=entry.Mapping[13+slot];expectedFlags[unit]++};predictions++
  case 5:if len(effects)!=1 {panic("expected one effect")}
  case 7:if len(effects)!=2 {panic("sample expects two live targets")}
  default:panic("unsupported selector")
  }
  if !slices.Equal(expectedFlags,finish.Flags) {panic("flag prediction")}
  expectedUnits:=slices.Clone(entry.Units)
  for _,v:=range effects {unit:=v["unit"].(uint16);after:=v["predicted_after"].(uint16);expectedUnits[unit*2+1]=after;if after==0 {expectedUnits[unit*2]=0}}
  if !slices.Equal(expectedUnits,finish.Units) {panic("complete action units")}
  result["predicted_flags"]=expectedFlags;result["actual_flags"]=finish.Flags;result["complete_units_match"]=true;rows=append(rows,result)
 }
 result:=map[string]any{"schema":1,"status":"offline-special-shadow-only","spec":"030 DRAFT","guest_execution":false,"policy_approved_for_production":false,"cases":rows,"predictions":predictions,"limits":[]string{"Preselected dispatch and controlled fixtures, not a natural encounter or complete round.","RNG remainders are observed inputs, never an oracle queried for policy.","No production strategy, spell names, mixed-board legality or balancing claim."}}
 raw,e:=json.MarshalIndent(result,"","  ");must(e);must(os.WriteFile(*out,append(raw,'\n'),0644));fmt.Printf("Go specials: cases=%d effect/flag predictions=%d\n",len(rows),predictions)
}
