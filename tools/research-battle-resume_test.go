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

func TestResumePursuitAtomicOpening(t *testing.T) {
	q := os.Getenv("EIGHTSWORD_RESUME_WORK")
	if q == "" {
		t.Fatal("fixed evidence required")
	}
	must := func(e error) {
		t.Helper()
		if e != nil {
			t.Fatal(e)
		}
	}
	out := filepath.Join(q, "opening-test-r1")
	must(os.Mkdir(out, 0700))
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
	var evidence struct {
		Begin OwnedWorld `json:"begin_world"`
	}
	raw, e := os.ReadFile(filepath.Join(q, "probe-r2/receipt.json"))
	must(e)
	must(json.Unmarshal(raw, &evidence))
	staged := evidence.Begin
	// The previously verified UI helper is the control. Its callbacks write only
	// to memory here, so the whole opening can be compared before publication.
	u := &battleUI{Catalog: c, Combat: cc, World: staged, Locked: true, CommitPair: func(OwnedWorld) (string, string, error) { return "", "", nil }}
	old := runtimeEnemyCurrent
	defer func() { runtimeEnemyCurrent = old }()
	runtimeEnemyCurrent = &runtimeEnemyBattle{Modifier: 1}
	must(pursuitOpening(&encounterExtra{UI: u}))
	expected := u.World
	got, e := resumeOpening(staged, cc, 1)
	must(e)
	if len(u.Events) == 0 || worldDigest(got) != worldDigest(expected) {
		t.Fatal("opening differs from admitted UI helper")
	}
	zero, e := resumeOpening(staged, cc, 0)
	must(e)
	if worldDigest(zero) != worldDigest(staged) {
		t.Fatal("ordinary encounter changed")
	}
	// Only the declared modifier is changed. Preserve every other VM byte,
	// register and original RNG value from the accepted held snapshot.
	o, e := oracle.LoadWith("/game/PAM.AY", "/game", oracle.Options{Adlib: true})
	must(e)
	defer o.Close()
	must(o.LoadStateFile(filepath.Join(q, "probe-r2/held.state")))
	seed := originalSeed(o)
	o.WriteU16(oracle.Far(0x1e88, 0x8d6a), 1)
	state := filepath.Join(out, "modifier1.state")
	must(o.SaveStateFile(state))
	raw, e = os.ReadFile(state)
	must(e)
	base, e := os.ReadFile(filepath.Join(q, "inputs/original-save.ay"))
	must(e)
	maps := map[string][]byte{}
	for i := 0; i < 9; i++ {
		n := fmtCheckpointTestName(i)
		maps[n], e = os.ReadFile(filepath.Join(q, "inputs/maps", n))
		must(e)
	}
	maps["map01.ay"] = append([]byte(nil), o.Bytes(oracle.Far(0x9c00, 0), 5761)...)
	dir := filepath.Join(out, "pair")
	must(initializeProgressPair(dir, base, c, cc, w))
	store, before, e := openProgressPair(dir, c, cc)
	must(e)
	store.Fault = func(p string) error {
		if p == "world-durable" {
			return errors.New("controlled activation interruption")
		}
		return nil
	}
	_, e = store.CommitSuspendedBattle(before.Token, got, raw, maps)
	if e == nil {
		t.Fatal("missing interruption")
	}
	store.Close()
	store, cold, e := openProgressPair(dir, c, cc)
	must(e)
	defer store.Close()
	if worldDigest(cold.World) != worldDigest(expected) {
		t.Fatal("partial opening was activated")
	}
	b := &controlledBattle{Store: store}
	ref, e := loadResumeInto(o, store, cold, b)
	must(e)
	if ref.Phase != "battle" || worldDigest(b.Current.World) != worldDigest(expected) || originalSeed(o) != seed {
		t.Fatal("cold opening/seed changed")
	}
	must(o.SaveStateFile(filepath.Join(out, "cold.state")))
	data := map[string]any{"status": "passed-atomic-pursuit-opening", "modifier": 1, "controlled_memory": true, "actions": u.Events, "world": expected, "seed": seed, "interruption": "world-durable", "cold_equal": true, "ordinary_unchanged": true}
	encoded, e := json.MarshalIndent(data, "", "  ")
	must(e)
	must(os.WriteFile(filepath.Join(out, "receipt.json"), append(encoded, '\n'), 0600))
}
func fmtCheckpointTestName(i int) string { return "map0" + string(rune('0'+i)) + ".ay" }
