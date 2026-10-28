// 030 DRAFT: bounded branch fixtures; original instructions execute all actions.
package main

import (
 "bytes"
 "crypto/sha256"
 "encoding/binary"
 "encoding/hex"
 "encoding/json"
 "flag"
 "fmt"
 "os"
 "path/filepath"
 "runtime"
 "strings"
 "github.com/wicanr2/dosgolem/internal/cpu"
 "github.com/wicanr2/dosgolem/internal/dos"
 "github.com/wicanr2/dosgolem/internal/machine"
 "github.com/wicanr2/dosgolem/internal/state"
)
type scenario struct {Name string; Slot,Kind uint16; PlayerRear bool; Variant int; Count uint16}
var scenarios=[]scenario{
 {"front-3",0,3,false,-1,50},{"front-24",0,24,false,-1,50},
 {"rear-3",3,3,false,-1,50},{"rear-24",3,24,false,-1,50},
 {"rear-10",3,10,false,-1,50},{"rear-12",3,12,false,-1,50},
 {"rear-ineligible-6",3,6,false,-1,50},
 {"front-to-rear",0,6,true,-1,50},{"ranged-to-rear",0,3,true,-1,50},
 {"special-12-case0",3,12,false,0,50},{"special-12-case6",3,12,false,6,50},
 {"special-10-case6-49",3,10,false,6,49},{"special-10-case6-50",3,10,false,6,50},
}
func must(e error){if e!=nil{panic(e)}}
func hash(b []byte)string{return fmt.Sprintf("%x",sha256.Sum256(b))}
func write(path string,v any){b,e:=json.MarshalIndent(v,"","  ");must(e);must(os.WriteFile(path,append(b,'\n'),0644))}
func jhash(v any)string{b,e:=json.Marshal(v);must(e);return hash(b)}
func words(m *machine.Machine,seg,off uint16,n int)[]uint16{v:=make([]uint16,n);for i:=range v{v[i]=m.Read16(uint32(seg)*16+uint32(off+uint16(i*2)))};return v}
func snapshot(m *machine.Machine,name string)map[string]any{
 c:=m.CPU;ds:=c.Seg[cpu.DS];local:=[]uint16{};for i:=uint16(2);i<=24;i+=2{local=append(local,m.Read16(uint32(c.Seg[cpu.SS])*16+uint32(c.R[cpu.BP]-i)))}
 return map[string]any{"name":name,"step":m.Steps,"cs":c.Seg[cpu.CS],"ip":c.IP,"registers":c.R,"segments":c.Seg,"stack_words":words(m,c.Seg[cpu.SS],c.R[cpu.SP],16),"bp_minus_2_through_12":local[:6],"bp_minus_2_through_24":local,"ds_56e8_words":words(m,ds,0x56e8,24),"ds_6fa8_words":words(m,ds,0x6fa8,19),"ds_8e78_words":words(m,ds,0x8e78,6),"ds_26ac_word":words(m,ds,0x26ac,1)[0],"ds_70ce_words":words(m,ds,0x70ce,52),"ds_8ca4_words":words(m,ds,0x8ca4,6),"ds_8cb0_words":words(m,ds,0x8cb0,16)}
}
func main(){
 root:=flag.String("root","","read-only original");input:=flag.String("state","","fixed multi snapshot");out:=flag.String("out","","new batch output");only:=flag.String("only","","optional exact comma-separated scenario names");flag.Parse()
 if _,e:=os.Stat(*out);!os.IsNotExist(e){panic("output exists")};must(os.Mkdir(*out,0755))
 raw,e:=os.ReadFile(*input);must(e);if hash(raw)!="88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf"{panic("fixture mismatch")}
 pam,e:=os.ReadFile(filepath.Join(*root,"PAM.AY"));must(e);if hash(pam)!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"{panic("PAM mismatch")}
 u16:=func(at int)uint16{return binary.LittleEndian.Uint16(pam[at:at+2])};header:=int(u16(8))*16;code:=append([]byte(nil),pam[header:]...)
 for i:=0;i<int(u16(6));i++{at:=int(u16(24))+i*4;loc:=int(u16(at+2))*16+int(u16(at));v:=binary.LittleEndian.Uint16(code[loc:loc+2]);binary.LittleEndian.PutUint16(code[loc:loc+2],v+0x110)}
 targets:=map[uint16]string{0x216a:"sub_206DA",0x15fc:"sub_1FB6C",0x1532:"sub_1FAA2",0x484c:"sub_22DBC",0x4626:"sub_22B96",0x0cf6:"sub_1F266",0x0d88:"special-dispatch",0x16e7:"front-ranged-normalize",0x1974:"rear-ranged-normalize",0x180a:"normal-normalize",0x36c6:"sub_21C36",0x10d1:"special-growth-plan"}
 functions:=map[uint16]bool{0x216a:true,0x15fc:true,0x1532:true,0x484c:true,0x4626:true,0x0cf6:true,0x36c6:true}
 type returnKey struct{CS,IP,SS,SP uint16}
 results:=[]map[string]any{}
 for _,sc:=range scenarios{
  if *only!=""&&!strings.Contains(","+*only+",",","+sc.Name+","){continue}
  caseDir:=filepath.Join(*out,sc.Name);must(os.Mkdir(caseDir,0755));states:=map[string][]byte{};summaries:=map[string]any{}
  for _,observe:=range []bool{true,false}{
   label:="control";if observe{label="observed"};dir:=filepath.Join(caseDir,label);must(os.Mkdir(dir,0755));m:=machine.New();d:=dos.New(m,*root);d.Install();must(state.Load(*input,m,d));start:=m.Steps
   prefixes:=[]map[string]any{};for ip,name:=range targets{loc:=0xf67*16+int(ip)-0x1100;actual:=make([]byte,24);for i:=range actual{actual[i]=m.Read8(0xf67*16+uint32(ip)+uint32(i))};if !bytes.Equal(actual,code[loc:loc+24]){panic("prefix mismatch")};prefixes=append(prefixes,map[string]any{"name":name,"runtime_ip":ip,"ida_linear":0x1e570+uint32(ip),"file_offset":header+loc,"bytes":hex.EncodeToString(actual)})}
   events:=[]map[string]any{};changes:=[]map[string]any{};writes:=[]map[string]any{};returns:=map[returnKey]string{};initialized:=false;variantSet:=false;nextKey:=0;overflow:=false;stop:="step-bound";var roundReturn returnKey;var ds uint16
   mutate:=func(seg,off,value uint16,phase string){old:=m.Read16(uint32(seg)*16+uint32(off));if old==value{return};changes=append(changes,map[string]any{"phase":phase,"step":m.Steps,"segment":seg,"offset":off,"old":old,"new":value});m.Write16(uint32(seg)*16+uint32(off),value)}
   for m.Steps<start+40000000{
    if nextKey<6&&m.Steps>=start+uint64(nextKey)*2000000{m.PushKey(0x39);nextKey++}
    c:=m.CPU;k:=returnKey{c.Seg[cpu.CS],c.IP,c.Seg[cpu.SS],c.R[cpu.SP]}
    if !initialized&&c.Seg[cpu.CS]==0xf67&&c.IP==0x216a{
     ds=c.Seg[cpu.DS];ret:=words(m,c.Seg[cpu.SS],c.R[cpu.SP],2);roundReturn=returnKey{ret[1],ret[0],c.Seg[cpu.SS],c.R[cpu.SP]+4};must(state.Save(filepath.Join(dir,"before-fixture.state"),m,d))
     for unit:=uint16(0);unit<6;unit++{count:=uint16(0);if unit==sc.Slot{count=sc.Count};mutate(ds,0x5702+unit*4,count,"fixture")};mutate(ds,0x5700+sc.Slot*4,sc.Kind,"fixture")
     if sc.PlayerRear{for i,v:=range []uint16{5,5,5,0,1,5}{mutate(ds,0x6fb6+uint16(i*2),v,"fixture")}}
     must(state.Save(filepath.Join(dir,"after-fixture.state"),m,d));initialized=true
     if observe{base:=uint32(ds)*16;for _,region:=range [][2]uint32{{0x56e8,0x5717},{0x6fb6,0x6fcd},{0x8ca4,0x8ccf},{0x8e78,0x8e83}}{m.WatchWrite(base+region[0],base+region[1],func(mm *machine.Machine,addr uint32,old,next uint8){if len(writes)>=4096{overflow=true;return};cs,ip:=mm.Insn();writes=append(writes,map[string]any{"step":mm.Steps,"cs":cs,"ip":ip,"offset":addr-base,"old":old,"new":next})})}}
    }
    if initialized&&c.Seg[cpu.CS]==0xf67&&c.IP==0xd88&&sc.Variant>=0&&!variantSet{mutate(c.Seg[cpu.SS],c.R[cpu.BP]-4,uint16(sc.Variant),"dispatch");variantSet=true}
    if observe{if name,ok:=returns[k];ok{delete(returns,k);if len(events)<512{events=append(events,snapshot(m,name+":return"))}else{overflow=true}};if c.Seg[cpu.CS]==0xf67{if name,ok:=targets[c.IP];ok{if len(events)<512{events=append(events,snapshot(m,name))}else{overflow=true};if functions[c.IP]{ret:=words(m,c.Seg[cpu.SS],c.R[cpu.SP],2);returns[returnKey{ret[1],ret[0],c.Seg[cpu.SS],c.R[cpu.SP]+4}]=name}}}}
    if initialized&&k==roundReturn{stop="round-return";break}
    if e:=m.Step();e!=nil{stop=e.Error();break}
   }
   if !initialized{panic("no AI entry")};must(state.Save(filepath.Join(dir,"final.state"),m,d));final,e:=os.ReadFile(filepath.Join(dir,"final.state"));must(e);states[label]=final
   summary:=map[string]any{"stop":stop,"start_step":start,"end_step":m.Steps,"state_sha256":hash(final),"opl_sha256":jhash(m.OPL),"ports_sha256":jhash(m.PortLog),"dos_sha256":jhash(d.CallTrace),"units":words(m,ds,0x56e8,24),"mapping":words(m,ds,0x6fb6,12),"action_flags":words(m,ds,0x8e78,6),"changes":changes,"variant_forced":variantSet,"keys_queued":nextKey};summaries[label]=summary
   write(filepath.Join(dir,"trace.json"),map[string]any{"schema":1,"scenario":sc,"go_version":runtime.Version(),"source_state_sha256":hash(raw),"observer_guest_writes":false,"controller_changes":changes,"summary":summary,"prefixes":prefixes,"events":events,"writes":writes,"overflow":overflow})
  }
  equal:=bytes.Equal(states["observed"],states["control"]);equalIO:=true;for _,key:=range []string{"opl_sha256","ports_sha256","dos_sha256"}{if summaries["observed"].(map[string]any)[key]!=summaries["control"].(map[string]any)[key]{equalIO=false}}
  result:=map[string]any{"scenario":sc,"state_equal":equal,"io_equal":equalIO,"results":summaries};write(filepath.Join(caseDir,"paired.json"),result);results=append(results,result)
  if !equal||!equalIO{panic("observer changed outcome")};fmt.Printf("%s: %s state_equal=true\n",sc.Name,summaries["observed"].(map[string]any)["stop"])
 }
 write(filepath.Join(*out,"summary.json"),map[string]any{"schema":1,"spec":"030 DRAFT","source_sha256":hash(raw),"controlled_fixtures":true,"production_changed":false,"cases":results})
}
