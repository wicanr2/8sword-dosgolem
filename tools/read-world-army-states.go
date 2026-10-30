//go:build ignore

// Read world-army experiment snapshot bytes without loading the emulator or executing code.
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
	calls := flag.String("calls", "", "original states")
	out := flag.String("out", "", "new decoding output")
	flag.Parse()
	check := func(err error) {
		if err != nil {
			panic(err)
		}
	}
	if *out == "" || os.Getuid() != 1000 {
		panic("paths and UID1000 required")
	}
	if _, e := os.Stat(*out); !os.IsNotExist(e) {
		panic("output exists")
	}
	check(os.Mkdir(*out, 0755))
	rows := map[string]any{}
	for _, name := range []string{"before-commit.state", "after-commit.state", "final-map.state"} {
		f, e := os.Open(filepath.Join(*calls, name))
		check(e)
		z, e := gzip.NewReader(f)
		check(e)
		raw, e := io.ReadAll(io.LimitReader(z, 64<<20))
		check(e)
		check(z.Close())
		check(f.Close())
		if len(raw) < 16 {
			panic("short state")
		}
		size := binary.LittleEndian.Uint64(raw)
		if size > uint64(len(raw)-16) {
			panic("machine section bound")
		}
		dosAt := 8 + size
		dosSize := binary.LittleEndian.Uint64(raw[dosAt:])
		if dosSize != uint64(len(raw))-dosAt-8 {
			panic("DOS section bound")
		}
		var s struct {
			Magic   string
			Version int
			Mem     []byte
			R       [8]uint16
			Seg     [4]uint16
			IP      uint16
			Flags   uint16
			Steps   uint64
		}
		check(gob.NewDecoder(bytes.NewReader(raw[8 : 8+size])).Decode(&s))
		if s.Magic != "DOSGOLEM-M" || s.Version != 3 || len(s.Mem) != 1<<20 {
			panic("state schema")
		}
		h := fmt.Sprintf("%x", sha256.Sum256(s.Mem))
		file := h + ".ram.gz"
		if _, err := os.Stat(filepath.Join(*out, file)); os.IsNotExist(err) {
			b := bytes.Buffer{}
			g := gzip.NewWriter(&b)
			_, e = g.Write(s.Mem)
			check(e)
			check(g.Close())
			check(os.WriteFile(filepath.Join(*out, file), b.Bytes(), 0644))
		}
		rows[name] = map[string]any{"memory_sha256": h, "memory_file": file, "registers": s.R, "segments": s.Seg, "ip": s.IP, "flags": s.Flags, "steps": s.Steps}
	}
	b, e := json.MarshalIndent(rows, "", "  ")
	check(e)
	check(os.WriteFile(filepath.Join(*out, "index.json"), append(b, '\n'), 0644))
	fmt.Println("Read three original snapshots without running guest instructions")
}
