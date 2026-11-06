//go:build ignore
// Original shore result/dispatch/clock and consumer coordinate lookups. No GUI.
package main
import("crypto/sha256";"encoding/binary";"fmt";"os";dg "github.com/wicanr2/dosgolem")
func main(){
 if os.Getuid()!=1000||len(os.Args)!=3{panic("UID/args")};if _,e:=os.Stat("/.dockerenv");e!=nil{panic(e)}
 pam,e:=os.ReadFile(os.Args[1]);if e!=nil{panic(e)};if fmt.Sprintf("%x",sha256.Sum256(pam))!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"{panic("PAM")}
 word:=func(at int)uint16{return binary.LittleEndian.Uint16(pam[at:])};code:=append([]byte(nil),pam[int(word(8))*16:]...)
 for i:=0;i<int(word(6));i++{at:=int(word(24))+4*i;p:=int(word(at+2))*16+int(word(at));binary.LittleEndian.PutUint16(code[p:],binary.LittleEndian.Uint16(code[p:])+0x110)}
 fresh:=func()*dg.Machine{m:=dg.New();copy(m.Mem[0x1100:],code);m.CPU.Seg[dg.CS]=0x110;m.CPU.Seg[dg.DS]=0x1e88;m.CPU.Seg[dg.SS]=0x1e88;m.CPU.R[dg.SP]=0xee00;m.CPU.R[dg.BP]=0xed00;m.Write16(0x2d680,0xfff0);m.Write16(0x2d682,0x110);return m}
 ret:=func(m *dg.Machine){at:=uint32(m.CPU.Seg[dg.SS])*16+uint32(m.CPU.R[dg.SP]);m.CPU.IP=m.Read16(at);m.CPU.Seg[dg.CS]=m.Read16(at+2);m.CPU.R[dg.SP]+=4}
 out,e:=os.OpenFile(os.Args[2],os.O_CREATE|os.O_EXCL|os.O_WRONLY,0644);if e!=nil{panic(e)};defer out.Close()
 fmt.Fprintln(out,"# FLOW tile choice key remaining after_x after_y boat blocked area after_remaining consumer discarded_rolls; 1255E..126E3; controlled AX result/target40,40; consumer/UI/loaders skipped. LOOK kind area matched result; actual consumer lookup, header/draw skipped.")
 keys:=[]uint16{0x4700,0x4800,0x4900,0x4b00,0x4d00,0x4f00,0x5000,0x5100}
 io:=map[uint16]bool{0x1f60:true,0x716c:true,0x4542:true,0x4878:true,0x479a:true,0x5f56:true,0x5cd0:true,0x512c:true,0x59c4:true,0x5a54:true,0x5ae4:true,0x5b74:true,0x5c04:true,0x20b0:true}
 for _,tile:=range []uint16{49,50,53,54,55,56,57,58,59}{for _,choice:=range []uint16{0,1}{for _,key:=range keys{for _,remaining:=range []uint16{1,2}{
  m:=fresh();set:=func(at uint32,n uint16){m.Write16(0x1e880+at,n)};get:=func(at uint32)uint16{return m.Read16(0x1e880+at)}
  set(0x8cba,key);set(0x8e12,40);set(0x8e44,40);set(0x56c4,3);set(0x56ce,2);set(0x56d6,1);set(0x56da,remaining);set(0x56e4,1)
  m.CPU.R[dg.BP]=0xee00;m.CPU.R[dg.SP]=0xedc0;set(0xedf0,tile);set(0xedfe,0);m.CPU.R[dg.AX]=choice;m.CPU.IP=0x255e
  randAt:=uint32(m.Read16(0x1100+0x2592+3))*16+uint32(m.Read16(0x1100+0x2592+1));rolls,consumer:=0,uint16(0);done:=false
  for n:=0;n<3000;n++{
   if uint32(m.CPU.Seg[dg.CS])*16+uint32(m.CPU.IP)==randAt{rolls++;m.CPU.R[dg.AX]=0;ret(m);continue}
   if m.CPU.Seg[dg.CS]==0x110{
    if m.CPU.IP==0x2851||m.CPU.IP==0x26e3{done=true;break}
    if io[m.CPU.IP]{if m.CPU.IP==0x512c||m.CPU.IP==0x20b0||m.CPU.IP>=0x59c4&&m.CPU.IP<=0x5c04{consumer=m.CPU.IP};ret(m);continue}
   };if e:=m.Step();e!=nil{panic(e)}
  };if !done{panic(fmt.Sprintf("FLOW budget %x:%x",m.CPU.Seg[dg.CS],m.CPU.IP))}
  fmt.Fprintf(out,"FLOW\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n",tile,choice,key,remaining,get(0x8e12),get(0x8e44),get(0x56ce),get(0xedfe),get(0x56d6),get(0x56da),consumer,rolls)
 }}}}
 // Original15354, all eight regions, first row configured to40/40. No match
 // returns its actual default0. Matched row reads pristine PAM offer table.
 for area:=uint16(0);area<8;area++{for _,matched:=range []uint16{0,1}{
  m:=fresh();set:=func(at uint32,n uint16){m.Write16(0x1e880+at,n)};set(0x56d6,area);set(0x8e12,39+matched);set(0x8e44,40)
  for i:=uint32(0);i<16;i++{set(0x8d6c+i*4,0xffff);set(0x8d6e+i*4,0xffff)};set(0x8d6c,40);set(0x8d6e,40)
  m.CPU.R[dg.BP]=0xee00;m.CPU.R[dg.SP]=0xedc0;set(0xee00,0);set(0xee02,0xfff0);set(0xee04,0x110);m.CPU.IP=0x5360;done:=false
  for n:=0;n<6000;n++{if m.CPU.Seg[dg.CS]==0x110&&m.CPU.IP==0xfff0{done=true;break};if m.CPU.Seg[dg.CS]!=0x110||m.CPU.IP==0x7e28{ret(m);continue};if e:=m.Step();e!=nil{panic(e)}};if !done{panic("LOOK shop budget")}
  fmt.Fprintf(out,"LOOK\t53\t%d\t%d\t%d\n",area,matched,m.CPU.R[dg.AX])
 }}
 for kind,entry:=range []uint16{0x59c4,0x5a54,0x5ae4,0x5b74,0x5c04}{for _,matched:=range []uint16{0,1}{
  m:=fresh();set:=func(at uint32,n uint16){m.Write16(0x1e880+at,n)};set(0x56d6,0);set(0x8e12,39+matched);set(0x8e44,40);base:=uint32(0x3f00+kind*0xf0)
  for i:=uint32(0);i<3;i++{set(base+i*10,0xffff);set(base+i*10+2,0xffff)};set(base,40);set(base+2,40);m.CPU.IP=entry;count:=0;done:=false
  for n:=0;n<3000;n++{if m.CPU.Seg[dg.CS]==0x110{if m.CPU.IP==0xfff0{done=true;break};if m.CPU.IP==0x4a06||m.CPU.IP==0x54ea{if m.CPU.IP==0x54ea{count++};m.CPU.R[dg.AX]=0;ret(m);continue}};if e:=m.Step();e!=nil{panic(e)}};if !done{panic("LOOK camp budget")}
  fmt.Fprintf(out,"LOOK\t%d\t0\t%d\t%d\n",54+kind,matched,count)
 }}
 for _,matched:=range []uint16{0,1}{m:=fresh();set:=func(at uint32,n uint16){m.Write16(0x1e880+at,n)};set(0x56d6,0);set(0x8e12,39+matched);set(0x8e44,40);for i:=uint32(0);i<10;i++{set(0x8c60+i*4,0xffff);set(0x8c62+i*4,0xffff)};set(0x8c60,40);set(0x8c62,40);set(0x4490,50);m.CPU.IP=0x20b0;result:=0;done:=false
  for n:=0;n<3000;n++{if m.CPU.Seg[dg.CS]==0x110{if m.CPU.IP==0xfff0{done=true;break};if m.CPU.IP==0x2360{result=1;done=true;break}};if e:=m.Step();e!=nil{panic(e)}};if !done{panic("LOOK treasure budget")};fmt.Fprintf(out,"LOOK\t59\t0\t%d\t%d\n",matched,result)
 }
}
