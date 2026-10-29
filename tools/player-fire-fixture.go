//go:build ignore

// Only for a private GUI diagnostic copy. Original menu and navigation consume IRQ1 keys.
package eightsword

import (
	"fmt"
	"github.com/wicanr2/dosgolem/oracle"
	"os"
)

var playerFireMenu, playerFireTarget bool

func (e *Engine) ResearchVFXTick() error {
	if os.Getenv("EIGHTSWORD_VFX_FIXTURE") != "1" || researchVFX.armed || e.battleVFX == nil {
		return nil
	}
	researchVFX.armed = true
	v := e.battleVFX
	e.Oracle.OnCall(oracle.Addr{Seg: v.code, Off: 0x19ac}, func(o *oracle.Oracle) {
		if researchVFX.changed {
			return
		}
		change := func(off, value uint16) {
			at := oracle.Addr{Seg: v.data, Off: off}
			old := o.Word(at)
			if old != value {
				o.WriteU16(at, value)
				researchVFX.mutations = append(researchVFX.mutations, map[string]any{"step": o.Steps(), "offset": off, "old": old, "new": value})
			}
		}
		for i := uint16(0); i < 6; i++ {
			kind, count := uint16(0), uint16(0)
			if i == 0 {
				kind, count = 10, 50
			}
			change(0x56e8+i*4, kind)
			change(0x56ea+i*4, count)
			id := uint16(5)
			if i == 3 {
				id = 0
			}
			change(0x6fb6+i*2, id)
			change(0x8e46+i*2, 1)
		}
		change(0x26aa, 1)
		for i := uint16(0); i < 8; i++ {
			n := uint16(0)
			if i == 0 {
				n = 2
			}
			change(0x2aa8+i*2, n)
		}
		researchVFX.changed = true
	})
	e.Oracle.OnCall(oracle.Addr{Seg: v.code, Off: 0x122}, func(o *oracle.Oracle) {
		if researchVFX.changed && !playerFireMenu {
			o.PressKey(oracle.KeyEnter)
			playerFireMenu = true
		}
	})
	e.Oracle.OnCall(oracle.Addr{Seg: v.code, Off: 0x283e}, func(o *oracle.Oracle) {
		if !researchVFX.changed || !playerFireMenu || playerFireTarget {
			return
		}
		playerFireTarget = true
		word := func(off uint16) uint16 { return o.Word(oracle.Addr{Seg: v.data, Off: off}) }
		type route struct {
			node int
			keys []oracle.Key
		}
		pending := []route{{node: int(o.Arg(0))}}
		seen := map[int]bool{int(o.Arg(0)): true}
		for len(pending) > 0 {
			at := pending[0]
			pending = pending[1:]
			if at.node >= 1 && at.node <= 6 {
				id := word(0x6fc0 + uint16(at.node)*2)
				if id < 6 && word(0x5702+id*4) > 0 {
					for _, key := range at.keys {
						o.PressKey(key)
					}
					o.PressKey(oracle.KeyEnter)
					return
				}
			}
			for i, key := range []oracle.Key{oracle.KeyUp, oracle.KeyDown, oracle.KeyLeft, oracle.KeyRight} {
				next := int(o.Byte(oracle.Addr{Seg: v.data, Off: 0x709a + uint16(at.node*4+i)}))
				if next > 0 && next <= 12 && !seen[next] {
					seen[next] = true
					keys := append(append([]oracle.Key{}, at.keys...), key)
					pending = append(pending, route{next, keys})
				}
			}
		}
		panic(fmt.Sprintf("No original target route from %d", o.Arg(0)))
	})
	return nil
}
