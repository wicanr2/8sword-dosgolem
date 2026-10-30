package main

import (
	"encoding/json"
	"fmt"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func TestEncounterOriginalGuardControls(t *testing.T) {
	raw, e := os.ReadFile(os.Getenv("EIGHTSWORD_ENCOUNTER_CONTROLS"))
	if e != nil {
		t.Fatal(e)
	}
	var controls struct {
		Rows []struct {
			Case struct {
				Name                       string
				Region, Result, Legacy26AA uint16
				Boss                       bool
			}
			Before, After struct {
				Progress []uint16
				Pool     []uint16
				Pieces   []uint16
			}
			Random int `json:"random_input"`
		} `json:"rows"`
	}
	if e = json.Unmarshal(raw, &controls); e != nil {
		t.Fatal(e)
	}
	if len(controls.Rows) != 10 {
		t.Fatal("ten native caller controls required")
	}
	for _, row := range controls.Rows {
		t.Run(row.Case.Name, func(t *testing.T) {
			c, cc, _, _ := defeatFixture(t, false)
			army := OwnedArmy{Gold: 500, Leadership: 100, RecruitRank: 1, Rules: "tactics", Offers: map[string]ArmyOffer{}}
			army.Slots[0] = ArmyStack{Unit: "native:01", Count: 12}
			id := fmtGuardID(row.Case.Region, 0)
			w := OwnedWorld{Schema: "eightsword-owned-world/1", Army: army, Progress: WorldProgress{Rank: 1, Merit: 10000, Legacy04F6: 100, Legacy04FC: 10, Thresholds: [6]uint64{0, 2000, 5000, 8000, 12000, 30000}}, Encounters: map[string]WorldEncounter{id: {Enemy: [6]ArmyStack{{Unit: "native:01", Count: 12}, {Unit: "native:03", Count: 7}, {Unit: "native:05", Count: 4}}}}}
			w, e = w.begin(c, cc, id, game.OwnedCombatConfig{Rules: "tactics", Divisors: [2]uint32{5, 5}, Multipliers: [2]uint32{1, 1}})
			if e != nil {
				t.Fatal(e)
			}
			w.Battle.State.Rows[0][0].Count = 11
			in := DefeatInput{}
			if row.Case.Result == 0 {
				for i := range w.Battle.State.Rows[1] {
					w.Battle.State.Rows[1][i].Count = 0
				}
				w.Battle.State.Result = "win"
			} else {
				w.Battle.State.Rows[1][0].Count = 8
				w.Battle.State.Rows[1][1].Count = 0
				w.Battle.State.Rows[1][2].Count = 2
				if row.Case.Result == 1 {
					v := uint32(row.Random)
					in = DefeatInput{Reason: "retreat", Random: &v}
				} else {
					w.Battle.State.Rows[0][0].Count = 0
					w.Battle.State.Result = "loss"
					in = DefeatInput{Reason: "annihilation", Choice: "roam"}
				}
			}
			ctx := EncounterContext{Kind: "guarded", Region: row.Case.Region, Legacy26AA: row.Case.Legacy26AA, Boss: row.Case.Boss, EndingGuardAlive: true}
			s, err := w.resolveEncounter(c, cc, ctx, in)
			if err != nil {
				t.Fatal(err)
			}
			actual := []uint64{uint64(s.After.Progress.Rank), s.After.Progress.Merit, s.After.Progress.Legacy04F6, s.After.Army.Gold, s.After.Army.Leadership, s.After.Progress.Legacy04FC}
			for i, v := range row.After.Progress {
				if actual[i] != uint64(v) {
					t.Fatal("native guard reward mismatch", actual, row.After.Progress)
				}
			}
			for i, v := range row.After.Pieces {
				if s.Result.Pieces[i] != (v == 1) {
					t.Fatal("guard piece flag mismatch")
				}
			}
			base := []int{0x365e, 0x3706, 0x3766, 0x37c6, 0x3826, 0x3886, 0x38e6, 0x3946}[row.Case.Region]
			at := (base - 0x365e) / 2
			for i, v := range s.Result.EnemyRows {
				kind := uint16(0)
				if v.Count > 0 {
					for _, u := range c.Profiles {
						if u.ID == v.Unit {
							kind = u.NativeKind
						}
					}
				}
				if row.After.Pool[at+i*2] != kind || row.After.Pool[at+i*2+1] != uint16(v.Count) {
					t.Fatal("guard residual troops mismatch")
				}
			}
		})
	}
}
func fmtGuardID(region, index uint16) string { return fmt.Sprintf("guarded:%02d:%02d", region, index) }

func TestEncounterSourcesAndUnknownBoundaries(t *testing.T) {
	c, cc, _, _ := defeatFixture(t, false)
	for _, name := range []string{"source", "region", "index", "identity", "ending-unknown", "ending-target", "draw", "input", "stale", "duplicate"} {
		t.Run(name, func(t *testing.T) {
			w, ctx, e := newEncounterFixture(c, cc, true, false)
			if e != nil {
				t.Fatal(e)
			}
			v := uint32(2730)
			in := DefeatInput{Reason: "retreat", Random: &v}
			switch name {
			case "source":
				ctx.Kind = "unknown"
			case "region":
				ctx.Region = 8
			case "index":
				ctx.Index = 12
			case "identity":
				ctx.Region = 7
			case "ending-unknown":
				ctx.EndingGuardAlive = false
			case "ending-target":
				ctx.Region = 0
				ctx.Index = 4
				record := w.Encounters[w.Battle.Encounter]
				delete(w.Encounters, w.Battle.Encounter)
				w.Battle.Encounter = "guarded:00:04"
				w.Encounters[w.Battle.Encounter] = record
				w.Battle.StartSHA = w.baseDigest()
			case "draw":
				w.Battle.State.Result = "draw"
			case "input":
				in.Random = nil
			case "stale":
				w.Army.Gold++
			case "duplicate":
				s, e := w.resolveEncounter(c, cc, ctx, in)
				if e != nil {
					t.Fatal(e)
				}
				w = s.After
			}
			before := worldDigest(w)
			if _, e := w.resolveEncounter(c, cc, ctx, in); e == nil || worldDigest(w) != before {
				t.Fatal("invalid encounter accepted or input changed", e)
			}
		})
	}
	for _, guarded := range []bool{false, true} {
		w, ctx, e := newEncounterFixture(c, cc, guarded, false)
		if e != nil {
			t.Fatal(e)
		}
		v := uint32(2730)
		in := DefeatInput{Reason: "retreat", Random: &v}
		before := worldDigest(w)
		s, e := w.resolveEncounter(c, cc, ctx, in)
		if e != nil || worldDigest(w) != before {
			t.Fatal(e)
		}
		if s.Result.Persistent != guarded {
			t.Fatal("persistence")
		}
		_, exists := s.After.Encounters[w.Battle.Encounter]
		if exists != guarded {
			t.Fatal("random source persisted")
		}
		if (s.After.Progress.Rank == 1) != guarded {
			t.Fatal("guarded retreat promoted")
		}
		w.Encounters["guarded:07:03"] = WorldEncounter{}
		*in.Random = 0
		if e = s.validate(c, cc); e != nil {
			t.Fatal("session aliases inputs", e)
		}
	}
}

func TestEncounterAtomicSaveAndMalformed(t *testing.T) {
	c, cc, _, _ := defeatFixture(t, false)
	w, ctx, e := newEncounterFixture(c, cc, true, false)
	if e != nil {
		t.Fatal(e)
	}
	v := uint32(2730)
	s, e := w.resolveEncounter(c, cc, ctx, DefeatInput{Reason: "retreat", Random: &v})
	if e != nil {
		t.Fatal(e)
	}
	dir := t.TempDir()
	base := make([]byte, 2987)
	if e = os.WriteFile(filepath.Join(dir, "gamedata.ay"), base, 0600); e != nil {
		t.Fatal(e)
	}
	if e = saveEncounter(dir, c, cc, s, ""); e != nil {
		t.Fatal(e)
	}
	target := filepath.Join(dir, "gamedata.ay.army.json")
	saved, e := os.ReadFile(target)
	if e != nil {
		t.Fatal(e)
	}
	if loaded, e := loadEncounter(dir, c, cc); e != nil || !reflect.DeepEqual(loaded, s) {
		t.Fatal(e)
	}
	if e = saveEncounter(dir, c, cc, s, ""); e == nil {
		t.Fatal("stale write")
	}
	os.Mkdir(filepath.Join(dir, ".owned-world.lock"), 0700)
	if e = saveEncounter(dir, c, cc, s, contentSHA(saved)); e == nil {
		t.Fatal("locked writer")
	}
	os.Remove(filepath.Join(dir, ".owned-world.lock"))
	if e = saveEncounter(dir, c, cc, s, contentSHA(saved)); e != nil {
		t.Fatal(e)
	}
	for _, name := range []string{"missing-context", "null-boss", "short-pieces", "long-enemy", "null-gain", "changed-result", "other-version", "missing-reward-field", "missing-origin-field"} {
		t.Run(name, func(t *testing.T) {
			var obj map[string]any
			json.Unmarshal(saved, &obj)
			session := obj["session"].(map[string]any)
			context := session["context"].(map[string]any)
			result := session["result"].(map[string]any)
			switch name {
			case "missing-context":
				delete(context, "ending_guard_alive")
			case "null-boss":
				context["boss"] = nil
			case "short-pieces":
				context["pieces"] = []any{}
			case "long-enemy":
				enemy := result["enemy_rows"].([]any)
				result["enemy_rows"] = append(enemy, enemy[0])
			case "null-gain":
				result["guard_gain"] = []any{nil, 0}
			case "changed-result":
				result["persistent"] = false
			case "other-version":
				obj["schema"] = "other"
			case "missing-reward-field":
				delete(result["random_reward"].(map[string]any), "promoted")
			case "missing-origin-field":
				session["input"].(map[string]any)["origin"] = map[string]any{"region": "native:00", "facing": 3}
			}
			raw, _ := json.Marshal(obj)
			os.WriteFile(target, raw, 0600)
			if _, e = loadEncounter(dir, c, cc); e == nil {
				t.Fatal("malformed encounter accepted")
			}
		})
	}
	os.WriteFile(target, saved, 0600)
	base[0] = 1
	os.WriteFile(filepath.Join(dir, "gamedata.ay"), base, 0600)
	if _, e = loadEncounter(dir, c, cc); e == nil {
		t.Fatal("wrong original save")
	}
}

func TestEncounterGuardRewardCapsAndClearedReentry(t *testing.T) {
	c, cc, _, _ := defeatFixture(t, false)
	w, ctx, err := newEncounterFixture(c, cc, true, false)
	if err != nil {
		t.Fatal(err)
	}
	w.Progress.Legacy04F6 = 29999
	w.Progress.Legacy04FC = 29999
	w.Battle.StartSHA = w.baseDigest()
	for i := range w.Battle.State.Rows[1] {
		w.Battle.State.Rows[1][i].Count = 0
	}
	w.Battle.State.Result = "win"
	ctx.Legacy26AA = 1
	ctx.Boss = true
	s, err := w.resolveEncounter(c, cc, ctx, DefeatInput{})
	if err != nil {
		t.Fatal(err)
	}
	if s.After.Progress.Legacy04F6 != 30000 || s.After.Progress.Legacy04FC != 30000 || s.Result.GuardGain != [2]uint64{1, 1} || !s.Result.Pieces[1] {
		t.Fatal("guard reward cap or piece")
	}
	if _, err = s.After.begin(c, cc, w.Battle.Encounter, w.Battle.State.Config); err == nil {
		t.Fatal("cleared guard restarted")
	}
	if s.After.Progress.Rank != w.Progress.Rank || s.After.Progress.Merit != w.Progress.Merit || s.After.Army.Gold != w.Army.Gold {
		t.Fatal("guard received random reward")
	}
}
