//go:build ignore

package main

import (
	"encoding/json"
	"fmt"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"os"
	"path/filepath"
	"testing"
)

func rearRead(t *testing.T, name string, v any) {
	t.Helper()
	b, e := os.ReadFile(filepath.Join(os.Getenv("EIGHTSWORD_REAR_INPUT"), name))
	if e != nil {
		t.Fatal(e)
	}
	if e = pairStrictJSON(b, v); e != nil {
		t.Fatal(e)
	}
}
func rearTestSeed(t *testing.T) (ArmyCatalog, game.OwnedCombatCatalog, OwnedWorld) {
	t.Helper()
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	var w OwnedWorld
	rearRead(t, "army-catalog.json", &c)
	rearRead(t, "combat-catalog.json", &cc)
	rearRead(t, "world-normal.json", &w)
	w.Army.Gold = 500
	w.Army.Leadership = 1000
	w.Army.Slots = [6]ArmyStack{{"native:01", 30}, {"openkb:wolf", 5}, {"native:06", 120}, {"native:12", 10}}
	return c, cc, w
}
func rearTestBattle(t *testing.T, c ArmyCatalog, cc game.OwnedCombatCatalog, w OwnedWorld, enemy [6]ArmyStack) (*battleUI, *int) {
	t.Helper()
	w.Encounters = map[string]WorldEncounter{"random:rear-check": {Enemy: enemy}}
	n, e := w.begin(c, cc, "random:rear-check", game.OwnedCombatConfig{Rules: w.Army.Rules, Divisors: [2]uint32{5, 5}, Multipliers: [2]uint32{1, 1}})
	if e != nil {
		t.Fatal(e)
	}
	calls := new(int)
	u := &battleUI{Catalog: c, Combat: cc, World: n, Locked: true, Source: 3}
	u.CommitPair = func(next OwnedWorld) (string, string, error) {
		if e := next.validate(c, cc); e != nil {
			return "", "", e
		}
		*calls++
		return "native-kept", worldDigest(next), nil
	}
	return u, calls
}
func TestRearActions(t *testing.T) {
	if os.Getuid() != 1000 || os.Getenv("EIGHTSWORD_REAR_INPUT") == "" {
		t.Fatal("controlled Docker inputs required")
	}
	c, cc, seed := rearTestSeed(t)
	rows := []map[string]any{}
	for _, tc := range []struct {
		Name                   string
		Kind, Selector, Target int
		Enemy                  [6]ArmyStack
		Loss                   uint32
	}{
		{"fixed", 12, 0, 0, [6]ArmyStack{{"native:01", 20}}, 2},
		{"counter", 12, 2, 0, [6]ArmyStack{{"native:06", 20}}, 6},
		{"proportion", 12, 5, 1, [6]ArmyStack{{"native:01", 20}, {"native:06", 30}}, 11},
		{"taoist", 10, 0, 0, [6]ArmyStack{{"native:01", 20}}, 5},
	} {
		t.Run(tc.Name, func(t *testing.T) {
			w := cloneCampWorld(seed)
			w.Army.Slots[3].Unit = fmt.Sprintf("native:%02d", tc.Kind)
			u, calls := rearTestBattle(t, c, cc, w, tc.Enemy)
			u.Target = tc.Target
			before := cloneCampWorld(u.World)
			if e := u.action(fmt.Sprintf("rear:%d", tc.Selector)); e != nil {
				t.Fatal(e)
			}
			s := u.World.Battle.State
			ev := u.Events[0]
			if ev.Loss != tc.Loss || !s.Acted[0][3] || *calls != 1 || s.Rows[1][tc.Target].Count != before.Battle.State.Rows[1][tc.Target].Count-tc.Loss {
				t.Fatal("rear action result")
			}
			rows = append(rows, map[string]any{"name": tc.Name, "before": before, "after": u.World, "event": ev, "persist_calls": *calls})
			if e := u.action(fmt.Sprintf("rear:%d", tc.Selector)); e == nil || *calls != 1 {
				t.Fatal("repeat action admitted")
			}
		})
	}
	for _, tc := range []struct {
		Name             string
		Source, Selector int
	}{{"front-refused", 0, 0}, {"wrong-target-refused", 3, 2}, {"closed-zero-gate-refused", 3, 5}} {
		t.Run(tc.Name, func(t *testing.T) {
			u, calls := rearTestBattle(t, c, cc, seed, [6]ArmyStack{{"native:01", 20}})
			u.Source = tc.Source
			before := cloneCampWorld(u.World)
			if e := u.action(fmt.Sprintf("rear:%d", tc.Selector)); e == nil || *calls != 0 || worldDigest(u.World) != worldDigest(before) {
				t.Fatal("refusal changed state")
			}
			rows = append(rows, map[string]any{"name": tc.Name, "before": before, "after": u.World, "persist_calls": *calls, "rejected": true})
		})
	}
	t.Run("enemy-rear", func(t *testing.T) {
		u, calls := rearTestBattle(t, c, cc, seed, [6]ArmyStack{{}, {}, {}, {"native:12", 10}})
		before := cloneCampWorld(u.World)
		if e := u.action("enemy"); e != nil {
			t.Fatal(e)
		}
		ev := u.Events[0]
		if ev.Action.Kind != "special" || ev.Action.Selector != 0 || ev.Action.Source != 3 || ev.Action.Target != 1 || ev.Loss != 2 || *calls != 1 {
			t.Fatal("enemy rear route")
		}
		rows = append(rows, map[string]any{"name": "enemy-rear", "before": before, "after": u.World, "event": ev, "persist_calls": *calls})
	})
	t.Run("rear-pass-round", func(t *testing.T) {
		w := cloneCampWorld(seed)
		w.Army.Slots = [6]ArmyStack{{"native:01", 30}}
		u, calls := rearTestBattle(t, c, cc, w, [6]ArmyStack{{}, {}, {}, {}, {}, {"native:02", 5}})
		u.World.Battle.State.Acted[0][0] = true
		before := cloneCampWorld(u.World)
		if e := u.action("enemy"); e != nil {
			t.Fatal(e)
		}
		passed := cloneCampWorld(u.World)
		if !passed.Battle.State.Acted[1][5] || *calls != 1 {
			t.Fatal("rear pass")
		}
		if e := u.action("round"); e != nil {
			t.Fatal(e)
		}
		if u.World.Battle.State.Round != 2 || *calls != 2 {
			t.Fatal("round remains blocked")
		}
		rows = append(rows, map[string]any{"name": "rear-pass-round", "before": before, "passed": passed, "after": u.World, "persist_calls": *calls})
	})
	if t.Failed() {
		return
	}
	if out := os.Getenv("EIGHTSWORD_REAR_OUT"); out != "" {
		if e := os.Mkdir(out, 0700); e != nil {
			t.Fatal(e)
		}
		raw, e := os.ReadFile(filepath.Join(os.Getenv("EIGHTSWORD_REAR_INPUT"), "original-save.ay"))
		if e != nil {
			t.Fatal(e)
		}
		if e = initializeProgressPair(filepath.Join(filepath.Dir(out), "session-gui-r1"), raw, c, cc, seed); e != nil {
			t.Fatal(e)
		}
		b, e := json.MarshalIndent(map[string]any{"status": "passed-rear-actions-ui-helpers", "cases": rows, "normal_player_path": false, "persist_collector_only": true}, "", "  ")
		if e != nil {
			t.Fatal(e)
		}
		if e = os.WriteFile(filepath.Join(out, "receipt.json"), append(b, '\n'), 0600); e != nil {
			t.Fatal(e)
		}
	}
}
