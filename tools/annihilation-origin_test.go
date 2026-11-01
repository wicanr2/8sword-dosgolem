//go:build ignore

package main

import (
	"encoding/json"
	"errors"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
	"os"
	"path/filepath"
	"testing"
)

func TestAnnihilationOrigin(t *testing.T) {
	q := os.Getenv("EIGHTSWORD_ORIGIN_WORK")
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
	packed, e := os.ReadFile(filepath.Join(q, "inputs/origin-terrain-packed.ay"))
	must(e)
	if os.Getenv("EIGHTSWORD_ORIGIN_COLD") != "" {
		store, before, e := openProgressPair(filepath.Join(q, "session-loss-r1"), c, cc)
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
		bad := append([]byte(nil), packed...)
		bad[4] ^= 1
		if e = settleRuntimeOrigin(b, o, bad); e == nil {
			t.Fatal("modified terrain admitted")
		}
		unchanged, e := store.Recover()
		must(e)
		if unchanged.Token != before.Token || originalSeed(o) != seed {
			t.Fatal("refused source changed progress")
		}
		store.Fault = func(p string) error {
			if p == "intent-durable" {
				return errors.New("controlled origin interruption")
			}
			return nil
		}
		if e = settleRuntimeOrigin(b, o, packed); e == nil {
			t.Fatal("interruption missing")
		}
		store.Close()
		store, cold, e := openProgressPair(filepath.Join(q, "session-loss-r1"), c, cc)
		must(e)
		defer store.Close()
		expected, e := before.World.resolveEncounter(c, cc, EncounterContext{Kind: "random"}, DefeatInput{Reason: "annihilation", Choice: "return-origin", Origin: &DefeatOrigin{Region: "native:00", X: 40, Y: 40, Facing: 3}})
		must(e)
		if worldDigest(cold.World) != worldDigest(expected.After) {
			t.Fatal("partial origin settlement")
		}
		b = &controlledBattle{Store: store, Code: code}
		ref, e := loadResumeInto(o, store, cold, b)
		must(e)
		if !b.Settled || b.Result != 3 || ref.Phase != "return" || ref.Seed != seed || originalSeed(o) != seed {
			t.Fatal("cold origin choice/seed")
		}
		if e = settleRuntimeOrigin(b, o, packed); e == nil {
			t.Fatal("duplicate origin admitted")
		}
		after, e := store.Recover()
		must(e)
		if after.Token != cold.Token {
			t.Fatal("duplicate changed token")
		}
		out := map[string]any{"status": "passed-origin-interrupted-cold-return", "before": before, "after": cold, "resume": ref, "seed": seed, "fault": "intent-durable", "modified_terrain_refused": true, "duplicate_refused": true, "native_unchanged": nativeSHA(before.Bytes.Native) == nativeSHA(cold.Bytes.Native)}
		raw, e := json.MarshalIndent(out, "", "  ")
		must(e)
		must(os.WriteFile(filepath.Join(q, "cold-model-r1.json"), append(raw, '\n'), 0600))
		return
	}
	mem, e := os.ReadFile(filepath.Join(q, "original-r3/region-1/branch-before.ram"))
	must(e)
	var maps map[string][]byte
	raw, e := os.ReadFile(filepath.Join(q, "original-r3/region-1/before-maps.json"))
	must(e)
	must(json.Unmarshal(raw, &maps))
	plan, e := planOriginMap(mem, maps, packed)
	must(e)
	if plan.CurrentName != "map02.ay" || plan.X != 40 || plan.Y != 40 {
		t.Fatal("cross-map input")
	}
	bad := append([]byte(nil), mem...)
	bad[0x276d2] = 'x'
	if _, e = planOriginMap(bad, maps, packed); e == nil {
		t.Fatal("map name admitted")
	}
	if _, e = decodeOriginTerrain(packed[:7]); e == nil {
		t.Fatal("short tree admitted")
	}
	if _, e = decodeOriginTerrain(packed[:188]); e == nil {
		t.Fatal("truncated tree admitted")
	}
	w.Army.Gold = 500
	w.Army.Leadership = 1000
	w.Army.Slots = [6]ArmyStack{{"openkb:wolf", 5}}
	base, e := os.ReadFile(filepath.Join(q, "inputs/original-save.ay"))
	must(e)
	must(initializeProgressPair(filepath.Join(q, "session-gui-r1"), base, c, cc, w))
	out := map[string]any{"status": "passed-origin-input-guards", "controlled_initial_army": true, "bad_map_name_refused": true, "short_tree_refused": true, "truncated_tree_refused": true, "initial": w}
	raw, e = json.MarshalIndent(out, "", "  ")
	must(e)
	must(os.WriteFile(filepath.Join(q, "model-r1.json"), append(raw, '\n'), 0600))
}
