// 030 DRAFT. Pure Go replay of sampled actions; no DOS execution or writes.
package main

import (
 "crypto/sha256"
 "encoding/json"
 "flag"
 "fmt"
 "os"
 "path/filepath"
)
type event struct {
 Name string `json:"name"`; Step uint64 `json:"step"`
 Locals []uint16 `json:"bp_minus_2_through_12"`; Wide []uint16 `json:"bp_minus_2_through_24"`
 Stack []uint16 `json:"stack_words"`; Units []uint16 `json:"ds_56e8_words"`; Mapping []uint16 `json:"ds_6fa8_words"`
 Factors []uint16 `json:"ds_70ce_words"`; Divisor uint16 `json:"ds_26ac_word"`; Special []uint16 `json:"ds_8cb0_words"`
}
type candidate struct {Slot,Unit,Count,Damage,Loss uint16; Eliminates bool}
type advice struct {Step uint64; Route string; SourceSlot,OriginalSlot,SuggestedSlot uint16; Candidates []candidate; ObservedLoss uint16}
func must(e error){if e!=nil{panic(e)}}
func hash(b []byte)string{return fmt.Sprintf("%x",sha256.Sum256(b))}
func growth(count,kind uint16)(desired,after uint16){
 rate:=uint16(10);switch{case count<50:rate=20;case count<100:rate=14;case count<200:rate=13;case count<300:rate=12;case count<400:rate=11}
 div:=uint16(10);if kind==12{div=20};desired=uint16(uint32(count)*uint32(rate))/div;return desired,max(count,desired)
}
func ordinary(v event,source,slot uint16)candidate{
 unit:=v.Mapping[7+slot];count:=v.Units[unit*2+1];kind:=v.Units[12+source*2];qty:=v.Units[13+source*2];div:=uint16(v.Divisor+5);hp:=v.Factors[v.Units[unit*2]*2+1]
 if div==0||hp==0||count==0{panic("unsupported ordinary operands")};damage:=uint16(uint32(v.Factors[kind*2])*uint32(qty))/div;encoded:=uint16(damage/hp+1);loss:=uint16(0);if encoded>1{loss=encoded-1;if encoded>=count{loss=count}}
 return candidate{slot,unit,count,damage,loss,loss==count}
}
func prefer(a,b candidate)bool{if a.Eliminates!=b.Eliminates{return a.Eliminates};return uint64(a.Loss)*uint64(b.Count)>uint64(b.Loss)*uint64(a.Count)}
func main(){
 batch:=flag.String("batch","","battle research root");out:=flag.String("out","","new output JSON");flag.Parse();if _,e:=os.Stat(*out);!os.IsNotExist(e){panic("output exists")}
 names:=[]string{"front-3","front-24","rear-3","rear-24","rear-10","rear-12","rear-ineligible-6","front-to-rear","ranged-to-rear","special-12-case0","special-12-case6","special-10-case6-49","special-10-case6-50"}
 cases:=[]map[string]any{};ordinaryCount,specialCount,growthCount:=0,0,0
 for _,name:=range names{
  directory:="ai-branches-r1";if name=="special-10-case6-49"||name=="special-10-case6-50"{directory="ai-branches-extra-r2"};path:=filepath.Join(*batch,directory,name,"observed/trace.json");raw,e:=os.ReadFile(path);must(e)
  var trace struct{Events []event `json:"events"`;Scenario struct{Slot,Kind uint16} `json:"scenario"`;Summary struct{Stop string `json:"stop"`} `json:"summary"`};must(json.Unmarshal(raw,&trace));if trace.Summary.Stop!="round-return"{panic("incomplete oracle")}
  rows:=[]advice{};effects:=[]map[string]any{};var pending *advice;var original candidate;var spell *event;var specialEntry *event;selector:=uint16(65535);hadGrowth:=false
  for _,v:=range trace.Events{
   if v.Name=="normal-normalize"||v.Name=="front-ranged-normalize"||v.Name=="rear-ranged-normalize"{
    if pending!=nil{panic("overlapping action")};slot,target:=v.Locals[2],v.Locals[1]-7;if slot>=6||target>=6{panic("slot range")};source:=v.Mapping[13+slot];kind:=v.Units[12+source*2];ranged:=kind==3||kind==24
    if (v.Name=="normal-normalize")==ranged||(!ranged&&slot>=3){panic("unsupported route")};first,last:=uint16(0),uint16(6)
    if !ranged{last=3;alive:=false;for s:=uint16(0);s<3;s++{if v.Units[v.Mapping[7+s]*2+1]>0{alive=true}};if !alive{first,last=3,6}}
    candidates:=[]candidate{};for s:=first;s<last;s++{if v.Units[v.Mapping[7+s]*2+1]>0{candidates=append(candidates,ordinary(v,source,s))}}
    if !ranged&&first==0{for _,c:=range candidates{if c.Slot==slot{candidates=[]candidate{c};break}}}
    found:=false;for _,c:=range candidates{if c.Slot==target{original=c;found=true}};if !found{panic("original target outside candidate set")};best:=original;for _,c:=range candidates{if prefer(c,best){best=c}}
    pending=&advice{Step:v.Step,Route:v.Name,SourceSlot:slot,OriginalSlot:target,SuggestedSlot:best.Slot,Candidates:candidates}
   }else if v.Name=="sub_22B96:return"&&pending!=nil{
    pending.ObservedLoss=original.Count-v.Units[original.Unit*2+1];if pending.ObservedLoss!=original.Loss{panic("ordinary loss mismatch")};rows=append(rows,*pending);pending=nil;ordinaryCount++
   }else if v.Name=="sub_1F266"{x:=v;specialEntry=&x
   }else if v.Name=="special-dispatch"{selector=v.Locals[1];if selector!=0&&selector!=1&&selector!=6{panic("unsupported special selector")}
   }else if v.Name=="sub_21C36"{x:=v;spell=&x
   }else if v.Name=="sub_21C36:return"&&spell!=nil{
    target:=spell.Mapping[7+spell.Stack[3]];before:=spell.Units[target*2+1];amount:=spell.Special[1];predicted:=min(before,amount);actual:=before-v.Units[target*2+1];if actual!=predicted{panic("special loss mismatch")};effects=append(effects,map[string]any{"kind":"fixed-casualties","selector":selector,"target_slot":spell.Stack[3],"target_unit":target,"before":before,"amount":amount,"predicted_loss":predicted,"actual_loss":actual});specialCount++;spell=nil
   }else if v.Name=="special-growth-plan"{
    targetSlot:=v.Locals[3];target:=v.Mapping[13+targetSlot];before:=v.Units[13+target*2];desired,_:=growth(before,trace.Scenario.Kind);if desired!=v.Wide[8]{panic("growth intermediate mismatch")};hadGrowth=true
   }else if v.Name=="sub_1F266:return"&&selector==6{
    if specialEntry==nil{panic("no special entry")};alive:=[]uint16{};for u:=uint16(0);u<6;u++{if specialEntry.Units[13+u*2]>0{alive=append(alive,u)}};if len(alive)!=1{panic("unsampled multi-target growth choice")};unit:=alive[0];before:=specialEntry.Units[13+unit*2];desired,predicted:=growth(before,trace.Scenario.Kind);actual:=v.Units[13+unit*2];if actual!=predicted{panic("growth outcome mismatch")};effects=append(effects,map[string]any{"kind":"own-count-growth","selector":selector,"unit":unit,"before":before,"computed_bound":desired,"predicted_after":predicted,"actual_after":actual,"intermediate_observed":hadGrowth});growthCount++
   }
  }
  if pending!=nil||spell!=nil{panic("unreturned action")};if name=="rear-ineligible-6"&&(len(rows)!=0||len(effects)!=0){panic("ineligible rear acted")}
  cases=append(cases,map[string]any{"name":name,"trace_sha256":hash(raw),"decisions":rows,"effects":effects,"selector":selector})
 }
 result:=map[string]any{"schema":1,"spec":"030 DRAFT","status":"offline-branch-shadow-only","guest_execution":false,"policy_approved_for_production":false,"ordinary_predictions":ordinaryCount,"special_loss_predictions":specialCount,"growth_predictions":growthCount,"cases":cases,"limits":"sampled original selectors 0/1/6 only; selectors 2/3/4/5/7 and general strategy withheld"};raw,e:=json.MarshalIndent(result,"","  ");must(e);must(os.WriteFile(*out,append(raw,'\n'),0644));fmt.Printf("Go branch shadow: ordinary=%d special-loss=%d growth=%d\n",ordinaryCount,specialCount,growthCount)
}
