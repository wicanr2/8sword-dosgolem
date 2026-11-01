//go:build ignore

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
	root := flag.String("root", "", "original")
	input := flag.String("input", "", "fixed inputs")
	out := flag.String("out", "", "new output")
	flag.Parse()
	must := func(e error) {
		if e != nil {
			panic(e)
		}
	}
	if os.Getuid() != 1000 {
		panic("UID1000")
	}
	must(os.Mkdir(*out, 0700))
	raw, e := os.ReadFile(filepath.Join(*input, "origin-source.state"))
	must(e)
	if fmt.Sprintf("%x", sha256.Sum256(raw)) != "e618d4343697fa00a50ab4b6021b169f6a5e21e4eaf86100c1fac9cd7a98777b" {
		panic("source")
	}
	o, e := oracle.LoadWith(filepath.Join(*root, "PAM.AY"), *root, oracle.Options{Adlib: true})
	must(e)
	defer o.Close()
	must(o.LoadStateFile(filepath.Join(*input, "origin-source.state")))
	scratch := filepath.Join(*out, "scratch")
	must(os.Mkdir(scratch, 0700))
	o.SetScratch(scratch)
	for i := 0; i < 9; i++ {
		n := fmt.Sprintf("map%02d.ay", i)
		b, e := os.ReadFile(filepath.Join(*input, "maps", n))
		must(e)
		must(os.WriteFile(filepath.Join(scratch, n), b, 0600))
	}
	coords := make([][2]uint16, 8)
	names := make([][]byte, 8)
	word := func(at uint16) uint16 { return o.Word(oracle.Far(0x1e88, at)) }
	for i := 0; i < 8; i++ {
		coords[i] = [2]uint16{word(0x26bc + uint16(i*6)), word(0x26be + uint16(i*6))}
		names[i] = append([]byte{}, o.Bytes(oracle.Far(0x1e88, 0x26ea+uint16(i*14)), 14)...)
		o.WriteU16(oracle.Far(0x1e88, 0x275a+uint16(i*2)), 0x6000+uint16(i))
	}
	must(o.SaveStateFile(filepath.Join(*out, "before.state")))
	_, e = o.CallBudget(3000000, oracle.Far(0x110, 0x84c0))
	must(e)
	native, e := os.ReadFile(filepath.Join(scratch, "gamedata.ay"))
	must(e)
	offsets := make([]int, 8)
	for i := range offsets {
		atFound := -1
		for at := 0; at+2 <= len(native); at += 2 {
			if binary.LittleEndian.Uint16(native[at:])-uint16(at+3) == 0x6000+uint16(i) {
				if atFound != -1 {
					panic("duplicate")
				}
				atFound = at
			}
		}
		if atFound < 0 {
			panic("missing sword")
		}
		offsets[i] = atFound
	}
	must(o.SaveStateFile(filepath.Join(*out, "after.state")))
	b, e := json.MarshalIndent(map[string]any{"status": "passed-original-sword-save-layout", "offsets": offsets, "boss_coordinates": coords, "raw_names": names, "source_state_sha256": fmt.Sprintf("%x", sha256.Sum256(raw)), "controlled_serializer_words": 8, "player_path": false}, "", "  ")
	must(e)
	must(os.WriteFile(filepath.Join(*out, "receipt.json"), append(b, '\n'), 0600))
}
