//go:build ignore

package main

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"testing"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

func TestAnnihilationRoam(t *testing.T) {
	q := os.Getenv("EIGHTSWORD_ROAM_WORK")
	if q == "" || os.Getuid() != 1000 {
		t.Fatal("fixed Docker work required")
	}
	must := func(e error) {
		t.Helper()
		if e != nil {
			t.Fatal(e)
		}
	}
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	var w OwnedWorld
	for _, v := range []struct {
		Name string
		Dst  any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}, {"world-normal.json", &w}} {
		raw, e := os.ReadFile(filepath.Join(q, "inputs", v.Name))
		must(e)
		must(pairStrictJSON(raw, v.Dst))
	}
	if os.Getenv("EIGHTSWORD_ROAM_COLD") != "" {
		dir := filepath.Join(q, "session-loss-r1")
		store, before, e := openProgressPair(dir, c, cc)
		must(e)
		pam, e := os.ReadFile("/game/PAM.AY")
		must(e)
		code, e := worldArmyCode(pam)
		must(e)
		o, e := oracle.LoadWith("/game/PAM.AY", "/game", oracle.Options{Adlib: true})
		must(e)
		defer o.Close()
		b := &controlledBattle{Store: store, Code: code}
		_, e = loadResumeInto(o, store, before, b)
		must(e)
		seed := originalSeed(o)
		location := checkpointLocation(o)
		store.Fault = func(p string) error {
			if p == "intent-durable" {
				return errors.New("controlled roam interruption")
			}
			return nil
		}
		if e = settleRuntimeRoam(b, o); e == nil {
			t.Fatal("interruption missing")
		}
		store.Close()
		store, cold, e := openProgressPair(dir, c, cc)
		must(e)
		defer store.Close()
		expected, e := before.World.resolveEncounter(c, cc, EncounterContext{Kind: "random"}, DefeatInput{Reason: "annihilation", Choice: "roam"})
		must(e)
		if worldDigest(cold.World) != worldDigest(expected.After) {
			t.Fatal("partial settlement")
		}
		b = &controlledBattle{Store: store, Code: code}
		ref, e := loadResumeInto(o, store, cold, b)
		must(e)
		if !b.Settled || b.Result != 2 || ref.Phase != "return" || ref.Seed != seed || originalSeed(o) != seed {
			t.Fatal("cold return lost choice/seed")
		}
		if e = settleRuntimeRoam(b, o); e == nil {
			t.Fatal("duplicate settlement admitted")
		}
		after, e := store.Recover()
		must(e)
		if after.Token != cold.Token {
			t.Fatal("duplicate changed token")
		}
		out := map[string]any{"status": "passed-roam-interrupted-cold-return", "before": before, "after": cold, "resume": ref, "seed": seed, "location": location, "fault": "intent-durable", "duplicate_refused": true, "native_unchanged": nativeSHA(before.Bytes.Native) == nativeSHA(cold.Bytes.Native)}
		raw, e := json.MarshalIndent(out, "", "  ")
		must(e)
		must(os.WriteFile(filepath.Join(q, "cold-model-r1.json"), append(raw, '\n'), 0600))
		return
	}
	w.Army.Gold = 500
	w.Army.Leadership = 1000
	w.Army.Slots = [6]ArmyStack{{"openkb:wolf", 5}}
	base, e := os.ReadFile(filepath.Join(q, "inputs/original-save.ay"))
	must(e)
	initial := cloneCampWorld(w)
	w.Encounters = map[string]WorldEncounter{"random:roam-check": {Enemy: [6]ArmyStack{{"native:06", 200}}}}
	battle, e := w.begin(c, cc, "random:roam-check", game.OwnedCombatConfig{Rules: w.Army.Rules, Divisors: [2]uint32{5, 5}, Multipliers: [2]uint32{1, 1}})
	must(e)
	state, ev, e := battle.Battle.State.Apply(cc, game.OwnedCombatAction{Side: 1, Source: 0, Target: 0, Kind: "normal"})
	must(e)
	loss := cloneCampWorld(battle)
	loss.Battle.State = state
	if loss.Battle.State.Result != "loss" || ev.Loss != 5 {
		t.Fatal("fixture did not lose through core")
	}
	settled, e := loss.resolveEncounter(c, cc, EncounterContext{Kind: "random"}, DefeatInput{Reason: "annihilation", Choice: "roam"})
	must(e)
	r := &nativeResumeRef{Phase: "battle", Seed: 0x12345678}
	next, e := resumeAfterSettlement(loss, settled.After, r, c, cc)
	must(e)
	if next.Phase != "return" || next.Result != 2 || next.Seed != r.Seed || settled.After.Army.Gold != w.Army.Gold || settled.After.Progress != w.Progress {
		t.Fatal("roam result")
	}
	if _, e = battle.resolveEncounter(c, cc, EncounterContext{Kind: "random"}, DefeatInput{Reason: "annihilation", Choice: "roam"}); e == nil {
		t.Fatal("living army admitted")
	}
	bad := cloneCampWorld(settled.After)
	bad.Army.Gold++
	if _, e = resumeAfterSettlement(loss, bad, r, c, cc); e == nil {
		t.Fatal("mismatched world admitted")
	}
	if _, e = loss.resolveEncounter(c, cc, EncounterContext{Kind: "random"}, DefeatInput{Reason: "annihilation"}); e == nil {
		t.Fatal("implicit choice admitted")
	}
	must(initializeProgressPair(filepath.Join(q, "session-gui-r1"), base, c, cc, initial))
	out := map[string]any{"status": "passed-roam-core-and-resume", "initial": initial, "battle": battle, "loss": loss, "event": ev, "after": settled.After, "resume": next, "living_refused": true, "mismatch_refused": true, "implicit_choice_refused": true, "controlled_initial_army": true}
	raw, e := json.MarshalIndent(out, "", "  ")
	must(e)
	must(os.WriteFile(filepath.Join(q, "model-r1.json"), append(raw, '\n'), 0600))
}
