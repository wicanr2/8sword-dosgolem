//go:build ignore
// Original11650..116A8, controlled third roll, before drawing/waiting.
package main
import("crypto/sha256";"encoding/binary";"fmt";"os";dg "github.com/wicanr2/dosgolem")
func main(){
 if os.Getuid()!=1000||len(os.Args)!=3{panic("UID/args")};if _,e:=os.Stat("/.dockerenv");e!=nil{panic(e)}
 pam,e:=os.ReadFile(os.Args[1]);if e!=nil{panic(e)};if fmt.Sprintf("%x",sha256.Sum256(pam))!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"{panic("PAM")}
 word:=func(at int)uint16{return binary.LittleEndian.Uint16(pam[at:])};code:=append([]byte(nil),pam[int(word(8))*16:]...)
 for i:=0;i<int(word(6));i++{at:=int(word(24))+4*i;p:=int(word(at+2))*16+int(word(at));binary.LittleEndian.PutUint16(code[p:],binary.LittleEndian.Uint16(code[p:])+0x110)}
 out,e:=os.OpenFile(os.Args[2],os.O_CREATE|os.O_EXCL|os.O_WRONLY,0644);if e!=nil{panic(e)};defer out.Close()
 fmt.Fprintln(out,"# LOSS roll gold after stolen rand_calls; ARMY slot count protected; original11650..116A8; explicit scalar replaces third_rand only; text skipped; no GUI/full-flow RNG parity")
 run:=func(roll,gold uint16,slot int,count uint16)(bool,uint16,uint16,int){
  m:=dg.New();copy(m.Mem[0x1100:],code);m.CPU.Seg[dg.CS]=0x110;m.CPU.Seg[dg.DS]=0x1e88;m.CPU.Seg[dg.SS]=0x1e88;m.CPU.R[dg.BP]=0xee00;m.CPU.R[dg.SP]=0xedc0
  set:=func(at uint32,n uint16){m.Write16(0x1e880+at,n)};get:=func(at uint32)uint16{return m.Read16(0x1e880+at)}
  for i:=0;i<6;i++{set(uint32(0x54a+i*4),0)};if slot>=0{set(uint32(0x54a+slot*4),count)};set(0x4f8,gold);set(0xedfe,1);m.CPU.IP=0x1650
  randAt:=uint32(m.Read16(0x1100+0x168b+3))*16+uint32(m.Read16(0x1100+0x168b+1));calls:=0
  for n:=0;n<1000;n++{
   if m.CPU.Seg[dg.CS]==0x110{if m.CPU.IP==0x16e0{return true,get(0x4f8),0,calls};if m.CPU.IP==0x16a8{return false,get(0x4f8),get(0xedfa),calls}}
   if m.CPU.Seg[dg.CS]!=0x110{
    if uint32(m.CPU.Seg[dg.CS])*16+uint32(m.CPU.IP)==randAt{m.CPU.R[dg.AX]=roll;calls++}
    at:=uint32(m.CPU.Seg[dg.SS])*16+uint32(m.CPU.R[dg.SP]);m.CPU.IP=m.Read16(at);m.CPU.Seg[dg.CS]=m.Read16(at+2);m.CPU.R[dg.SP]+=4;continue
   };if e:=m.Step();e!=nil{panic(e)}
  };panic("instruction budget")
 }
 rolls:=[]uint16{0};for b:=uint16(2730);b<=32760;b+=2730{rolls=append(rolls,b-1,b)};rolls=append(rolls,32767)
 for _,roll:=range rolls{for _,gold:=range []uint16{0,1,2,13,14,27,75,499,500,29999,30000}{protected,after,stolen,calls:=run(roll,gold,-1,0);if protected{panic("empty army protected")};fmt.Fprintf(out,"LOSS\t%d\t%d\t%d\t%d\t%d\n",roll,gold,after,stolen,calls)}}
 for slot:=0;slot<6;slot++{for _,count:=range []uint16{0,1,32767}{protected,_,_,_:=run(0,500,slot,count);p:=0;if protected{p=1};fmt.Fprintf(out,"ARMY\t%d\t%d\t%d\n",slot,count,p)}}
}
