//go:build ignore

// Only for a private GUI diagnostic copy. Original menu and navigation consume IRQ1 keys.
package eightsword

import (
	"fmt"
	"github.com/wicanr2/dosgolem/oracle"
	"os"
)

var playerFireMenu, playerFireTarget bool
var playerFireFinished bool
var playerFireExpected uint64
var playerFirePlannedNode = -1
var playerFireMenuCursor = -1

func (e *Engine) ResearchVFXTick() error {
	if os.Getenv("EIGHTSWORD_VFX_FIXTURE") != "1" || researchVFX.armed || e.battleVFX == nil {
		return nil
	}
	researchVFX.armed = true
	v := e.battleVFX
	spell := uint16(0)
	if os.Getenv("EIGHTSWORD_PLAYER_GUI_SPELL") == "thunder" {
		spell = 1
	}
	if os.Getenv("EIGHTSWORD_PLAYER_GUI_SPELL") == "exorcism" {
		spell = 2
	}
	if os.Getenv("EIGHTSWORD_PLAYER_GUI_SPELL") == "half" {
		spell = 5
	}
	if os.Getenv("EIGHTSWORD_PLAYER_GUI_SPELL") == "quake" {
		spell = 7
	}
	if os.Getenv("EIGHTSWORD_PLAYER_GUI_SPELL") == "clone" {
		spell = 6
	}
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
		if spell == 2 {
			for i := uint16(0); i < 6; i++ {
				id := o.Word(oracle.Addr{Seg: v.data, Off: 0x6fc2 + i*2})
				if id < 6 && o.Word(oracle.Addr{Seg: v.data, Off: 0x5702 + id*4}) > 0 {
					change(0x5700+id*4, 6)
					break
				}
			}
		}
		playerFireExpected = 1
		if spell == 1 {
			playerFireExpected = 0
			for i := uint16(0); i < 6; i++ {
				id := o.Word(oracle.Addr{Seg: v.data, Off: 0x6fc2 + i*2})
				if id < 6 && o.Word(oracle.Addr{Seg: v.data, Off: 0x5702 + id*4}) > 0 {
					playerFireExpected++
				}
			}
		}
		for i := uint16(0); i < 8; i++ {
			n := uint16(0)
			if i == spell {
				n = 2
			}
			change(0x2aa8+i*2, n)
		}
		researchVFX.changed = true
	})
	e.Oracle.OnCall(oracle.Addr{Seg: v.code, Off: 0x122}, func(o *oracle.Oracle) {
		if researchVFX.changed && !playerFireMenu {
			for i := uint16(0); i < spell && spell < 3; i++ {
				o.PressKey(oracle.KeyDown)
			}
			if spell < 3 {
				o.PressKey(oracle.KeyEnter)
			}
			playerFireMenu = true
		}
	})
	e.Oracle.OnCall(oracle.Addr{Seg: v.code, Off: 0x2b4}, func(o *oracle.Oracle) {
		if spell < 3 || !researchVFX.changed || !playerFireMenu {
			return
		}
		r := o.Regs()
		cursor := int(o.Word(oracle.Addr{Seg: r.SS, Off: r.BP - 6}))
		if cursor != playerFireMenuCursor {
			if cursor == int(spell) {
				o.PressKey(oracle.KeyEnter)
			} else {
				o.PressKey(oracle.KeyDown)
			}
			playerFireMenuCursor = cursor
		}
	})
	e.Oracle.OnCall(oracle.Addr{Seg: v.code, Off: 0x334}, func(o *oracle.Oracle) {
		if !researchVFX.changed {
			return
		}
		r := o.Regs()
		retIP := o.Word(oracle.Addr{Seg: r.SS, Off: r.SP})
		retCS := o.Word(oracle.Addr{Seg: r.SS, Off: r.SP + 2})
		ss, sp := r.SS, r.SP+4
		o.OnCall(oracle.Addr{Seg: retCS, Off: retIP}, func(o *oracle.Oracle) {
			r := o.Regs()
			if r.SS == ss && r.SP == sp {
				playerFireFinished = true
			}
		})
	})
	planTarget := func(o *oracle.Oracle) {
		if !researchVFX.changed || !playerFireMenu || (playerFireTarget && spell < 2) {
			return
		}
		playerFireTarget = true
		word := func(off uint16) uint16 { return o.Word(oracle.Addr{Seg: v.data, Off: off}) }
		type route struct {
			node int
			keys []oracle.Key
		}
		node := int(o.Arg(0))
		if spell >= 2 {
			r := o.Regs()
			node = int(o.Word(oracle.Addr{Seg: r.SS, Off: r.BP - 10}))
		}
		pending := []route{{node: node}}
		seen := map[int]bool{node: true}
		for len(pending) > 0 {
			at := pending[0]
			pending = pending[1:]
			if spell == 6 && at.node >= 7 && at.node <= 12 {
				id := word(0x6fa8 + uint16(at.node)*2)
				if id < 6 && word(0x56ea+id*4) > 0 {
					for _, key := range at.keys {
						o.PressKey(key)
						return
					}
					o.PressKey(oracle.KeyEnter)
					return
				}
			}
			if spell != 6 && at.node >= 1 && at.node <= 6 {
				id := word(0x6fc0 + uint16(at.node)*2)
				kind := word(0x5700 + id*4)
				if id < 6 && word(0x5702+id*4) > 0 && (spell != 2 || (kind >= 6 && kind <= 15)) {
					for _, key := range at.keys {
						o.PressKey(key)
						if spell >= 2 {
							return
						}
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
		panic(fmt.Sprintf("No original target route from %d", node))
	}
	e.Oracle.OnCall(oracle.Addr{Seg: v.code, Off: 0x283e}, func(o *oracle.Oracle) {
		if spell < 2 {
			planTarget(o)
		}
	})
	e.Oracle.OnCall(oracle.Addr{Seg: v.code, Off: 0x29f2}, func(o *oracle.Oracle) {
		if spell < 2 || !researchVFX.changed || !playerFireMenu {
			return
		}
		r := o.Regs()
		node := int(o.Word(oracle.Addr{Seg: r.SS, Off: r.BP - 10}))
		if node != playerFirePlannedNode {
			playerFirePlannedNode = node
			planTarget(o)
		}
	})
	return nil
}
