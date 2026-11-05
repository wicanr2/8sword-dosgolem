//go:build ignore

// Controlled original jump arming, motion, landing and exploration, no GUI/tail.
package main
import("crypto/sha256";"encoding/binary";"fmt";"hash/fnv";"os";dg "github.com/wicanr2/dosgolem")
func main(){
 if os.Getuid()!=1000||len(os.Args)!=3{panic("UID/args")};if _,e:=os.Stat("/.dockerenv");e!=nil{panic(e)}
 pam,e:=os.ReadFile(os.Args[1]);if e!=nil{panic(e)};if fmt.Sprintf("%x",sha256.Sum256(pam))!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"{panic("PAM")};word:=func(at int)uint16{return binary.LittleEndian.Uint16(pam[at:])};code:=append([]byte(nil),pam[int(word(8))*16:]...)
 for i:=0;i<int(word(6));i++{at:=int(word(24))+4*i;p:=int(word(at+2))*16+int(word(at));binary.LittleEndian.PutUint16(code[p:],binary.LittleEndian.Uint16(code[p:])+0x110)}
 out,e:=os.OpenFile(os.Args[2],os.O_CREATE|os.O_EXCL|os.O_WRONLY,0644);if e!=nil{panic(e)};defer out.Close();fmt.Fprintln(out,"# phase key raw_tile amount before_x before_y after_x after_y facing flag effective_tile explored_fnv; original CS0110:B85/C32/1FBB/2014/3B40; controlled inputs; excludes GUI and12446 tail")
 tiles:=[][2]uint16{{1,0},{2,0},{3,0},{10,0},{11,0},{14,0},{15,0},{30,0},{46,0},{47,0},{49,0},{52,0},{53,0},{59,1},{59,0},{60,0},{65,0}}
 for _,phase:=range []uint16{1,2}{for _,key:=range []uint16{0x4700,0x4800,0x4900,0x4b00,0x4d00,0x4f00,0x5000,0x5100,0x3920}{if phase==2&&key==0x3920{continue};for _,pair:=range tiles{for _,p:=range [][2]uint16{{0,0},{69,79},{40,40},{0,79},{69,0}}{
  tile,amount:=pair[0],pair[1];m:=dg.New();copy(m.Mem[0x1100:],code);m.CPU.Seg[dg.CS]=0x110;m.CPU.Seg[dg.DS]=0x1e88;m.CPU.Seg[dg.SS]=0x1e88
  set:=func(at uint32,n uint16){m.Write16(0x1e880+at,n)};get:=func(at uint32)uint16{return m.Read16(0x1e880+at)}
  run:=func(stop uint16){for n:=0;n<10000;n++{if m.CPU.Seg[dg.CS]==0x110&&m.CPU.IP==stop{return};if e:=m.Step();e!=nil{panic(e)}};panic("budget")}
  stack:=func(){m.CPU.R[dg.SP]=0xee00;m.CPU.R[dg.BP]=0xed00;set(0xee00,0xfff0);set(0xee02,0x110)}
  m.Write16(0x1e82a,0);m.Write16(0x1e82c,0x4000);m.Write16(0x1e84a,0);m.Write16(0x1e84c,0x5000);for i:=0;i<5760;i++{m.Mem[0x40000+i]=byte(tile+48);m.Mem[0x50000+i]=0}
  set(0x8cba,key);set(0x8e12,p[0]);set(0x8e44,p[1]);set(0x56c4,3);set(0x56cc,phase)
  reveal:=func(){stack();set(0xee04,4);set(0xee06,4);m.CPU.IP=0x3b40;run(0xfff0)};reveal()
  m.CPU.IP=0xb85;run(0xb92);stack();m.CPU.IP=0xc32;run(0xfff0)
  effective:=tile
  if tile==59{for i:=0;i<10;i++{set(0x8c60+uint32(i*4),0xffff);set(0x8c62+uint32(i*4),0xffff)};set(0x8c60,get(0x8e12));set(0x8c62,get(0x8e44));set(0x56d6,0);set(0x4490,amount);stack();set(0xee04,4);set(0xee06,4);m.CPU.IP=0x2014;run(0xfff0);effective=m.CPU.R[dg.AX]}
  reveal();m.CPU.R[dg.BP]=0xee00;m.CPU.R[dg.SP]=0xedec;set(0xedfa,effective);m.CPU.IP=0x1fbb;run(0x1fe0)
  mask:=make([]byte,700);for y:=0;y<80;y++{for x:=0;x<70;x++{if m.Mem[0x50000+y*72+x]!=0{at:=y*70+x;mask[at/8]|=1<<uint(at%8)}}};h:=fnv.New64a();h.Write(mask)
  fmt.Fprintf(out,"%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%016x\n",phase,key,tile,amount,p[0],p[1],get(0x8e12),get(0x8e44),get(0x56c4),get(0x56cc),effective,h.Sum64())
 }}}}
}
