//go:build ignore

// 030 DRAFT: read-only source/timing observation of already validated effects.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"github.com/wicanr2/dosgolem/oracle"
)

func check(e error) {
	if e != nil {
		panic(e)
	}
}
func hash(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func write(p string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	check(e)
	check(os.WriteFile(p, append(b, '\n'), 0644))
}

type trace struct {
	StartStep, DecisionStep, EndStep uint64
	StateSHA256                      string
	HookIP                           uint16
}

func main() {
	root := flag.String("root", "", "read-only original")
	batch := flag.String("batch", "", "existing battle study")
	out := flag.String("out", "", "new output")
	lifecycle := flag.Bool("lifecycle", false, "record clocks, six arguments, geometry and exact return")
	flag.Parse()
	if _, e := os.Stat(*out); !os.IsNotExist(e) {
		panic("output exists")
	}
	check(os.Mkdir(*out, 0755))
	pam, e := os.ReadFile(filepath.Join(*root, "PAM.AY"))
	check(e)
	if hash(pam) != "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0" {
		panic("PAM identity")
	}
	word := func(at int) uint16 { return binary.LittleEndian.Uint16(pam[at:]) }
	header := int(word(8)) * 16
	code := append([]byte(nil), pam[header:]...)
	for i := 0; i < int(word(6)); i++ {
		at := int(word(24)) + 4*i
		loc := int(word(at+2))*16 + int(word(at))
		binary.LittleEndian.PutUint16(code[loc:], binary.LittleEndian.Uint16(code[loc:])+0x110)
	}
	results := []map[string]any{}
	for _, name := range []string{"special0-choice", "special2-choice", "special5-empty-original"} {
		source := filepath.Join(*batch, "ai-policy-r1", name, "baseline")
		if name == "special5-empty-original" {
			source = filepath.Join(*batch, "ai-policy-extra-r2", name, "baseline")
		}
		raw, e := os.ReadFile(filepath.Join(source, "trace.json"))
		check(e)
		var t trace
		check(json.Unmarshal(raw, &t))
		if t.EndStep < t.DecisionStep || t.EndStep-t.DecisionStep > 10000000 {
			panic("step bound")
		}
		dir := filepath.Join(*out, name)
		check(os.Mkdir(dir, 0755))
		finals := map[string][]byte{}
		events := []map[string]any{}
		for _, observe := range []bool{false, true} {
			label := "control"
			if observe {
				label = "observed"
			}
			runDir := filepath.Join(dir, label)
			check(os.Mkdir(runDir, 0755))
			o, e := oracle.LoadWith(filepath.Join(*root, "PAM.AY"), *root, oracle.Options{})
			check(e)
			check(o.LoadStateFile(filepath.Join(source, "before-decision.state")))
			if o.Steps() != t.DecisionStep {
				panic("start step")
			}
			if observe {
				check(o.WritePNG(filepath.Join(runDir, "before.png")))
				pending := map[uint16]map[string]any{}
				for _, site := range []struct {
					entry, ret uint16
					planes     int
				}{{0x4f2, 0x625, 6}, {0x626, 0x76e, 6}, {0x76f, 0x854, 5}, {0x99c, 0xa6f, 4}} {
					site := site
					start := 0x13c2*16 + int(site.entry)
					want := code[start : start+24]
					if !bytes.Equal(want, o.Bytes(oracle.Addr{Seg: 0x14d2, Off: site.entry}, 24)) {
						panic("bitmap prefix")
					}
					o.OnCall(oracle.Addr{Seg: 0x14d2, Off: site.entry}, func(o *oracle.Oracle) {
						if len(events) >= 256 || pending[site.entry] != nil {
							panic("bitmap budget/nesting")
						}
						ptr := oracle.Addr{Seg: o.Arg(1), Off: o.Arg(0)}
						w, h := int(o.Word(ptr)), int(o.Word(oracle.Addr{Seg: ptr.Seg, Off: ptr.Off + 2}))
						if w < 1 || w > 80 || h < 1 || h > 200 || int(ptr.Off)+4+w*h*site.planes > 65536 {
							panic("bitmap shape")
						}
						b := o.Bytes(ptr, 4+w*h*site.planes)
						r := o.Regs()
						v := map[string]any{"entry_step": o.Steps(), "entry": site.entry, "return": site.ret, "runtime_segment": 0x14d2, "planes": site.planes, "xywh": []int{int(o.Arg(2)) * 8, int(o.Arg(3)), w * 8, h}, "source_sha256": hash(b), "native_sha256": hash(b[:4+w*h*4]), "ds": r.DS, "destination": o.Word(oracle.Addr{Seg: r.DS, Off: 0x748a})}
						if *lifecycle {
							v["entry_cycles"] = o.Cycles()
							v["entry_ticks"] = o.Ticks()
						}
						pending[site.entry] = v
					})
					o.OnCall(oracle.Addr{Seg: 0x14d2, Off: site.ret}, func(o *oracle.Oracle) {
						v := pending[site.entry]
						if v == nil {
							return
						}
						v["return_step"] = o.Steps()
						if *lifecycle {
							v["return_cycles"] = o.Cycles()
							v["return_ticks"] = o.Ticks()
						}
						events = append(events, v)
						delete(pending, site.entry)
						if len(events) <= 24 {
							file := fmt.Sprintf("bitmap-%03d.png", len(events))
							check(o.WritePNG(filepath.Join(runDir, file)))
							v["png"] = file
						}
					})
				}
				for _, ip := range []uint16{0x36c6, 0x38cc} {
					ip := ip
					o.OnCall(oracle.Addr{Seg: 0xf67, Off: ip}, func(o *oracle.Oracle) {
						if len(events) >= 256 {
							panic("event budget")
						}
						v := map[string]any{"effect_entry": ip, "step": o.Steps(), "source_slot": o.Arg(0), "target_slot": o.Arg(1), "amount": o.Word(oracle.Addr{Seg: o.Regs().DS, Off: 0x8cb2})}
						if *lifecycle {
							r := o.Regs()
							args := []uint16{}
							for j := 0; j < 6; j++ {
								args = append(args, o.Arg(j))
							}
							v["args"] = args
							v["cycles"] = o.Cycles()
							v["ticks"] = o.Ticks()
							v["ds"] = r.DS
							v["ss"] = r.SS
							v["sp"] = r.SP
							v["bp"] = r.BP
							v["caller_ip"] = o.Word(oracle.Addr{Seg: r.SS, Off: r.SP})
							v["caller_cs"] = o.Word(oracle.Addr{Seg: r.SS, Off: r.SP + 2})
							v["caller_selector"] = o.Word(oracle.Addr{Seg: r.SS, Off: r.BP - 4})
							v["position_table"] = o.Bytes(oracle.Addr{Seg: r.DS, Off: 0x703c}, 24)
							for _, pair := range []struct {
								name           string
								row, col, base uint16
							}{{"source_xy", args[2], args[3], 0x701e}, {"target_xy", args[4], args[5], 0x703c}} {
								if pair.row > 3 || pair.col > 2 {
									panic("position argument")
								}
								at := pair.base + pair.row*6 + pair.col*2
								v[pair.name] = []int{int(o.Byte(oracle.Addr{Seg: r.DS, Off: at})) * 8, int(o.Byte(oracle.Addr{Seg: r.DS, Off: at + 1}))}
							}
						}
						events = append(events, v)
					})
				}
				if *lifecycle {
					o.OnCall(oracle.Addr{Seg: 0xf67, Off: 0x38cb}, func(o *oracle.Oracle) {
						r := o.Regs()
						events = append(events, map[string]any{"effect_return": 0x38cb, "step": o.Steps(), "cycles": o.Cycles(), "ticks": o.Ticks(), "ss": r.SS, "sp": r.SP})
					})
				}
			}
			next := t.StartStep
			for next < t.DecisionStep && next < t.StartStep+12000000 {
				next += 2000000
			}
			for o.Steps() < t.EndStep {
				if next >= t.StartStep+12000000 {
					next = t.EndStep + 1
				}
				if o.Steps() >= next {
					o.PressScan(" ")
					next += 2000000
				}
				end := min(t.EndStep, next)
				if end <= o.Steps() {
					panic("progress")
				}
				check(o.Run(end - o.Steps()))
			}
			check(o.SaveStateFile(filepath.Join(runDir, "final.state")))
			finals[label], e = os.ReadFile(filepath.Join(runDir, "final.state"))
			check(e)
			if observe {
				check(o.WritePNG(filepath.Join(runDir, "after.png")))
			}
		}
		reference, e := os.ReadFile(filepath.Join(source, "final.state"))
		check(e)
		if !bytes.Equal(finals["control"], finals["observed"]) || !bytes.Equal(reference, finals["observed"]) {
			panic("observer/reference state differs")
		}
		result := map[string]any{"case": name, "source_trace_sha256": hash(raw), "events": events, "observer_guest_writes": false, "state_equal": true, "historical_final_equal": true, "final_sha256": hash(reference), "start_step": t.DecisionStep, "end_step": t.EndStep}
		write(filepath.Join(dir, "events.json"), result)
		results = append(results, result)
		fmt.Printf("%s events=%d complete state equal\n", name, len(events))
	}
	write(filepath.Join(*out, "summary.json"), map[string]any{"schema": 1, "scope": "Controlled existing enemy special effects only; not player spell names or normal entry", "pam_sha256": hash(pam), "production_changed": false, "results": results})
}
