//go:build ignore

// Compiled only into the explicitly named GUI fixture, never resume-ui.
package main

import (
	"encoding/binary"
	"errors"
	"flag"
	"os"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

var resumeFixture = flag.String("controlled-resume-fixture", "", "explicit fixed 3733 diagnostic state")

func init() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		old, err := previous(e, p)
		if err != nil || *resumeFixture == "" {
			return old, err
		}
		raw, err := os.ReadFile(*resumeFixture)
		if err != nil {
			return nil, err
		}
		if nativeSHA(raw) != "d3fdfd4f739d0256f6a29ed5a55a9506dfb753964bf4af7388b20827e17605df" {
			return nil, errors.New("fixture SHA")
		}
		r, err := savedResume(p.Current.Bytes.World)
		if err != nil || r != nil {
			return nil, errors.New("fixture cannot replace saved resume")
		}
		x := encounterCurrent
		if err = e.Oracle.LoadStateFile(*resumeFixture); err != nil {
			return nil, err
		}
		injected := false
		e.Oracle.OnHostInstruction(oracle.Far(0x110, 0x3733), func(m *dg.Machine) (bool, error) {
			c := m.CPU
			ds := uint32(0x1e880)
			bp := c.R[dg.BP]
			if injected || bp < 32 || m.Read16(ds+uint32(bp)+2) != 0x171d || m.Read16(ds+uint32(bp)+4) != 0x110 {
				return false, errors.New("fixture original caller")
			}
			c.R[dg.SI] = m.Read16(ds + uint32(bp) - 0x12)
			c.R[dg.DI] = m.Read16(ds + uint32(bp) - 0x10)
			c.R[dg.SP] = bp + 6
			c.R[dg.BP] = m.Read16(ds + uint32(bp))
			c.IP = 0x16e0
			for i, n := range pairWorldResources(p.Current.World).words() {
				m.Write16(ds+0x4f2+uint32(i*2), uint16(n))
			}
			for i := 0; i < 12; i++ {
				off := 12 + i*2
				m.Write16(ds+0x54a+uint32(i*2), binary.LittleEndian.Uint16(p.Current.Bytes.Native[off:])-uint16(off+3))
			}
			x.NativeRows = append([]byte(nil), m.Mem[ds+0x54a:ds+0x562]...)
			a := x.Presence
			a.Active = true
			a.HasArmy = true
			a.Prompt = false
			a.BP = c.R[dg.BP]
			a.SP = c.R[dg.SP]
			a.Token = p.Current.Token
			a.NativeRows = append([]byte(nil), x.NativeRows...)
			x.Sequence = 1
			x.Events = append(x.Events, map[string]any{"command": "controlled-resume-fixture", "native_rows_preserved": true})
			injected = true
			c.Cycles++
			return true, nil
		})
		return old, nil
	}
}
