// 030 DRAFT. Offline Go candidate evaluation; never invokes the DOS helper.
package main

import (
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
)

type event struct {
	Name string `json:"name"`
	Step uint64 `json:"step"`
	Locals []uint16 `json:"bp_minus_2_through_12"`
	Units []uint16 `json:"ds_56e8_words"`
	Mapping []uint16 `json:"ds_6fa8_words"`
	Factors []uint16 `json:"ds_70ce_words"`
	Divisor uint16 `json:"ds_26ac_word"`
}
type candidate struct {
	Slot, Unit, Class, Count uint16
	RawDamage, PredictedLoss uint16
	Eliminates bool
}
type decision struct {
	Step uint64
	SourceSlot, SourceUnit uint16
	OriginalSlot, SuggestedSlot uint16
	ObservedOriginalLoss uint16
	Candidates []candidate
	Reason string
}
func must(e error) {if e!=nil {panic(e)}}
func predicted(e event, enemy, target, slot uint16) candidate {
	typeID,count:=e.Units[target*2],e.Units[target*2+1]
	sourceType,sourceCount:=e.Units[12+enemy*2],e.Units[13+enemy*2]
	div:=uint16(e.Divisor+5);hp:=e.Factors[typeID*2+1]
	if div==0||hp==0||count==0 {panic("unsupported divisor or empty target")}
	product:=uint16(uint32(e.Factors[sourceType*2])*uint32(sourceCount))
	damage:=product/div;returned:=uint16(damage/hp+1);loss:=uint16(0)
	// sub_22B96 compares the encoded return against count before its
	// decrement animation; equality enters the original whole-stack branch.
	if returned>1 {loss=returned-1;if returned>=count {loss=count}}
	return candidate{slot,target,typeID,count,damage,loss,loss==count}
}
func better(a,b candidate) bool {
	if a.Eliminates!=b.Eliminates {return a.Eliminates}
	return uint64(a.PredictedLoss)*uint64(b.Count)>uint64(b.PredictedLoss)*uint64(a.Count)
}
func main() {
	input:=flag.String("trace","","validated read-only trace");out:=flag.String("out","","new shadow JSON");flag.Parse()
	if _,e:=os.Stat(*out);!os.IsNotExist(e) {panic("output exists")}
	b,e:=os.ReadFile(*input);must(e);var trace struct {Events []event `json:"events"`;Equal bool `json:"state_equal"`;IO bool `json:"io_equal"`};must(json.Unmarshal(b,&trace));if !trace.Equal||!trace.IO {panic("unpaired trace")}
	rows:=[]decision{};var pending *decision;var pendingOriginal candidate
	for _,v:=range trace.Events {
		if v.Name=="IDA 0x1FD7A before target normalization" {
			if pending!=nil {panic("overlapping action")}
			source:=v.Locals[2];original:=v.Locals[1]-7
			if source>=3||original>=6 {panic("outside sampled front-row branch")}
			enemy:=v.Mapping[13+source];kind:=v.Units[12+enemy*2]
			if kind==3||kind==24 {panic("ranged branch not yet sampled")}
			candidates:=[]candidate{}
			for slot:=uint16(0);slot<3;slot++ {
				unit:=v.Mapping[7+slot];if unit>=6||v.Units[unit*2+1]==0 {continue}
				candidates=append(candidates,predicted(v,enemy,unit,slot))
			}
			if len(candidates)==0 {panic("back-row branch not yet sampled")}
			for _,c:=range candidates {if c.Slot==source {candidates=[]candidate{c};break}}
			var originalCandidate *candidate
			for i:=range candidates {if candidates[i].Slot==original {originalCandidate=&candidates[i]}}
			if originalCandidate==nil {panic("original outside supported candidate set")}
			best:=*originalCandidate
			for _,c:=range candidates {if better(c,best) {best=c}}
			pendingOriginal=*originalCandidate
			pending=&decision{Step:v.Step,SourceSlot:source,SourceUnit:enemy,OriginalSlot:original,SuggestedSlot:best.Slot,Candidates:candidates,Reason:"研究排序：先清除整隊，再比較預期減員比例；同分保留原目標"}
		} else if v.Name=="sub_22B96:return"&&pending!=nil {
			pending.ObservedOriginalLoss=pendingOriginal.Count-v.Units[pendingOriginal.Unit*2+1]
			if pending.ObservedOriginalLoss!=pendingOriginal.PredictedLoss {panic("Go loss prediction differs from original executor")}
			rows=append(rows,*pending);pending=nil
		}
	}
	if pending!=nil||len(rows)!=3 {panic("incomplete sampled round")}
	digest:=sha256.Sum256(b);result:=map[string]any{"schema":1,"spec":"030 DRAFT","status":"offline-shadow-only","trace_sha256":fmt.Sprintf("%x",digest),"guest_executed":false,"guest_writes":false,"scope":"sampled normal front-row selection; ranged, rear-row and special actions rejected","policy_approved_for_production":false,"decisions":rows}
	b,e=json.MarshalIndent(result,"","  ");must(e);must(os.WriteFile(*out,append(b,'\n'),0644));fmt.Printf("Go shadow: %d original outcomes predicted\n",len(rows))
}
