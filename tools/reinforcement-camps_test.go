//go:build ignore

package main

import (
	"bytes"
	"encoding/json"
	"errors"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"os"
	"path/filepath"
	"testing"
)

func TestReinforcementCamps(t *testing.T) {
	q := os.Getenv("EIGHTSWORD_REINFORCEMENT_WORK")
	if q == "" || os.Getuid() != 1000 {
		t.Fatal("bounded Docker work required")
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
	must(setMonthlySavePAM(filepath.Join(q, "inputs/PAM.AY")))
	base, e := os.ReadFile(filepath.Join(q, "inputs/original-save.ay"))
	must(e)
	maps, e := readNativeCheckpointMaps(filepath.Join(q, "inputs/maps"))
	must(e)
	w.Army.Gold = 500
	w.Army.Leadership = 1000
	w.Army.Rules = "tactics"
	w.Army.Slots = [6]ArmyStack{{"native:01", 30}}
	w.Army.Offers = map[string]ArmyOffer{}
	w.Progress.Rank = 1
	w.Army.RecruitRank = 1
	w.Progress.Legacy04F6 = 100
	if os.Getenv("EIGHTSWORD_REINFORCEMENT_INIT_ONLY") != "" {
		must(initializeProgressPair(filepath.Join(q, "session-gui-r2"), base, c, cc, w))
		return
	}
	session := filepath.Join(q, "session-camp-r2")
	must(initializeProgressPair(session, base, c, cc, w))
	s, b, e := openProgressPair(session, c, cc)
	must(e)
	b, e = s.BindCamp(b.Token, 0, 0, maps)
	must(e)
	// A genuine completed v4 is accepted; its next commit publishes v5.
	var old checkpointSave
	must(pairStrictJSON(b.Bytes.World, &old))
	old.Schema = legacyCampSchema
	raw, e := json.MarshalIndent(old, "", "  ")
	must(e)
	oldBytes := progressPairBytes{b.Bytes.Native, append(raw, '\n')}
	_, e = decodeProgressPair(oldBytes, c, cc)
	must(e)
	must(os.WriteFile(filepath.Join(q, "legacy-v4.json"), oldBytes.World, 0600))
	s.Close()
	must(os.WriteFile(filepath.Join(session, "gamedata.ay.army.json"), oldBytes.World, 0600))
	s, b, e = openProgressPair(session, c, cc)
	must(e)
	before := b
	b, e = s.BindReinforcements(b.Token, 0, 0)
	must(e)
	bound := b
	if len(reinforcementOffers(b.World.Army)) != 8 || !bytes.Equal(before.Bytes.Native, b.Bytes.Native) {
		t.Fatal("bind changed original")
	}
	id := reinforcementKey(0, 0, 2, "openkb:wolf")
	if b.World.Army.Offers[id].Stock != 150 {
		t.Fatal("initial wolf stock", b.World.Army.Offers)
	}
	var saved checkpointSave
	must(pairStrictJSON(b.Bytes.World, &saved))
	if saved.Schema != campSchema {
		t.Fatal("missing v5")
	}
	again, e := s.BindReinforcements(b.Token, 0, 0)
	must(e)
	if again.Token != b.Token {
		t.Fatal("duplicate binding")
	}
	if _, e = s.RecruitReinforcement(before.Token, id, 1); e == nil {
		t.Fatal("stale token accepted")
	}
	if _, e = s.RecruitReinforcement(b.Token, id, 0); e == nil {
		t.Fatal("zero purchase")
	}
	if _, e = s.RecruitReinforcement(b.Token, id, 151); e == nil {
		t.Fatal("over quote")
	}
	if _, e = s.RecruitReinforcement(b.Token, reinforcementKey(0, 0, 2, "openkb:drag"), 1); e == nil {
		t.Fatal("rank ignored")
	}
	b, e = s.RecruitReinforcement(b.Token, id, 1)
	must(e)
	purchased := b
	if b.World.Army.Gold != 460 || b.World.Army.Slots[1] != (ArmyStack{"openkb:wolf", 1}) || b.World.Army.Offers[id].Stock != 149 || !sameReinforcementNative(before.Bytes.Native, b.Bytes.Native) {
		t.Fatal("purchase projection")
	}
	if _, e = s.RecruitReinforcement(bound.Token, id, 1); e == nil {
		t.Fatal("duplicate purchase")
	}
	// Generic camp writes cannot fabricate reinforcement stock or remove a pool.
	bad := cloneCampWorld(b.World)
	o := bad.Army.Offers[id]
	o.Stock++
	bad.Army.Offers[id] = o
	bad.Revision++
	if _, e = s.Commit(b.Token, bad); e == nil {
		t.Fatal("stock fabrication")
	}
	bad = cloneCampWorld(b.World)
	delete(bad.Army.Offers, id)
	bad.Revision++
	if _, e = s.Commit(b.Token, bad); e == nil {
		t.Fatal("incomplete pool")
	}
	bad = cloneCampWorld(b.World)
	bad.Army.Rules = "native"
	bad.Revision++
	if _, e = s.Commit(b.Token, bad); e == nil {
		t.Fatal("native downgrade")
	}
	// Canonical monthly branch updates native and independent stocks separately.
	mw, budget, refreshed, e := buildMonthlyWorld(b, c, monthlySavePAM)
	must(e)
	if mw.Army.Offers[id].Stock != 150 || budget.After != 490 {
		t.Fatal("monthly", mw.Army.Offers[id], budget)
	}
	rec, e := decodeCampRecord(refreshed, 0, 0)
	must(e)
	if rec.Words[4] != 2000 {
		t.Fatal("original refill", rec)
	}
	// The same monthly serializer used by runtime must retain all pools.
	projected, e := buildProgressPair(refreshed, c, cc, mw)
	must(e)
	month, e := buildMonthlyPair(b, c, cc, projected.Native, maps)
	must(e)
	_, e = decodeProgressPair(month, c, cc)
	must(e)
	must(os.WriteFile(filepath.Join(q, "monthly-v5.json"), month.World, 0600))
	// Journal interruption after intent is durable recovers once in a new store.
	s.Fault = func(at string) error {
		if at == "intent-durable" {
			return errors.New("controlled reinforcement interruption")
		}
		return nil
	}
	if _, e = s.RecruitReinforcement(b.Token, id, 1); e == nil {
		t.Fatal("missing interruption")
	}
	s.Close()
	s, cold, e := openProgressPair(session, c, cc)
	must(e)
	if cold.World.Army.Gold != 420 || cold.World.Army.Offers[id].Stock != 148 || cold.World.Army.Slots[1].Count != 2 {
		t.Fatal("cold recovery")
	}
	if _, e = s.RecruitReinforcement(purchased.Token, id, 1); e == nil {
		t.Fatal("recovery duplicate")
	}
	s.Close()
	// Keep the GUI sample clean: no pregranted openKB troops or fixture position.
	must(initializeProgressPair(filepath.Join(q, "session-gui-r1"), base, c, cc, w))
	// Offer shape is bounded even if all 50 nonzero records are visited.
	all := before
	for g := 0; g < 5; g++ {
		for r := 0; r < 24; r++ {
			rec, e := decodeCampRecord(base, g, r)
			must(e)
			if rec.Words[3] == 0 {
				continue
			}
			all.World, e = bindReinforcementWorld(all, c, g, r)
			must(e)
		}
	}
	full, e := buildCampUpdate(before.Bytes, c, cc, all.World, nil, maps, nil)
	must(e)
	if len(reinforcementOffers(all.World.Army)) != 400 {
		t.Fatal("all active camps")
	}
	result := map[string]any{"status": "passed-reinforcement-transactions", "before": before, "bound": bound, "purchased": purchased, "recovered": cold, "monthly_world": mw, "monthly_budget": budget, "monthly_native": refreshed, "all_active_offers": 400, "all_active_save_bytes": len(full.World), "legacy_completed_v4_read": true, "fault_recovery_once": true, "original_kind_stock_unchanged_on_recruit": true}
	raw, e = json.MarshalIndent(result, "", "  ")
	must(e)
	must(os.WriteFile(filepath.Join(q, "model-r1.json"), append(raw, '\n'), 0600))
}
