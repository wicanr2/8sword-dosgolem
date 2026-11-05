//go:build ignore

// Original numeric exit/clock path and encounter prefix. Controlled IO/rolls.
package main

import (
 "crypto/sha256"
 "encoding/binary"
 "fmt"
 "os"
 dg "github.com/wicanr2/dosgolem"
)
func main() {
 if os.Getuid()!=1000 || len(os.Args)!=4 { panic("UID/args") }; if _,e:=os.Stat("/.dockerenv");e!=nil{panic(e)}
 pam,e:=os.ReadFile(os.Args[1]);if e!=nil{panic(e)}
 if fmt.Sprintf("%x",sha256.Sum256(pam))!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"{panic("PAM")}
 word:=func(at int)uint16{return binary.LittleEndian.Uint16(pam[at:])};code:=append([]byte(nil),pam[int(word(8))*16:]...)
 for i:=0;i<int(word(6));i++{at:=int(word(24))+4*i;p:=int(word(at+2))*16+int(word(at));binary.LittleEndian.PutUint16(code[p:],binary.LittleEndian.Uint16(code[p:])+0x110)}
 fresh:=func()*dg.Machine{m:=dg.New();copy(m.Mem[0x1100:],code);m.CPU.Seg[dg.CS]=0x110;m.CPU.Seg[dg.DS]=0x1e88;m.CPU.Seg[dg.SS]=0x1e88;m.CPU.R[dg.SP]=0xee00;m.CPU.R[dg.BP]=0xed00;m.Write16(0x1e880+0xee00,0xfff0);m.Write16(0x1e880+0xee02,0x110);return m}
 farReturn:=func(m *dg.Machine){at:=uint32(m.CPU.Seg[dg.SS])*16+uint32(m.CPU.R[dg.SP]);m.CPU.IP=m.Read16(at);m.CPU.Seg[dg.CS]=m.Read16(at+2);m.CPU.R[dg.SP]+=4}
 out,e:=os.OpenFile(os.Args[2],os.O_CREATE|os.O_EXCL|os.O_WRONLY,0644);if e!=nil{panic(e)};defer out.Close()
 fmt.Fprintln(out,"# area x y tile key remaining boat dest after_x after_y facing after_remaining after_boat; source actual10BDC/10C32/12649..126E3, loader/draw/music skipped, actual139F2 executed; before monthly")
 sites:=[][4]uint16{{0,3,64,50},{1,10,31,50},{1,60,76,49},{2,31,26,49},{2,41,77,50},{3,44,49,50},{3,10,69,49},{4,10,25,49},{4,32,61,50},{5,11,43,49},{5,59,59,50},{6,58,38,49},{6,40,64,50}}
 keys:=[]uint16{0x4700,0x4800,0x4900,0x4b00,0x4d00,0x4f00,0x5000,0x5100,0x3920}
 deltas:=[][2]int{{-1,-1},{0,-1},{1,-1},{-1,0},{1,0},{-1,1},{0,1},{1,1},{0,0}}
 skipped:=map[uint16]bool{0x1f60:true,0x716c:true,0x4542:true,0x4878:true,0x479a:true,0x5f56:true}
 for _,s:=range sites { for k,key:=range keys {for _,remaining:=range []uint16{1,2}{for _,boat:=range []uint16{0,1}{
  m:=fresh();set:=func(at uint32,n uint16){m.Write16(0x1e880+at,n)};get:=func(at uint32)uint16{return m.Read16(0x1e880+at)}
  set(0x56d6,s[0]);set(0x8e12,uint16((int(s[1])-deltas[k][0]+70)%70));set(0x8e44,uint16((int(s[2])-deltas[k][1]+80)%80));set(0x56c4,3);set(0x56da,remaining);set(0x56ce,boat);set(0x8cba,key)
  run:=func(stop uint16,io bool){for n:=0;n<3000;n++{if m.CPU.Seg[dg.CS]==0x110{if m.CPU.IP==stop{return};if io&&skipped[m.CPU.IP]{farReturn(m);continue}};if e:=m.Step();e!=nil{panic(e)}};panic(fmt.Sprintf("budget %x:%x",m.CPU.Seg[dg.CS],m.CPU.IP))}
  set(0xee04,key);m.CPU.IP=0xbdc;run(0xfff0,false);m.CPU.R[dg.SP]=0xee00;m.CPU.IP=0xc32;run(0xfff0,false)
  if get(0x8e12)!=s[1]||get(0x8e44)!=s[2]{panic("motion")}
  m.CPU.R[dg.BP]=0xee00;m.CPU.R[dg.SP]=0xede0;set(0xedf0,s[3]);set(0xedfe,0);m.CPU.IP=0x2649;run(0x26e3,true)
  fmt.Fprintf(out,"%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n",s[0],s[1],s[2],s[3],key,remaining,boat,get(0x56d6),get(0x8e12),get(0x8e44),get(0x56c4),get(0x56da),get(0x56ce))
 }}}}
 rngout,e:=os.OpenFile(os.Args[3],os.O_CREATE|os.O_EXCL|os.O_WRONLY,0644);if e!=nil{panic(e)};defer rngout.Close()
 fmt.Fprintln(rngout,"# flag rank ahead_tile seed first_roll second_roll encounter cue calls; actual1151C prefix; two explicit roll inputs replace_rand; no enemy/GUI/empty-army theft")
 // Modular inverse of214013, obtained by Newton iteration modulo2^32.
 inv:=uint32(1);for i:=0;i<5;i++{inv*=2-uint32(214013)*inv}
 for rank,div:=range []uint32{640,576,512,448,384}{for _,flag:=range []uint16{0,1,2}{for _,tile:=range []uint16{1,15,46,47,49,50}{for _,roll:=range []uint32{0,div-1,div,2*div-1,2*div,32767}{
  seed:=(roll<<16-2531011)*inv;secondState:=(roll<<16)*214013+2531011;second:=uint16((secondState>>16)&32767)
  m:=fresh();set:=func(at uint32,n uint16){m.Write16(0x1e880+at,n)};set(0x04f2,uint16(rank+1));set(0x56cc,flag);set(0x8e12,40);set(0x8e44,40);set(0x56c4,4);m.Write16(0x1e82a,0);m.Write16(0x1e82c,0x4000)
  for i:=0;i<5760;i++{m.Mem[0x40000+i]=byte(tile+48)}
  randAt:=uint32(m.Read16(0x1100+0x154a+3))*16+uint32(m.Read16(0x1100+0x154a+1));m.CPU.IP=0x151c;calls:=0;enc:=0;cue:=uint16(255);done:=false
  for n:=0;n<3000;n++{at:=uint32(m.CPU.Seg[dg.CS])*16+uint32(m.CPU.IP);if at==randAt{if calls==0{m.CPU.R[dg.AX]=uint16(roll)}else if calls==1{m.CPU.R[dg.AX]=second}else{panic("third RNG")};calls++;farReturn(m);continue}
   if m.CPU.Seg[dg.CS]==0x110{if m.CPU.IP==0x1792||m.CPU.IP==0x16da{done=true;break};if m.CPU.IP==0x1606{enc=1;cue=m.Read16(uint32(m.CPU.Seg[dg.SS])*16+uint32(m.CPU.R[dg.BP])-16);done=true;break}}
   if e:=m.Step();e!=nil{panic(e)}
  };if !done{panic("rng budget")};fmt.Fprintf(rngout,"%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n",flag,rank+1,tile,seed,roll,second,enc,cue,calls)
 }}}}
}
