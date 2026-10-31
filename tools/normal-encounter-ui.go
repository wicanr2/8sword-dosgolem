//go:build ignore

// Isolated normal-map encounter adapter. Formal Engine sidecar guard stays enabled.
package main

import (
	"bytes"
	"errors"
	"flag"
	"fmt"
	"image"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

var encounterEvidence = flag.String("encounter-evidence", "", "可選遇敵狀態輸出目錄")
var encounterCurrent *encounterExtra

type encounterExtra struct {
	Previous                             armyScreenExtra
	Presence                             *armyPresence
	Port                                 *worldArmyPort
	Engine                               *game.Engine
	Bridge                               *controlledBattle
	UI                                   *battleUI
	Confirmed, Opened, Finished          bool
	Sequence                             uint64
	EntrySteps, EntryCycles, HeldUpdates uint64
	ReturnSteps                          uint64
	NativeRows                           []byte
	Events                               []map[string]any
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
		e = settleRuntimeRetreat(x.Bridge, x.Engine.Oracle)
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
	runtimeEnemyState(v)
	refusalState(v)
	v["controlled_memory"], v["normal_player_path"] = false, true
	v["encounter_sequence"] = x.Sequence
	v["encounter_injected"], v["encounter_confirmed"] = false, x.Confirmed
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
		if e := pursuitOpening(x); e != nil {
			return e
		}
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
		if *refusalSeedSet {
			return nil, errors.New("normal entry forbids test seed")
		}
		code, err := worldArmyCode(e.PAM)
		if err != nil {
			return nil, err
		}
		x := &encounterExtra{Previous: old, Presence: wrapper.Presence, Port: p, Engine: e}
		runtimeEnemyCurrent = installRuntimeEnemyBattle(e.Oracle, p.Store, p.Current, code)
		x.Bridge = runtimeEnemyCurrent.controlledBattle
		encounterCurrent = x
		o := e.Oracle
		// Reuse the existing host gates and their pointer identity. No callback
		// is registered inside a per-encounter callback.
		o.OnCall(oracle.Far(0x110, 0x1650), func(o *oracle.Oracle) {
			if x.Presence.Active {
				panic(&worldArmyPortFault{"unfinished presence context"})
			}
			if x.Opened && (!x.Finished || !x.Bridge.Returned) {
				panic(&worldArmyPortFault{"unfinished Go encounter"})
			}
			s, err := p.snapshot()
			if err != nil {
				panic(&worldArmyPortFault{err.Error()})
			}
			regs := o.Regs()
			if regs.CS != 0x110 || regs.DS != 0x1e88 || regs.SS != 0x1e88 || regs.BP < 32 || regs.BP > 65520 || regs.SP > regs.BP || o.Word(oracle.Far(regs.SS, regs.BP+2)) != 0xbd3 || o.Word(oracle.Far(regs.SS, regs.BP+4)) != 0x110 || !bytes.Equal(code[0x151c:0x1796], o.Bytes(oracle.Far(0x110, 0x151c), 0x27a)) {
				panic(&worldArmyPortFault{"normal encounter source/frame"})
			}
			for i, n := range pairWorldResources(s.World).words() {
				if uint64(o.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
					panic(&worldArmyPortFault{"normal encounter resources"})
				}
			}
			b := x.Bridge
			*b = controlledBattle{Store: p.Store, Current: s, Code: code}
			*runtimeEnemyCurrent = runtimeEnemyBattle{controlledBattle: b}
			if g := currentRefusal; g != nil {
				g.Applied = false
				g.Pursued = false
				g.Plan = originalRandPlan{}
				g.BP = 0
				g.SP = 0
			}
			refusalReturned = false
			lastRetreatRand = nil
			x.Confirmed = false
			x.Opened = false
			x.Finished = false
			x.UI = nil
			x.EntrySteps = 0
			x.EntryCycles = 0
			x.ReturnSteps = 0
			x.HeldUpdates = 0
			x.Sequence++
			x.NativeRows = append([]byte(nil), o.Bytes(oracle.Far(0x1e88, 0x54a), 24)...)
			x.Events = append(x.Events, map[string]any{"command": "natural-encounter", "sequence": x.Sequence, "token": s.Token, "ip": regs.IP})
		})
		o.OnCall(oracle.Far(0x110, 0x1713), func(o *oracle.Oracle) {
			r := o.Regs()
			a := x.Presence
			if x.Sequence == 0 || x.Confirmed || !a.Active || !a.Prompt || r.AX != 1 || r.BP != a.BP || r.SP != a.SP {
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
			if err := saveEncounterState(o, fmt.Sprintf("encounter-%03d-return.state", x.Sequence)); err != nil {
				panic(&worldArmyPortFault{err.Error()})
			}
			x.Events = append(x.Events, map[string]any{"command": "return", "ip": o.Regs().IP, "world": s.World})
		})
		installRefusalUI(x)
		return x, nil
	}
	armyReviewTitle = "神州八劍・軍隊試作・正常遇敵"
}

// Evidence output is optional. A normal player session never requires a snapshot.
func saveEncounterState(o *oracle.Oracle, name string) error {
	if *encounterEvidence == "" {
		return nil
	}
	return o.SaveStateFile(*encounterEvidence + "/" + name)
}
