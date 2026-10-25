//go:build ignore

package eightsword

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"github.com/wicanr2/dosgolem/oracle"
)

type vgaReadSite struct {
	CS, IP      uint16
	Count       uint64
	First, Last uint64
	Min, Max    uint32
	Class       string
}

// ResearchVGAReads observes actual planar CPU reads, before latch loading.
// It does not replace drawing or read pixel values into the owned renderer.
func (e *Engine) ResearchVGAReads(out string) func() error {
	sites := map[uint32]*vgaReadSite{}
	total := uint64(0)
	e.Oracle.ObserveVideoReads(func(v oracle.VideoRead) {
		key := uint32(v.CS)<<16 | uint32(v.IP)
		s := sites[key]
		if s == nil {
			s = &vgaReadSite{CS: v.CS, IP: v.IP, First: v.Step, Min: v.Offset, Max: v.Offset, Class: "unknown"}
			sites[key] = s
		}
		s.Count++
		total++
		s.Last = v.Step
		if v.Offset < s.Min {
			s.Min = v.Offset
		}
		if v.Offset > s.Max {
			s.Max = v.Offset
		}
		t := e.Tracker
		if t == nil {
			return
		}
		if v.CS == t.stringSeg {
			for _, r := range []struct {
				first, last uint16
				name        string
			}{
				{0x274, 0x322, "pixel"}, {0x33d, 0x371, "page-A000-to-A400"},
				{0x3b0, 0x3e4, "page-A400-to-A000"}, {0x423, 0x4f1, "rectangle-copy"},
				{0x4f2, 0x625, "masked-bitmap"}, {0x626, 0x76e, "masked-mirror-bitmap"},
				{0x76f, 0x854, "five-plane-bitmap"}, {0x99c, 0xa6f, "opaque-four-plane-bitmap"},
				{0xb86, 0xc85, "half-width-glyph"}, {0xd3e, 0xd74, "clear"},
			} {
				if v.IP >= r.first && v.IP <= r.last {
					s.Class = r.name
					break
				}
			}
		}
		if v.CS == t.fontSeg && v.IP >= 0x4a98 && v.IP <= 0x4bf7 {
			s.Class = "full-width-glyph"
		}
	})
	return func() error {
		e.Oracle.ObserveVideoReads(nil)
		ordered := make([]*vgaReadSite, 0, len(sites))
		classes := map[string]uint64{}
		for _, s := range sites {
			ordered = append(ordered, s)
			classes[s.Class] += s.Count
		}
		sort.Slice(ordered, func(i, j int) bool {
			a, b := ordered[i], ordered[j]
			if a.CS == b.CS {
				return a.IP < b.IP
			}
			return a.CS < b.CS
		})
		report := map[string]any{"schema": 1, "production": false, "drawing_replaced": false, "total": total, "sites": ordered, "classes": classes, "address_space": "runtime CS:IP from CPU.OpAddr; VGA offsets relative to A0000", "method": "metadata-only pre-read callback; original VGA.Read and latch side effects execute normally", "limits": []string{"Observed normal route only; absence here does not prove absence elsewhere.", "Unknown sites retain raw addresses and require caller evidence before classification."}}
		raw, err := json.MarshalIndent(report, "", "  ")
		if err != nil {
			return err
		}
		path := filepath.Join(out, "vga-reads.json")
		f, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
		if err != nil {
			return err
		}
		if _, err = f.Write(append(raw, 10)); err != nil {
			f.Close()
			return err
		}
		if err = f.Close(); err == nil {
			fmt.Printf("planar pre-read trace: %d reads, %d sites\n", total, len(sites))
		}
		return err
	}
}
