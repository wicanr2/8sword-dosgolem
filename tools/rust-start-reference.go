//go:build ignore

// Normal original boot, menu wrapping/cancel/new-game, and first-world data.
package main
import("crypto/sha256";"encoding/binary";"encoding/json";"fmt";"image";"image/png";"os";"path/filepath";"strings";dg "github.com/wicanr2/dosgolem";"github.com/wicanr2/dosgolem/oracle")
func must(e error){if e!=nil{panic(e)}}
func main(){
 if len(os.Args)!=3||os.Getuid()!=1000{panic("game out")};root,out:=os.Args[1],os.Args[2];must(os.Mkdir(out,0755));pam,e:=os.ReadFile(filepath.Join(root,"PAM.AY"));must(e);if fmt.Sprintf("%x",sha256.Sum256(pam))!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"{panic("PAM")}
 o,e:=oracle.LoadWith(filepath.Join(root,"PREDELLA.EXE"),root,oracle.Options{Adlib:true,ProgramPath:`C:\PREDELLA.EXE`});must(e);defer o.Close();o.SetScratch(filepath.Join(out,"scratch"));o.SetClock(12,0,0,0);o.SetDOSBoxCycles(3000)
 var load uint16;scene:="";shots:=[]map[string]any{};inputs:=[]map[string]any{};bitmaps:=[]map[string]any{};seen:=map[string]bool{}
 bind:=func(){if load!=0{return};for _,v:=range o.Overlays(){if strings.EqualFold(v.Name,"PAM.AY"){if v.Seg!=0x110||v.Reloc!=v.Seg{panic("load")};load=v.Seg
  o.OnCall(oracle.Far(load+0x13c2,0xae3),func(q *oracle.Oracle){switch q.Arg(0){case 158,218,278:scene="main";case 338,398:scene="confirm";case 990,1010,1030,1050,1070,1090,1110:scene="world"}})
  o.OnCall(oracle.Far(load+0x13c2,0x99c),func(q *oracle.Oracle){ptr:=oracle.Far(q.Arg(1),q.Arg(0));w,h:=q.Word(ptr),q.Word(oracle.Far(ptr.Seg,ptr.Off+2));if w==0||w>80||h==0||h>200{return};raw:=q.Bytes(ptr,4+int(w)*int(h)*4);sum:=fmt.Sprintf("%x",sha256.Sum256(raw));if seen[sum]{return};seen[sum]=true;name:=fmt.Sprintf("bitmap-%02d.bin",len(bitmaps));must(os.WriteFile(filepath.Join(out,name),raw,0644));bitmaps=append(bitmaps,map[string]any{"file":name,"sha256":sum,"width_bytes":w,"height":h,"segment":ptr.Seg,"offset":ptr.Off,"x_byte":q.Arg(2),"y":q.Arg(3),"step":q.Steps()})})
  o.OnCall(oracle.Far(load,0x6b7),func(*oracle.Oracle){scene="main"})
  return}}}
 advance:=func(ms int){for ;ms>0;ms-=10{if o.Steps()>100000000{panic("boot budget")};must(o.RunCycles(30000));bind()}}
 press:=func(scan uint8){inputs=append(inputs,map[string]any{"scan":scan,"step":o.Steps(),"route":"IRQ1"});o.KeyDown(scan);advance(100);o.KeyUp(scan);advance(150)}
 shot:=func(name string){w,h,rgb:=o.ScreenRGB();im:=image.NewRGBA(image.Rect(0,0,w,h));for i:=0;i<w*h;i++{copy(im.Pix[i*4:i*4+3],rgb[i*3:i*3+3]);im.Pix[i*4+3]=255};f,e:=os.Create(filepath.Join(out,name+".png"));must(e);must(png.Encode(f,im));must(f.Close());regs:=o.Regs();seed:=uint32(o.Word(oracle.Far(regs.DS,0x81bc)))|uint32(o.Word(oracle.Far(regs.DS,0x81be)))<<16;shots=append(shots,map[string]any{"name":name,"scene":scene,"step":o.Steps(),"cycles":o.Cycles(),"registers":regs,"seed":seed});must(o.SaveStateFile(filepath.Join(out,name+".state")));fmt.Println(name,scene,o.Steps())}
 advance(200);for i:=0;i<2;i++{must(o.TypeKeys("1"));advance(250)};advance(500);if load==0{must(o.SendKeys("Esc"))};for i:=0;i<300&&scene!="main";i++{advance(100)};if scene!="main"{panic("main not reached")};advance(200);shot("main-default")
 o.WriteU16(oracle.Far(0x1e88,0x81bc),0x5678);o.WriteU16(oracle.Far(0x1e88,0x81be),0x1234)
 press(0x48);shot("main-wrap-music");press(0x50);press(0x50);press(0x1c);shot("new-confirm");if scene!="confirm"{panic("confirm")};press(0x4d);press(0x1c);shot("new-cancel");press(0x1c);press(0x1c);advance(1000);shot("new-world");if scene!="world"{panic("world")}
 must(os.WriteFile(filepath.Join(out,"new-world-ram.bin"),o.Bytes(oracle.Far(0,0),0xa0000),0644));ds:=uint16(0x1e88);resources:=[]uint16{};for i:=0;i<6;i++{resources=append(resources,o.Word(oracle.Far(ds,0x4f2+uint16(i*2))))};army:=[]uint16{};for i:=0;i<12;i++{army=append(army,o.Word(oracle.Far(ds,0x54a+uint16(i*2))))}
 data:=map[string]any{"resources":resources,"army_words":army,"area":o.Word(oracle.Far(ds,0x56d6)),"x":o.Word(oracle.Far(ds,0x8e12)),"y":o.Word(oracle.Far(ds,0x8e44)),"steps":o.Word(oracle.Far(ds,0x56da)),"flags":o.Bytes(oracle.Far(ds,0x26aa),16),"initial_seed":uint32(0x12345678),"raw_header_paragraphs":binary.LittleEndian.Uint16(pam[8:])}
 vectors:=localVectors(pam,out)
 raw,e:=json.MarshalIndent(map[string]any{"status":"passed-original-start-prefix","source_sha256":fmt.Sprintf("%x",sha256.Sum256(pam)),"shots":shots,"inputs":inputs,"bitmaps":bitmaps,"initial":data,"local_input_vectors":vectors,"scope":"Normal PREDELLA/PAM boot,IRQ1 menu inputs. Only source RNG seed explicitly fixed at main before tested inputs. No coordinate/IP/army injection; stopped at first world,not DOS exit or full intro playback. Separate local input vectors use explicit stack locals and skip draw calls only."},"","  ");must(e);must(os.WriteFile(filepath.Join(out,"receipt.json"),append(raw,'\n'),0644))
}

