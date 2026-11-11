//go:build ignore
// sub1649A lookup and124DE..126E3 notice/shore/clock. Display calls skipped.
package main
import("crypto/sha256";"encoding/binary";"fmt";"os";"strings";"strconv";dg "github.com/wicanr2/dosgolem")
func main(){
 if os.Getuid()!=1000||len(os.Args)!=4{panic("args/uid")};if _,e:=os.Stat("/.dockerenv");e!=nil{panic(e)}
 pam,e:=os.ReadFile(os.Args[1]);if e!=nil{panic(e)};if fmt.Sprintf("%x",sha256.Sum256(pam))!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"{panic("PAM")}
 word:=func(at int)uint16{return binary.LittleEndian.Uint16(pam[at:])};code:=append([]byte(nil),pam[int(word(8))*16:]...)
 for i:=0;i<int(word(6));i++{at:=int(word(24))+4*i;p:=int(word(at+2))*16+int(word(at));binary.LittleEndian.PutUint16(code[p:],binary.LittleEndian.Uint16(code[p:])+0x110)}
 fresh:=func()*dg.Machine{m:=dg.New();copy(m.Mem[0x1100:],code);m.CPU.Seg[dg.CS]=0x110;m.CPU.Seg[dg.DS]=0x1e88;m.CPU.Seg[dg.SS]=0x1e88;m.CPU.R[dg.SP]=0xee00;m.CPU.R[dg.BP]=0xed00;m.Write16(0x2d680,0xfff0);m.Write16(0x2d682,0x110);return m}
 ret:=func(m *dg.Machine){at:=uint32(m.CPU.Seg[dg.SS])*16+uint32(m.CPU.R[dg.SP]);m.CPU.IP=m.Read16(at);m.CPU.Seg[dg.CS]=m.Read16(at+2);m.CPU.R[dg.SP]+=4}
 f,e:=os.OpenFile(os.Args[3],os.O_CREATE|os.O_EXCL|os.O_WRONLY,0644);if e!=nil{panic(e)};defer f.Close();fmt.Fprintln(f,"# TEXT area index x y original_DS_string_offset; FLOW boat choice key remaining after_boat after_remaining blocked notice_calls shore_calls; original instructions, listed draw/IO skipped")
 cat,e:=os.ReadFile(os.Args[2]);if e!=nil{panic(e)}
 for _,line:=range strings.Split(strings.TrimSpace(string(cat)),"\n"){if strings.HasPrefix(line,"#"){continue};s:=strings.Split(line,"\t");nums:=make([]uint16,4);for i:=range nums{v,e:=strconv.ParseUint(s[i],10,16);if e!=nil{panic(e)};nums[i]=uint16(v)}
  m:=fresh();set:=func(at uint32,n uint16){m.Write16(0x1e880+at,n)};for i:=uint32(0);i<31;i++{set(0x8cbc+i*4,0xffff);set(0x8cbe+i*4,0xffff)};set(0x8cbc+uint32(nums[1])*4,nums[2]);set(0x8cbe+uint32(nums[1])*4,nums[3]);set(0x56d6,nums[0]);set(0x8e12,nums[2]);set(0x8e44,nums[3]);m.CPU.IP=0x649a;ptr:=uint16(0);calls:=0;done:=false
  for n:=0;n<7000;n++{if m.CPU.Seg[dg.CS]==0x110&&m.CPU.IP==0xfff0{done=true;break};if m.CPU.Seg[dg.CS]!=0x110||m.CPU.IP==0x6226{if uint32(m.CPU.Seg[dg.CS])*16+uint32(m.CPU.IP)==0x15803{ptr=m.Read16(0x1e880+uint32(m.CPU.R[dg.SP])+4);calls++};ret(m);continue};if e:=m.Step();e!=nil{panic(e)}};if !done||calls!=1{panic(fmt.Sprintf("lookup %v %d",nums,calls))};fmt.Fprintf(f,"TEXT\t%d\t%d\t%d\t%d\t%d\n",nums[0],nums[1],nums[2],nums[3],ptr)
 }
 for _,boat:=range []uint16{0,1,2}{for _,choice:=range []uint16{0,1}{for _,key:=range []uint16{0x4700,0x4800,0x4900,0x4b00,0x4d00,0x4f00,0x5000,0x5100,0x3920}{for _,remaining:=range []uint16{1,2}{
  m:=fresh();set:=func(at uint32,n uint16){m.Write16(0x1e880+at,n)};get:=func(at uint32)uint16{return m.Read16(0x1e880+at)};m.CPU.R[dg.BP]=0xee00;m.CPU.R[dg.SP]=0xedc0;set(0xedf0,51);set(0xedfe,0);set(0x56ce,boat);set(0x56e4,1);set(0x56da,remaining);set(0x8cba,key);set(0x8e12,40);set(0x8e44,40);m.CPU.IP=0x24de;notice,shore:=0,0;done:=false
  for n:=0;n<3000;n++{if m.CPU.Seg[dg.CS]==0x110{ip:=m.CPU.IP;if ip==0x26e3||ip==0x2851{done=true;break};if ip==0x1f60||ip==0x716c||ip==0x649a||ip==0x844c||ip==0x6226||ip==0x4442||ip==0x5cd0{if ip==0x649a{notice++};if ip==0x4442{if notice!=1{panic("order")};shore++;m.CPU.R[dg.AX]=choice};ret(m);continue}};if m.CPU.Seg[dg.CS]!=0x110{ret(m);continue};if e:=m.Step();e!=nil{panic(e)}};if !done{panic("FLOW budget")};fmt.Fprintf(f,"FLOW\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n",boat,choice,key,remaining,get(0x56ce),get(0x56da),get(0xedfe),notice,shore)
 }}}}
}
