package ownedworld

import (
	"bytes"
	"errors"
	"fmt"
	"image"
	"image/draw"
	"math"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

var errOriginalBattleSetupHeld = errors.New("original battle setup preview held before all actions")

type originalSetupPlan struct {
	Rows     [2][6]ArmyStack `json:"rows"`
	Slots    [2][6]uint16    `json:"slots"`
	Occupied [2][6]byte      `json:"occupied"`
	HP       [2][6]uint64    `json:"hp"`
	NativeHP [2][6]uint16    `json:"native_hp"`
	Extended bool            `json:"extended"`
}

func planOriginalBattleSetup(catalog game.OwnedCombatCatalog, rows [2][6]ArmyStack) (originalSetupPlan, error) {
	x := originalSetupPlan{Rows: rows}
	if err := catalog.Validate(); err != nil {
		return x, err
	}
	for side := range rows {
		lastEmpty := uint16(255)
		assigned := [6]bool{}
		seen := map[string]bool{}
		for i := range x.Slots[side] {
			x.Slots[side][i] = 255
		}
		place := func(raw int, back bool) {
			for j := 0; j < 6; j++ {
				slot := j
				if back {
					slot = 5 - j
				}
				if x.Occupied[side][slot] == 0 {
					x.Occupied[side][slot] = 1
					x.Slots[side][slot] = uint16(raw)
					assigned[raw] = true
					return
				}
			}
		}
		for i, s := range rows[side] {
			if s.Unit == "" && s.Count == 0 {
				lastEmpty = uint16(i)
				continue
			}
			p, ok := catalog.Profiles[s.Unit]
			if !ok || s.Count == 0 || seen[s.Unit] || p.HP > math.MaxUint64/uint64(s.Count) {
				return originalSetupPlan{}, errors.New("setup identity/count/HP bounds")
			}
			seen[s.Unit] = true
			x.HP[side][i] = p.HP * uint64(s.Count)
			if p.NativeKind != 0 {
				if s.Unit != fmt.Sprintf("native:%02d", p.NativeKind) || p.NativeKind > 25 {
					return originalSetupPlan{}, errors.New("setup native identity")
				}
				x.NativeHP[side][i] = uint16(x.HP[side][i])
				if p.NativeKind == 10 || p.NativeKind == 12 {
					place(i, true)
				}
			} else {
				if !originalOpenKBID(s.Unit) {
					return originalSetupPlan{}, errors.New("setup extension identity")
				}
				x.Extended = true
			}
		}
		for i, s := range rows[side] {
			if s.Unit != "" && !assigned[i] {
				p := catalog.Profiles[s.Unit]
				place(i, p.Ranged)
			}
		}
		for i := range x.Slots[side] {
			if x.Slots[side][i] == 255 {
				x.Slots[side][i] = lastEmpty
			}
		}
	}
	return x, nil
}

type originalBattleSetup struct {
	Code                    []byte
	Catalog                 game.OwnedCombatCatalog
	Override                *[6]ArmyStack
	Plan                    originalSetupPlan
	Phase                   string
	FormationCalls, HPCalls uint64
	Actions                 *originalBattleActions
}

func (x *originalBattleSetup) rows(m *dg.Machine) ([2][6]ArmyStack, error) {
	var rows [2][6]ArmyStack
	for side, base := range []uint32{0x56e8, 0x5700} {
		for i := 0; i < 6; i++ {
			k, n := m.Read16(0x1e880+base+uint32(i*4)), m.Read16(0x1e880+base+uint32(i*4+2))
			if side == 0 && x.Override != nil {
				s := x.Override[i]
				p, ok := x.Catalog.Profiles[s.Unit]
				if s.Unit == "" && s.Count == 0 {
					if k != 0 || n != 0 {
						return rows, errors.New("setup empty shadow mismatch")
					}
				} else if !ok {
					return rows, errors.New("setup override profile")
				} else if p.NativeKind == 0 {
					if k != 0 || n != 0 {
						return rows, errors.New("extension entered original table")
					}
				} else if k != p.NativeKind || uint32(n) != s.Count {
					return rows, errors.New("setup native projection mismatch")
				}
				rows[side][i] = s
				continue
			}
			if k == 0 && n == 0 {
				continue
			}
			if k < 1 || k > 25 || n == 0 {
				return rows, errors.New("setup original rows")
			}
			rows[side][i] = ArmyStack{fmt.Sprintf("native:%02d", k), uint32(n)}
		}
	}
	return rows, nil
}

func (x *originalBattleSetup) execute(m *dg.Machine, ip uint16) (bool, error) {
	fail := func(s string) (bool, error) { return false, &worldArmyPortFault{"original setup: " + s} }
	c := m.CPU
	if c.IP != ip || c.Seg[dg.CS] != 0xf67 || c.Seg[dg.DS] != 0x1e88 || c.Seg[dg.SS] != 0x1e88 || c.R[dg.SP] > 65531 || c.Cycles == math.MaxUint64 || len(x.Code) < 0x1055e {
		return fail("site/segments/source shape")
	}
	start, end, ret := uint16(0x1daa), uint16(0x1fee), uint16(0x1b)
	if ip == 0x14ba {
		start, end, ret = 0x14ba, 0x1532, 0x35
	} else if ip != 0x1daa {
		return fail("unknown helper")
	}
	if !bytes.Equal(x.Code[0xe570+int(start):0xe570+int(end)], m.Mem[0xf670+int(start):0xf670+int(end)]) || m.Read16(0x1e880+uint32(c.R[dg.SP])) != ret || m.Read16(0x1e880+uint32(c.R[dg.SP])+2) != 0xf67 {
		return fail("source/caller")
	}
	rows, err := x.rows(m)
	if err != nil {
		return fail(err.Error())
	}
	plan, err := planOriginalBattleSetup(x.Catalog, rows)
	if err != nil {
		return fail(err.Error())
	}
	for _, side := range rows {
		for _, s := range side {
			if s.Unit != "" {
				p := x.Catalog.Profiles[s.Unit]
				if p.NativeKind != 0 && uint64(m.Read16(0x1e880+0x70d0+uint32(p.NativeKind)*4)) != p.HP {
					return fail("native HP catalog binding")
				}
			}
		}
	}
	if ip == 0x1daa {
		if x.Phase != "" {
			return fail("formation phase")
		}
		for side, base := range []uint32{0x6fb6, 0x6fc2} {
			for i, n := range plan.Slots[side] {
				m.Write16(0x1e880+base+uint32(i*2), n)
			}
		}
		for side, base := range []uint32{0x8cb4, 0x8e6e} {
			copy(m.Mem[0x1e880+base:0x1e880+base+6], plan.Occupied[side][:])
		}
		x.Plan = plan
		x.Phase = "formation"
		x.FormationCalls++
	} else {
		if x.Phase != "formation" || x.Plan != plan {
			return fail("HP phase/rows changed")
		}
		for side, base := range []uint32{0x8ca4, 0x8e60} {
			for i, n := range plan.NativeHP[side] {
				m.Write16(0x1e880+base+uint32(i*2), n)
			}
		}
		x.Phase = "ready"
		x.HPCalls++
	}
	c.R[dg.SP] += 4
	c.IP = ret
	c.Cycles++
	return true, nil
}

func installOriginalBattleSetup(e *game.Engine, catalog game.OwnedCombatCatalog, preview *[6]ArmyStack) (*originalBattleSetup, error) {
	if !e.PAMLoaded || e.BattleRulesMode() != "native" {
		return nil, errors.New("setup requires loaded PAM/native rules")
	}
	if err := catalog.Validate(); err != nil {
		return nil, err
	}
	code, err := worldArmyCode(e.PAM)
	if err != nil {
		return nil, err
	}
	x := &originalBattleSetup{Code: code, Catalog: catalog, Override: preview}
	for _, ip := range []uint16{0x1daa, 0x14ba} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return x.execute(m, ip) })
		swordOnCall(e.Oracle, oracle.Far(0xf67, ip+1), func(*oracle.Oracle) { panic(&worldArmyPortFault{"original setup escaped host helper"}) })
	}
	if preview != nil {
		// An expanded setup is never allowed to fall through to native actions.
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x35), func(m *dg.Machine) (bool, error) {
			if x.Phase != "ready" {
				return false, &worldArmyPortFault{"setup preview phase"}
			}
			if x.Actions != nil {
				return x.Actions.begin(m)
			}
			return false, errOriginalBattleSetupHeld
		})
	}
	return x, nil
}

