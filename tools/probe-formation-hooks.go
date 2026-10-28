// 030 DRAFT: isolated original helper calls; no claim of normal combat flow.
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

 "github.com/wicanr2/dosgolem/internal/cpu"
 "github.com/wicanr2/dosgolem/internal/dos"
 "github.com/wicanr2/dosgolem/internal/machine"
 "github.com/wicanr2/dosgolem/internal/state"
)
func must(e error){if e!=nil{panic(e)}}
func sha(b []byte)string{return fmt.Sprintf("%x",sha256.Sum256(b))}
func write(p string,v any){b,e:=json.MarshalIndent(v,"","  ");must(e);must(os.WriteFile(p,append(b,'\n'),0644))}
func main(){
 root:=flag.String("root","","read-only original");input:=flag.String("state","","fixed original snapshot");out:=flag.String("out","","new output");flag.Parse()
 if _,e:=os.Stat(*out);!os.IsNotExist(e){panic("output exists")};must(os.Mkdir(*out,0755))
 raw,e:=os.ReadFile(*input);must(e);if sha(raw)!="88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf"{panic("snapshot mismatch")}
 pam,e:=os.ReadFile(filepath.Join(*root,"PAM.AY"));must(e);if sha(pam)!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"{panic("source mismatch")}
 word:=func(at int)uint16{return binary.LittleEndian.Uint16(pam[at:])};header:=int(word(8))*16;code:=append([]byte(nil),pam[header:]...)
 for i:=0;i<int(word(6));i++{at:=int(word(24))+i*4;loc:=int(word(at+2))*16+int(word(at));binary.LittleEndian.PutUint16(code[loc:],binary.LittleEndian.Uint16(code[loc:])+0x110)}
 all:=[]map[string]any{}
 for _,side:=range []string{"player","enemy"}{for _,name:=range []string{"front-ally","alone","rear-ally","rear-target","other-kind","two-allies"}{
  dir:=filepath.Join(*out,side+"-"+name);must(os.Mkdir(dir,0755));finals:=map[string][]byte{};ioHashes:=map[string]string{}
  for _,mode:=range []string{"baseline","observe","formation"}{
   dest:=filepath.Join(dir,mode);must(os.Mkdir(dest,0755));m:=machine.New();d:=dos.New(m,*root);d.Install();must(state.Load(*input,m,d));ds:=uint16(0x1e88)
   get:=func(off uint16)uint16{return m.Read16(uint32(ds)*16+uint32(off))};put:=func(off,v uint16){m.Write16(uint32(ds)*16+uint32(off),v)}
   for i:=uint16(0);i<6;i++{put(0x56e8+i*4,0);put(0x56ea+i*4,0);put(0x5700+i*4,0);put(0x5702+i*4,0);put(0x6fb6+i*2,i);put(0x6fc2+i*2,i)}
   units,slots,accumulator:=uint16(0x56e8),uint16(0x6fb6),uint16(0x8ca4);attackUnits:=uint16(0x5700);entry,hook:=uint16(0x1532),uint16(0x1560)
   if side=="enemy"{units,slots,accumulator,attackUnits=0x5700,0x6fc2,0x8e60,0x56e8;entry,hook=0x1592,0x15ca}
   put(units,1);put(units+2,31);put(attackUnits,6);put(attackUnits+2,50);put(units+4,21);put(units+6,69)
   switch name{case "alone":put(units+6,0);case "rear-ally":put(slots+2,3);put(slots+6,1);case "rear-target":put(slots,3);put(slots+6,0);case "other-kind":put(units,2);case "two-allies":put(units+8,2);put(units+10,10)}
   put(0x26ac,0);put(0x26b2,0);put(0x26b8,0);hp:=get(0x70d0+get(units)*4);put(accumulator,hp*31)
   m.CPU.Seg[cpu.CS]=0xf67;m.CPU.Seg[cpu.DS]=ds;m.CPU.Seg[cpu.SS]=ds;m.CPU.IP=entry;m.CPU.R[cpu.SP]=0xe000
   put(0xe000,0xfff0);put(0xe002,0xf67);put(0xe004,0);put(0xe006,0)
   at:=0xe57*16+int(hook);prefix:=make([]byte,24);for i:=range prefix{prefix[i]=m.Read8(0xf67*16+uint32(hook)+uint32(i))};if !bytes.Equal(prefix,code[at:at+24]){panic("hook bytes mismatch")}
   must(state.Save(filepath.Join(dest,"start-call.state"),m,d))
   start:=m.Steps;seen:=false;eligible:=false;beforeAmount,afterAmount:=uint16(0),uint16(0);var beforeRegs,afterRegs []uint16;beforeRAM,afterRAM:="",""
   for m.Steps<start+10000{
    c:=m.CPU
    if c.Seg[cpu.CS]==0xf67&&c.IP==hook{
     if seen{panic("duplicate helper point")};seen=true;beforeAmount=c.R[cpu.AX];afterAmount=beforeAmount
     if get(c.R[cpu.BP]+6)!=0||get(c.R[cpu.BP]+8)!=0{panic("unexpected helper arguments")}
     targetSlot:=-1
     for i:=0;i<6;i++{if get(slots+uint16(i*2))==0{targetSlot=i}}
     if get(units)==1&&get(units+2)>0&&targetSlot>=0&&targetSlot<3{
      for i:=0;i<3;i++{id:=get(slots+uint16(i*2));if i!=targetSlot&&id!=0&&get(units+id*4+2)>0{eligible=true}}
     }
     if mode!="baseline"{
      beforeRegs=append([]uint16(nil),c.R[:]...);beforeRAM=sha(m.Mem);must(state.Save(filepath.Join(dest,"before-hook.state"),m,d))
      if mode=="formation"&&eligible{c.R[cpu.AX]=uint16(uint32(beforeAmount)*80/100)}
      afterAmount=c.R[cpu.AX];afterRegs=append([]uint16(nil),c.R[:]...);afterRAM=sha(m.Mem);if beforeRAM!=afterRAM{panic("controller wrote RAM")};for i:=range beforeRegs{if i!=cpu.AX&&beforeRegs[i]!=afterRegs[i]{panic("controller changed other register")}}
      must(state.Save(filepath.Join(dest,"after-hook.state"),m,d))
     }
    }
    if seen&&c.Seg[cpu.CS]==0xf67&&c.IP==0xfff0{break};must(m.Step())
   }
   if !seen||m.CPU.IP!=0xfff0{panic("helper failed to return")};expected:=uint16(afterAmount/hp+1);if m.CPU.R[cpu.AX]!=expected||get(accumulator)!=hp*31-afterAmount||get(units+2)!=31{panic("original helper did not consume proposed amount")}
   must(state.Save(filepath.Join(dest,"final.state"),m,d));final,e:=os.ReadFile(filepath.Join(dest,"final.state"));must(e);finals[mode]=final
   io,e:=json.Marshal([]any{m.OPL,m.PortLog,d.CallTrace});must(e);ioHashes[mode]=sha(io)
   trace:=map[string]any{"side":side,"case":name,"mode":mode,"entry_ip":entry,"hook_ip":hook,"hook_bytes":fmt.Sprintf("%x",prefix),"eligible":eligible,"amount_before":beforeAmount,"amount_after":afterAmount,"hp":hp,"encoded_return":m.CPU.R[cpu.AX],"remaining_total_hp":get(accumulator),"unit_count_unchanged":get(units+2),"before_registers":beforeRegs,"after_registers":afterRegs,"before_ram_sha256":beforeRAM,"after_ram_sha256":afterRAM,"final_state_sha256":sha(final),"io_sha256":ioHashes[mode],"steps":m.Steps-start,"go_version":runtime.Version()};write(filepath.Join(dest,"trace.json"),trace);all=append(all,trace)
  }
  if !bytes.Equal(finals["baseline"],finals["observe"])||ioHashes["baseline"]!=ioHashes["observe"]||ioHashes["baseline"]!=ioHashes["formation"]{panic("read-only/control I/O differs")}
 }
 }
 write(filepath.Join(*out,"summary.json"),map[string]any{"status":"isolated-original-helper-calls-only","runs":all,"input_sha256":sha(raw),"pam_sha256":sha(pam),"production_changed":false});fmt.Println("36 isolated original helper calls passed")
}
