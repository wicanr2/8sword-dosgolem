//go:build ignore

// Fixed-PAM local item acquisition and gold-token recruitment ceiling.
package main
import("encoding/binary";"crypto/sha256";"encoding/json";"fmt";"os";"path/filepath"; dg "github.com/wicanr2/dosgolem")
func must(e error){if e!=nil{panic(e)}}
func main(){
 if len(os.Args)!=3||os.Getuid()!=1000{panic("game out")};pam,e:=os.ReadFile(filepath.Join(os.Args[1],"PAM.AY"));must(e);if fmt.Sprintf("%x",sha256.Sum256(pam))!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"{panic("PAM")};w:=func(at int)uint16{return binary.LittleEndian.Uint16(pam[at:])};code:=append([]byte(nil),pam[int(w(8))*16:]...)
 for i:=0;i<int(w(6));i++{at:=int(w(24))+4*i;p:=int(w(at+2))*16+int(w(at));binary.LittleEndian.PutUint16(code[p:],binary.LittleEndian.Uint16(code[p:])+0x110)}
 out:=os.Args[2];must(os.Mkdir(out,0755));lines:="# item mode found capacity seed_after counter_after; original17FB4 with only graphics and wait calls skipped\n";records:=[]map[string]any{}
 fresh:=func()*dg.Machine{m:=dg.New();copy(m.Mem[0x1100:],code);m.CPU.Seg[dg.CS]=0x110;m.CPU.Seg[dg.DS]=0x1e88;m.CPU.Seg[dg.SS]=0x1e88;m.CPU.R[dg.SP]=0xecf8;m.Write16(0x1e880+0xecf8,0xfff0);m.Write16(0x1e880+0xecfa,0x110);return m}
 for item:=0;item<8;item++{for mode:=0;mode<4;mode++{m:=fresh();ds:=uint32(0x1e880);at:=uint32(0x260a+6*item);area,x,y:=m.Read16(ds+at),m.Read16(ds+at+2),m.Read16(ds+at+4);m.Write16(ds+0x56d6,area);m.Write16(ds+0x8e12,x);m.Write16(ds+0x8e44,y);m.Write16(ds+0x4fc,9);m.Write16(ds+0x56e6,0);m.Write16(ds+0x81bc,0x5678);m.Write16(ds+0x81be,0x1234)
  if mode==1{m.Write16(ds+0x8e12,x+1)};if mode==2{m.Write16(ds+0x56d6,(area+1)%8)};if mode==3{m.Write16(ds+at,255);m.Write16(ds+uint32(0x26aa+2*item),1)}
  initialFlags:=[]uint16{};for i:=0;i<8;i++{initialFlags=append(initialFlags,m.Read16(ds+uint32(0x26aa+2*i)))};m.CPU.IP=0x7fb4;randCalls:=0
  for step:=0;step<100000;step++{ip:=m.CPU.IP;cs:=m.CPU.Seg[dg.CS];if cs==0x110&&ip==0xfff0{break};if uint32(cs)*16+uint32(ip)==0x1a63e{randCalls++}
   if cs==0x110{switch ip{case 0x7fba,0x622c:m.CPU.R[dg.SP]-=m.CPU.R[dg.AX];m.CPU.IP+=5;continue
    case 0x7fd1,0x801b,0x802b,0x8049,0x806c,0x80c6,0x6487:m.CPU.IP+=5;continue
    case 0x80cf:m.CPU.IP+=3;m.CPU.R[dg.SP]+=2;continue}}
   must(m.Step());if step==99999{panic("search budget")}}
  flags:=[]uint16{};for i:=0;i<8;i++{flags=append(flags,m.Read16(ds+uint32(0x26aa+2*i)))};found:=m.Read16(ds+at)==255&&mode==0;seed:=uint32(m.Read16(ds+0x81bc))|uint32(m.Read16(ds+0x81be))<<16;if randCalls!=1{panic(fmt.Sprint("rand calls ",randCalls))}
  n:=0;if found{n=1};fmt.Sscanf("","");lines+=fmt.Sprintf("%d\t%d\t%d\t%d\t%d\t%d\n",item,mode,n,m.Read16(ds+0x4fc),seed,m.Read16(ds+0x56e6));records=append(records,map[string]any{"item":item,"mode":mode,"area":area,"x":x,"y":y,"found":found,"flags_before":initialFlags,"flags_after":flags,"disabled_area":m.Read16(ds+at),"capacity":m.Read16(ds+0x4fc),"seed_after":seed,"rand_calls":randCalls})
 }}
 must(os.WriteFile(filepath.Join(out,"items-reference.tsv"),[]byte(lines),0644));ceil:="# lead used cost token maximum; original155D0..155E7 with AX=used SI=cost\n";count:=0
 for _,lead:=range []uint16{100,1000,30000}{for _,used:=range []uint16{0,30,99,100,101,999,1000,30000}{for _,cost:=range []uint16{1,3,50,300}{for token:=uint16(0);token<2;token++{m:=fresh();m.CPU.IP=0x55d0;m.CPU.R[dg.BP]=0xed00;m.CPU.R[dg.AX]=used;m.CPU.R[dg.SI]=cost;m.Write16(0x1e880+0x4fa,lead);m.Write16(0x1e880+0x26b8,token);for i:=0;i<20;i++{if m.CPU.IP==0x55e7{break};must(m.Step())};value:=int16(m.Read16(0x1e880+0xed00-6));ceil+=fmt.Sprintf("%d\t%d\t%d\t%d\t%d\n",lead,used,cost,token,value);count++}}}}
 must(os.WriteFile(filepath.Join(out,"recruit-token-reference.tsv"),[]byte(ceil),0644));raw,e:=json.MarshalIndent(map[string]any{"status":"passed-original-items","acquisition_cases":len(records),"recruitment_vectors":count,"records":records,"source_sha256":fmt.Sprintf("%x",sha256.Sum256(pam)),"scope":"Explicit stack locals for __chkstk; graphics and input wait skipped; real sub16226 and original _rand executed; no original complete GUI claim"},"","  ");must(e);must(os.WriteFile(filepath.Join(out,"receipt.json"),append(raw,'\n'),0644));fmt.Println("passed",len(records),count)
}
