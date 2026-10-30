// Standalone std-only gob reader. No CPU execution or game helper imports.
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
	input := flag.String("input", "", "saved original controls")
	out := flag.String("out", "", "new directory")
	flag.Parse()
	check := func(e error) {
		if e != nil {
			panic(e)
		}
	}
	check(os.Mkdir(*out, 0755))
	files, e := filepath.Glob(filepath.Join(*input, "*", "*.state"))
	check(e)
	if len(files) != 20 {
		panic("ten paired controls required")
	}
	rows := map[string]any{}
	for _, p := range files {
		stored, e := os.ReadFile(p)
		check(e)
		z, e := gzip.NewReader(bytes.NewReader(stored))
		check(e)
		raw, e := io.ReadAll(io.LimitReader(z, 64<<20))
		check(e)
		check(z.Close())
		if len(raw) < 16 {
			panic("short state")
		}
		n := binary.LittleEndian.Uint64(raw)
		if n > uint64(len(raw)-16) {
			panic("machine section bound")
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
		hash := fmt.Sprintf("%x", sha256.Sum256(state.Mem))
		target := filepath.Join(*out, hash+".ram.gz")
		if _, e := os.Stat(target); os.IsNotExist(e) {
			f, e := os.OpenFile(target, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
			check(e)
			gz := gzip.NewWriter(f)
			_, e = gz.Write(state.Mem)
			check(e)
			check(gz.Close())
			check(f.Close())
		}
		name, e := filepath.Rel(*input, p)
		check(e)
		rows[name] = map[string]any{"state_sha256": fmt.Sprintf("%x", sha256.Sum256(stored)), "memory_sha256": hash, "memory_bytes": len(state.Mem)}
	}
	raw, e := json.MarshalIndent(rows, "", "  ")
	check(e)
	check(os.WriteFile(filepath.Join(*out, "index.json"), append(raw, '\n'), 0600))
	fmt.Println("independently decoded", len(rows), "saved states")
}
