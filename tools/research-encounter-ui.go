//go:build ignore

// DRAFT controlled confirmation -> Go UI -> original caller integration.
package main

import (
	"bytes"
	"errors"
	"flag"
	"fmt"
	"image"
	"path/filepath"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

var encounterState = flag.String("controlled-state", "", "明示固定3733快照，僅受控驗證")
var encounterFixture = flag.String("controlled-case", "win", "win或retreat固定案例")
var encounterEvidence = flag.String("controlled-evidence", "", "完整受控狀態輸出目錄")
var encounterCurrent *encounterExtra

type encounterExtra struct {
	Previous                              armyScreenExtra
	Presence                              *armyPresence
	Port                                  *worldArmyPort
	Engine                                *game.Engine
	Bridge                                *controlledBattle
	UI                                    *battleUI
	Injected, Confirmed, Opened, Finished bool
	EntrySteps, EntryCycles, HeldUpdates  uint64
	ReturnSteps                           uint64
	NativeRows                            []byte
	Events                                []map[string]any
}

func (x *encounterExtra) IsActive() bool {
	return x.Opened && !x.Finished || x.Previous != nil && x.Previous.IsActive()
}
func (x *encounterExtra) active() bool { return x.Opened && !x.Finished }
func (x *encounterExtra) NoteKey(k byte, d bool) {
	if x.active() {
		if d && k == 1 {
			x.command("retreat")
		}
		return
	}
	if x.Previous != nil {
		x.Previous.NoteKey(k, d)
	}
}
func (x *encounterExtra) Click(a, b int) (byte, error) {
	if !x.active() {
		if x.Previous != nil {
			return x.Previous.Click(a, b)
		}
		return 0, nil
	}
	s := battleHit(x.UI, a, b)
	var side, slot int
	if _, e := fmt.Sscanf(s, "card:%d:%d", &side, &slot); e == nil {
		if side == 0 {
			x.UI.Source = slot
		} else {
			x.UI.Target = slot
		}
		return 0, nil
	}
	if image.Pt(a, b).In(image.Rect(60, 190, 650, 260)) {
		s = "retreat"
	}
	if s != "" {
		x.command(s)
	}
	return 0, nil
}
func (x *encounterExtra) command(s string) {
	if !x.active() {
		return
	}
	var e error
	switch s {
	case "attack", "enemy", "round", "pass":
		e = x.UI.action(s)
	case "settle":
		e = x.Bridge.settle(DefeatInput{})
	case "retreat":
		n := uint32(2730)
		e = x.Bridge.settle(DefeatInput{Reason: "retreat", Random: &n})
	default:
		return
	}
	if e != nil {
		x.UI.Message = e.Error()
		return
	}
	x.Port.Current = x.Bridge.Current
	x.UI.World = x.Bridge.Current.World
	x.Events = append(x.Events, map[string]any{"command": s, "world": x.UI.World, "token": x.Bridge.Current.Token})
	if x.Bridge.Settled {
		x.UI.Message = "戰果已儲存，返回地圖。"
	}
}
func (x *encounterExtra) Paint(f *armyUIFonts, id string) (*image.RGBA, []armyUIText) {
	if !x.active() {
		return x.Previous.Paint(f, id)
	}
	x.UI.Font = id
	out, texts := paintBattleUI(x.UI, f)
	// Replace the standalone prototype's recruit/begin controls. Hit testing is
	// likewise replaced; neither action can reach the world adapter.
	uiFill(out, image.Rect(50, 180, 665, 264), out.RGBAAt(5, 5))
	kept := texts[:0]
	for _, t := range texts {
		if t.Role != "recruit" && t.Role != "begin" {
			kept = append(kept, t)
		}
	}
	p := armyUIPaint{Fonts: f, Canvas: out, Font: id}
	p.button("retreat", "撤退返回地圖", image.Rect(60, 190, 650, 260), false, x.UI.World.Battle != nil && x.UI.World.Battle.State.Result == "")
	return out, append(kept, p.Texts...)
}
func (x *encounterExtra) State() map[string]any {
	v := map[string]any{}
	if x.Previous != nil {
		v = x.Previous.State()
	}
	v["controlled_memory"], v["normal_player_path"] = true, false
	v["encounter_injected"], v["encounter_confirmed"] = x.Injected, x.Confirmed
	v["battle_opened"], v["battle_finished"] = x.Opened, x.Finished
	v["battle_native_calls"], v["battle_events"] = x.Bridge.NativeCalls, x.Events
	v["battle_entry_steps"], v["battle_entry_cycles"], v["battle_held_updates"] = x.EntrySteps, x.EntryCycles, x.HeldUpdates
	v["battle_return_steps"] = x.ReturnSteps
	v["battle_guest_steps"], v["battle_guest_cycles"] = x.Engine.Oracle.Steps(), x.Engine.Oracle.Cycles()
	if x.UI != nil {
		v["battle_source"], v["battle_target"], v["battle_message"] = x.UI.Source, x.UI.Target, x.UI.Message
		v["combat_events"] = x.UI.Events
	}
	return v
}

func encounterGuestKey(g *armyReviewApp, k byte, d bool) error {
	if encounterCurrent != nil && encounterCurrent.active() {
		return nil
	}
	return g.Engine.Key(k, d)
}
func advanceEncounterUI(g *armyReviewApp) error {
	x := encounterCurrent
	if x != nil && x.active() && !x.Bridge.Settled {
		if g.Engine.Oracle.Steps() != x.EntrySteps || g.Engine.Oracle.Cycles() != x.EntryCycles {
			return errors.New("paused battle CPU changed")
		}
		x.HeldUpdates++
		return nil
	}
	e := g.Engine.AdvanceCycles(100000)
	if errors.Is(e, errControlledBattleYield) {
		if x == nil || !x.Confirmed || x.Opened {
			return errors.New("unexpected UI battle yield")
		}
		x.Opened = true
		x.Port.Current = x.Bridge.Current
		x.EntrySteps = g.Engine.Oracle.Steps()
		x.EntryCycles = g.Engine.Oracle.Cycles()
		x.UI = &battleUI{Catalog: x.Port.Store.Catalog, Combat: x.Port.Store.Combat, World: x.Bridge.Current.World, Locked: true, Dirty: true, Message: "點選部隊與指令，每個有效動作自動儲存。"}
		x.UI.CommitPair = func(w OwnedWorld) (string, string, error) {
			if e := x.Bridge.commit(w); e != nil {
				return "", "", e
			}
			x.Port.Current = x.Bridge.Current
			return x.Bridge.Current.NativeSHA, x.Bridge.Current.WorldSHA, nil
		}
		g.Engine.ReleaseAll()
		return nil
	}
	return e
}

func init() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		old, err := previous(e, p)
		if err != nil {
			return nil, err
		}
		wrapper, ok := old.(*presenceExtra)
		if !ok {
			return nil, errors.New("presence integration missing")
		}
		if *encounterState == "" || *encounterEvidence == "" || (*encounterFixture != "win" && *encounterFixture != "retreat") {
			return nil, errors.New("explicit controlled fixture required")
		}
		raw, err := armyUIRead(*encounterState, 64<<20)
		if err != nil {
			return nil, err
		}
		if contentSHA(raw) != "d3fdfd4f739d0256f6a29ed5a55a9506dfb753964bf4af7388b20827e17605df" {
			return nil, errors.New("fixed state hash")
		}
		code, err := worldArmyCode(e.PAM)
		if err != nil {
			return nil, err
		}
		x := &encounterExtra{Previous: old, Presence: wrapper.Presence, Port: p, Engine: e}
		x.Bridge = installControlledBattle(e.Oracle, p.Store, p.Current, code)
		encounterCurrent = x
		o := e.Oracle
		if err = o.LoadStateFile(*encounterState); err != nil {
			return nil, err
		}
		o.OnHostInstruction(oracle.Far(0x110, 0x3733), func(m *dg.Machine) (bool, error) {
			c := m.CPU
			ds := uint32(0x1e880)
			bp := c.R[dg.BP]
			if x.Injected || c.Seg[dg.CS] != 0x110 || c.Seg[dg.DS] != 0x1e88 || c.Seg[dg.SS] != 0x1e88 || bp < 32 || m.Read16(ds+uint32(bp)+2) != 0x171d || m.Read16(ds+uint32(bp)+4) != 0x110 {
				return false, errors.New("confirmation source frame")
			}
			if err := o.SaveStateFile(filepath.Join(*encounterEvidence, "before-commit.state")); err != nil {
				return false, err
			}
			c.R[dg.SI] = m.Read16(ds + uint32(bp) - 0x12)
			c.R[dg.DI] = m.Read16(ds + uint32(bp) - 0x10)
			c.R[dg.SP] = bp + 6
			c.R[dg.BP] = m.Read16(ds + uint32(bp))
			c.IP = 0x16e0
			for i, n := range pairWorldResources(p.Current.World).words() {
				m.Write16(ds+0x4f2+uint32(i*2), uint16(n))
			}
			for _, r := range [][2]uint32{{ds + 0x54a, 24}, {ds + 0x56e8, 48}} {
				for j := uint32(0); j < r[1]; j++ {
					m.Write8(r[0]+j, 255)
				}
			}
			x.Injected = true
			x.NativeRows = append([]byte(nil), m.Mem[ds+0x54a:ds+0x562]...)
			a := x.Presence
			a.Active = true
			a.HasArmy = true
			a.Prompt = false
			a.BP = c.R[dg.BP]
			a.SP = c.R[dg.SP]
			a.Token = p.Current.Token
			a.NativeRows = append([]byte(nil), x.NativeRows...)
			x.Events = append(x.Events, map[string]any{"command": "injection", "ip": c.IP, "bp": c.R[dg.BP], "sp": c.R[dg.SP], "world": p.Current.World})
			c.Cycles++
			if err := o.SaveStateFile(filepath.Join(*encounterEvidence, "after-commit.state")); err != nil {
				return false, err
			}
			return true, nil
		})
		o.OnCall(oracle.Far(0x110, 0x1713), func(o *oracle.Oracle) {
			r := o.Regs()
			a := x.Presence
			if !x.Injected || x.Confirmed || !a.Active || !a.Prompt || r.AX != 1 || r.BP != a.BP || r.SP != a.SP {
				panic(&worldArmyPortFault{"confirmation binding"})
			}
			x.Confirmed = true
			x.Events = append(x.Events, map[string]any{"command": "confirmation", "ax": r.AX, "ip": r.IP})
		})
		o.OnCall(oracle.Far(0x110, 0x0bd3), func(o *oracle.Oracle) {
			if !x.Opened || !x.Bridge.Returned || x.Finished {
				return
			}
			a := x.Presence
			if !bytes.Equal(x.NativeRows, o.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
				panic(&worldArmyPortFault{"battle changed native army"})
			}
			s, err := p.snapshot()
			if err != nil || s.Token != x.Bridge.Current.Token {
				panic(&worldArmyPortFault{"battle return pair"})
			}
			for i, n := range pairWorldResources(s.World).words() {
				if uint64(o.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
					panic(&worldArmyPortFault{"battle return resources"})
				}
			}
			a.Active = false
			a.Prompt = false
			a.Token = s.Token
			a.Completed++
			x.Finished = true
			x.ReturnSteps = o.Steps()
			if err := o.SaveStateFile(filepath.Join(*encounterEvidence, "final-map.state")); err != nil {
				panic(&worldArmyPortFault{err.Error()})
			}
			x.Events = append(x.Events, map[string]any{"command": "return", "ip": o.Regs().IP, "world": s.World})
		})
		return x, nil
	}
	armyReviewTitle = "神州八劍・軍隊試作・Go戰鬥交接"
}
