// 030 DRAFT. One controlled target-word experiment, never production.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"github.com/wicanr2/dosgolem/internal/cpu"
	"github.com/wicanr2/dosgolem/internal/dos"
	"github.com/wicanr2/dosgolem/internal/machine"
	"github.com/wicanr2/dosgolem/internal/state"
)

func must(e error) {if e!=nil {panic(e)}}
func hash(b []byte) string {return fmt.Sprintf("%x",sha256.Sum256(b))}
func write(path string,v any) {b,e:=json.MarshalIndent(v,"","  ");must(e);must(os.WriteFile(path,append(b,'\n'),0644))}
func readWords(m *machine.Machine,seg,off uint16,n int)[]uint16 {v:=make([]uint16,n);for i:=range v {v[i]=m.Read16(uint32(seg)*16+uint32(off+uint16(i*2)))};return v}
func main() {
	root:=flag.String("root","","read-only original");input:=flag.String("state","","fixed multi-unit snapshot");out:=flag.String("out","","new output");flag.Parse()
	raw,e:=os.ReadFile(*input);must(e);if hash(raw)!="88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf" {panic("wrong fixture")}
	pam,e:=os.ReadFile(filepath.Join(*root,"PAM.AY"));must(e);if hash(pam)!="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0" {panic("wrong PAM")}
	if _,e:=os.Stat(*out);!os.IsNotExist(e) {panic("output exists")};must(os.Mkdir(*out,0755))
	results:=map[string]any{}
	for _,replace:=range []bool{false,true} {
		label:="original";if replace {label="suggested"};dir:=filepath.Join(*out,label);must(os.Mkdir(dir,0755))
		m:=machine.New();d:=dos.New(m,*root);d.Install();must(state.Load(*input,m,d));start:=m.Steps;nextKey:=0;decisions:=0;changes:=[]map[string]any{};dataDS:=uint16(0);roundReturned:=false;var decisionAfter []uint16
		for m.Steps<start+40000000 {
			if nextKey<6&&m.Steps>=start+uint64(nextKey)*2000000 {m.PushKey(0x39);nextKey++}
			c:=m.CPU
			if c.Seg[cpu.CS]==0x0f67&&c.IP==0x180a {
				decisions++
				if decisions==3 {
					dataDS=c.Seg[cpu.DS];locals:=readWords(m,c.Seg[cpu.SS],c.R[cpu.BP]-6,2)
					if locals[0]!=2||locals[1]!=8 {panic("unexpected original source or target")}
					units:=readWords(m,dataDS,0x56e8,24);mapping:=readWords(m,dataDS,0x6fb6,12)
					if mapping[0]!=0||mapping[1]!=1||units[1]!=15||units[3]!=64||units[mapping[2]*2+1]!=0 {panic("target reachability guard")}
					must(state.Save(filepath.Join(dir,"before.state"),m,d))
					must(os.WriteFile(filepath.Join(dir,"before-ram.bin"),m.Mem,0644))
					if replace {
						addr:=uint32(c.Seg[cpu.SS])*16+uint32(c.R[cpu.BP]-4)
						m.Write16(addr,7)
						changes=append(changes,map[string]any{"step":m.Steps,"cs":c.Seg[cpu.CS],"ip":c.IP,"segment":c.Seg[cpu.SS],"offset":c.R[cpu.BP]-4,"old":8,"new":7,"purpose":"controlled third enemy target: slot 1 to slot 0"})
					}
					must(os.WriteFile(filepath.Join(dir,"after-write-ram.bin"),m.Mem,0644))
				}
			}
			if dataDS!=0&&c.Seg[cpu.CS]==0x0f67&&c.IP==0x1818&&decisions==3&&decisionAfter==nil {decisionAfter=readWords(m,dataDS,0x56e8,24);must(state.Save(filepath.Join(dir,"after.state"),m,d))}
			if dataDS!=0&&c.Seg[cpu.CS]==0x0f67&&c.IP==0x20dc {roundReturned=true}
			must(m.Step())
		}
		if decisions!=3||len(decisionAfter)!=24||!roundReturned {panic("incomplete controlled round")}
		must(state.Save(filepath.Join(dir,"final.state"),m,d));final,e:=os.ReadFile(filepath.Join(dir,"final.state"));must(e)
		results[label]=map[string]any{"final_state_sha256":hash(final),"start_step":start,"end_step":m.Steps,"controller_writes":changes,"decision_after_units":decisionAfter,"round_returned":roundReturned,"decisions":decisions}
	}
	a,e:=os.ReadFile(filepath.Join(*out,"original/before.state"));must(e);b,e:=os.ReadFile(filepath.Join(*out,"suggested/before.state"));must(e);if !bytes.Equal(a,b) {panic("pre-target states differ")}
	write(filepath.Join(*out,"experiment.json"),map[string]any{"schema":1,"spec":"030 DRAFT","source_sha256":hash(raw),"controlled_experiment":true,"production_changed":false,"before_states_equal":true,"before_state_sha256":hash(a),"results":results})
	fmt.Println("controlled target experiment completed; original rules execute both branches")
}
