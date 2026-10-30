//go:build ignore

// Spec 030 DRAFT: fixed original state, controlled random inputs and both defeat choices.
package main

import (
 "crypto/sha256"
 "encoding/json"
 "flag"
 "fmt"
 "os"
 "path/filepath"
 "runtime"

 "github.com/wicanr2/dosgolem/oracle"
)

func must(err error){if err!=nil{panic(err)}}
func sha(raw []byte)string{return fmt.Sprintf("%x",sha256.Sum256(raw))}
func write(p string,v any){b,e:=json.MarshalIndent(v,"","  ");must(e);must(os.WriteFile(p,append(b,'\n'),0600))}
type defeatCase struct {Name string;Gold,Count uint16;Random int;Choice int;Merit uint16}
func main(){
 root:=flag.String("root","","read-only original");state:=flag.String("state","","fixed normal-return state");out:=flag.String("out","","new output");flag.Parse()
 if os.Getuid()!=1000||*root==""||*state==""||*out==""{panic("explicit paths and UID1000")};if _,e:=os.Stat(*out);!os.IsNotExist(e){panic("output exists")};must(os.Mkdir(*out,0755))
 raw,e:=os.ReadFile(*state);must(e);if sha(raw)!="e618d4343697fa00a50ab4b6021b169f6a5e21e4eaf86100c1fac9cd7a98777b"{panic("fixed source state")}
 pam,e:=os.ReadFile(filepath.Join(*root,"PAM.AY"));must(e);if sha(pam)!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"{panic("PAM source")}
 o,e:=oracle.LoadWith(filepath.Join(*root,"PAM.AY"),*root,oracle.Options{Adlib:true});must(e);defer o.Close();must(o.LoadStateFile(*state));o.SetScratch(filepath.Join(*out,"scratch"));base:=o.Save()
 cases:=[]defeatCase{{"natural-survivor",500,12,-1,0,0},{"minimum",500,12,0,0,0},{"before-quotient",500,12,2729,0,0},{"at-quotient",500,12,2730,0,0},{"maximum",500,12,32767,0,0},{"zero-gold",0,12,0,0,0},{"tiny-gold",2,12,0,0,0},{"return-origin",500,0,-1,1,0},{"roam",500,0,-1,2,0},{"retreat-promotion",500,12,0,0,10000},{"return-origin-no-promotion",500,0,-1,1,10000},{"roam-promotion",500,0,-1,2,10000}}
 ds:=uint16(0x1e88);word:=func(off uint16)uint16{return o.Word(oracle.Addr{Seg:ds,Off:off})};words:=func(off uint16,n int)[]uint16{v:=make([]uint16,n);for i:=range v{v[i]=word(off+uint16(i*2))};return v}
 capture:=func()map[string]any{return map[string]any{"regs":o.Regs(),"step":o.Steps(),"progress":words(0x4f2,6),"army":words(0x54a,12),"travel_56c4":words(0x56c4,10),"position_x":word(0x8e12),"position_y":word(0x8e44),"origin":words(0x3be,2)}}
 var sc defeatCase;randCount:=0;rawRandom,effective:=-1,-1;choiceShown,downSent,confirmSent:=false,false,false;lastInput:=uint64(0);events:=[]map[string]any{}
 for _,ip:=range []uint16{0x1900,0x1930,0x1944,0x196c,0x1970,0x1975,0x1994,0x19bc,0x19be,0x1ab8,0x1daa,0x1ecf}{ip:=ip;o.OnCall(oracle.Addr{Seg:0x110,Off:ip},func(o *oracle.Oracle){
  if ip==0x1930 {randCount++;rawRandom=int(o.Regs().AX);effective=rawRandom;if sc.Random>=0{effective=sc.Random;o.SetRegs(oracle.CallRegs{AX:uint16(effective),SetAX:true})}}
  if ip==0x1daa{choiceShown=true};if ip==0x1ecf{choiceShown=false}
  if len(events)>64{panic("bounded events")};v:=capture();v["ip"]=ip;events=append(events,v)
 })}
 // Supply real keyboard IRQ/BIOS input only inside the explicit helper fixture.
 o.OnCall(oracle.Addr{Seg:0x160a,Off:0x87},func(o *oracle.Oracle){
  if o.Steps()-lastInput<50000{return};lastInput=o.Steps();scan:=uint8(0x1c);key:="Return"
  if choiceShown&&sc.Choice==2&&!downSent {scan=0x50;key="Down";downSent=true}else if choiceShown {confirmSent=true}
  o.KeyDown(scan);o.KeyUp(scan);must(o.SendKeys(key))
 })
 rows:=[]map[string]any{}
 for _,v:=range cases {sc=v;o.Restore(base);randCount=0;rawRandom=-1;effective=-1;choiceShown=false;downSent=false;confirmSent=false;lastInput=0;events=nil
  set:=func(off,v uint16){o.WriteU16(oracle.Addr{Seg:ds,Off:off},v)};set(0x4f8,sc.Gold);set(0x4f4,sc.Merit)
  for i:=0;i<6;i++{kind,count:=uint16(0),uint16(0);if i==0&&sc.Count>0{kind=1;count=sc.Count};set(0x54a+uint16(i*4),kind);set(0x54c+uint16(i*4),count)}
  dir:=filepath.Join(*out,sc.Name);must(os.Mkdir(dir,0755));before:=capture();must(o.SaveStateFile(filepath.Join(dir,"before.state")))
  result,err:=o.CallBudget(18000000,oracle.Addr{Seg:0x110,Off:0x1796},1)
  row:=map[string]any{"case":sc,"before":before,"after":capture(),"raw_random":rawRandom,"effective_random":effective,"random_calls":randCount,"choice_down_sent":downSent,"choice_confirm_sent":confirmSent,"return_ax":uint16(result),"events":events,"error":fmt.Sprint(err)};rows=append(rows,row);write(filepath.Join(dir,"receipt.json"),row);must(o.SaveStateFile(filepath.Join(dir,"after.state")));if err!=nil{write(filepath.Join(*out,"incomplete.json"),rows);panic(err)}
 }
 write(filepath.Join(*out,"receipt.json"),map[string]any{"status":"passed-original-defeat-controls","rows":rows,"go_version":runtime.Version(),"state_sha256":sha(raw),"pam_sha256":sha(pam),"seed_method":"Full fixed source snapshot restored before each case; controlled cases replace only the returned random input after the original call.","player_path":false,"limits":[]string{"Direct calls and explicit army/gold fixtures; not natural annihilation.","No original RNG state is rewritten or rerolled.","Home-return map side effects are original, not a complete Go world implementation."}})
 fmt.Println("original defeat controls passed",len(rows))
}
