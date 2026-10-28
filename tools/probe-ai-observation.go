// 030 DRAFT: snapshot diagnostic, read-only observers, real keyboard only.
// Build inside a temporary copy of the pinned dosgolem module, never production.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"runtime"

	"github.com/wicanr2/dosgolem/internal/cpu"
	"github.com/wicanr2/dosgolem/internal/dos"
	"github.com/wicanr2/dosgolem/internal/machine"
	"github.com/wicanr2/dosgolem/internal/state"
)

type key struct { Offset uint64 `json:"offset"`; Scan uint8 `json:"scan"` }
type result struct { State, OPL, Ports, DOS string; Steps uint64; Stop string; KeyIRQs uint64 }
func must(err error) { if err != nil { panic(err) } }
func hash(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func jsonHash(v any) string { b,e:=json.Marshal(v);must(e);return hash(b) }
func write(path string,v any) { b,e:=json.MarshalIndent(v,"","  ");must(e);must(os.WriteFile(path,append(b,'\n'),0644)) }
func words(m *machine.Machine,seg,off uint16,n int) []uint16 {
	v:=make([]uint16,n);for i:=range v {v[i]=m.Read16(uint32(seg)*16+uint32(off+uint16(i*2)))};return v
}
func frame(m *machine.Machine,path string) {
	w,h,rgb:=m.PlanarRGB();if w==0||h==0{return};im:=image.NewRGBA(image.Rect(0,0,w,h))
	for i:=0;i<w*h;i++ {copy(im.Pix[i*4:i*4+3],rgb[i*3:i*3+3]);im.Pix[i*4+3]=255}
	f,e:=os.Create(path);must(e);must(png.Encode(f,im));must(f.Close())
}
func main() {
	root:=flag.String("root","","read-only original game");inputs:=flag.String("inputs","","prepared input directory");out:=flag.String("out","","new output directory");snapshot:=flag.String("state","03-attack-00-before.state","prepared choi snapshot basename");budget:=flag.Uint64("steps",20000000,"bounded instructions");schedule:=flag.String("schedule","","optional fixed JSON keyboard schedule");flag.Parse()
	if *root==""||*inputs==""||*out==""||*budget==0||*budget>100000000||filepath.Base(*snapshot)!=*snapshot {panic("invalid scope")}
	if _,e:=os.Stat(*out);!os.IsNotExist(e){panic("output already exists")};must(os.Mkdir(*out,0755))
	path:=filepath.Join(*inputs,"choi-hd-r1",*snapshot);raw,e:=os.ReadFile(path);must(e)
	keys:=[]key{};for i:=0;i<6;i++ {keys=append(keys,key{uint64(i)*2000000,0x39})}
	if *schedule!="" {b,e:=os.ReadFile(*schedule);must(e);must(json.Unmarshal(b,&keys))}
	if len(keys)>64 {panic("key limit")};for i,k:=range keys {if k.Offset>=*budget||(i>0&&k.Offset<=keys[i-1].Offset){panic("invalid key schedule")}}
	write(filepath.Join(*out,"planned-inputs.json"),keys)
	var audit struct {Rows []struct{Runtime string `json:"runtime"`; Bytes string `json:"bytes"`} `json:"rows"`}
	b,e:=os.ReadFile(filepath.Join(*inputs,"ai-hook-audit-r1.json"));must(e);must(json.Unmarshal(b,&audit))
	targets:=map[uint16]string{0x216a:"sub_206DA",0x15fc:"sub_1FB6C",0x1532:"sub_1FAA2",0x180a:"IDA 0x1FD7A before target normalization",0x1818:"IDA 0x1FD88 after executor",0x484c:"sub_22DBC",0x4626:"sub_22B96"}
	events:=[]map[string]any{};writes:=[]map[string]any{};prefixes:=[]map[string]any{};overflow:=false
	run:=func(label string,observe bool)result {
		dir:=filepath.Join(*out,label);must(os.Mkdir(dir,0755));m:=machine.New();d:=dos.New(m,*root);d.Install();must(state.Load(path,m,d));start:=m.Steps;initialIRQs:=m.KeyIRQs
		initialCPU:=fmt.Sprintf("%04x:%04x",m.CPU.Seg[cpu.CS],m.CPU.IP);initialSegments:=m.CPU.Seg
		// IDA sub_1FAA2, file+0x10F12. Reconstruct its relocated prefix
		// from the fixed MZ instead of assuming an unvalidated new hook.
		pam,e:=os.ReadFile(filepath.Join(*root,"PAM.AY"));must(e)
		if hash(pam)!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0" {panic("PAM mismatch")}
		header:=int(binary.LittleEndian.Uint16(pam[8:10]))*16;code:=append([]byte(nil),pam[header:]...)
		count:=int(binary.LittleEndian.Uint16(pam[6:8]));table:=int(binary.LittleEndian.Uint16(pam[24:26]))
		for i:=0;i<count;i++ {at:=table+i*4;off:=int(binary.LittleEndian.Uint16(pam[at:at+2]));seg:=int(binary.LittleEndian.Uint16(pam[at+2:at+4]));loc:=seg*16+off;v:=binary.LittleEndian.Uint16(code[loc:loc+2]);binary.LittleEndian.PutUint16(code[loc:loc+2],v+0x110)}
		loc:=0x0f67*16+0x1532-0x1100;if header+loc!=0x10f12 {panic("MZ helper mapping")}
		for i:=0;i<24;i++ {if m.Read8(0x0f67*16+0x1532+uint32(i))!=code[loc+i] {panic("helper prefix mismatch")}}
		if observe {prefixes=append(prefixes,map[string]any{"runtime":"0f67:1532","bytes":hex.EncodeToString(code[loc:loc+24])})}
		for _,v:=range audit.Rows {
			var seg,off uint16;_,e:=fmt.Sscanf(v.Runtime,"%x:%x",&seg,&off);must(e);code:=make([]byte,24);for i:=range code {code[i]=m.Read8(uint32(seg)*16+uint32(off)+uint32(i))};if hex.EncodeToString(code)!=v.Bytes {panic("source prefix mismatch "+v.Runtime)}
			if observe {prefixes=append(prefixes,map[string]any{"runtime":v.Runtime,"bytes":v.Bytes})}
		}
		capture:=func(name string) {
			if len(events)>=512 {overflow=true;return};c:=m.CPU;ds:=c.Seg[cpu.DS];sp:=c.R[cpu.SP];bp:=c.R[cpu.BP]
			locals:=[]uint16{};for i:=uint16(2);i<=12;i+=2 {locals=append(locals,m.Read16(uint32(c.Seg[cpu.SS])*16+uint32(bp-i)))}
			events=append(events,map[string]any{"name":name,"step":m.Steps,"cs":c.Seg[cpu.CS],"ip":c.IP,"registers":c.R,"segments":c.Seg,"flags":c.Flags,"stack_words":words(m,c.Seg[cpu.SS],sp,16),"bp_minus_2_through_12":locals,"ds_56e8_words":words(m,ds,0x56e8,24),"ds_6fa8_words":words(m,ds,0x6fa8,19),"ds_8e78_words":words(m,ds,0x8e78,6),"ds_26ac_word":words(m,ds,0x26ac,1)[0],"ds_70ce_words":words(m,ds,0x70ce,52),"ds_8ca4_words":words(m,ds,0x8ca4,6)})
			if len(events)<=12 {frame(m,filepath.Join(dir,fmt.Sprintf("event-%03d.png",len(events))))}
		}
		watchedDS:=map[uint16]bool{}
		installWrites:=func(ds uint16) {
			if watchedDS[ds] {return};watchedDS[ds]=true;base:=uint32(ds)*16
			for _,r:=range [][2]uint32{{0x56e8,0x5717},{0x6fa8,0x6fcd},{0x8e78,0x8e83},{0x8ca4,0x8caf}} {
				m.WatchWrite(base+r[0],base+r[1],func(mm *machine.Machine,addr uint32,old,next uint8){if len(writes)>=4096 {overflow=true;return};cs,ip:=mm.Insn();writes=append(writes,map[string]any{"step":mm.Steps,"cs":cs,"ip":ip,"ds":ds,"offset":addr-base,"old":old,"new":next})})
			}
		}
		type returnKey struct {CS,IP,SS,SP uint16};returns:=map[returnKey]string{}
		frame(m,filepath.Join(dir,"initial.png"));nextKey:=0;stop:="step-bound"
		for m.Steps<start+*budget {
			if nextKey<len(keys)&&m.Steps>=start+keys[nextKey].Offset {m.PushKey(keys[nextKey].Scan);nextKey++}
			if observe {
				c:=m.CPU;k:=returnKey{c.Seg[cpu.CS],c.IP,c.Seg[cpu.SS],c.R[cpu.SP]}
				if name,ok:=returns[k];ok {delete(returns,k);capture(name+":return")}
				if c.Seg[cpu.CS]==0x0f67 {if name,ok:=targets[c.IP];ok {
					installWrites(c.Seg[cpu.DS]);capture(name)
					if c.IP==0x216a||c.IP==0x15fc||c.IP==0x1532||c.IP==0x484c||c.IP==0x4626 {
						ret:=words(m,c.Seg[cpu.SS],c.R[cpu.SP],2);returns[returnKey{ret[1],ret[0],c.Seg[cpu.SS],c.R[cpu.SP]+4}]=name
					}
				}}
			}
			if e:=m.Step();e!=nil {stop=e.Error();break}
		}
		frame(m,filepath.Join(dir,"final.png"));stateFile:=filepath.Join(dir,"final.state");must(state.Save(stateFile,m,d));stateBytes,e:=os.ReadFile(stateFile);must(e)
		r:=result{hash(stateBytes),jsonHash(m.OPL),jsonHash(m.PortLog),jsonHash(d.CallTrace),m.Steps,stop,m.KeyIRQs-initialIRQs};write(filepath.Join(dir,"result.json"),map[string]any{"result":r,"start_step":start,"initial_cpu":initialCPU,"initial_segments":initialSegments,"final_cpu":fmt.Sprintf("%04x:%04x",m.CPU.Seg[cpu.CS],m.CPU.IP),"watched_ds":watchedDS,"keys_queued":nextKey,"keys_pending":m.KeyQueueLen(),"clock_model_cycle":m.CycleClock,"cpu_hz":m.CPUHz,"irq0_every":m.IRQ0Every});return r
	}
	observed:=run("observed",true);control:=run("control",false)
	a,e:=os.ReadFile(filepath.Join(*out,"observed/final.state"));must(e);b,e=os.ReadFile(filepath.Join(*out,"control/final.state"));must(e)
	write(filepath.Join(*out,"trace.json"),map[string]any{"schema":1,"spec":"030 DRAFT","source_state_sha256":hash(raw),"tool_go_version":runtime.Version(),"snapshot_diagnostic_only":true,"observer_guest_writes":false,"keyboard_only":true,"rng":"fixed full initial snapshot, numeric seed unknown, no reroll","step_budget":*budget,"prefixes":prefixes,"events":events,"writes":writes,"overflow":overflow,"observed":observed,"control":control,"state_equal":bytes.Equal(a,b),"io_equal":observed.OPL==control.OPL&&observed.Ports==control.Ports&&observed.DOS==control.DOS})
	if !bytes.Equal(a,b)||observed.OPL!=control.OPL||observed.Ports!=control.Ports||observed.DOS!=control.DOS {panic("observation changed control")}
	fmt.Printf("paired trace: events=%d writes=%d steps=%d state_equal=true\n",len(events),len(writes),observed.Steps)
}
