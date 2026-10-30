// Standalone std-only saved-state reader; no CPU or game code is imported.
package main

import (
	"bytes"
	"compress/gzip"
	"crypto/sha256"
	"encoding/binary"
	"encoding/gob"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
)

func main() {
	input := flag.String("input", "", "original control directory")
	out := flag.String("out", "", "new JSON receipt")
	flag.Parse()
	check := func(err error) {
		if err != nil {
			panic(err)
		}
	}
	rows := map[string]any{}
	files, err := filepath.Glob(filepath.Join(*input, "*", "*.state"))
	check(err)
	if len(files) != 24 {
		panic("expected twelve before/after pairs")
	}
	for _, path := range files {
		stored, err := os.ReadFile(path)
		check(err)
		z, err := gzip.NewReader(bytes.NewReader(stored))
		check(err)
		raw, err := io.ReadAll(io.LimitReader(z, 64<<20))
		check(err)
		check(z.Close())
		if len(raw) < 16 {
			panic("short state")
		}
		n := binary.LittleEndian.Uint64(raw)
		if n > uint64(len(raw)-16) {
			panic("state section bound")
		}
		var state struct {
			Magic   string
			Version int
			Mem     []byte
		}
		check(gob.NewDecoder(bytes.NewReader(raw[8 : 8+n])).Decode(&state))
		if state.Magic != "DOSGOLEM-M" || state.Version != 3 || len(state.Mem) < 1<<20 {
			panic("fixed core state schema")
		}
		word := func(off int) uint16 { return binary.LittleEndian.Uint16(state.Mem[0x1e880+off:]) }
		words := func(off, count int) []uint16 {
			v := make([]uint16, count)
			for i := range v {
				v[i] = word(off + i*2)
			}
			return v
		}
		name, err := filepath.Rel(*input, path)
		check(err)
		rows[name] = map[string]any{"state_sha256": fmt.Sprintf("%x", sha256.Sum256(stored)), "progress": words(0x4f2, 6), "army": words(0x54a, 12), "origin": words(0x3be, 2), "position_x": word(0x8e12), "position_y": word(0x8e44), "travel_56c4": words(0x56c4, 10)}
	}
	raw, err := json.MarshalIndent(rows, "", "  ")
	check(err)
	f, err := os.OpenFile(*out, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	check(err)
	_, err = f.Write(append(raw, '\n'))
	check(err)
	check(f.Close())
	fmt.Println("independently decoded", len(rows), "original states")
}
