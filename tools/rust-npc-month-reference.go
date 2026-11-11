//go:build ignore

// Fixed-PAM local NPC instructions and the existing real monthly caller frame.
package main
import("encoding/binary";"encoding/json";"fmt";"os";"path/filepath";"crypto/sha256";dg "github.com/wicanr2/dosgolem";"github.com/wicanr2/dosgolem/oracle")
func must(e error){if e!=nil{panic(e)}}
func main(){
 if os.Getuid()!=1000||len(os.Args)!=4{panic("UID1000: game state out")};root,state,out:=os.Args[1],os.Args[2],os.Args[3];pam,e:=os.ReadFile(filepath.Join(root,"PAM.AY"));must(e);if fmt.Sprintf("%x",sha256.Sum256(pam))!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"{panic("PAM")};word:=func(at int)uint16{return binary.LittleEndian.Uint16(pam[at:])};code:=append([]byte(nil),pam[int(word(8))*16:]...)
 for i:=0;i<int(word(6));i++{at:=int(word(24))+4*i;p:=int(word(at+2))*16+int(word(at));binary.LittleEndian.PutUint16(code[p:],binary.LittleEndian.Uint16(code[p:])+0x110)}
 must(os.Mkdir(out,0755));ts,e:=os.OpenFile(filepath.Join(out,"npc-month-reference.tsv"),os.O_CREATE|os.O_EXCL|os.O_WRONLY,0644);must(e);defer ts.Close();fmt.Fprintln(ts,"# case site slot before cap after; forced scalar boundaries include otherwise invalid kind/count combinations")
 bases:=[]uint32{0x365e,0x3706,0x3766,0x37c6,0x3826,0x3886,0x38e6,0x3946};sizes:=[]int{7,4,4,4,4,4,4,11}
 for c:=0;c<10;c++{m:=dg.New();copy(m.Mem[0x1100:],code);m.CPU.Seg[dg.CS]=0x110;m.CPU.Seg[dg.DS]=0x1e88;m.CPU.Seg[dg.SS]=0x1e88;m.CPU.R[dg.BP]=0xed00;m.CPU.R[dg.SP]=0xecf8;m.Write16(0x1e880+0xed00,0);m.Write16(0x1e880+0xed02,0xfff0);m.Write16(0x1e880+0xed04,0x110);m.CPU.IP=0x29f9
  before:=[][3]uint16{};site:=0
  for area,b:=range bases{for i:=0;i<sizes[area];i++{for slot:=0;slot<6;slot++{at:=b+uint32(i*24+slot*4)+2;cap:=m.Read16(0x1e880+at-0x3f0);n:=[]uint16{cap,0,1,2,9,10,29,24575,24576,32767}[c];if c==6{n=cap+5};before=append(before,[3]uint16{n,cap,uint16(at)});m.Write16(0x1e880+at,n)};site++}}
  if site!=42{panic("sites")};for step:=0;step<20000;step++{if m.CPU.Seg[dg.CS]==0x110&&m.CPU.IP==0xfff0{break};must(m.Step());if step==19999{panic("NPC budget")}}
  for i,v:=range before{fmt.Fprintf(ts,"%d\t%d\t%d\t%d\t%d\t%d\n",c,i/6,i%6,v[0],v[1],m.Read16(0x1e880+uint32(v[2])))}
 }
 controls:=[]map[string]any{}
 for _,counter:=range []uint16{0,35,375,65535}{
  o,e:=oracle.LoadWith(filepath.Join(root,"PAM.AY"),root,oracle.Options{Adlib:true});must(e);must(o.LoadStateFile(state));scratch:=filepath.Join(out,fmt.Sprint("month-",counter));must(os.Mkdir(scratch,0755));o.SetScratch(scratch);regs:=o.Regs();commonBP:=regs.BP;wrapperBP:=o.Word(oracle.Far(0x1e88,commonBP));outerBP:=o.Word(oracle.Far(0x1e88,wrapperBP));if o.Word(oracle.Far(0x1e88,commonBP+2))!=0x5a21||o.Word(oracle.Far(0x1e88,wrapperBP+2))!=0x25b1||o.Word(oracle.Far(0x1e88,outerBP+2))!=0xbc7{panic("real frame")}
  o.OnHostInstruction(oracle.Far(0x110,0x56ec),func(m *dg.Machine)(bool,error){m.CPU.R[dg.BP]=outerBP;m.CPU.R[dg.SP]=outerBP-18;m.CPU.IP=0x26d6;m.Write16(0x1e880+uint32(outerBP)-2,0);m.Write16(0x1e880+uint32(outerBP)-10,0);m.CPU.Cycles++;return true,nil});must(o.RunUntil(oracle.At(oracle.Far(0x110,0x26d6)),oracle.Budget(16)))
  o.WriteU16(oracle.Far(0x1e88,0x56da),1);o.WriteU16(oracle.Far(0x1e88,0x56e6),counter);o.WriteU16(oracle.Far(0x1e88,0x81bc),0x5678);o.WriteU16(oracle.Far(0x1e88,0x81be),0x1234)
  calls:=[]map[string]any{};randAt:=oracle.Far(binary.LittleEndian.Uint16(code[0x173d:]),binary.LittleEndian.Uint16(code[0x173b:]));if randAt.Linear()!=0x1a63e{panic("rand address")}
  o.OnCall(randAt,func(q *oracle.Oracle){r:=q.Regs();calls=append(calls,map[string]any{"return_segment":q.Word(oracle.Far(r.SS,r.SP+2)),"return_offset":q.Word(oracle.Far(r.SS,r.SP)),"step":q.Steps(),"seed_before":uint32(q.Word(oracle.Far(0x1e88,0x81bc)))|uint32(q.Word(oracle.Far(0x1e88,0x81be)))<<16})})
  must(o.SaveStateFile(filepath.Join(scratch,"before.state")));must(o.RunUntil(oracle.At(oracle.Far(0x110,0x284d)),oracle.Budget(6000000)));must(o.SaveStateFile(filepath.Join(scratch,"after.state")))
  if counter==0{must(os.WriteFile(filepath.Join(out,"travel-ticks-source.bin"),o.Bytes(oracle.Far(0x7000,0xfeec),57),0644))}
  controls=append(controls,map[string]any{"counter_before":counter,"counter_after":o.Word(oracle.Far(0x1e88,0x56e6)),"remaining":o.Word(oracle.Far(0x1e88,0x56da)),"tempo":o.Word(oracle.Far(0x1e88,0x56dc)),"seed_before":uint32(0x12345678),"seed_after":uint32(o.Word(oracle.Far(0x1e88,0x81bc)))|uint32(o.Word(oracle.Far(0x1e88,0x81be)))<<16,"rand_calls":calls})
 }
 raw,e:=json.MarshalIndent(map[string]any{"status":"passed-original-npc-month-probe","scalar_vectors":2520,"source_sha256":fmt.Sprintf("%x",sha256.Sum256(pam)),"controls":controls,"scope":"NPC body129F9 uses explicit6byte locals and savedSI; monthly uses existing real caller frame, fixed seed before run, no rerolls; source bytes and clock otherwise retained"},"","  ");must(e);must(os.WriteFile(filepath.Join(out,"receipt.json"),append(raw,'\n'),0644));fmt.Println(string(raw))
}
