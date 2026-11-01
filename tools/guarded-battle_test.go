//go:build ignore

package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"errors"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
	"os"
	"path/filepath"
	"testing"
)

func TestGuardedBattle(t *testing.T) {
	q := os.Getenv("EIGHTSWORD_GUARDED_WORK")
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
		b, e := os.ReadFile(filepath.Join(q, "inputs", v.Name))
		must(e)
		must(pairStrictJSON(b, v.Dst))
	}
	if os.Getenv("EIGHTSWORD_GUARDED_COLD") != "" {
		store, before, e := openProgressPair(filepath.Join(q, "session-held-r1"), c, cc)
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
		if b.Guard == nil || !b.Pending {
			t.Fatal("guard cold caller")
		}
		seed := originalSeed(o)
		_, im, e := readResumeObject(store.Dir, before)
		must(e)
		must(os.WriteFile(filepath.Join(q, "guarded-held.ram"), im.M.Mem, 0600))
		bad := bytes.Clone(im.M.Mem)
		bad[0x1100+0x2dde] ^= 1
		if _, e = bindGuard(bad, c, cc); e == nil {
			t.Fatal("modified guard code")
		}
		bad = bytes.Clone(im.M.Mem)
		for at, v := range map[int]uint16{0x8e12: 48, 0x8e44: 5} {
			binary.LittleEndian.PutUint16(bad[0x1e880+at:], v)
		}
		if _, e = bindGuard(bad, c, cc); e == nil {
			t.Fatal("boss entered shared path")
		}
		for at, v := range map[int]uint16{0x8e12: 58, 0x8e44: 52} {
			binary.LittleEndian.PutUint16(bad[0x1e880+at:], v)
		}
		if _, e = bindGuard(bad, c, cc); e == nil {
			t.Fatal("ending guard entered shared path")
		}
		store.Fault = func(p string) error {
			if p == "intent-durable" {
				return errors.New("controlled guard interruption")
			}
			return nil
		}
		if e = settleGuardRuntime(b, o, 1); e == nil {
			t.Fatal("interruption missing")
		}
		store.Close()
		store, cold, e := openProgressPair(filepath.Join(q, "session-held-r1"), c, cc)
		must(e)
		defer store.Close()
		b = &controlledBattle{Store: store, Code: code}
		ref, e := loadResumeInto(o, store, cold, b)
		must(e)
		if b.Guard == nil || !b.Settled || b.Result != 1 || ref.Phase != "return" || originalSeed(o) != planOriginalRand(seed).After {
			t.Fatal("guard cold settlement or seed")
		}
		if e = settleGuardRuntime(b, o, 1); e == nil {
			t.Fatal("duplicate guard settlement")
		}
		after, e := store.Recover()
		must(e)
		if after.Token != cold.Token || !bytes.Equal(before.Bytes.Native[12:36], cold.Bytes.Native[12:36]) {
			t.Fatal("duplicate token or player shadow")
		}
		random, e := guardBeginWorld(cold.World, c, cc, nil, [6]ArmyStack{{"native:01", 2}})
		must(e)
		if random.Encounters[b.Guard.key()] != cold.World.Encounters[b.Guard.key()] || random.Battle.Encounter != "random:runtime-r1" {
			t.Fatal("random erased guard")
		}
		raw, e := json.MarshalIndent(map[string]any{"status": "passed-guarded-interrupted-cold-return", "before": before, "after": cold, "resume": ref, "seed": seed, "duplicate_refused": true, "source_refused": true, "boss_refused": true, "ending_refused": true, "player_shadow_unchanged": true}, "", "  ")
		must(e)
		must(os.WriteFile(filepath.Join(q, "cold-model-r2.json"), append(raw, '\n'), 0600))
		return
	}
	w.Army.Rules = "tactics"
	w.Army.Leadership = 30000
	w.Army.Gold = 500
	w.Army.RecruitRank = 1
	w.Progress.Rank = 1
	w.Progress.Merit = 10000
	w.Progress.Legacy04F6 = 100
	w.Progress.Legacy04FC = 10
	w.Army.Slots = [6]ArmyStack{{"native:25", 2000}, {"native:03", 2000}, {"native:24", 2000}, {"openkb:drag", 10}, {"openkb:wolf", 5}, {"openkb:arcr", 100}}
	base, e := os.ReadFile(filepath.Join(q, "inputs/original-save.ay"))
	must(e)
	must(initializeProgressPair(filepath.Join(q, "session-gui-r1"), base, c, cc, w))
	g := &guardedBinding{Context: EncounterContext{Kind: "guarded", Region: 0, Index: 0, EndingGuardAlive: true}, Rows: [6]ArmyStack{{"native:01", 8}, {"native:05", 2}}}
	battle, e := guardBeginWorld(w, c, cc, g, g.Rows)
	must(e)
	old := &nativeResumeRef{Phase: "battle", Seed: 0x12345678}
	ret, ref, e := guardSettledReference(battle, g, old, 1, c, cc)
	must(e)
	plan := planOriginalRand(old.Seed)
	if ref.Seed != plan.After || ret.Army.Gold != 500-500/uint64(uint32(plan.Value)/2730+3) || ret.Progress.Rank != 1 || ret.Progress.Merit != 10000 || ret.Progress.Legacy04F6 != 100 {
		t.Fatal("guard retreat reward or promotion")
	}
	random, e := guardBeginWorld(ret, c, cc, nil, [6]ArmyStack{{"native:01", 2}})
	must(e)
	if random.Encounters[g.key()] != ret.Encounters[g.key()] || random.Battle.Encounter != "random:runtime-r1" {
		t.Fatal("random encounter erased guard")
	}
	projected, e := projectGuardNPC(base, g, ret.Encounters[g.key()].Enemy)
	must(e)
	for i := range base {
		if i < 1508 || i >= 1532 {
			if base[i] != projected[i] {
				t.Fatal("neighbor save changed")
			}
		}
	}
	g2 := &guardedBinding{Context: EncounterContext{Region: 7, Index: 11}}
	if _, e = projectGuardNPC(base, g2, [6]ArmyStack{}); e == nil {
		t.Fatal("guard actual count ignored")
	}
	if _, e = projectGuardNPC(base, g, [6]ArmyStack{{"openkb:wolf", 1}}); e == nil {
		t.Fatal("extended NPC ID projected")
	}
	if _, _, e = guardSettledReference(battle, g, old, 0, c, cc); e == nil {
		t.Fatal("unfinished victory")
	}
	data := map[string]any{"status": "passed-guarded-rules-and-projection", "before": battle, "retreat": ret, "reference": ref, "extended_npc_refused": true, "actual_capacity_refused": true, "unwon_refused": true, "controlled_initial_army": true}
	raw, e := json.MarshalIndent(data, "", "  ")
	must(e)
	must(os.WriteFile(filepath.Join(q, "model-r1.json"), append(raw, '\n'), 0600))
}
