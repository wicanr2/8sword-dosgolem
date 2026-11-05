//go:build ignore

// Controlled original PAM instructions: modal result/rollback only, no GUI claim.
package main
import("crypto/sha256";"encoding/binary";"fmt";"hash/fnv";"os";dg "github.com/wicanr2/dosgolem")
func main(){
 if os.Getuid()!=1000||len(os.Args)!=3{panic("UID/args")};if _,e:=os.Stat("/.dockerenv");e!=nil{panic(e)}
 pam,e:=os.ReadFile(os.Args[1]);if e!=nil{panic(e)};if fmt.Sprintf("%x",sha256.Sum256(pam))!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"{panic("PAM")}
 word:=func(at int)uint16{return binary.LittleEndian.Uint16(pam[at:])};code:=append([]byte(nil),pam[int(word(8))*16:]...)
 for i:=0;i<int(word(6));i++{at:=int(word(24))+4*i;p:=int(word(at+2))*16+int(word(at));binary.LittleEndian.PutUint16(code[p:],binary.LittleEndian.Uint16(code[p:])+0x110)}
 out,e:=os.OpenFile(os.Args[2],os.O_CREATE|os.O_EXCL|os.O_WRONLY,0644);if e!=nil{panic(e)};defer out.Close();fmt.Fprintln(out,"# choice key before_x before_y after_x after_y facing boat blocked; original CS0110:255E ->257B; controlled result, original13B40 reveal before prompt and after rollback; skips GUI and event tail")
 for _,choice:=range []uint16{0,1}{for _,key:=range []uint16{0x4700,0x4800,0x4900,0x4b00,0x4d00,0x4f00,0x5000,0x5100,0x3920}{for _,p:=range [][2]uint16{{0,0},{69,79},{40,40},{0,79},{69,0}}{
  m:=dg.New();copy(m.Mem[0x1100:],code);m.CPU.Seg[dg.CS]=0x110;m.CPU.Seg[dg.DS]=0x1e88;m.CPU.Seg[dg.SS]=0x1e88;m.CPU.R[dg.SP]=0xee00;m.CPU.R[dg.BP]=0xed00;m.Write16(0x2d680,0xfff0);m.Write16(0x2d682,0x110)
  set:=func(at uint32,n uint16){m.Write16(0x1e880+at,n)};get:=func(at uint32)uint16{return m.Read16(0x1e880+at)}
  set(0x8cba,key);set(0x8e12,p[0]);set(0x8e44,p[1]);set(0x56c4,3);set(0x56ce,2)
  run:=func(stop uint16){for n:=0;n<10000;n++{if m.CPU.Seg[dg.CS]==0x110&&m.CPU.IP==stop{return};if e:=m.Step();e!=nil{panic(e)}};panic("budget")}
  m.Write16(0x1e82a,0);m.Write16(0x1e82c,0x4000);m.Write16(0x1e84a,0);m.Write16(0x1e84c,0x5000);for i:=0;i<5760;i++{m.Mem[0x40000+i]=49;m.Mem[0x50000+i]=0}
  reveal:=func(){m.CPU.R[dg.SP]=0xee00;m.Write16(0x2d680,0xfff0);m.Write16(0x2d682,0x110);m.Write16(0x2d684,4);m.Write16(0x2d686,4);m.CPU.IP=0x3b40;run(0xfff0)}
  reveal();m.CPU.R[dg.SP]=0xee00;m.CPU.IP=0xc32;run(0xfff0);reveal()
  m.CPU.IP=0x255e;m.CPU.R[dg.BP]=0xee00;m.CPU.R[dg.SP]=0xedec;m.CPU.R[dg.AX]=choice;set(0xedfe,0);run(0x257b);blocked:=get(0xedfe);reveal()
  mask:=make([]byte,700);for y:=0;y<80;y++{for x:=0;x<70;x++{if m.Mem[0x50000+y*72+x]!=0{at:=y*70+x;mask[at/8]|=1<<uint(at%8)}}};hash:=fnv.New64a();hash.Write(mask)
  fmt.Fprintf(out,"%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%016x\n",choice,key,p[0],p[1],get(0x8e12),get(0x8e44),get(0x56c4),get(0x56ce),blocked,hash.Sum64())

 }}}
}