func localVectors(pam []byte,out string)int{
 word:=func(at int)uint16{return binary.LittleEndian.Uint16(pam[at:])};code:=append([]byte(nil),pam[int(word(8))*16:]...);for i:=0;i<int(word(6));i++{at:=int(word(24))+i*4;p:=int(word(at+2))*16+int(word(at));binary.LittleEndian.PutUint16(code[p:],binary.LittleEndian.Uint16(code[p:])+0x110)}
 fresh:=func()*dg.Machine{m:=dg.New();copy(m.Mem[0x1100:],code);m.CPU.Seg[dg.CS]=0x110;m.CPU.Seg[dg.DS]=0x1e88;m.CPU.Seg[dg.SS]=0x1e88;m.CPU.R[dg.BP]=0xed00;m.CPU.R[dg.SP]=0xece0;m.Write16(0x1e880+0xed02,0xfff0);m.Write16(0x1e880+0xed04,0x110);return m}
 lines:="# kind selected dos_key next; CONF key is comma-separated sequence\n";count:=0
 for kind,n:=range []int{3,10}{for selected:=0;selected<n;selected++{for _,key:=range []uint16{0x4800,0x5000,0x4b00,0x4d00,0x1c0d,0x11b}{m:=fresh();m.CPU.R[dg.AX]=key;m.Write16(0x1e880+0xed00-8,uint16(selected));m.Write16(0x1e880+0xed00-6,uint16(selected));m.Write16(0x1e880+0xed00-2,10);stop:=uint16(0x60f);m.CPU.IP=0x55f;if kind==1{m.CPU.IP=0x9b5;stop=0xa82};for step:=0;step<1000;step++{if m.CPU.IP==stop{break};pc:=uint32(m.CPU.Seg[dg.CS])*16+uint32(m.CPU.IP);if m.CPU.Seg[dg.CS]==0x110&&m.Mem[pc]==0x9a{m.CPU.IP+=5;continue};must(m.Step());if step==999{panic("navigation budget")}};lines+=fmt.Sprintf("%d\t%d\t%d\t%d\n",kind,selected,key,m.Read16(0x1e880+0xed00-8));count++}}}
 sequences:=[][]uint16{{0x1c0d},{0x11b},{0x4b00,0x1c0d},{0x4d00,0x1c0d},{0x4800,0x1c0d},{0x5000,0x1c0d},{0x3920,0x1c0d}}
 for yes:=0;yes<2;yes++{for _,keys:=range sequences{m:=fresh();m.CPU.IP=0x4362;m.Write16(0x1e880+0xed00-2,uint16(yes));m.Write16(0x1e880+0xed00-4,0);m.CPU.R[dg.SP]=0xecfc;used:=0;for step:=0;step<1000;step++{if m.CPU.IP==0xfff0{break};pc:=uint32(m.CPU.Seg[dg.CS])*16+uint32(m.CPU.IP);if m.CPU.Seg[dg.CS]==0x110&&m.Mem[pc]==0x9a{if m.CPU.IP==0x436c{if used>=len(keys){panic("confirmation input exhausted")};m.CPU.R[dg.AX]=keys[used];used++};m.CPU.IP+=5;continue};must(m.Step());if step==999{panic("confirmation budget")}};parts:=[]string{};for _,k:=range keys{parts=append(parts,fmt.Sprint(k))};lines+=fmt.Sprintf("2\t%d\t%s\t%d\n",yes,strings.Join(parts,","),m.CPU.R[dg.AX]);count++}}
 must(os.WriteFile(filepath.Join(out,"start-input-reference.tsv"),[]byte(lines),0644));return count
}
