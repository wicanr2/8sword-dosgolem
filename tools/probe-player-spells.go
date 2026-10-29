// 030 DRAFT. Build in a temporary pinned dosgolem module; controlled spell resources.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
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

func must(e error) {
	if e != nil {
		panic(e)
	}
}
func sha(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func saveJSON(p string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	must(e)
	must(os.WriteFile(p, append(b, '\n'), 0644))
}
func shot(m *machine.Machine, p string) {
	w, h, rgb := m.PlanarRGB()
	if w == 0 || h == 0 {
		return
	}
	im := image.NewRGBA(image.Rect(0, 0, w, h))
	for i := 0; i < w*h; i++ {
		copy(im.Pix[i*4:i*4+3], rgb[i*3:i*3+3])
		im.Pix[i*4+3] = 255
	}
	f, e := os.Create(p)
	must(e)
	must(png.Encode(f, im))
	must(f.Close())
}
func main() {
	root := flag.String("root", "", "read-only original")
	snapshot := flag.String("state", "", "fixed original snapshot")
	out := flag.String("out", "", "new output")
	spell := flag.Int("spell", 0, "original menu index 0,1,2,3 assassination,5 halve,7 quake")
	fixture := flag.String("fixture", "mixed", "mixed, sparse, no-ghost, or odd live enemy counts")
	targetKind := flag.String("target-kind", "any", "any, ghost (kind6..15), or ordinary target via original navigation")
	cancelMenu := flag.Bool("cancel-menu", false, "cancel original spell menu with Escape")
	chanceStat := flag.Int("chance-stat", -1, "explicit DS:26AE fixture, -1 unchanged or 0..4")
	cancelTarget := flag.Bool("cancel-target", false, "cancel original target menu with Escape")
	flag.Parse()
	if *root == "" || *snapshot == "" || *out == "" || *spell < 0 || (*spell > 3 && *spell != 5 && *spell != 7) || (*fixture != "mixed" && *fixture != "sparse" && *fixture != "no-ghost" && *fixture != "odd") || (*chanceStat < -1 || *chanceStat > 4) || (*targetKind != "any" && *targetKind != "ghost" && *targetKind != "ordinary") {
		panic("missing inputs")
	}
	if _, e := os.Stat(*out); !os.IsNotExist(e) {
		panic("existing output")
	}
	must(os.Mkdir(*out, 0755))
	input, e := os.ReadFile(*snapshot)
	must(e)
	pam, e := os.ReadFile(filepath.Join(*root, "PAM.AY"))
	must(e)
	if sha(pam) != "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0" {
		panic("PAM")
	}
	code := append([]byte(nil), pam[int(binary.LittleEndian.Uint16(pam[8:]))*16:]...)
	for i := 0; i < int(binary.LittleEndian.Uint16(pam[6:])); i++ {
		at := int(binary.LittleEndian.Uint16(pam[24:])) + i*4
		loc := int(binary.LittleEndian.Uint16(pam[at+2:]))*16 + int(binary.LittleEndian.Uint16(pam[at:]))
		binary.LittleEndian.PutUint16(code[loc:], binary.LittleEndian.Uint16(code[loc:])+0x110)
	}
	runs := []map[string]any{}
	for _, observe := range []bool{false, true} {
		label := "control"
		if observe {
			label = "observed"
		}
		dir := filepath.Join(*out, label)
		must(os.Mkdir(dir, 0755))
		m := machine.New()
		d := dos.New(m, *root)
		d.Install()
		must(state.Load(*snapshot, m, d))
		start := m.Steps
		word := func(off uint16) uint16 { return m.Read16(0x1e880 + uint32(off)) }
		words := func(seg, off uint16, n int) []uint16 {
			a := make([]uint16, n)
			for i := range a {
				a[i] = m.Read16(uint32(seg)*16 + uint32(off) + uint32(i*2))
			}
			return a
		}
		for _, ip := range []uint16{0x19ac, 0x122, 0x334, 0x345c} {
			at := 0xe570 + int(ip)
			for i := 0; i < 24; i++ {
				if m.Read8(0xf670+uint32(ip)+uint32(i)) != code[at+i] {
					panic("entry prefix")
				}
			}
		}
		initial := map[string]any{"cs": m.CPU.Seg[cpu.CS], "ip": m.CPU.IP, "ds": m.CPU.Seg[cpu.DS], "step": start, "player": words(0x1e88, 0x56e8, 12), "enemy": words(0x1e88, 0x5700, 12), "map": words(0x1e88, 0x6fb6, 6), "learned": word(0x26aa), "charges": words(0x1e88, 0x2aa8, 8)}
		events := []map[string]any{}
		mutations := []map[string]any{}
		keys := []map[string]any{}
		bitmaps := []map[string]any{}
		quakePans := []map[string]any{}
		configured, castStarted, finished := false, false, false
		menuKey, targetKey := false, false
		menu, target := false, false
		targetPlanNode, menuPlanNode := -1, -1
		var retCS, retIP, retSS, retSP uint16
		var bitmap map[string]any
		effectCount := 0
		targets := map[uint16]string{0x19ac: "player-turn", 0x122: "spell-menu", 0x31e: "consume-charge", 0x334: "player-spell", 0x345c: "player-effect", 0x283e: "target-selection", 0x36c6: "enemy-effect", 0x960: "player-quake", 0x3662: "quake-damage"}
		capture := func(name string) {
			if !observe {
				return
			}
			if len(events) >= 200 {
				panic("event bound")
			}
			c := m.CPU
			sp := c.R[cpu.SP]
			bp := c.R[cpu.BP]
			v := map[string]any{"name": name, "step": m.Steps, "cycles": m.CPU.Cycles, "cs": c.Seg[cpu.CS], "ip": c.IP, "registers": c.R, "segments": c.Seg, "stack": words(c.Seg[cpu.SS], sp, 10), "bp_minus_4": m.Read16(uint32(c.Seg[cpu.SS])*16 + uint32(bp-4)), "charges": words(0x1e88, 0x2aa8, 8), "player": words(0x1e88, 0x56e8, 12), "enemy": words(0x1e88, 0x5700, 12), "enemy_map": words(0x1e88, 0x6fc2, 6), "player_positions": words(0x1e88, 0x703c, 6), "enemy_positions": words(0x1e88, 0x701e, 6), "chance_stat": word(0x26ae)}
			events = append(events, v)
			if name == "spell-menu" || name == "player-spell" || name == "player-effect" || name == "player-spell:return" || name == "player-quake" {
				file := name
				if name == "player-effect" {
					effectCount++
					file = fmt.Sprintf("player-effect-%02d", effectCount)
					if effectCount == 1 {
						must(state.Save(filepath.Join(dir, "player-effect.state"), m, d))
					}
				}
				must(state.Save(filepath.Join(dir, file+".state"), m, d))
				shot(m, filepath.Join(dir, file+".png"))
			}
		}
		queue := func(scan uint8, why string) {
			m.PushKey(scan)
			keys = append(keys, map[string]any{"step": m.Steps, "scan": scan, "why": why})
			if len(keys) > 100 {
				panic("key bound")
			}
		}
		selectEnemy := func(startNode int) {
			type route struct {
				node int
				keys []uint8
			}
			pending := []route{{node: startNode}}
			seen := map[int]bool{startNode: true}
			for len(pending) > 0 {
				at := pending[0]
				pending = pending[1:]
				if at.node >= 1 && at.node <= 6 {
					id := word(0x6fc0 + uint16(at.node)*2)
					kind := word(0x5700 + id*4)
					eligible := *targetKind == "any" || (*targetKind == "ghost" && kind >= 6 && kind <= 15) || (*targetKind == "ordinary" && (kind < 6 || kind > 15))
					if id < 6 && word(0x5702+id*4) > 0 && eligible {
						for _, scan := range at.keys {
							queue(scan, "original navigation table to live enemy")
							if *spell >= 2 {
								return
							}
						}
						queue(0x1c, "confirm live enemy with Enter")
						return
					}
				}
				for i, scan := range []uint8{0x48, 0x50, 0x4b, 0x4d} {
					next := int(m.Read8(0x1e880 + 0x709a + uint32(at.node)*4 + uint32(i)))
					if next > 0 && next <= 12 && !seen[next] {
						seen[next] = true
						keys := append(append([]uint8{}, at.keys...), scan)
						pending = append(pending, route{next, keys})
					}
				}
			}
			panic("no original navigation route to enemy")
		}
		queue(0x39, "single initial original action input")
		maxSteps := uint64(100000000)
		if *spell == 7 {
			maxSteps = 200000000
		}
		for m.Steps < start+maxSteps {
			c := m.CPU
			if configured && castStarted && c.Seg[cpu.CS] == retCS && c.IP == retIP && c.Seg[cpu.SS] == retSS && c.R[cpu.SP] == retSP {
				capture("player-spell:return")
				finished = true
				break
			}
			if c.Seg[cpu.CS] == 0xf67 {
				if observe && configured && *spell == 7 {
					phase := map[uint16]int{0xa05: 1, 0xa6e: 2, 0xad7: 3, 0xb40: 4, 0xba9: 5}[c.IP]
					if phase != 0 {
						quakePans = append(quakePans, map[string]any{"phase": phase, "step": m.Steps, "cycles": m.CPU.Cycles, "port_value": words(c.Seg[cpu.SS], c.R[cpu.SP], 2)})
						if len(quakePans) > 250 {
							panic("quake pan bound")
						}
					}
				}

				if *spell >= 3 && configured && menu && !menuKey && c.IP == 0x2b4 {
					node := int(m.Read16(uint32(c.Seg[cpu.SS])*16 + uint32(c.R[cpu.BP]-6)))
					if node != menuPlanNode {
						capture("spell-cursor")
						if *cancelMenu {
							queue(0x01, "cancel original spell menu")
							menuKey = true
						} else if node == *spell {
							queue(0x1c, "confirm original spell cursor")
							menuKey = true
						} else {
							queue(0x50, "original spell cursor Down")
						}
						menuPlanNode = node
					}
				}
				if configured && *spell == 3 && c.IP == 0x6ef {
					capture("assassination-die")
				}

				if *spell >= 2 && target && c.IP == 0x29f2 {
					node := int(m.Read16(uint32(c.Seg[cpu.SS])*16 + uint32(c.R[cpu.BP]-10)))
					if node != targetPlanNode {
						targetKey = true
						capture("target-cursor")
						if *cancelTarget {
							queue(0x01, "cancel original target menu")
						} else {
							selectEnemy(node)
						}
						targetPlanNode = node
					}
				}
				if name, ok := targets[c.IP]; ok {
					if c.IP == 0x19ac && !configured {
						must(state.Save(filepath.Join(dir, "before-fixture.state"), m, d))
						change := func(off, next uint16) {
							old := word(off)
							m.Write16(0x1e880+uint32(off), next)
							mutations = append(mutations, map[string]any{"offset": off, "old": old, "next": next, "step": m.Steps})
						}
						for i := uint16(0); i < 6; i++ {
							kind, count := uint16(0), uint16(0)
							if i == 0 {
								kind, count = 10, 50
							}
							change(0x56e8+i*4, kind)
							change(0x56ea+i*4, count)
							id := uint16(5)
							if i == 3 {
								id = 0
							}
							change(0x6fb6+i*2, id)
							change(0x8e46+i*2, 1)
						}
						change(0x26aa, 1)
						if *chanceStat >= 0 {
							change(0x26ae, uint16(*chanceStat))
						}
						if *fixture == "odd" {
							for i := uint16(0); i < 6; i++ {
								count := word(0x5702 + i*4)
								if count > 0 && count%2 == 0 {
									change(0x5702+i*4, count+1)
								}
							}
						}
						if *fixture == "no-ghost" {
							for i := uint16(0); i < 6; i++ {
								kind := word(0x5700 + i*4)
								if kind >= 6 && kind <= 15 {
									change(0x5700+i*4, 16)
								}
							}
						}
						if *fixture == "sparse" {
							for i := uint16(0); i < 6; i++ {
								if i != 1 {
									change(0x5702+i*4, 0)
								}
							}
						}
						for i := uint16(0); i < 8; i++ {
							n := uint16(0)
							if int(i) == *spell {
								n = 2
							}
							change(0x2aa8+i*2, n)
						}
						configured = true
						must(state.Save(filepath.Join(dir, "after-fixture.state"), m, d))
					}
					capture(name)
					if configured && c.IP == 0x334 && !castStarted {
						retIP = m.Read16(uint32(c.Seg[cpu.SS])*16 + uint32(c.R[cpu.SP]))
						retCS = m.Read16(uint32(c.Seg[cpu.SS])*16 + uint32(c.R[cpu.SP]) + 2)
						retSS = c.Seg[cpu.SS]
						retSP = c.R[cpu.SP] + 4
						castStarted = true
					}
					if configured && c.IP == 0x122 {
						menu = true
						if !menuKey && *spell < 3 {
							if *cancelMenu {
								queue(0x01, "cancel original spell menu")
							} else {
								for i := 0; i < *spell; i++ {
									queue(0x50, "original spell menu Down")
								}
								queue(0x1c, "select spell via original menu")
							}
							menuKey = true
						}
					}
					if configured && c.IP == 0x283e {
						target = true
						menu = false
						if !targetKey && *spell < 2 {
							if *cancelTarget {
								queue(0x01, "cancel original target menu")
							} else {
								selectEnemy(int(m.Read16(uint32(c.Seg[cpu.SS])*16 + uint32(c.R[cpu.SP]) + 4)))
							}
							targetKey = true
						}
					}
				}
			}
			if c.Seg[cpu.CS] == 0x14d2 && c.IP == 0xc86 {
				if menu && !menuKey && *spell < 3 {
					queue(0x1c, "select fireball via original menu")
					menuKey = true
				}
				if target && !targetKey {
					panic("target input must be planned at its validated entry")
					targetKey = true
				}
			}
			if observe && configured && c.Seg[cpu.CS] == 0x14d2 {
				if c.IP == 0x626 || c.IP == 0x4f2 {
					sp := c.R[cpu.SP]
					args := words(c.Seg[cpu.SS], sp+4, 4)
					source := args[0]
					a := uint32(args[1])*16 + uint32(source)
					w, h := m.Read16(a), m.Read16(a+2)
					if w > 100 || h > 200 {
						panic("bitmap geometry")
					}
					planes := 6
					raw := make([]byte, 4+int(w)*int(h)*planes)
					for i := range raw {
						raw[i] = m.Read8(a + uint32(i))
					}
					bitmap = map[string]any{"entry": c.IP, "entry_step": m.Steps, "entry_cycles": m.CPU.Cycles, "source_sha256": sha(raw), "width_bytes": w, "height": h, "args": args}
				}
				if bitmap != nil && ((c.IP == 0x76e && bitmap["entry"].(uint16) == 0x626) || (c.IP == 0x625 && bitmap["entry"].(uint16) == 0x4f2)) {
					bitmap["return_step"] = m.Steps
					bitmap["return_cycles"] = m.CPU.Cycles
					bitmaps = append(bitmaps, bitmap)
					if len(bitmaps) > 512 {
						must(state.Save(filepath.Join(dir, "diagnostic-bound.state"), m, d))
						shot(m, filepath.Join(dir, "diagnostic-bound.png"))
						saveJSON(filepath.Join(dir, "diagnostic-bound.json"), map[string]any{"events": events, "keys": keys, "bitmaps": bitmaps, "step": m.Steps, "registers": m.CPU.R, "segments": m.CPU.Seg, "ip": m.CPU.IP})
						panic("bitmap bound")
					}
					bitmap = nil
				}
			}
			must(m.Step())
		}
		must(state.Save(filepath.Join(dir, "final.state"), m, d))
		shot(m, filepath.Join(dir, "final.png"))
		raw, e := os.ReadFile(filepath.Join(dir, "final.state"))
		must(e)
		result := map[string]any{"initial": initial, "configured": configured, "completed": finished, "steps": m.Steps, "state_sha256": sha(raw), "mutations": mutations, "keys": keys, "events": events, "bitmaps": bitmaps, "quake_pans": quakePans, "charges": words(0x1e88, 0x2aa8, 8), "player": words(0x1e88, 0x56e8, 12), "enemy": words(0x1e88, 0x5700, 12), "spell": *spell, "fixture": *fixture, "target_kind": *targetKind, "cancel_menu": *cancelMenu, "cancel_target": *cancelTarget, "chance_stat": *chanceStat, "effect_count": effectCount}
		saveJSON(filepath.Join(dir, "trace.json"), result)
		runs = append(runs, result)
	}
	a, e := os.ReadFile(filepath.Join(*out, "control/final.state"))
	must(e)
	b, e := os.ReadFile(filepath.Join(*out, "observed/final.state"))
	must(e)
	equal := bytes.Equal(a, b)
	saveJSON(filepath.Join(*out, "receipt.json"), map[string]any{"schema": 1, "go": runtime.Version(), "input_sha256": sha(input), "pam_sha256": sha(pam), "state_equal": equal, "runs": runs, "limits": "Explicit rear caster and learned/charge fixture; not natural learning or production. Fixed full original RNG state, no reroll."})
	if !equal {
		panic("observer changed guest")
	}
	fmt.Println("paired player spell state_equal", equal, "completed", runs[0]["completed"])
}