func composeOriginalBattleSetup(e *game.Engine, x *originalBattleSetup, art *hdUnitArtwork) (*image.RGBA, error) {
	if !e.HD || x.Override == nil || x.Phase != "ready" || art == nil {
		return nil, errors.New("setup composition requires held HD preview")
	}
	base := e.Frame()
	out := image.NewRGBA(base.Bounds())
	draw.Draw(out, out.Bounds(), base, base.Bounds().Min, draw.Src)
	f := &originalArmyFields{Art: art, Boxes: map[string]image.Rectangle{}}
	for slot, raw := range x.Plan.Slots[0] {
		if raw >= 6 {
			continue
		}
		s := x.Plan.Rows[0][raw]
		p, ok := x.Catalog.Profiles[s.Unit]
		if !ok || p.NativeKind != 0 || s.Count == 0 {
			continue
		}
		im := art.Images[s.Unit]
		if im == nil {
			return nil, errors.New("setup missing extended image")
		}
		box := image.Rectangle{}
		for y := 0; y < im.Rect.Dy(); y++ {
			for xx := 0; xx < im.Rect.Dx(); xx++ {
				if im.RGBAAt(xx, y).A != 0 {
					box = box.Union(image.Rect(xx, y, xx+1, y+1))
				}
			}
		}
		if box.Empty() {
			return nil, errors.New("setup empty silhouette")
		}
		f.Boxes[s.Unit] = box
		coords := e.Oracle.Bytes(oracle.Far(0x1e88, uint16(0x703c+slot*2)), 2)
		left, top := int(coords[0])*24, int(coords[1])*6
		area := image.Rect(left, top, left+264, top+300)
		if !area.In(out.Bounds()) {
			return nil, errors.New("setup sprite area bounds")
		}
		f.icon(out, s.Unit, area)
	}
	return out, nil
}
