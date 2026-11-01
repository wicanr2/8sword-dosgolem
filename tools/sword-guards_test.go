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

func TestSwordGuards(t *testing.T) {
	q := os.Getenv("EIGHTSWORD_SWORD_WORK")
	if q == "" || os.Getuid() != 1000 {
		t.Fatal("fixed Docker work")
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
		n string
		v any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}, {"world-normal.json", &w}} {
		b, e := os.ReadFile(filepath.Join(q, "inputs", v.n))
		must(e)
		must(pairStrictJSON(b, v.v))
	}
	if os.Getenv("EIGHTSWORD_SWORD_COLD") != "" {
		s, before, e := openProgressPair(filepath.Join(q, "session-won-r1"), c, cc)
		must(e)
		pam, e := os.ReadFile("/game/PAM.AY")
		must(e)
		code, e := worldArmyCode(pam)
		must(e)
		o, e := oracle.LoadWith("/game/PAM.AY", "/game", oracle.Options{Adlib: true})
		must(e)
		defer o.Close()
		b := &controlledBattle{Store: s, Code: code}
		_, e = loadResumeInto(o, s, before, b)
		must(e)
		if before.World.Battle == nil || before.World.Battle.State.Result != "win" || !b.Pending || b.Settled || b.Returned {
			t.Fatal("fresh won battle required for interruption test")
		}
		_, im, e := readResumeObject(s.Dir, before)
		must(e)
		must(os.WriteFile(filepath.Join(q, "boss-held.ram"), im.M.Mem, 0600))
		seed := originalSeed(o)
		s.Fault = func(at string) error {
			if at == "intent-durable" {
				return errors.New("controlled sword interruption")
			}
			return nil
		}
		if e = settleGuardRuntime(b, o, 0); e == nil {
			t.Fatal("missing fault")
		}
		s.Close()
		s, cold, e := openProgressPair(filepath.Join(q, "session-won-r1"), c, cc)
		must(e)
		defer s.Close()
		b = &controlledBattle{Store: s, Code: code}
		ref, e := loadResumeInto(o, s, cold, b)
		must(e)
		flags, e := savedSwords(cold.Bytes.Native)
		must(e)
		if !flags[0] || ref.Result != 0 || !b.Settled || originalSeed(o) != seed {
			t.Fatal("cold sword result")
		}
		if e = settleGuardRuntime(b, o, 0); e == nil {
			t.Fatal("duplicate sword")
		}
		bad := append([]byte{}, cold.Bytes.Native...)
		binary.LittleEndian.PutUint16(bad[1322:], 1325+1)
		if e = swordNativeBinding(im.M.Mem, bad, b.Guard, true); e == nil {
			t.Fatal("unrelated sword accepted")
		}
		raw, e := json.MarshalIndent(map[string]any{"status": "passed-sword-interrupted-cold-return", "before": before, "after": cold, "reference": ref, "seed": seed, "unrelated_sword_refused": true, "duplicate_refused": true, "flags": flags}, "", "  ")
		must(e)
		must(os.WriteFile(filepath.Join(q, "cold-model-r1.json"), append(raw, '\n'), 0600))
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
	finalBase := append([]byte{}, base...)
	for region := 0; region < 8; region++ {
		finalBase, e = projectSwords(finalBase, region, int(swordBossIndex[region]), 0)
		must(e)
	}
	if os.Getenv("EIGHTSWORD_SWORD_FINAL_ONLY") != "" {
		must(initializeProgressPair(filepath.Join(q, "session-final-r2"), finalBase, c, cc, w))
		return
	}
	must(initializeProgressPair(filepath.Join(q, "session-boss-r1"), base, c, cc, w))
	must(initializeProgressPair(filepath.Join(q, "session-final-r1"), finalBase, c, cc, w))
	var rows []any
	for region := 0; region < 8; region++ {
		for _, result := range []uint16{0, 1} {
			after, e := projectSwords(base, region, int(swordBossIndex[region]), result)
			must(e)
			f, e := savedSwords(after)
			must(e)
			if f[region] != (result == 0) {
				t.Fatal("sword result")
			}
			for at := range base {
				if at != 1318+region*4 && at != 1319+region*4 && base[at] != after[at] {
					t.Fatal("neighbor save changed")
				}
			}
			rows = append(rows, map[string]any{"region": region, "result": result, "flags": f})
		}
	}
	after, e := projectSwords(base, 0, 4, 0)
	must(e)
	if !bytes.Equal(base, after) {
		t.Fatal("ending grants a sword")
	}
	bad := append([]byte{}, base...)
	binary.LittleEndian.PutUint16(bad[1318:], 1323)
	if _, e = savedSwords(bad); e == nil {
		t.Fatal("invalid flag")
	}
	raw, e := json.MarshalIndent(map[string]any{"status": "passed-sword-projection-boundaries", "cases": rows, "initial": w, "ending_no_sword": true, "invalid_flag_refused": true}, "", "  ")
	must(e)
	must(os.WriteFile(filepath.Join(q, "model-r1.json"), append(raw, '\n'), 0600))
}
