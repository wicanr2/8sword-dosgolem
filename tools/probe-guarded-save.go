//go:build ignore

// Source serializer mapping only. Tagged NPC words never enter gameplay.
package main

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	"github.com/wicanr2/dosgolem/oracle"
	"os"
	"path/filepath"
)

func main() {
	root := flag.String("root", "", "original root")
	input := flag.String("input", "", "fixed input")
	out := flag.String("out", "", "new output")
	flag.Parse()
	must := func(e error) {
		if e != nil {
			panic(e)
		}
	}
	if os.Getuid() != 1000 {
		panic("UID1000 required")
	}
	must(os.Mkdir(*out, 0700))
	state := filepath.Join(*input, "origin-source.state")
	raw, e := os.ReadFile(state)
	must(e)
	if fmt.Sprintf("%x", sha256.Sum256(raw)) != "e618d4343697fa00a50ab4b6021b169f6a5e21e4eaf86100c1fac9cd7a98777b" {
		panic("source state")
	}
	o, e := oracle.LoadWith(filepath.Join(*root, "PAM.AY"), *root, oracle.Options{Adlib: true})
	must(e)
	defer o.Close()
	must(o.LoadStateFile(state))
	scratch := filepath.Join(*out, "scratch")
	must(os.Mkdir(scratch, 0700))
	o.SetScratch(scratch)
	for i := 0; i < 9; i++ {
		name := fmt.Sprintf("map%02d.ay", i)
		b, e := os.ReadFile(filepath.Join(*input, "maps", name))
		must(e)
		must(os.WriteFile(filepath.Join(scratch, name), b, 0600))
	}
	for i := 0; i < 504; i++ {
		o.WriteU16(oracle.Far(0x1e88, 0x365e+uint16(i*2)), 0x5000+uint16(i))
	}
	must(o.SaveStateFile(filepath.Join(*out, "before.state")))
	_, e = o.CallBudget(3000000, oracle.Far(0x110, 0x84c0))
	must(e)
	native, e := os.ReadFile(filepath.Join(scratch, "gamedata.ay"))
	must(e)
	if len(native) != 2987 {
		panic("source save size")
	}
	offsets := make([]int, 504)
	for i := range offsets {
		found := -1
		for at := 0; at+2 <= len(native); at += 2 {
			v := binary.LittleEndian.Uint16(native[at:]) - uint16(at+3)
			if v == 0x5000+uint16(i) {
				if found != -1 {
					panic("duplicate tagged word")
				}
				found = at
			}
		}
		if found < 0 {
			panic(fmt.Sprint("missing NPC word ", i))
		}
		offsets[i] = found
	}
	must(o.SaveStateFile(filepath.Join(*out, "after.state")))
	b, e := json.MarshalIndent(map[string]any{"status": "passed-native-guard-save-mapping", "offsets": offsets, "source_state_sha256": fmt.Sprintf("%x", sha256.Sum256(raw)), "controlled_words": 504, "player_path": false, "scope": "Only the existing source serializer runs; no tagged NPC troop is used by combat."}, "", "  ")
	must(e)
	must(os.WriteFile(filepath.Join(*out, "receipt.json"), append(b, '\n'), 0600))
}
