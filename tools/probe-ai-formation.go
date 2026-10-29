// 030 DRAFT: original executor controls, known formation rule, bounded scenarios.
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
 "slices"

 "github.com/wicanr2/dosgolem/internal/cpu"
 "github.com/wicanr2/dosgolem/internal/dos"
 "github.com/wicanr2/dosgolem/internal/machine"
 "github.com/wicanr2/dosgolem/internal/state"
)
type formationCase struct {Name string;Source,Kind uint16;Selector int;Mapping [6]uint16;Counts,Kinds [3]uint16}
var formationCases=[]formationCase{
 {"normal-ratio",2,6,-1,[6]uint16{0,1,5,5,5,5},[3]uint16{15,15,0},[3]uint16{1,21,0}},
 {"ranged-ratio",0,3,-1,[6]uint16{0,1,5,5,5,5},[3]uint16{15,15,0},[3]uint16{1,21,0}},
 {"ranged-rear",0,3,-1,[6]uint16{0,2,5,1,5,5},[3]uint16{15,15,100},[3]uint16{1,21,21}},
 {"normal-locked",0,6,-1,[6]uint16{0,1,5,5,5,5},[3]uint16{15,15,0},[3]uint16{1,21,0}},
 {"no-support",0,3,-1,[6]uint16{0,5,5,1,5,5},[3]uint16{15,15,0},[3]uint16{1,21,0}},
 {"special0",3,12,0,[6]uint16{0,1,5,5,5,5},[3]uint16{31,69,0},[3]uint16{1,21,0}},
}
func must(e error){if e!=nil{panic(e)}}
func hash(b []byte)string{return fmt.Sprintf("%x",sha256.Sum256(b))}
func write(p string,v any){b,e:=json.MarshalIndent(v,"","  ");must(e);must(os.WriteFile(p,append(b,'\n'),0644))}
func words(m *machine.Machine,seg,off uint16,n int)[]uint16{v:=make([]uint16,n);for i:=range v{v[i]=m.Read16(uint32(seg)*16+uint32(off)+uint32(i*2))};return v}
func capture(m *machine.Machine,sc formationCase,route string,target uint16)policyView{
 ds:=m.CPU.Seg[cpu.DS];v:=policyView{Route:route,SourceSlot:sc.Source,OriginalSlot:target,Selector:uint16(sc.Selector),Divisor:words(m,ds,0x26ac,1)[0],ShiftedSlotZero:words(m,ds,0x6fb4,1)[0]};u:=words(m,ds,0x56e8,24)
 for i:=0;i<6;i++{v.Friendly[i]=policyUnit{u[i*2],u[i*2+1]};v.Enemy[i]=policyUnit{u[12+i*2],u[13+i*2]}}
 copy(v.FriendlySlots[:],words(m,ds,0x6fb6,6));copy(v.EnemySlots[:],words(m,ds,0x6fc2,6));copy(v.Factors[:],words(m,ds,0x70ce,52));return v
}
func main(){
 root:=flag.String("root","","read-only original");input:=flag.String("state","","fixed original snapshot");out:=flag.String("out","","new output");flag.Parse();_,err:=os.Stat(*out);if !os.IsNotExist(err){panic("output exists")};must(os.Mkdir(*out,0755))
 raw,err:=os.ReadFile(*input);must(err);if hash(raw)!="88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf"{panic("snapshot SHA")}
 pam,err:=os.ReadFile(filepath.Join(*root,"PAM.AY"));must(err);if hash(pam)!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"{panic("PAM SHA")}
 u16:=func(at int)uint16{return binary.LittleEndian.Uint16(pam[at:])};header:=int(u16(8))*16;code:=append([]byte(nil),pam[header:]...)
 for i:=0;i<int(u16(6));i++{at:=int(u16(24))+i*4;loc:=int(u16(at+2))*16+int(u16(at));binary.LittleEndian.PutUint16(code[loc:],binary.LittleEndian.Uint16(code[loc:])+0x110)}
 hooks:=map[uint16]string{0x180a:"normal",0x16e7:"ranged",0x1974:"ranged",0xdbd:"special"};rows:=[]map[string]any{}
 for _,sc:=range formationCases{for _,rules:=range []string{"native","formation"}{
  name:=sc.Name+"-"+rules;caseDir:=filepath.Join(*out,name);must(os.Mkdir(caseDir,0755));befores:=map[string][]byte{}
  for _,mode:=range []string{"baseline","blind","aware"}{
   dir:=filepath.Join(caseDir,mode);must(os.Mkdir(dir,0755));m:=machine.New();d:=dos.New(m,*root);d.Install();must(state.Load(*input,m,d));start:=m.Steps;initialized,dispatched,decided,executing:=false,false,false,false;nextKey:=0;var ds uint16;var view policyView;var decision *policyDecision;var prediction policyCandidate;var returnCS,returnIP,returnSS,returnSP uint16;var beforeUnits,stack []uint16;changes:=[]map[string]any{};damage:=[]map[string]any{};hookIP:=uint16(0)
   mutate:=func(seg,off,value uint16,phase string){old:=words(m,seg,off,1)[0];if old==value{return};m.Write16(uint32(seg)*16+uint32(off),value);changes=append(changes,map[string]any{"Segment":seg,"Offset":off,"Old":old,"New":value,"Phase":phase,"Step":m.Steps})}
   for m.Steps<start+40000000{
    if nextKey<6&&m.Steps>=start+uint64(nextKey)*2000000{m.PushKey(0x39);nextKey++};c:=m.CPU
    if !initialized&&c.Seg[cpu.CS]==0xf67&&c.IP==0x216a{
     ds=c.Seg[cpu.DS]
     for id:=uint16(0);id<6;id++{n:=uint16(0);if id==sc.Source{n=50};mutate(ds,0x5702+id*4,n,"fixture")};mutate(ds,0x5700+sc.Source*4,sc.Kind,"fixture")
     for i:=0;i<3;i++{mutate(ds,0x56e8+uint16(i*4),sc.Kinds[i],"fixture");mutate(ds,0x56ea+uint16(i*4),sc.Counts[i],"fixture")}
     for i,id:=range sc.Mapping{mutate(ds,0x6fb6+uint16(i*2),id,"fixture")};initialized=true
    }
    if initialized&&sc.Selector>=0&&!dispatched&&c.Seg[cpu.CS]==0xf67&&c.IP==0xd88{mutate(c.Seg[cpu.SS],c.R[cpu.BP]-4,uint16(sc.Selector),"dispatch");dispatched=true}
    if route,ok:=hooks[c.IP];ok&&initialized&&!decided&&c.Seg[cpu.CS]==0xf67{
     if (sc.Selector<0&&route=="special")||(sc.Selector>=0&&route!="special"){panic("unexpected route")};at:=0xe57*16+int(c.IP);expected:=code[at:at+24];actual:=m.Mem[0xf67*16+int(c.IP):0xf67*16+int(c.IP)+24];if !bytes.Equal(actual,expected){panic("target bytes")}
     offset:=c.R[cpu.BP]-4;if route=="special"{offset=c.R[cpu.BP]-8};target:=words(m,c.Seg[cpu.SS],offset,1)[0];if route!="special"{if target<7||target>12{panic("encoded target")};target-=7}
     view=capture(m,sc,route,target);view.Formation=rules=="formation"&&mode=="aware";hookIP=c.IP;must(state.Save(filepath.Join(dir,"before-decision.state"),m,d));must(os.WriteFile(filepath.Join(dir,"before-decision-ram.bin"),m.Mem,0644))
     selected:=target
     if mode!="baseline"{v,e:=evaluatePolicy(view);must(e);decision=&v;selected=v.SuggestedSlot;value:=selected;if route!="special"{value+=7};mutate(c.Seg[cpu.SS],offset,value,"policy-target")}
     actualView:=view;actualView.Formation=rules=="formation";prediction,err=policyPredict(actualView,selected);must(err)
     must(state.Save(filepath.Join(dir,"after-decision.state"),m,d));must(os.WriteFile(filepath.Join(dir,"after-decision-ram.bin"),m.Mem,0644));decided=true
    }
    if decided&&c.Seg[cpu.CS]==0xf67&&c.IP==0x1560{
     at:=0xe57*16+0x1560;if !bytes.Equal(m.Mem[0xf67*16+0x1560:0xf67*16+0x1560+24],code[at:at+24]){panic("damage bytes")}
     id:=words(m,c.Seg[cpu.SS],c.R[cpu.BP]+8,1)[0];slot:=-1;mapping:=words(m,ds,0x6fb6,6);for i,n:=range mapping{if n==id{slot=i}}
     eligible:=false;if slot>=0&&slot<3&&words(m,ds,0x56e8+id*4,1)[0]==1&&words(m,ds,0x56ea+id*4,1)[0]>0{for i:=0;i<3;i++{if i!=slot&&words(m,ds,0x56ea+mapping[i]*4,1)[0]>0{eligible=true}}}
     before:=c.R[cpu.AX];if rules=="formation"&&eligible{c.R[cpu.AX]=uint16(uint32(before)*80/100)};damage=append(damage,map[string]any{"Step":m.Steps,"Unit":id,"Slot":slot,"Eligible":eligible,"Original":before,"Adjusted":c.R[cpu.AX],"InsideExecutor":executing})
    }
    if decided&&!executing&&c.Seg[cpu.CS]==0xf67&&(c.IP==0x4626||c.IP==0x36c6){stack=words(m,c.Seg[cpu.SS],c.R[cpu.SP],8);returnIP,returnCS,returnSS,returnSP=stack[0],stack[1],c.Seg[cpu.SS],c.R[cpu.SP]+4;beforeUnits=words(m,ds,0x56e8,24);executing=true}
    if executing&&c.Seg[cpu.CS]==returnCS&&c.IP==returnIP&&c.Seg[cpu.SS]==returnSS&&c.R[cpu.SP]==returnSP{break};must(m.Step())
   }
   if !executing||m.CPU.Seg[cpu.CS]!=returnCS||m.CPU.IP!=returnIP{panic("incomplete effect")};after:=words(m,ds,0x56e8,24);want:=slices.Clone(beforeUnits);want[prediction.Unit*2+1]-=prediction.Loss;if want[prediction.Unit*2+1]==0{want[prediction.Unit*2]=0};if !slices.Equal(want,after){panic(fmt.Sprintf("prediction mismatch %s %s: %+v",name,mode,prediction))}
   must(state.Save(filepath.Join(dir,"final.state"),m,d));final,err:=os.ReadFile(filepath.Join(dir,"final.state"));must(err);befores[mode],err=os.ReadFile(filepath.Join(dir,"before-decision.state"));must(err)
   result:=map[string]any{"Case":sc.Name,"Rules":rules,"Mode":mode,"Scenario":sc,"View":view,"Decision":decision,"Prediction":prediction,"BeforeUnits":beforeUnits,"AfterUnits":after,"Changes":changes,"Damage":damage,"StartStep":start,"EndStep":m.Steps,"HookIP":hookIP,"ExecutorStack":stack,"StateSHA256":hash(final),"GoVersion":runtime.Version(),"PAMSHA256":hash(pam),"InputSHA256":hash(raw)};write(filepath.Join(dir,"trace.json"),result);rows=append(rows,result);d.Close()
  }
  if !bytes.Equal(befores["baseline"],befores["blind"])||!bytes.Equal(befores["blind"],befores["aware"]){panic("different decision initial states")}
 }}
 write(filepath.Join(*out,"summary.json"),map[string]any{"status":"DRAFT-original-executor-controls","rows":rows,"cases":len(formationCases),"calls":len(rows)});fmt.Printf("original executor controls passed: %d\n",len(rows))
}
