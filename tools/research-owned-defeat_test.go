package main

import (
	"encoding/json"
	"math"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

func defeatFixture(t *testing.T, annihilated bool) (ArmyCatalog, game.OwnedCombatCatalog, OwnedWorld, DefeatInput) {
	t.Helper()
	var c ArmyCatalog
	raw, e := os.ReadFile(os.Getenv("EIGHTSWORD_WORLD_ARMY"))
	if e != nil {
		t.Fatal(e)
	}
	if e = strictJSON(raw, &c); e != nil {
		t.Fatal(e)
	}
	var cc game.OwnedCombatCatalog
	raw, e = os.ReadFile(os.Getenv("EIGHTSWORD_WORLD_COMBAT"))
	if e != nil {
		t.Fatal(e)
	}
	if e = strictJSON(raw, &cc); e != nil {
		t.Fatal(e)
	}
	army := OwnedArmy{Gold: 500, Leadership: 1000, RecruitRank: 1, Rules: "tactics", Offers: map[string]ArmyOffer{}}
	army.Slots[5] = ArmyStack{Unit: "openkb:wolf", Count: 12}
	w := OwnedWorld{Schema: "eightsword-owned-world/1", Army: army, Progress: WorldProgress{Rank: 1, Legacy04F6: 100, Thresholds: [6]uint64{0, 2000, 5000, 8000, 12000, 30000}}, Encounters: map[string]WorldEncounter{"test": {Enemy: [6]ArmyStack{{Unit: "openkb:skel", Count: 15}}}}}
	w, e = w.begin(c, cc, "test", game.OwnedCombatConfig{Rules: "tactics", Divisors: [2]uint32{5, 5}, Multipliers: [2]uint32{1, 1}})
	if e != nil {
		t.Fatal(e)
	}
	random := uint32(2730)
	input := DefeatInput{Reason: "retreat", Random: &random}
	if annihilated {
		w.Battle.State.Rows[0][5].Count = 0
		w.Battle.State.Result = "loss"
		input = DefeatInput{Reason: "annihilation", Choice: "roam"}
	}
	return c, cc, w, input
}
func TestDefeatOriginalResourceControls(t *testing.T) {
	raw, e := os.ReadFile(os.Getenv("EIGHTSWORD_DEFEAT_CONTROLS"))
	if e != nil {
		t.Fatal(e)
	}
	var controls struct {
		Rows []struct {
			Case struct {
				Name   string
				Count  uint16
				Choice int
			}
			Before, After struct {
				Progress  []uint16
				Origin    []uint16
				PositionX uint16 `json:"position_x"`
				PositionY uint16 `json:"position_y"`
			}
			Effective   int `json:"effective_random"`
			RandomCalls int `json:"random_calls"`
			Error       string
		} `json:"rows"`
	}
	if e = json.Unmarshal(raw, &controls); e != nil {
		t.Fatal(e)
	}
	if len(controls.Rows) != 12 {
		t.Fatal("twelve original controls required")
	}
	for _, v := range controls.Rows {
		t.Run(v.Case.Name, func(t *testing.T) {
			if v.Error != "<nil>" || len(v.Before.Progress) != 6 || len(v.After.Progress) != 6 {
				t.Fatal(v)
			}
			c, cc, w, input := defeatFixture(t, v.Case.Count == 0)
			p := v.Before.Progress
			w.Army.Gold = uint64(p[3])
			w.Army.Leadership = uint64(p[4])
			w.Army.RecruitRank = uint32(p[0])
			w.Progress.Rank = uint32(p[0])
			w.Progress.Merit = uint64(p[1])
			w.Progress.Legacy04F6 = uint64(p[2])
			w.Progress.Legacy04FC = uint64(p[5])
			if v.Case.Count > 0 {
				r := uint32(v.Effective)
				input.Random = &r
				if v.RandomCalls != 1 {
					t.Fatal("random count")
				}
			} else {
				if v.RandomCalls != 0 {
					t.Fatal("annihilation consumed random")
				}
				if v.Case.Choice == 1 {
					input.Choice = "return-origin"
					input.Origin = &DefeatOrigin{Region: "native:00", X: v.Before.Origin[0], Y: v.Before.Origin[1], Facing: 3}
				}
			}
			w.Battle.State.ArmySHA = worldDigest(w.Army)
			w.Battle.StartSHA = w.baseDigest()
			s, e := w.resolveDefeat(c, cc, input)
			if e != nil {
				t.Fatal(e)
			}
			actual := []uint64{uint64(s.After.Progress.Rank), s.After.Progress.Merit, s.After.Progress.Legacy04F6, s.After.Army.Gold, s.After.Army.Leadership, s.After.Progress.Legacy04FC}
			for i, x := range v.After.Progress {
				if actual[i] != uint64(x) {
					t.Fatal("original resource mismatch", actual, v.After.Progress)
				}
			}
			if v.Case.Choice == 1 {
				if s.Resolution.NextOrigin == nil || s.Resolution.NextOrigin.X != v.After.PositionX || s.Resolution.NextOrigin.Y != v.After.PositionY {
					t.Fatal("origin mismatch")
				}
			} else if s.Resolution.NextOrigin != nil {
				t.Fatal("unexpected teleport")
			}
		})
	}
}
func TestDefeatRejectsAndDetachedInputs(t *testing.T) {
	for _, name := range []string{"missing-random", "bad-random", "unexpected-choice", "bad-reason", "stale-army", "win", "draw", "missing-choice", "random-on-annihilation", "bad-origin"} {
		t.Run(name, func(t *testing.T) {
			full := name == "missing-choice" || name == "random-on-annihilation" || name == "bad-origin"
			c, cc, w, in := defeatFixture(t, full)
			switch name {
			case "missing-random":
				in.Random = nil
			case "bad-random":
				r := uint32(32768)
				in.Random = &r
			case "unexpected-choice":
				in.Choice = "roam"
			case "bad-reason":
				in.Reason = "unknown"
			case "stale-army":
				w.Army.Gold++
			case "win":
				w.Battle.State.Rows[1][0].Count = 0
				w.Battle.State.Result = "win"
			case "draw":
				w.Battle.State.Rows[0][5].Count = 0
				w.Battle.State.Rows[1][0].Count = 0
				w.Battle.State.Result = "draw"
			case "missing-choice":
				in.Choice = ""
			case "random-on-annihilation":
				r := uint32(0)
				in.Random = &r
			case "bad-origin":
				in.Choice = "return-origin"
				in.Origin = &DefeatOrigin{Region: "native:25", Facing: 3}
			}
			before := worldDigest(w)
			if _, e := w.resolveDefeat(c, cc, in); e == nil || worldDigest(w) != before {
				t.Fatal("invalid defeat accepted or input changed", e)
			}
		})
	}
	c, cc, w, in := defeatFixture(t, false)
	before := worldDigest(w)
	s, e := w.resolveDefeat(c, cc, in)
	if e != nil || s.After.Army.Slots[0].Count != 12 || s.After.Army.Slots[5].Count != 0 || worldDigest(w) != before {
		t.Fatal(e)
	}
	*in.Random = 0
	w.Army.Gold = 1
	if e = s.validate(c, cc); e != nil {
		t.Fatal("returned plan aliases input", e)
	}
	if _, e = s.After.resolveDefeat(c, cc, s.Input); e == nil {
		t.Fatal("defeat submitted twice")
	}
	for _, r := range []uint32{0, 2729, 2730, 32767} {
		lost, e := retreatPenalty(math.MaxUint64, r)
		if e != nil || lost > math.MaxUint64/3 {
			t.Fatal("wide penalty overflow", lost, e)
		}
	}
}
func TestDefeatSaveAtomicBindings(t *testing.T) {
	c, cc, w, in := defeatFixture(t, true)
	s, e := w.resolveDefeat(c, cc, in)
	if e != nil {
		t.Fatal(e)
	}
	dir := t.TempDir()
	base := make([]byte, 2987)
	if e = os.WriteFile(filepath.Join(dir, "gamedata.ay"), base, 0600); e != nil {
		t.Fatal(e)
	}
	if e = saveDefeat(dir, c, cc, s, ""); e != nil {
		t.Fatal(e)
	}
	target := filepath.Join(dir, "gamedata.ay.army.json")
	original, e := os.ReadFile(target)
	if e != nil {
		t.Fatal(e)
	}
	if decoded, e := loadDefeat(dir, c, cc); e != nil || !reflect.DeepEqual(decoded, s) {
		t.Fatal(e)
	}
	if e = saveDefeat(dir, c, cc, s, ""); e == nil {
		t.Fatal("stale write")
	}
	if current, err := os.ReadFile(target); err != nil || !reflect.DeepEqual(current, original) {
		t.Fatal("stale writer changed the saved transition", err)
	}
	if e = saveDefeat(dir, c, cc, s, contentSHA(original)); e != nil {
		t.Fatal("matching writer rejected", e)
	}
	os.Mkdir(filepath.Join(dir, ".owned-world.lock"), 0700)
	if e = saveDefeat(dir, c, cc, s, contentSHA(original)); e == nil {
		t.Fatal("locked write")
	}
	os.Remove(filepath.Join(dir, ".owned-world.lock"))
	for _, name := range []string{"missing-input", "null-revision", "short-threshold", "long-threshold", "short-enemy", "long-enemy", "missing-resolution", "changed-after", "unknown-version", "duplicate", "trailing", "deep"} {
		t.Run(name, func(t *testing.T) {
			var object map[string]any
			json.Unmarshal(original, &object)
			session := object["session"].(map[string]any)
			after := session["after"].(map[string]any)
			switch name {
			case "missing-input":
				delete(session["input"].(map[string]any), "random")
			case "null-revision":
				after["revision"] = nil
			case "short-threshold":
				after["progress"].(map[string]any)["thresholds"] = []any{}
			case "long-threshold":
				after["progress"].(map[string]any)["thresholds"] = []any{0, 1, 2, 3, 4, 5, 6}
			case "short-enemy":
				session["resolution"].(map[string]any)["enemy_survivors"] = []any{}
			case "long-enemy":
				enemy := session["resolution"].(map[string]any)["enemy_survivors"].([]any)
				session["resolution"].(map[string]any)["enemy_survivors"] = append(enemy, enemy[0])
			case "missing-resolution":
				delete(session["resolution"].(map[string]any), "promoted")
			case "changed-after":
				after["army"].(map[string]any)["gold"] = 1
			case "unknown-version":
				object["schema"] = "unknown"
			}
			raw, _ := json.Marshal(object)
			if name == "duplicate" {
				raw = []byte(`{"schema":"x","schema":"y"}`)
			}
			if name == "trailing" {
				raw = append(raw, []byte(" {}")...)
			}
			if name == "deep" {
				raw = []byte(strings.Repeat("[", 33) + "0" + strings.Repeat("]", 33))
			}
			os.WriteFile(target, raw, 0600)
			if _, e = loadDefeat(dir, c, cc); e == nil {
				t.Fatal("malformed defeat save accepted")
			}
		})
	}
	os.WriteFile(target, original, 0600)
	base[0] = 1
	os.WriteFile(filepath.Join(dir, "gamedata.ay"), base, 0600)
	if _, e = loadDefeat(dir, c, cc); e == nil {
		t.Fatal("wrong original save")
	}
}

func TestDefeatPromotionAndSparseCompaction(t *testing.T) {
	for _, test := range []struct {
		name    string
		rank    uint32
		merit   uint64
		promote bool
	}{
		{"equal-threshold", 1, 2000, false},
		{"above-threshold", 1, 2001, true},
		{"only-one-rank", 1, 30000, true},
		{"last-promotion", 4, 12001, true},
		{"rank-cap", 5, 30000, false},
	} {
		t.Run(test.name, func(t *testing.T) {
			c, cc, w, in := defeatFixture(t, false)
			w.Battle = nil
			w.Army.Slots[2] = ArmyStack{Unit: "native:01", Count: 3}
			w.Army.RecruitRank = test.rank
			w.Progress.Rank = test.rank
			w.Progress.Merit = test.merit
			w.Progress.Legacy04F6 = 29999
			w.Progress.Legacy04FC = 29999
			w.Army.Leadership = 29999
			var err error
			w, err = w.begin(c, cc, "test", game.OwnedCombatConfig{Rules: "tactics", Divisors: [2]uint32{5, 5}, Multipliers: [2]uint32{1, 1}})
			if err != nil {
				t.Fatal(err)
			}
			w.Battle.State.Rows[0][2].Count = 1
			before := worldDigest(w)
			s, err := w.resolveDefeat(c, cc, in)
			if err != nil {
				t.Fatal(err)
			}
			if s.Resolution.Promoted != test.promote || worldDigest(w) != before {
				t.Fatal("promotion or input mutation")
			}
			if s.After.Army.Slots[0] != (ArmyStack{Unit: "native:01", Count: 1}) || s.After.Army.Slots[1] != (ArmyStack{Unit: "openkb:wolf", Count: 12}) || s.After.Army.Slots[5].Count != 0 {
				t.Fatal("stable survivor compaction")
			}
			want := uint64(29999)
			if test.promote {
				want = 30000
			}
			if s.After.Progress.Legacy04F6 != want || s.After.Progress.Legacy04FC != want || s.After.Army.Leadership != want {
				t.Fatal("promotion stat caps")
			}
			wantRank := test.rank
			if test.promote {
				wantRank++
			}
			if s.After.Progress.Rank != wantRank {
				t.Fatal("rank gate")
			}
		})
	}
}

func TestDefeatSaveRejectsOtherSchemasAndCatalogs(t *testing.T) {
	c, cc, w, in := defeatFixture(t, true)
	s, err := w.resolveDefeat(c, cc, in)
	if err != nil {
		t.Fatal(err)
	}
	dir := t.TempDir()
	if err = os.WriteFile(filepath.Join(dir, "gamedata.ay"), make([]byte, 2987), 0600); err != nil {
		t.Fatal(err)
	}
	if err = saveDefeat(dir, c, cc, s, ""); err != nil {
		t.Fatal(err)
	}
	target := filepath.Join(dir, "gamedata.ay.army.json")
	original, err := os.ReadFile(target)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = loadWorld(dir, c, cc); err == nil {
		t.Fatal("world loader discarded defeat session")
	}
	changed := c
	changed.Profiles = append([]UnitProfile(nil), c.Profiles...)
	changed.Profiles[0].Name += "changed"
	if _, err = loadDefeat(dir, changed, cc); err == nil {
		t.Fatal("catalog binding")
	}
	other := []byte(`{"schema":"eightsword-owned-world-save/1"}`)
	if err = os.WriteFile(target, other, 0600); err != nil {
		t.Fatal(err)
	}
	if err = saveDefeat(dir, c, cc, s, contentSHA(other)); err == nil {
		t.Fatal("overwrote another schema")
	}
	if current, e := os.ReadFile(target); e != nil || !reflect.DeepEqual(current, other) {
		t.Fatal("changed other schema", e)
	}
	if err = os.Remove(target); err != nil {
		t.Fatal(err)
	}
	if err = saveDefeat(dir, c, cc, s, contentSHA(original)); err == nil {
		t.Fatal("missing old save accepted")
	}
}
