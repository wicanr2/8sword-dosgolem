//go:build ignore

// 053 DRAFT: bounded original PAE startup, no HD or guest patches.
package main

import (
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"

	"github.com/wicanr2/dosgolem/oracle"
)

func check(err error) {
	if err != nil {
		panic(err)
	}
}

func main() {
	root := flag.String("root", "", "read-only original directory")
	out := flag.String("out", "", "new research receipt directory")
	steps := flag.Uint64("steps", 2000000, "bounded startup steps, maximum 20000000")
	cmdline := flag.String("cmdline", "", "explicit research command tail, not a normal PAM handoff")
	state := flag.String("state", "", "resume this exact diagnostic snapshot; does not prove a natural player path")
	flag.Parse()
	if *root == "" || *out == "" || *steps == 0 || *steps > 20000000 {
		panic("invalid bounded ending probe arguments")
	}
	exe := filepath.Join(*root, "PAE.AY")
	raw, err := os.ReadFile(exe)
	check(err)
	sourceSHA := fmt.Sprintf("%x", sha256.Sum256(raw))
	if sourceSHA != "8ae11b4c89f0361ed0a2d5b1859bbb4750047d37f0e26885e6903e4feb721a0c" {
		panic("unknown PAE source")
	}
	check(os.Mkdir(*out, 0755))
	o, err := oracle.LoadWith(exe, *root, oracle.Options{Adlib: true, ProgramPath: `C:\PAE.AY`})
	check(err)
	if *state != "" {
		check(o.LoadStateFile(*state))
	} else {
		o.SetClock(12, 0, 0, 0)
		o.SetCmdLine(*cmdline)
	}
	o.SetScratch(filepath.Join(*out, "scratch"))
	var rows []map[string]any
	var runError string
	for _, target := range []uint64{1000, 100000, 1000000, 2000000, 5000000, 10000000, 20000000} {
		if target > *steps {
			break
		}
		if target <= o.Steps() {
			continue
		}
		err := o.Run(target - o.Steps())
		w, h, rgb := o.ScreenRGB()
		im := image.NewRGBA(image.Rect(0, 0, w, h))
		for i := 0; i < w*h; i++ {
			copy(im.Pix[i*4:i*4+3], rgb[i*3:i*3+3])
			im.Pix[i*4+3] = 255
		}
		name := fmt.Sprintf("native-%09d.png", o.Steps())
		f, fileErr := os.Create(filepath.Join(*out, name))
		check(fileErr)
		check(png.Encode(f, im))
		check(f.Close())
		rows = append(rows, map[string]any{"step": o.Steps(), "mode": o.VideoMode(), "ip": o.IP(), "registers": o.Regs(), "screen": name})
		if err != nil {
			runError = err.Error()
			break
		}
	}
	check(o.SaveStateFile(filepath.Join(*out, "final.state")))
	// Raw program RAM is retained locally for later narrow disassembly.
	check(os.WriteFile(filepath.Join(*out, "ram-00000-9ffff.bin"), o.Bytes(oracle.Addr{}, 0xa0000), 0644))
	report := map[string]any{"spec": "053", "status": "original-direct-entry-startup-research", "source": "PAE.AY", "source_sha256": sourceSHA,
		"steps": o.Steps(), "clock": "fixed12:00:00.00 before execution", "input_events": []any{}, "guest_patches": false,
		"research_command_tail": *cmdline,
		"diagnostic_snapshot":   *state,
		"checkpoints":           rows, "run_error": runError, "file_ops": o.FileOps(), "exec_log": o.ExecLog(), "console": o.Console(), "unimplemented": o.Unimplemented(),
		"address_space": "dosgolem runtime segmented registers and linear RAM dump",
		"limits":        []string{"Standalone PAE diagnostic, not natural completion or production HD playback.", "Explicit research command tail only; no key or scene injection. Natural PAM handoff is not verified."}}
	b, err := json.MarshalIndent(report, "", "  ")
	check(err)
	check(os.WriteFile(filepath.Join(*out, "source-startup.json"), append(b, '\n'), 0644))
	fmt.Printf("PAE steps=%d checkpoints=%d error=%q\n", o.Steps(), len(rows), runError)
}
