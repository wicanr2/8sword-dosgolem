//go:build ignore

package main

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"path/filepath"
	"strings"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

type nativeCheckpointPort struct {
	Engine                     *game.Engine
	Port                       *worldArmyPort
	Scratch                    string
	Code                       []byte
	EntrySP, EntryBP, ReturnIP uint16
	Active, Committed          bool
	FileCursor                 int
	WriteCursor                int
	Token                      string
	Saves                      uint64
	Events                     []map[string]any
	NativeRows                 []byte
	NativeReads                uint64
}

func checkpointLocation(o *oracle.Oracle) map[string]any {
	words := map[string]uint16{}
	for _, off := range []uint16{0x56c4, 0x56ca, 0x56cc, 0x56ce, 0x56d0, 0x56d2, 0x56d6, 0x56dc, 0x8e12, 0x8e44} {
		words[fmt.Sprintf("DS:%04X", off)] = o.Word(oracle.Far(0x1e88, off))
	}
	name := o.Bytes(oracle.Far(0x1e88, 0x8e52), 16)
	if at := bytes.IndexByte(name, 0); at >= 0 {
		name = name[:at]
	}
	return map[string]any{"raw_words": words, "map_name": strings.ToLower(string(name)), "map_sha256": nativeSHA(o.Bytes(oracle.Far(0x9c00, 0), 5761))}
}
func installNativeCheckpoint(e *game.Engine, p *worldArmyPort, scratch string) (*nativeCheckpointPort, error) {
	code, x := worldArmyCode(e.PAM)
	if x != nil {
		return nil, x
	}
	v := &nativeCheckpointPort{Engine: e, Port: p, Scratch: scratch, Code: code}
	checkSource := func(o *oracle.Oracle) bool {
		return bytes.Equal(code[0x84c0:0x8d38], o.Bytes(oracle.Far(0x110, 0x84c0), 0x878)) && bytes.Equal(code[0x4878:0x48ee], o.Bytes(oracle.Far(0x110, 0x4878), 0x76))
	}
	e.Oracle.OnCall(oracle.Far(0x110, 0x84c0), func(o *oracle.Oracle) {
		r := o.Regs()
		fail := func(s string) { panic(&worldArmyPortFault{"native checkpoint: " + s}) }
		if !checkSource(o) || r.CS != 0x110 || r.DS != 0x1e88 || r.SS != 0x1e88 || r.SP < 32 || r.SP > 65520 || o.Word(oracle.Far(r.SS, r.SP+2)) != 0x110 {
			fail("entry source/frame")
		}
		ret := o.Word(oracle.Far(r.SS, r.SP))
		if ret != 0x4186 {
			fail(fmt.Sprintf("unadmitted save caller %04x", ret))
		}
		if v.Active {
			if r.SP == v.EntrySP && r.BP == v.EntryBP && !v.Committed {
				return
			}
			fail("overlapping save")
		}
		s, x := p.snapshot()
		if x != nil {
			fail(x.Error())
		}
		for i, n := range pairWorldResources(s.World).words() {
			if uint64(o.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
				fail("entry resources")
			}
		}
		rows := o.Bytes(oracle.Far(0x1e88, 0x54a), 24)
		for i := 0; i < 12; i++ {
			off := 12 + i*2
			if binary.LittleEndian.Uint16(rows[i*2:]) != binary.LittleEndian.Uint16(s.Bytes.Native[off:])-uint16(off+3) {
				fail("original shadow army differs")
			}
		}
		v.NativeRows = bytes.Clone(rows)
		v.Active = true
		v.Committed = false
		v.EntrySP = r.SP
		v.EntryBP = r.BP
		v.ReturnIP = ret
		v.Token = s.Token
		v.FileCursor = len(o.FileOps())
		v.WriteCursor = len(o.Wrote())
	})
	e.Oracle.OnCall(oracle.Far(0x110, 0x8524), func(o *oracle.Oracle) {
		r := o.Regs()
		if !v.Active || v.Committed || !checkSource(o) || r.CS != 0x110 || r.DS != 0x1e88 || r.SS != 0x1e88 || r.BP != v.EntrySP-2 || r.SP != r.BP-10 || !bytes.Equal(v.NativeRows, o.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
			panic(&worldArmyPortFault{"native checkpoint: unbound shadow army copy"})
		}
		v.NativeReads++
	})
	e.Oracle.OnHostInstruction(oracle.Far(0x110, 0x8d31), func(m *dg.Machine) (bool, error) {
		fault := func(s string) (bool, error) { return false, &worldArmyPortFault{"native checkpoint: " + s} }
		o := e.Oracle
		c := m.CPU
		bp := c.R[dg.BP]
		ds := uint32(0x1e880)
		if !v.Active || !checkSource(o) || c.Seg[dg.CS] != 0x110 || c.Seg[dg.DS] != 0x1e88 || c.Seg[dg.SS] != 0x1e88 || bp != v.EntrySP-2 || c.R[dg.SP] != bp-10 || m.Read16(ds+uint32(bp)) != v.EntryBP || m.Read16(ds+uint32(bp)+2) != v.ReturnIP || m.Read16(ds+uint32(bp)+4) != 0x110 {
			return fault("completed frame/source")
		}
		if v.Committed {
			return false, nil
		}
		s, x := p.snapshot()
		if x != nil {
			return fault(x.Error())
		}
		if s.Token != v.Token {
			return fault("save token changed")
		}
		native, x := pairRead(filepath.Join(scratch, "gamedata.ay"), 2987)
		if x != nil {
			return fault(x.Error())
		}
		if !bytes.Equal(native, o.Bytes(oracle.Far(0x9e00, 0), 2987)) {
			return fault("progress buffer mismatch")
		}
		files, x := readNativeCheckpointMaps(scratch)
		if x != nil {
			return fault(x.Error())
		}
		loc := checkpointLocation(o)
		name := loc["map_name"].(string)
		if !bytes.Equal(files[name], o.Bytes(oracle.Far(0x9c00, 0), 5761)) {
			return fault("map buffer mismatch")
		}
		ops := o.FileOps()
		if v.FileCursor > len(ops) {
			return fault("file log reset")
		}
		written := map[string]int{}
		closed := map[string]bool{}
		writes := o.Wrote()
		if v.WriteCursor > len(writes) {
			return fault("write log reset")
		}
		for _, w := range writes[v.WriteCursor:] {
			n := strings.ToLower(filepath.Base(strings.ReplaceAll(w.Name, "\\", "/")))
			written[n] += w.N
		}
		for _, op := range ops[v.FileCursor:] {
			n := strings.ToLower(filepath.Base(strings.ReplaceAll(op.Name, "\\", "/")))
			if op.Failed {
				return fault("DOS file operation failed")
			}
			if op.Op == "close" {
				closed[n] = true
			}
		}
		if written["gamedata.ay"] != 2987 || written[name] != 5761 || !closed["gamedata.ay"] || !closed[name] {
			return fault("incomplete source writes")
		}
		next, x := p.Store.CommitCheckpoint(s.Token, native, files)
		if x != nil {
			return fault(x.Error())
		}
		p.Current = next
		v.Token = next.Token
		v.Committed = true
		v.Saves++
		v.Events = append(v.Events, map[string]any{"token": next.Token, "native_sha256": next.NativeSHA, "location": loc, "file_ops": ops[v.FileCursor:], "write_requests": writes[v.WriteCursor:], "world": next.World, "shadow_army_reads": v.NativeReads})
		return false, nil // Original pop SI/pop DI/RETF still own the far return.
	})
	e.Oracle.OnCall(oracle.Far(0x110, 0x8d36), func(o *oracle.Oracle) {
		if v.Active {
			if !v.Committed {
				panic(&worldArmyPortFault{errors.New("checkpoint returned uncommitted").Error()})
			}
			v.Active = false
		}
	})
	return v, nil
}
