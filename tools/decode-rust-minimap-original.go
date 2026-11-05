//go:build ignore

// Decode an existing dosgolem receipt only. This is not a runtime game helper.
package main

import (
	"compress/gzip"
	"encoding/binary"
	"encoding/gob"
	"fmt"
	"io"
	"os"
)

func main() {
	if os.Getuid() != 1000 {
		panic("UID")
	}
	if _, e := os.Stat("/.dockerenv"); e != nil {
		panic(e)
	}
	f, e := os.Open("/in/final.state")
	if e != nil {
		panic(e)
	}
	defer f.Close()
	z, e := gzip.NewReader(f)
	if e != nil {
		panic(e)
	}
	defer z.Close()
	// internal/state.readSection: gzip stream starts with a LE64 section length.
	var n uint64
	if e = binary.Read(z, binary.LittleEndian, &n); e != nil {
		panic(e)
	}
	if n == 0 || n > 4<<20 {
		panic("section length")
	}
	var s struct {
		Magic   string
		Version int
		Mem     []byte
		Seg     [4]uint16
	}
	if e = gob.NewDecoder(io.LimitReader(z, int64(n))).Decode(&s); e != nil {
		panic(e)
	}
	if s.Magic != "DOSGOLEM-M" || s.Version < 2 || s.Version > 3 {
		panic("state identity")
	}
	if len(s.Mem) < 1048576 {
		panic("short RAM")
	}
	if e = os.WriteFile("/out/evidence/original-ram.bin", s.Mem, 0644); e != nil {
		panic(e)
	}
	fmt.Printf("RAM %d segments %v\n", len(s.Mem), s.Seg)
}
