//go:build ignore
// Local original guard entry and reward scalars. Draw/IO and battle skipped.
package main
import("crypto/sha256";"encoding/binary";"fmt";"os";"strings";"strconv";dg "github.com/wicanr2/dosgolem")
func main(){
 if os.Getuid()!=1000||len(os.Args)!=4{panic("UID/args")};if _,e:=os.Stat("/.dockerenv");e!=nil{panic(e)}
 pam,e:=os.ReadFile(os.Args[1]);if e!=nil{panic(e)};if fmt.Sprintf("%x",sha256.Sum256(pam))!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"{panic("PAM")};word:=func(at int)uint16{return binary.LittleEndian.Uint16(pam[at:])};code:=append([]byte(nil),pam[int(word(8))*16:]...)
 for i:=0;i<int(word(6));i++{at:=int(word(24))+4*i;p:=int(word(at+2))*16+int(word(at));binary.LittleEndian.PutUint16(code[p:],binary.LittleEndian.Uint16(code[p:])+0x110)}
 fresh:=func()*dg.Machine{m:=dg.New();copy(m.Mem[0x1100:],code);m.CPU.Seg[dg.CS]=0x110;m.CPU.Seg[dg.DS]=0x1e88;m.CPU.Seg[dg.SS]=0x1e88;m.CPU.R[dg.SP]=0xee00;m.CPU.R[dg.BP]=0xed00;m.Write16(0x2d680,0xfff0);m.Write16(0x2d682,0x110);return m}
 ret:=func(m *dg.Machine){at:=uint32(m.CPU.Seg[dg.SS])*16+uint32(m.CPU.R[dg.SP]);m.CPU.IP=m.Read16(at);m.CPU.Seg[dg.CS]=m.Read16(at+2);m.CPU.R[dg.SP]+=4}
 raw,e:=os.ReadFile(os.Args[2]);if e!=nil{panic(e)};rows:=[][]uint16{}
 for _,l:=range strings.Split(strings.TrimSpace(string(raw)),"\n"){if strings.HasPrefix(l,"#"){continue};v:=[]uint16{};for _,s:=range strings.Split(l,"\t"){n,e:=strconv.ParseUint(s,10,16);if e!=nil{panic(e)};v=append(v,uint16(n))};rows=append(rows,v)}
 out,e:=os.OpenFile(os.Args[3],os.O_CREATE|os.O_EXCL|os.O_WRONLY,0644);if e!=nil{panic(e)};defer out.Close();fmt.Fprintln(out,"# ENTER site facing mode phase(0return1cleared2noarmy3missing4battle) prompt_calls; modes cancel/yes/noarmy/cleared/allswords/allswords-noarmy. GAIN area book before_pay after_pay before_power after_power. RETREAT roll gold after. All local actual original instructions.")
 for site,v:=range rows{for facing:=uint16(1);facing<=4;facing++{for mode:=0;mode<7;mode++{
  m:=fresh();set:=func(at uint32,n uint16){m.Write16(0x1e880+at,n)};set(0x56d6,v[0]);set(0x56c4,facing);set(0x8e12,v[2]);set(0x8e44,v[3]);for i:=uint32(0);i<12;i++{set(0x8c30+i*4,65535);set(0x8c32+i*4,65535)};set(0x8c30+uint32(v[1])*4,v[2]);set(0x8c32+uint32(v[1])*4,v[3]);for i:=uint32(0);i<8;i++{set(0x275a+i*2,0);if mode==4||mode==5{set(0x275a+i*2,1)}};for i:=uint32(0);i<6;i++{set(0x54a+i*4,0);set(0x54c+i*4,0)};if mode!=2&&mode!=5{set(0x54a,1);set(0x54c,30)};if mode==3{for i:=uint32(0);i<12;i++{set(uint32(v[6])+i*2,0)}}
  if mode==6{set(0x8e12,v[2]-1)};m.CPU.R[dg.BP]=0xee00;m.CPU.R[dg.SP]=0xedee;set(0xee00,0);set(0xee02,0xfff0);set(0xee04,0x110);m.CPU.IP=0x2deb;phase,prompts,last:=-1,0,uint16(0)
  for n:=0;n<10000;n++{
   if m.CPU.Seg[dg.CS]==0x110{ip:=m.CPU.IP;if ip==0xfff0{phase=0;break};if ip==0x32e0{phase=4;break};if ip==0x844c{switch last{case 0x460e:phase=1;case 0x4633:phase=2;case 0x485e:phase=3;default:panic(fmt.Sprintf("unknown notice%x",last))};break};if ip==0x4442{prompts++;m.CPU.R[dg.AX]=1;if mode==0{m.CPU.R[dg.AX]=0};ret(m);continue};if ip==0x1f60||ip==0x6226||ip==0x716c{ret(m);continue}}
   if m.CPU.Seg[dg.CS]!=0x110{if uint32(m.CPU.Seg[dg.CS])*16+uint32(m.CPU.IP)==0x15803{last=m.Read16(0x1e880+uint32(m.CPU.R[dg.SP])+4)};ret(m);continue};if e:=m.Step();e!=nil{panic(e)}
  };if phase<0{panic("ENTER budget")};fmt.Fprintf(out,"ENTER\t%d\t%d\t%d\t%d\t%d\n",site,facing,mode,phase,prompts)
 }}}
 for area:=uint16(0);area<8;area++{for _,book:=range []uint16{0,1}{for _,before:=range []uint16{100,20000}{
  m:=fresh();m.Write16(0x1e880+0x56d6,area);m.Write16(0x1e880+0x4f6,before);m.CPU.IP=0x1b71
  for n:=0;n<30&&m.CPU.IP!=0x1b7f;n++{if e:=m.Step();e!=nil{panic(e)}};if m.CPU.IP!=0x1b7f{panic("salary")};after:=m.Read16(0x1e880+0x4f6);m.Write16(0x1e880+0x4fc,100);if book==1{m.CPU.IP=0x1bd2;for n:=0;n<20&&m.CPU.IP!=0x1bda;n++{if e:=m.Step();e!=nil{panic(e)}};if m.CPU.IP!=0x1bda{panic("power")}};fmt.Fprintf(out,"GAIN\t%d\t%d\t%d\t%d\t100\t%d\n",area,book,before,after,m.Read16(0x1e880+0x4fc))
 }}}
 for _,roll:=range []uint16{0,2729,2730,30000,32767}{for _,gold:=range []uint16{0,1,500,30000}{m:=fresh();m.CPU.IP=0x1d08;m.CPU.R[dg.AX]=roll;m.Write16(0x1e880+0x4f8,gold);for n:=0;n<40&&m.CPU.IP!=0x1d20;n++{if e:=m.Step();e!=nil{panic(e)}};if m.CPU.IP!=0x1d20{panic("retreat")};fmt.Fprintf(out,"RETREAT\t%d\t%d\t%d\n",roll,gold,m.Read16(0x1e880+0x4f8))}}
}
