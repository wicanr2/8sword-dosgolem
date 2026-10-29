// 030 DRAFT: isolate snapshot resume from optional visual hooks.
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"github.com/wicanr2/dosgolem/internal/dos"
	"github.com/wicanr2/dosgolem/internal/machine"
	"github.com/wicanr2/dosgolem/internal/state"
	"github.com/wicanr2/dosgolem/oracle"
	"os"
	"path/filepath"
)

func must(e error) {
	if e != nil {
		panic(e)
	}
}
func main() {
	root := flag.String("root", "", "original")
	snapshot := flag.String("state", "", "fixed input")
	steps := flag.Uint64("steps", 0, "absolute final step")
	out := flag.String("out", "", "new output")
	flag.Parse()
	must(os.Mkdir(*out, 0755))
	original, e := os.ReadFile(*snapshot)
	must(e)
	for _, kind := range []string{"machine", "PAM.AY", "PREDELLA.EXE"} {
		name := kind
		if kind != "machine" {
			name = kind[:3]
		}
		dir := filepath.Join(*out, name)
		must(os.Mkdir(dir, 0755))
		if kind == "machine" {
			m := machine.New()
			d := dos.New(m, *root)
			d.Install()
			must(state.Load(*snapshot, m, d))
			must(state.Save(filepath.Join(dir, "loaded.state"), m, d))
			for m.Steps < *steps {
				must(m.Step())
			}
			must(state.Save(filepath.Join(dir, "final.state"), m, d))
		} else {
			o, e := oracle.LoadWith(filepath.Join(*root, kind), *root, oracle.Options{Adlib: true, ProgramPath: `C:\PREDELLA.EXE`})
			must(e)
			must(o.LoadStateFile(*snapshot))
			must(o.SaveStateFile(filepath.Join(dir, "loaded.state")))
			must(o.Run(*steps - o.Steps()))
			must(o.SaveStateFile(filepath.Join(dir, "final.state")))
		}
		loaded, e := os.ReadFile(filepath.Join(dir, "loaded.state"))
		must(e)
		fmt.Println(name, "load equals input", bytes.Equal(loaded, original))
	}
	rows := map[string]bool{}
	a, e := os.ReadFile(filepath.Join(*out, "machine/final.state"))
	must(e)
	for _, name := range []string{"PAM", "PRE"} {
		b, e := os.ReadFile(filepath.Join(*out, name, "final.state"))
		must(e)
		rows[name] = bytes.Equal(a, b)
	}
	raw, e := json.MarshalIndent(rows, "", "  ")
	must(e)
	must(os.WriteFile(filepath.Join(*out, "receipt.json"), raw, 0644))
	fmt.Println(string(raw))
}
