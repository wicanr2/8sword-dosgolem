//go:build ignore

// Read the fixed core's saved machine section without executing instructions.
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
)

func main() {
	input := flag.String("state", "", "state input")
	out := flag.String("out", "", "new JSON output")
	flag.Parse()
	check := func(e error) {
		if e != nil {
			panic(e)
		}
	}
	stored, e := os.ReadFile(*input)
	check(e)
	z, e := gzip.NewReader(bytes.NewReader(stored))
	check(e)
	raw, e := io.ReadAll(io.LimitReader(z, 64<<20))
	check(e)
	check(z.Close())
	if len(raw) < 16 {
		panic("short state")
	}
	size := binary.LittleEndian.Uint64(raw)
	if size > uint64(len(raw)-16) {
		panic("machine section bound")
	}
	var s struct {
		Magic     string
		Version   int
		Mem       []byte
		R         [8]uint16
		Seg       [4]uint16
		IP, Flags uint16
		Steps     uint64
		Cycles    uint64
	}
	check(gob.NewDecoder(bytes.NewReader(raw[8 : 8+size])).Decode(&s))
	if s.Magic != "DOSGOLEM-M" || s.Version != 3 || len(s.Mem) != 1<<20 {
		panic("fixed state schema")
	}
	word := func(at uint32) uint16 {
		if at+2 > uint32(len(s.Mem)) {
			panic("word bound")
		}
		return binary.LittleEndian.Uint16(s.Mem[at:])
	}
	ds := uint32(0x1e880)
	resources := make([]uint16, 6)
	army := make([]map[string]uint16, 6)
	for i := 0; i < 6; i++ {
		resources[i] = word(ds + 0x4f2 + uint32(i*2))
		army[i] = map[string]uint16{"kind": word(ds + 0x54a + uint32(i*4)), "count": word(ds + 0x54c + uint32(i*4))}
	}
	sp := s.R[4]
	stack := make([]uint16, 16)
	for i := range stack {
		stack[i] = word((uint32(s.Seg[2])*16 + uint32(uint16(int(sp)+i*2))) & 0xfffff)
	}
	code := (uint32(s.Seg[1])*16 + uint32(s.IP)) & 0xfffff
	end := code + 32
	if end > uint32(len(s.Mem)) {
		end = uint32(len(s.Mem))
	}
	report := map[string]any{"schema": 1, "input": *input, "state_sha256": fmt.Sprintf("%x", sha256.Sum256(stored)), "memory_sha256": fmt.Sprintf("%x", sha256.Sum256(s.Mem)), "steps": s.Steps, "registers": s.R, "segments": s.Seg, "ip": s.IP, "flags": s.Flags, "cs_ip": fmt.Sprintf("%04X:%04X", s.Seg[1], s.IP), "code_bytes": fmt.Sprintf("%x", s.Mem[code:end]), "stack_words": stack, "native_resources_04f2": resources, "native_army_054a": army, "ds_7484": word(ds + 0x7484), "ds_56bc": word(ds + 0x56bc), "bda_head": word(0x41a), "bda_tail": word(0x41c), "bda_ring_hex": fmt.Sprintf("%x", s.Mem[0x41e:0x43e]), "address_space": "dosgolem runtime linear; resources/army relative to verified PAM DS=1E88; raw register arrays follow core v923", "guest_execution": false}
	b, e := json.MarshalIndent(report, "", "  ")
	check(e)
	f, e := os.OpenFile(*out, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	check(e)
	_, e = f.Write(append(b, '\n'))
	check(e)
	check(f.Close())
	fmt.Println(report["cs_ip"], resources, army)
}
