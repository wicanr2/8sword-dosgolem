//go:build ignore

// Original16063..160D5; explicitBP locals and observed drawing calls.
package main
import("crypto/sha256";"encoding/binary";"encoding/json";"fmt";"hash/fnv";"os";"path/filepath";dg "github.com/wicanr2/dosgolem")
func must(e error){if e!=nil{panic(e)}}
func hash(b []byte)uint64{h:=fnv.New64a();h.Write(b);return h.Sum64()}
func main(){
 if os.Getuid()!=1000||len(os.Args)!=4{panic("game ticks output")};root,ticks,out:=os.Args[1],os.Args[2],os.Args[3];pam,e:=os.ReadFile(filepath.Join(root,"PAM.AY"));must(e);if fmt.Sprintf("%x",sha256.Sum256(pam))!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"{panic("source")};raw,e:=os.ReadFile(ticks);must(e);if len(raw)!=57{panic("tiles")};must(os.Mkdir(out,0755));word:=func(i int)uint16{return binary.LittleEndian.Uint16(pam[i:])};code:=append([]byte(nil),pam[int(word(8))*16:]...)
 for i:=0;i<int(word(6));i++{at:=int(word(24))+4*i;p:=int(word(at+2))*16+int(word(at));binary.LittleEndian.PutUint16(code[p:],binary.LittleEndian.Uint16(code[p:])+0x110)}
 f,e:=os.Create(filepath.Join(out,"travelbar-reference.tsv"));must(e);defer f.Close();fmt.Fprintln(f,"# remaining tempo stopped filled empty x_first x_last y rgba_fnv; original calls;source8x3 tiles scaled3x6")
 count:=0;for _,tempo:=range []uint16{6,8,10,12,15,18}{for _,remaining:=range []uint16{0,1,tempo-1,tempo,tempo+1,54*tempo-1,54*tempo}{for flag:=uint16(0);flag<2;flag++{
  m:=dg.New();copy(m.Mem[0x1100:],code);m.CPU.Seg[dg.CS]=0x110;m.CPU.Seg[dg.DS]=0x1e88;m.CPU.Seg[dg.SS]=0x1e88;m.CPU.R[dg.BP]=0xed00;m.CPU.R[dg.SP]=0xecfc;m.CPU.IP=0x6063;m.Write16(0x1e880+0xed00,0);m.Write16(0x1e880+0xed02,0xfff0);m.Write16(0x1e880+0xed04,0x110);m.Write16(0x1e880+0x56da,remaining);m.Write16(0x1e880+0x56dc,tempo);m.Write16(0x1e880+0x56ca,flag)
  cells:=[][3]uint16{};done:=false
  for n:=0;n<10000;n++{if m.CPU.IP==0xfff0{done=true;break};if m.CPU.IP==0x6092||m.CPU.IP==0x60c1{sp:=uint32(0x1e880)+uint32(m.CPU.R[dg.SP]);ptr,seg,x,y:=m.Read16(sp),m.Read16(sp+2),m.Read16(sp+4),m.Read16(sp+6);if seg!=0x7000||y!=193||ptr<0xfeec||(ptr-0xfeec)%19!=0{panic("call")};cells=append(cells,[3]uint16{x,y,(ptr-0xfeec)/19});m.CPU.IP+=5;continue};must(m.Step())};if !done||len(cells)!=54{panic("loop")}
  palette:=[16][3]byte{{0,0,0},{0,0,170},{0,170,0},{0,170,170},{170,0,0},{170,0,170},{170,85,0},{170,170,170},{85,85,85},{85,85,255},{85,255,85},{85,255,255},{255,85,85},{255,85,255},{255,255,85},{255,255,255}};image:=make([]byte,1296*18*4);filled:=0
  for i,c:=range cells{if c[0]!=uint16(i+2){panic("position")};if c[2]>0{filled++};tile:=raw[int(c[2])*19:];for y:=0;y<3;y++{for x:=0;x<8;x++{color:=byte(0);for p:=0;p<4;p++{color|=((tile[4+p*3+y]>>uint(7-x))&1)<<uint(p)};for yy:=0;yy<6;yy++{for xx:=0;xx<3;xx++{at:=((y*6+yy)*1296+i*24+x*3+xx)*4;copy(image[at:at+3],palette[color][:]);image[at+3]=255}}}}}
  fmt.Fprintf(f,"%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%016x\n",remaining,tempo,flag,filled,54-filled,cells[0][0],cells[53][0],cells[0][1],hash(image));count++
 }}}
 b,_:=json.MarshalIndent(map[string]any{"status":"passed-original-travelbar","vectors":count,"source_sha256":fmt.Sprintf("%x",sha256.Sum256(pam)),"tile_sha256":fmt.Sprintf("%x",sha256.Sum256(raw)),"scope":"Original16063..160D5 with explicitBP/SP and intercepted2438F calls;no RNG;54 cells and three source color rows. Primitive contract inherits047;not fresh VGA oracle."},"","  ");must(os.WriteFile(filepath.Join(out,"receipt.json"),b,0644))
}
