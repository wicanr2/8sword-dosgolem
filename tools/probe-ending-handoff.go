//go:build ignore

// 053 DRAFT: ordinary boot/menu/quit; optional explicitly controlled ending branch.
package main

import (
	"crypto/sha256"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"strings"

	"github.com/wicanr2/dosgolem/oracle"
)

func handoffMust(err error) {
	if err != nil {
		panic(err)
	}
}
func handoffSave(path string, value any) {
	data, err := json.MarshalIndent(value, "", "  ")
	handoffMust(err)
	handoffMust(os.WriteFile(path, append(data, '\n'), 0644))
}

func main() {
	root := flag.String("root", "", "read-only original game")
	out := flag.String("out", "", "new research output")
	force := flag.Bool("force-ending", false, "controlled DS:56E2=1 at original sub_1020E; not natural completion")
	follow := flag.Bool("follow", false, "follow original PAE overlay to DOS exit")
	escape := flag.String("escape-stage", "", "send ordinary IRQ1 Esc after first visible END1.AY or END5.AY page")
	escapeRoute := flag.String("escape-route", "bios", "bios or irq1; explicit input transport")
	catalog := flag.String("catalog", "", "read-only 053 ending source catalog, required for follow")
	flag.Parse()
	if os.Getuid() != 1000 || *root == "" || *out == "" {
		panic("UID1000 and explicit paths required")
	}
	if (*follow && *catalog == "") || (*escape != "" && (!*follow || (*escape != "END1.AY" && *escape != "END5.AY"))) {
		panic("invalid follow arguments")
	}
	if *escapeRoute != "bios" && *escapeRoute != "irq1" {
		panic("unknown escape transport")
	}
	_, err := os.Stat("/.dockerenv")
	handoffMust(err)
	for name, want := range map[string]string{
		"PREDELLA.EXE": "b9c7abdac7849711b68b6b6fd5861052e6f3d025b25af5f96d4605bf673cadaa",
		"PAM.AY":       "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0",
		"PAE.AY":       "8ae11b4c89f0361ed0a2d5b1859bbb4750047d37f0e26885e6903e4feb721a0c",
	} {
		data, e := os.ReadFile(filepath.Join(*root, name))
		handoffMust(e)
		if fmt.Sprintf("%x", sha256.Sum256(data)) != want {
			panic("unknown original " + name)
		}
	}
	handoffMust(os.Mkdir(*out, 0755))
	o, err := oracle.LoadWith(filepath.Join(*root, "PREDELLA.EXE"), *root, oracle.Options{Adlib: true, ProgramPath: `C:\PREDELLA.EXE`})
	handoffMust(err)
	defer o.Close()
	o.SetScratch(filepath.Join(*out, "scratch"))
	o.SetClock(12, 0, 0, 0)
	o.SetDOSBoxCycles(3000)
	var load uint16
	var scene string
	var calls, inputs, checkpoints, mutations []map[string]any
	var terminal error
	var handoff bool
	pamActive := func() bool { ov := o.Overlays(); return len(ov) > 0 && strings.EqualFold(ov[len(ov)-1].Name, "PAM.AY") }
	shot := func(name string) {
		w, h, rgb := o.ScreenRGB()
		im := image.NewRGBA(image.Rect(0, 0, w, h))
		for i := 0; i < w*h; i++ {
			copy(im.Pix[i*4:i*4+3], rgb[i*3:i*3+3])
			im.Pix[i*4+3] = 255
		}
		f, e := os.Create(filepath.Join(*out, name+".png"))
		handoffMust(e)
		handoffMust(png.Encode(f, im))
		handoffMust(f.Close())
		checkpoints = append(checkpoints, map[string]any{"name": name, "step": o.Steps(), "cycles": o.Cycles(), "registers": o.Regs(), "scene": scene, "mode": o.VideoMode()})
		fmt.Println(name, "steps", o.Steps(), "scene", scene, "IP", o.IP())
	}
	bind := func() {
		if load == 0 {
			for _, ov := range o.Overlays() {
				if strings.EqualFold(ov.Name, "PAM.AY") {
					if ov.Seg != ov.Reloc {
						panic("unexpected PAM relocation")
					}
					load = ov.Seg
					o.OnCall(oracle.Addr{Seg: load + 0x13c2, Off: 0xae3}, func(q *oracle.Oracle) {
						if !pamActive() {
							return
						}
						switch q.Arg(0) {
						case 158, 218, 278:
							scene = "main-menu"
						case 338, 398:
							scene = "new-game-confirm"
						case 990, 1010, 1030, 1050, 1070, 1090, 1110:
							scene = "map"
						case 12742, 12762, 12782, 12802, 12822, 12842:
							scene = "system-menu"
						}
					})
					o.OnCall(oracle.Addr{Seg: load, Off: 0x20e}, func(q *oracle.Oracle) {
						if !pamActive() {
							return
						}
						r := q.Regs()
						fields := map[string]uint16{}
						for _, at := range []uint16{0x56d0, 0x56de, 0x56e2, 0x7484, 0x7486} {
							fields[fmt.Sprintf("0x%04x", at)] = q.Word(oracle.Addr{Seg: r.DS, Off: at})
						}
						calls = append(calls, map[string]any{"stage": "sub_1020E-entry", "step": q.Steps(), "registers": r, "fields": fields, "stack": q.Bytes(oracle.Addr{Seg: r.SS, Off: r.SP}, 32)})
						if *force && len(mutations) == 0 {
							handoffMust(q.SaveStateFile(filepath.Join(*out, "before-controlled-branch.state")))
							address := oracle.Addr{Seg: r.DS, Off: 0x56e2}
							old := q.Word(address)
							q.WriteU16(address, 1)
							mutations = append(mutations, map[string]any{"step": q.Steps(), "address": address, "old": old, "new": 1, "reason": "controlled branch at original caller; field meaning unproven"})
						}
					})
					for _, off := range []uint16{0x2c0, 0x302, 0x344, 0x386, 0x3c8, 0x40a} {
						o.OnCall(oracle.Addr{Seg: load, Off: off}, func(q *oracle.Oracle) {
							if !pamActive() {
								return
							}
							r := q.Regs()
							pointers := []map[string]any{}
							for at := uint16(0); at < 36; at += 4 {
								off := q.Word(oracle.Addr{Seg: r.SS, Off: r.SP + at})
								seg := q.Word(oracle.Addr{Seg: r.SS, Off: r.SP + at + 2})
								raw := q.Bytes(oracle.Addr{Seg: seg, Off: off}, 32)
								text := string(raw)
								if n := strings.IndexByte(text, 0); n >= 0 {
									text = text[:n]
								}
								pointers = append(pointers, map[string]any{"stack_offset": at, "segment": seg, "offset": off, "text": text})
							}
							calls = append(calls, map[string]any{"stage": "original-execl-call", "step": q.Steps(), "registers": r, "pointers": pointers})
						})
					}
					break
				}
			}
		}
		for _, exec := range o.ExecLog() {
			if strings.EqualFold(exec.Base, "PAE.AY") {
				handoff = true
			}
		}
	}
	advance := func(ms int) {
		for ; ms > 0 && terminal == nil && !handoff; ms -= 10 {
			if o.Steps() > 200000000 {
				terminal = fmt.Errorf("bounded cold boot exceeded 200M steps")
				break
			}
			terminal = o.RunCycles(30000)
			bind()
		}
	}
	press := func(scan uint8) {
		if terminal != nil || handoff {
			return
		}
		inputs = append(inputs, map[string]any{"step": o.Steps(), "scan": scan, "down": true, "route": "irq1"})
		o.KeyDown(scan)
		advance(100)
		inputs = append(inputs, map[string]any{"step": o.Steps(), "scan": scan, "down": false, "route": "irq1"})
		o.KeyUp(scan)
		advance(150)
	}
	advance(200)
	for i := 0; i < 2 && terminal == nil; i++ {
		inputs = append(inputs, map[string]any{"step": o.Steps(), "text": "1", "route": "DOS"})
		handoffMust(o.TypeKeys("1"))
		advance(250)
	}
	advance(500)
	if load == 0 && terminal == nil {
		inputs = append(inputs, map[string]any{"step": o.Steps(), "key": "Esc", "route": "bios"})
		handoffMust(o.SendKeys("Esc"))
	}
	for n := 0; n < 300 && terminal == nil && scene != "main-menu"; n++ {
		advance(100)
	}
	shot("01-main-menu")
	if scene == "main-menu" && terminal == nil {
		press(0x50)
		press(0x1c)
		advance(500)
		shot("02-new-game-confirm")
		press(0x1c)
		advance(3000)
		shot("03-map")
		if scene == "map" && terminal == nil {
			press(0x41)
			advance(500)
			shot("04-system-menu")
			press(0x4d)
			press(0x1c)
			advance(500)
			shot("05-quit-confirm")
			press(0x1c)
			for n := 0; n < 300 && terminal == nil && !handoff; n++ {
				advance(100)
			}
		}
	}
	var endingCalls, endingPages []map[string]any
	var escaped bool
	var endingStart uint64
	var escapeStats []map[string]any
	keyStats := func(phase string) {
		escapeStats = append(escapeStats, map[string]any{"phase": phase, "step": o.Steps(), "bios_pending": o.KeysPending(), "irq1_delivered": o.IRQ1Delivered(), "irq1_stalls": o.KeyStalls(), "irq1_vector": o.Bytes(oracle.Addr{Off: 0x24}, 4)})
	}
	if handoff && *follow {
		endingStart = o.Steps()
		handoffMust(o.SaveStateFile(filepath.Join(*out, "pae-overlay.state")))
		handoffMust(os.WriteFile(filepath.Join(*out, "pae-overlay-ram.bin"), o.Bytes(oracle.Addr{}, 0xa0000), 0644))
		var endingLoad uint16
		for _, ov := range o.Overlays() {
			if strings.EqualFold(ov.Name, "PAE.AY") {
				if ov.Seg != ov.Reloc {
					panic("PAE relocation differs")
				}
				endingLoad = ov.Seg
			}
		}
		if endingLoad != 0x110 {
			panic("unreviewed PAE load segment")
		}
		manifest, e := os.ReadFile(filepath.Join(*catalog, "source.json"))
		handoffMust(e)
		var m struct {
			Records []struct {
				File   string `json:"source_file"`
				Record int    `json:"record"`
				SHA    string `json:"record_sha256"`
			}
		}
		handoffMust(json.Unmarshal(manifest, &m))
		known := map[string][]string{}
		files := map[string]string{}
		for _, r := range m.Records {
			known[r.SHA] = append(known[r.SHA], fmt.Sprintf("%s#%d", r.File, r.Record))
			files[r.SHA] = r.File
		}
		stage, visible := "", ""
		pages := map[string]bool{}
		for _, spec := range []struct {
			entry, ret uint16
			planes     int
			sha        string
		}{
			{0x4ec, 0x61f, 6, "85467a42c1b56b7eb880128fe34417adbe74fdf1bf42d857758908d8bbd79549"},
			{0x769, 0x84e, 5, "285723c100da394f2c125b5a1a293c0b24d4f18a8cf2276937ef4a47db4124bc"},
			{0x996, 0xa69, 4, "603833bfa266acbc8f7a3c8ecf3a30e9f15b5242211367534a7ca1145bb4cfad"},
		} {
			spec := spec
			var pending map[string]any
			o.OnCall(oracle.Addr{Seg: endingLoad + 0x283, Off: spec.entry}, func(q *oracle.Oracle) {
				reg := q.Regs()
				if pending != nil {
					if pending["sp"] == reg.SP {
						return
					}
					panic("nested PAE source")
				}
				code := q.Bytes(q.IP(), int(spec.ret-spec.entry)+1)
				if fmt.Sprintf("%x", sha256.Sum256(code)) != spec.sha {
					panic("PAE code identity")
				}
				ptr := oracle.Addr{Seg: q.Arg(1), Off: q.Arg(0)}
				w, h := int(q.Word(ptr)), int(q.Word(oracle.Addr{Seg: ptr.Seg, Off: ptr.Off + 2}))
				if w < 1 || w > 80 || h < 1 || h > 200 || int(ptr.Off)+4+w*h*spec.planes > 65536 {
					panic("PAE source bounds")
				}
				raw := q.Bytes(ptr, 4+w*h*spec.planes)
				key := fmt.Sprintf("%x", sha256.Sum256(raw))
				if len(known[key]) == 0 {
					panic("unknown PAE source")
				}
				pending = map[string]any{"entry_step": q.Steps(), "entry": q.IP(), "ds": reg.DS, "sp": reg.SP, "source_sha256": key, "catalog_records": known[key], "stage": files[key], "xywh": []int{int(q.Arg(2)) * 8, int(q.Arg(3)), w * 8, h}, "destination": q.Word(oracle.Addr{Seg: reg.DS, Off: 0x1780})}
			})
			o.OnCall(oracle.Addr{Seg: endingLoad + 0x283, Off: spec.ret}, func(q *oracle.Oracle) {
				if pending == nil {
					return
				}
				if pending["sp"] != q.Regs().SP {
					panic("PAE return stack")
				}
				pending["return_step"] = q.Steps()
				endingCalls = append(endingCalls, pending)
				stage = pending["stage"].(string)
				pending = nil
				if len(endingCalls) > 10000 {
					panic("PAE source event bound")
				}
			})
		}
		o.OnCall(oracle.Addr{Seg: endingLoad + 0x283, Off: 0x1a3}, func(q *oracle.Oracle) {
			visible = stage
			if stage != "" && !pages[stage] {
				pages[stage] = true
				shot(fmt.Sprintf("ending-%02d-%s", len(pages), stage))
				endingPages = append(endingPages, map[string]any{"stage": stage, "step": q.Steps(), "registers": q.Regs(), "irq1_vector": q.Bytes(oracle.Addr{Off: 0x24}, 4)})
			}
		})
		var releaseCycle uint64
		for n := 0; n < 12000 && terminal == nil; n++ {
			if *escape != "" && !escaped && visible == *escape {
				shot("escape-before-input")
				handoffMust(o.SaveStateFile(filepath.Join(*out, "escape-before-input.state")))
				keyStats("before-Esc")
				if *escapeRoute == "bios" {
					inputs = append(inputs, map[string]any{"step": o.Steps(), "key": "Esc", "route": "bios", "ending_stage": visible})
					handoffMust(o.SendKeys("Esc"))
				} else {
					inputs = append(inputs, map[string]any{"step": o.Steps(), "scan": 1, "down": true, "route": "irq1", "ending_stage": visible})
					o.KeyDown(1)
					releaseCycle = o.Cycles() + 300000
				}
				escaped = true
				keyStats("after-Esc-enqueued")
			}
			if releaseCycle != 0 && o.Cycles() >= releaseCycle {
				inputs = append(inputs, map[string]any{"step": o.Steps(), "scan": 1, "down": false, "route": "irq1", "ending_stage": visible})
				o.KeyUp(1)
				keyStats("after-Esc-release")
				releaseCycle = 0
			}
			if o.Steps() > 200000000 {
				terminal = fmt.Errorf("bounded complete path exceeded 200M steps")
				break
			}
			terminal = o.RunCycles(30000)
		}
		if escaped {
			keyStats("after-ending")
		}
	}
	shot("06-final")
	handoffMust(o.SaveStateFile(filepath.Join(*out, "final.state")))
	handoffMust(os.WriteFile(filepath.Join(*out, "ram-00000-9ffff.bin"), o.Bytes(oracle.Addr{}, 0xa0000), 0644))
	runError := ""
	exit := false
	code := uint8(255)
	if terminal != nil {
		runError = terminal.Error()
		var e *oracle.ExitError
		if errors.As(terminal, &e) {
			exit = true
			code = e.Code
		}
	}
	handoffSave(filepath.Join(*out, "handoff.json"), map[string]any{"schema": 1, "spec": "053", "production": false, "controlled_ending_branch": *force, "follow_original_ending": *follow, "escape_stage": *escape, "escape_route": *escapeRoute, "escape_transport_stats": escapeStats, "escaped": escaped, "ending_start_step": endingStart, "ending_calls": endingCalls, "ending_pages": endingPages, "steps": o.Steps(), "cycles": o.Cycles(), "clock_cycles_per_ms": 3000, "clock": "12:00:00.00 before execution", "scene": scene, "pam_load_segment": load, "pae_exec_seen": handoff, "exited": exit, "exit_code": code, "run_error": runError, "calls": calls, "inputs": inputs, "mutations": mutations, "checkpoints": checkpoints, "exec_log": o.ExecLog(), "overlays": o.Overlays(), "file_ops": o.FileOps(), "unimplemented": o.Unimplemented(), "limits": []string{"Cold boot/menu/quit uses ordinary inputs; optional branch mutation is explicitly controlled, not natural victory.", "Original execl runs without injected call, jump, altered stack or guest code patch.", "No HD, production or GUI claim; source observation follows actual original overlay."}})
	fmt.Printf("handoff=%v calls=%d controlled=%v error=%q\n", handoff, len(calls), *force, runError)
}
