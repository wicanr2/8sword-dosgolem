//go:build ignore

// 053 DRAFT. Read-only PAE source observation, never a production renderer.
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"github.com/wicanr2/dosgolem/oracle"
)

func check(err error) {
	if err != nil {
		panic(err)
	}
}

func digest(raw []byte) string { return fmt.Sprintf("%x", sha256.Sum256(raw)) }

type bitmapCall struct {
	Entry, Return, SP, DS, Mode, Destination uint16
	Step                                     uint64
	Kind, X, Y, WidthBytes, Height           int
	Raw                                      []byte
	SHA                                      string
}

func main() {
	root := flag.String("root", "", "read-only original game")
	catalog := flag.String("catalog", "", "ending-hd-r1 source catalog")
	out := flag.String("out", "", "new research output")
	flag.Parse()
	if *root == "" || *catalog == "" || *out == "" {
		panic("missing research arguments")
	}
	raw, err := os.ReadFile(filepath.Join(*root, "PAE.AY"))
	check(err)
	if digest(raw) != "8ae11b4c89f0361ed0a2d5b1859bbb4750047d37f0e26885e6903e4feb721a0c" {
		panic("unknown PAE source")
	}
	check(os.Mkdir(*out, 0755))
	check(os.Mkdir(filepath.Join(*out, "sources"), 0755))
	check(os.Mkdir(filepath.Join(*out, "native-samples"), 0755))
	manifest, err := os.ReadFile(filepath.Join(*catalog, "source.json"))
	check(err)
	var source struct {
		Records []struct {
			File   string `json:"source_file"`
			Record int    `json:"record"`
			SHA    string `json:"record_sha256"`
		} `json:"records"`
	}
	check(json.Unmarshal(manifest, &source))
	known := map[string][]string{}
	for _, r := range source.Records {
		known[r.SHA] = append(known[r.SHA], fmt.Sprintf("%s#%d", r.File, r.Record))
	}
	o, err := oracle.LoadWith(filepath.Join(*root, "PAE.AY"), *root, oracle.Options{Adlib: true, ProgramPath: `C:\PAE.AY`})
	check(err)
	o.SetScratch(filepath.Join(*out, "scratch"))
	o.SetClock(12, 0, 0, 0)
	o.SetCmdLine("v a y a n g")
	counts := map[string]int{}
	var calls, strings, samples []map[string]any
	seen, checked := map[string]bool{}, map[string]bool{}
	var checkedPixels uint64
	for _, spec := range []struct {
		Entry, Return uint16
		Kind          int
		SHA           string
	}{
		{0x4ec, 0x61f, 6, "85467a42c1b56b7eb880128fe34417adbe74fdf1bf42d857758908d8bbd79549"},
		{0x769, 0x84e, 5, "285723c100da394f2c125b5a1a293c0b24d4f18a8cf2276937ef4a47db4124bc"},
		{0x996, 0xa69, 4, "603833bfa266acbc8f7a3c8ecf3a30e9f15b5242211367534a7ca1145bb4cfad"},
	} {
		spec := spec
		var pending *bitmapCall
		o.OnCall(oracle.Addr{Seg: 0x393, Off: spec.Entry}, func(o *oracle.Oracle) {
			if pending != nil || digest(o.Bytes(oracle.Addr{Seg: 0x393, Off: spec.Entry}, int(spec.Return-spec.Entry)+1)) != spec.SHA {
				panic("PAE source routine identity or nesting differs")
			}
			ptr := oracle.Addr{Seg: o.Arg(1), Off: o.Arg(0)}
			w, h := int(o.Word(ptr)), int(o.Word(oracle.Addr{Seg: ptr.Seg, Off: ptr.Off + 2}))
			x, y := int(o.Arg(2)), int(o.Arg(3))
			if w < 1 || w > 80 || h < 1 || h > 200 || x+w > 80 || y+h > 200 || int(ptr.Off)+4+w*h*spec.Kind > 65536 {
				panic("unreviewed PAE source geometry")
			}
			r := o.Regs()
			data := o.Bytes(ptr, 4+w*h*spec.Kind)
			key := digest(data)
			if !seen[key] {
				check(os.WriteFile(filepath.Join(*out, "sources", key+".bin"), data, 0644))
				seen[key] = true
			}
			pending = &bitmapCall{Entry: spec.Entry, Return: spec.Return, SP: r.SP, DS: r.DS,
				Mode: o.Word(oracle.Addr{Seg: r.DS, Off: 0x177a}), Destination: o.Word(oracle.Addr{Seg: r.DS, Off: 0x1780}),
				Step: o.Steps(), Kind: spec.Kind, X: x, Y: y, WidthBytes: w, Height: h, Raw: data, SHA: key}
			counts[fmt.Sprintf("bitmap-%d", spec.Kind)]++
		})
		o.OnCall(oracle.Addr{Seg: 0x393, Off: spec.Return}, func(o *oracle.Oracle) {
			c := pending
			if c == nil {
				return
			}
			if o.Regs().SP != c.SP {
				panic("PAE source return stack differs")
			}
			pending = nil
			calls = append(calls, map[string]any{"entry_step": c.Step, "return_step": o.Steps(), "entry": c.Entry, "return": c.Return,
				"runtime_segment": 0x393, "ds": c.DS, "mode": c.Mode, "destination": c.Destination,
				"xywh": []int{c.X * 8, c.Y, c.WidthBytes * 8, c.Height}, "planes": c.Kind, "source_sha256": c.SHA, "catalog_records": known[c.SHA]})
			if len(calls) > 100000 {
				panic("bounded PAE source event budget exceeded")
			}
			if checked[c.SHA] || !o.EGAPlanarActive() || c.Mode != 1 || (c.Destination != 0xa000 && c.Destination != 0xa400) {
				return
			}
			pageStart := int(c.Destination-0xa000) * 16
			pixels := o.IndexedEGAFrom(pageStart, 640, 200)
			if len(pixels) != 640*200 {
				panic("PAE source display shape differs")
			}
			area, n := c.WidthBytes*c.Height, 0
			for y := 0; y < c.Height; y++ {
				for x := 0; x < c.WidthBytes*8; x++ {
					at, bit := y*c.WidthBytes+x/8, uint(7-x%8)
					if c.Kind == 6 && c.Raw[4+5*area+at]>>bit&1 == 0 {
						continue
					}
					var want byte
					for plane := 0; plane < 4; plane++ {
						want |= (c.Raw[4+plane*area+at] >> bit & 1) << uint(plane)
					}
					if got := pixels[(c.Y+y)*640+c.X*8+x]; got != want {
						panic(fmt.Sprintf("PAE source pixel mismatch %s x%d y%d got%d want%d", c.SHA, x, y, got, want))
					}
					n++
				}
			}
			checked[c.SHA] = true
			checkedPixels += uint64(n)
			name := "native-samples/" + c.SHA + ".idx"
			check(os.WriteFile(filepath.Join(*out, name), pixels, 0644))
			samples = append(samples, map[string]any{"source_sha256": c.SHA, "return_step": o.Steps(), "written_pixels": n,
				"destination": c.Destination, "plane_byte_start": pageStart, "xywh": []int{c.X * 8, c.Y, c.WidthBytes * 8, c.Height},
				"planes": c.Kind, "native_indices": name, "native_indices_sha256": digest(pixels)})
		})
	}
	o.OnCall(oracle.Addr{Seg: 0x393, Off: 0xadd}, func(o *oracle.Oracle) {
		if digest(o.Bytes(oracle.Addr{Seg: 0x393, Off: 0xadd}, 0x5f)) != "147f35d3df25d894c00f388f53f84317bc19754073b95ad811300b51e80f3244" {
			panic("PAE string routine differs")
		}
		ptr := oracle.Addr{Seg: o.Regs().DS, Off: o.Arg(0)}
		var data []byte
		for i := 0; i < 512; i++ {
			v := o.Byte(oracle.Addr{Seg: ptr.Seg, Off: ptr.Off + uint16(i)})
			if v == 0 {
				strings = append(strings, map[string]any{"step": o.Steps(), "ds": ptr.Seg, "source_offset": ptr.Off,
					"xy": []uint16{o.Arg(1), o.Arg(2)}, "raw_hex": hex.EncodeToString(data)})
				counts["string"]++
				return
			}
			data = append(data, v)
		}
		panic("PAE string exceeds research bound")
	})
	for _, site := range []struct {
		Offset uint16
		Name   string
	}{{0xd38, "clear"}, {0x196, "select-page"}} {
		site := site
		o.OnCall(oracle.Addr{Seg: 0x393, Off: site.Offset}, func(o *oracle.Oracle) { counts[site.Name]++ })
	}
	err = o.Run(200000000)
	runError := ""
	if err != nil {
		runError = err.Error()
	}
	if len(checked) != len(seen) || checkedPixels == 0 {
		panic("PAE native destination page sampling was incomplete")
	}
	check(o.SaveStateFile(filepath.Join(*out, "final.state")))
	report := map[string]any{"spec": "053", "status": "read-only-original-ending-source-observation", "source_sha256": digest(raw),
		"command_tail": "v a y a n g", "clock": "12:00:00.00 fixed before execution", "guest_patches": false, "normal_player_completion": false,
		"steps": o.Steps(), "run_error": runError, "counts": counts, "bitmap_calls": calls, "strings": strings,
		"unique_sources": len(seen), "checked_native_pixels": checkedPixels, "source_return_samples": samples,
		"file_ops": o.FileOps(), "exec_log": o.ExecLog(), "unimplemented": o.Unimplemented(),
		"address_space": "dosgolem runtime segmented addresses; glyph/string semantics remain separate",
		"limits":        []string{"No HD or pixel-loop replacement. Source observation and sampled written native indices only.", "Transparent preserved pixels, natural PAM handoff and normal completion are not proved."}}
	b, err := json.MarshalIndent(report, "", "  ")
	check(err)
	check(os.WriteFile(filepath.Join(*out, "source-observation.json"), append(b, '\n'), 0644))
	fmt.Printf("PAE steps=%d calls=%d strings=%d sources=%d pixels=%d error=%q\n", o.Steps(), len(calls), len(strings), len(seen), checkedPixels, runError)
}
