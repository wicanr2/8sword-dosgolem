// 030 DRAFT: live read-only scoring and controlled target experiments.
package main

import (
 "bytes"
 "crypto/sha256"
 "encoding/binary"
 "encoding/json"
 "flag"
 "fmt"
 "os"
 "path/filepath"
 "runtime"
 "strings"
 "slices"

 "github.com/wicanr2/dosgolem/internal/cpu"
 "github.com/wicanr2/dosgolem/internal/dos"
 "github.com/wicanr2/dosgolem/internal/machine"
 "github.com/wicanr2/dosgolem/internal/state"
)
type policyScenario struct {
 Name string
 Source, Kind uint16
 Selector int
 Mapping [6]uint16
 Counts [2]uint16
 Kinds [2]uint16
}
var policyScenarios=[]policyScenario{
 {"normal-locked",0,6,-1,[6]uint16{0,5,5,1,5,5},[2]uint16{31,69},[2]uint16{1,21}},
 {"normal-choice",2,6,-1,[6]uint16{0,1,5,5,5,5},[2]uint16{15,69},[2]uint16{1,21}},
 {"normal-rear-only",0,6,-1,[6]uint16{5,5,5,0,1,5},[2]uint16{15,69},[2]uint16{1,21}},
 {"front-ranged-mixed",0,3,-1,[6]uint16{0,5,5,1,5,5},[2]uint16{10,69},[2]uint16{1,21}},
 {"rear-ranged-mixed",3,24,-1,[6]uint16{0,5,5,1,5,5},[2]uint16{10,69},[2]uint16{1,21}},
 {"special0-choice",3,12,0,[6]uint16{0,1,5,5,5,5},[2]uint16{31,69},[2]uint16{1,21}},
 {"special2-choice",3,12,2,[6]uint16{0,1,5,5,5,5},[2]uint16{31,69},[2]uint16{6,15}},
 {"special5-empty-original",3,12,5,[6]uint16{0,1,5,5,5,5},[2]uint16{31,69},[2]uint16{1,21}},
}
func must(e error){if e!=nil {panic(e)}}
func hash(b []byte)string{return fmt.Sprintf("%x",sha256.Sum256(b))}
func write(path string,v any){b,e:=json.MarshalIndent(v,"","  ");must(e);must(os.WriteFile(path,append(b,'\n'),0644))}
func jhash(v any)string{b,e:=json.Marshal(v);must(e);return hash(b)}
func words(m *machine.Machine,seg,off uint16,n int)[]uint16 {v:=make([]uint16,n);for i:=range v {v[i]=m.Read16(uint32(seg)*16+uint32(off+uint16(i*2)))};return v}
func capture(m *machine.Machine,sc policyScenario,route string,target uint16)policyView{
 ds:=m.CPU.Seg[cpu.DS];v:=policyView{Route:route,SourceSlot:sc.Source,OriginalSlot:target,Selector:uint16(sc.Selector),ShiftedSlotZero:words(m,ds,0x6fb4,1)[0],Divisor:words(m,ds,0x26ac,1)[0]}
 u:=words(m,ds,0x56e8,24);for i:=0;i<6;i++ {v.Friendly[i]=policyUnit{u[i*2],u[i*2+1]};v.Enemy[i]=policyUnit{u[12+i*2],u[13+i*2]}}
 copy(v.FriendlySlots[:],words(m,ds,0x6fb6,6));copy(v.EnemySlots[:],words(m,ds,0x6fc2,6));copy(v.Factors[:],words(m,ds,0x70ce,52));return v
}
func replay(batch,out string){
 rows:=[]map[string]any{}
 for _,sc:=range policyScenarios {
  for _,mode:=range []string{"shadow","override"} {
   path:=filepath.Join(batch,sc.Name,mode,"trace.json");if sc.Name=="special5-empty-original" {path=filepath.Join(filepath.Dir(batch),"ai-policy-extra-r2",sc.Name,mode,"trace.json")};raw,e:=os.ReadFile(path);must(e)
   var t struct{View policyView;Decision *policyDecision;AfterUnits []uint16;Mode string};must(json.Unmarshal(raw,&t));d,e:=evaluatePolicy(t.View);must(e)
   a,e:=json.Marshal(d);must(e);b,e:=json.Marshal(t.Decision);must(e);if !bytes.Equal(a,b){panic("replayed decision differs")}
   rows=append(rows,map[string]any{"name":sc.Name,"mode":mode,"trace_sha256":hash(raw),"decision":d})
  }
 }
 write(out,map[string]any{"status":"offline-policy-replay-only","schema":1,"production_changed":false,"decisions":rows});fmt.Printf("replayed %d live decisions\n",len(rows))
}
func main(){
 root:=flag.String("root","","read-only original");input:=flag.String("state","","fixed snapshot");out:=flag.String("out","","new output path");only:=flag.String("only","","optional exact scenario name");offline:=flag.String("offline","","replay saved decisions only");flag.Parse()
 if _,e:=os.Stat(*out);!os.IsNotExist(e){panic("output exists")}
 if *offline!="" {replay(*offline,*out);return}
 must(os.Mkdir(*out,0755));raw,e:=os.ReadFile(*input);must(e);if hash(raw)!="88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf" {panic("fixed snapshot mismatch")}
 pam,e:=os.ReadFile(filepath.Join(*root,"PAM.AY"));must(e);if hash(pam)!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0" {panic("PAM mismatch")}
 u16:=func(at int)uint16{return binary.LittleEndian.Uint16(pam[at:])};header:=int(u16(8))*16;code:=append([]byte(nil),pam[header:]...)
 for i:=0;i<int(u16(6));i++ {at:=int(u16(24))+i*4;loc:=int(u16(at+2))*16+int(u16(at));binary.LittleEndian.PutUint16(code[loc:],binary.LittleEndian.Uint16(code[loc:])+0x110)}
 hooks:=map[uint16]string{0x180a:"normal",0x16e7:"ranged",0x1974:"ranged",0x0dbd:"special0",0x0f06:"special2",0x0fbb:"special5"}
 cases:=[]map[string]any{}
 for _,sc:=range policyScenarios {
  if *only!=""&&!strings.Contains(","+*only+",",","+sc.Name+","){continue}
  caseDir:=filepath.Join(*out,sc.Name);must(os.Mkdir(caseDir,0755));results:=map[string]map[string]any{};finals:=map[string][]byte{};befores:=map[string][]byte{}
  for _,mode:=range []string{"baseline","shadow","override"} {
   dir:=filepath.Join(caseDir,mode);must(os.Mkdir(dir,0755));m:=machine.New();d:=dos.New(m,*root);d.Install();must(state.Load(*input,m,d));start:=m.Steps
   prefixes:=[]map[string]any{}
   for ip,route:=range hooks {at:=0xf67*16+int(ip)-0x1100;actual:=make([]byte,24);for i:=range actual {actual[i]=m.Read8(0xf67*16+uint32(ip)+uint32(i))};if !bytes.Equal(actual,code[at:at+24]){panic("hook prefix mismatch")};prefixes=append(prefixes,map[string]any{"ip":ip,"route":route,"ida_linear":0x1e570+int(ip),"file_offset":header+at,"bytes":fmt.Sprintf("%x",actual)})}
   initialized,dispatched,decided,executing:=false,false,false,false;nextKey:=0;var ds uint16;var view policyView;var decision *policyDecision;var returnCS,returnIP,returnSS,returnSP uint16;var executorStack []uint16;var executorName string;var effectBefore []uint16
   changes:=[]map[string]any{};var prediction *policyCandidate;var beforeRAM,afterRAM []byte;var beforeRegisters,afterRegisters [8]uint16;decisionStep:=uint64(0);hookIP:=uint16(0);targetOffset:=uint16(0);targetSegment:=uint16(0)
   mutate:=func(seg,off,value uint16,phase string){old:=m.Read16(uint32(seg)*16+uint32(off));if old==value{return};m.Write16(uint32(seg)*16+uint32(off),value);changes=append(changes,map[string]any{"segment":seg,"offset":off,"old":old,"new":value,"phase":phase,"step":m.Steps})}
   for m.Steps<start+40000000 {
    if nextKey<6&&m.Steps>=start+uint64(nextKey)*2000000 {m.PushKey(0x39);nextKey++}
    c:=m.CPU
    if !initialized&&c.Seg[cpu.CS]==0xf67&&c.IP==0x216a {
     ds=c.Seg[cpu.DS];must(state.Save(filepath.Join(dir,"before-fixture.state"),m,d))
     for id:=uint16(0);id<6;id++ {q:=uint16(0);if id==sc.Source {q=50};mutate(ds,0x5702+id*4,q,"fixture")};mutate(ds,0x5700+sc.Source*4,sc.Kind,"fixture")
     for i:=0;i<2;i++ {mutate(ds,0x56e8+uint16(i*4),sc.Kinds[i],"fixture");mutate(ds,0x56ea+uint16(i*4),sc.Counts[i],"fixture")}
     for i,id:=range sc.Mapping {mutate(ds,0x6fb6+uint16(i*2),id,"fixture")}
     must(state.Save(filepath.Join(dir,"after-fixture.state"),m,d));initialized=true
    }
    if initialized&&sc.Selector>=0&&!dispatched&&c.Seg[cpu.CS]==0xf67&&c.IP==0xd88 {mutate(c.Seg[cpu.SS],c.R[cpu.BP]-4,uint16(sc.Selector),"dispatch");dispatched=true}
    if route,ok:=hooks[c.IP];ok&&initialized&&!decided&&c.Seg[cpu.CS]==0xf67 {
     routeMatch:=sc.Selector<0&&(route=="normal"||route=="ranged")||sc.Selector>=0&&route==fmt.Sprintf("special%d",sc.Selector)
     if !routeMatch {panic("unexpected target route")}
     off:=c.R[cpu.BP]-4;encoded:=true;if sc.Selector>=0 {off=c.R[cpu.BP]-8;encoded=false;route="special"}
     target:=words(m,c.Seg[cpu.SS],off,1)[0];if sc.Selector==5 {target=c.R[cpu.DX];if target>=6 {panic("selector5 register range")};guard:=words(m,ds,0x6fb4+target*2,1)[0];if guard>=6 {panic("selector5 shifted unit range")};if words(m,ds,0x56ea+guard*4,1)[0]==0 {must(m.Step());continue};off=0};if encoded {if target<7 {panic("unencoded target")};target-=7}
     view=capture(m,sc,route,target);must(state.Save(filepath.Join(dir,"before-decision.state"),m,d));beforeRAM=append([]byte(nil),m.Mem...);beforeRegisters=c.R;decisionStep=m.Steps;hookIP=c.IP;targetOffset=off;targetSegment=c.Seg[cpu.SS]
     if mode!="baseline" {v,e:=evaluatePolicy(view);must(e);decision=&v;if mode=="override" {selected:=v.SuggestedSlot;if encoded {selected+=7};if sc.Selector==5 {old:=c.R[cpu.DX];if old!=selected {c.R[cpu.DX]=selected;changes=append(changes,map[string]any{"phase":"policy-target","register":"DX","old":old,"new":selected,"step":m.Steps})}} else {mutate(c.Seg[cpu.SS],off,selected,"policy-target")}}}
     chosen:=target;if mode=="override" {chosen=decision.SuggestedSlot};if mode!="baseline"&&(mode=="override"||decision.OriginalEligible) {v,e:=policyPredict(view,chosen);must(e);prediction=&v}
     afterRAM=append([]byte(nil),m.Mem...);afterRegisters=c.R;must(os.WriteFile(filepath.Join(dir,"before-decision-ram.bin"),beforeRAM,0644));must(os.WriteFile(filepath.Join(dir,"after-decision-ram.bin"),afterRAM,0644));must(state.Save(filepath.Join(dir,"after-decision.state"),m,d));decided=true
    }
    if decided&&!executing&&c.Seg[cpu.CS]==0xf67&&(c.IP==0x4626||c.IP==0x36c6) {
     executorName="sub_22B96";if c.IP==0x36c6 {executorName="sub_21C36"};executorStack=words(m,c.Seg[cpu.SS],c.R[cpu.SP],8);returnIP,returnCS=executorStack[0],executorStack[1];returnSS,returnSP=c.Seg[cpu.SS],c.R[cpu.SP]+4;effectBefore=words(m,ds,0x56e8,24);executing=true
    }
    if executing&&c.Seg[cpu.CS]==returnCS&&c.IP==returnIP&&c.Seg[cpu.SS]==returnSS&&c.R[cpu.SP]==returnSP {break}
    must(m.Step())
   }
   if !executing||m.CPU.Seg[cpu.CS]!=returnCS||m.CPU.IP!=returnIP {panic("incomplete effect")}
   after:=words(m,ds,0x56e8,24)
   if prediction!=nil {want:=slices.Clone(effectBefore);want[prediction.Unit*2+1]-=prediction.Loss;if want[prediction.Unit*2+1]==0 {want[prediction.Unit*2]=0};if !slices.Equal(want,after){panic("live prediction differs from original executor")}}
   must(state.Save(filepath.Join(dir,"final.state"),m,d));final,e:=os.ReadFile(filepath.Join(dir,"final.state"));must(e);finals[mode]=final;befores[mode],e=os.ReadFile(filepath.Join(dir,"before-decision.state"));must(e)
   result:=map[string]any{"Mode":mode,"View":view,"Decision":decision,"Prediction":prediction,"Scenario":sc,"BeforeUnits":effectBefore,"AfterUnits":after,"Flags":words(m,ds,0x8e78,6),"Changes":changes,"StartStep":start,"EndStep":m.Steps,"DecisionStep":decisionStep,"HookIP":hookIP,"TargetSegment":targetSegment,"TargetOffset":targetOffset,"Executor":executorName,"ExecutorStack":executorStack,"StateSHA256":hash(final),"OPLSHA256":jhash(m.OPL),"PortsSHA256":jhash(m.PortLog),"DOSSHA256":jhash(d.CallTrace),"Prefixes":prefixes,"BeforeRAMSHA256":hash(beforeRAM),"AfterRAMSHA256":hash(afterRAM),"BeforeRegisters":beforeRegisters,"AfterRegisters":afterRegisters,"GoVersion":runtime.Version()};write(filepath.Join(dir,"trace.json"),result);results[mode]=result
  }
  if !bytes.Equal(finals["baseline"],finals["shadow"]) {panic("read-only policy changed state")}
  for _,key:=range []string{"OPLSHA256","PortsSHA256","DOSSHA256"} {if results["baseline"][key]!=results["shadow"][key] {panic("read-only policy changed I/O")}}
  if !bytes.Equal(befores["baseline"],befores["shadow"])||!bytes.Equal(befores["baseline"],befores["override"]) {panic("pre-decision states differ")}
  row:=map[string]any{"scenario":sc,"shadow_state_equal":true,"shadow_io_equal":true,"before_states_equal":true,"results":results};write(filepath.Join(caseDir,"paired.json"),row);cases=append(cases,row);fmt.Printf("%s: shadow equal; selected %d -> %d\n",sc.Name,results["shadow"]["Decision"].(*policyDecision).OriginalSlot,results["override"]["Decision"].(*policyDecision).SuggestedSlot)
 }
 write(filepath.Join(*out,"summary.json"),map[string]any{"schema":1,"spec":"030 DRAFT","status":"live-shadow-and-controlled-target-only","source_sha256":hash(raw),"production_changed":false,"cases":cases})
}
