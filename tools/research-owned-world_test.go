package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"reflect"
	"testing"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

func worldFixture(t *testing.T) (ArmyCatalog, game.OwnedCombatCatalog, OwnedWorld) {
	t.Helper()
	var c ArmyCatalog
	raw, err := os.ReadFile(os.Getenv("EIGHTSWORD_WORLD_ARMY"))
	if err != nil {
		t.Fatal(err)
	}
	if err = strictJSON(raw, &c); err != nil {
		t.Fatal(err)
	}
	var cc game.OwnedCombatCatalog
	raw, err = os.ReadFile(os.Getenv("EIGHTSWORD_WORLD_COMBAT"))
	if err != nil {
		t.Fatal(err)
	}
	if err = strictJSON(raw, &cc); err != nil {
		t.Fatal(err)
	}
	a := OwnedArmy{Gold: 500, Leadership: 1000, RecruitRank: 1, Rules: "tactics", Offers: map[string]ArmyOffer{}}
	a.Slots[5] = ArmyStack{Unit: "openkb:wolf", Count: 30}
	w := OwnedWorld{Schema: "eightsword-owned-world/1", Army: a, Progress: WorldProgress{Rank: 1, Merit: 90, Legacy04F6: 100, Legacy04FC: 10, Thresholds: [6]uint64{0, 100, 500, 1000, 5000, 10000}}, Encounters: map[string]WorldEncounter{"test": {Enemy: [6]ArmyStack{{Unit: "openkb:skel", Count: 15}}}}}
	w, err = w.begin(c, cc, "test", game.OwnedCombatConfig{Rules: "tactics", Divisors: [2]uint32{5, 5}, Multipliers: [2]uint32{1, 1}})
	if err != nil {
		t.Fatal(err)
	}
	// Explicit result fixture; the end-to-end runner executes real Go actions.
	w.Battle.State.Rows[1][0].Count = 0
	w.Battle.State.Result = "win"
	return c, cc, w
}
func TestWorldVictoryAtomicAndCompact(t *testing.T) {
	c, cc, w := worldFixture(t)
	before := worldDigest(w)
	next, r, err := w.settleVictory(c, cc)
	if err != nil {
		t.Fatal(err)
	}
	if worldDigest(w) != before || r.Gold != 600 || r.Merit != 22 || !r.Promoted || next.Army.Gold != 1100 || next.Army.Slots[0].Count != 30 || next.Army.Slots[5].Count != 0 || next.Progress.Rank != 2 || next.Army.RecruitRank != 2 || next.Army.Leadership != 1100 || next.Progress.Legacy04F6 != 200 || next.Progress.Legacy04FC != 16 {
		t.Fatal(next, r)
	}
	if _, _, err = next.settleVictory(c, cc); err == nil {
		t.Fatal("duplicate commit")
	}
}

func TestWorldLargeRewardsAndOverflow(t *testing.T) {
	c, cc, w := worldFixture(t)
	e := w.Encounters["test"]
	e.Enemy[0].Count = 1000000
	w.Encounters["test"] = e
	w.Battle.State.Initial[1][0].Count = 1000000
	w.Battle.StartSHA = w.baseDigest()
	next, reward, err := w.settleVictory(c, cc)
	if err != nil || reward.Gold != 40000000 || reward.Merit != 1500000 || next.Army.Gold != 30000 || next.Progress.Merit != 30000 || next.Progress.Rank != 2 {
		t.Fatal(next, reward, err)
	}
	c, cc, w = worldFixture(t)
	e = w.Encounters["test"]
	for i := 0; i < 6; i++ {
		id := fmt.Sprintf("openkb:overflow-%d", i)
		c.Profiles = append(c.Profiles, UnitProfile{ID: id, Name: id, Origin: "openkb-reference-prototype", Gold: 1000000000, Command: 1})
		cc.Profiles[id] = game.OwnedCombatProfile{ID: id, Attack: 1, HP: 1}
		e.Enemy[i] = ArmyStack{Unit: id, Count: math.MaxUint32}
		w.Battle.State.Initial[1][i] = game.OwnedCombatStack{Unit: id, Count: math.MaxUint32}
		w.Battle.State.Rows[1][i] = game.OwnedCombatStack{Unit: id}
	}
	w.Encounters["test"] = e
	w.Battle.State.CatalogSHA = cc.Digest()
	w.Battle.StartSHA = w.baseDigest()
	before := worldDigest(w)
	if next, _, err = w.settleVictory(c, cc); err == nil || worldDigest(next) != before || worldDigest(w) != before {
		t.Fatal("overflow reward was committed", err)
	}
}
func TestWorldRejectWithoutMutation(t *testing.T) {
	for _, mode := range []string{"army-change", "resource-change", "enemy-change", "incomplete", "loss", "double", "overflow-gold", "overflow-merit", "overflow-bonus", "unknown-unit", "wrong-rules"} {
		t.Run(mode, func(t *testing.T) {
			c, cc, w := worldFixture(t)
			switch mode {
			case "army-change":
				w.Army.Slots[5].Count--
			case "resource-change":
				w.Army.Gold++
			case "enemy-change":
				e := w.Encounters["test"]
				e.Enemy[0].Count++
				w.Encounters["test"] = e
			case "incomplete":
				w.Battle.State.Result = ""
			case "loss":
				w.Battle.State.Rows[0][5].Count = 0
				w.Battle.State.Rows[1][0].Count = 15
				w.Battle.State.Result = "loss"
			case "double":
				w.Battle.State.Committed = true
			case "overflow-gold":
				w.Army.Gold = math.MaxUint64
			case "overflow-merit":
				w.Progress.Merit = math.MaxUint64
			case "overflow-bonus":
				w.Progress.Legacy04F6 = math.MaxUint64
			case "unknown-unit":
				w.Army.Slots[5].Unit = "openkb:missing"
			case "wrong-rules":
				w.Battle.State.Config.Rules = "native"
			}
			if mode == "overflow-gold" || mode == "overflow-merit" || mode == "overflow-bonus" {
				w.Battle.StartSHA = w.baseDigest()
				w.Battle.State.ArmySHA = worldDigest(w.Army)
			}
			before := worldDigest(w)
			next, _, err := w.settleVictory(c, cc)
			if err == nil || worldDigest(w) != before || worldDigest(next) != before {
				t.Fatal("invalid commit mutated input", err)
			}
		})
	}
}
func TestWorldOriginalRewardControls(t *testing.T) {
	raw, err := os.ReadFile(os.Getenv("EIGHTSWORD_WORLD_CONTROLS"))
	if err != nil {
		t.Fatal(err)
	}
	var d struct {
		Fixtures []struct {
			Name          string
			RewardMerit   uint64 `json:"reward_merit"`
			RewardGold    uint64 `json:"reward_gold"`
			Before, After struct {
				Progress []uint16 `json:"progress_04f2"`
			}
			Error string
		} `json:"fixtures"`
	}
	if err = json.Unmarshal(raw, &d); err != nil {
		t.Fatal(err)
	}
	if len(d.Fixtures) != 7 {
		t.Fatal("seven original controls required")
	}
	for _, v := range d.Fixtures {
		t.Run(v.Name, func(t *testing.T) {
			if v.Error != "<nil>" || len(v.Before.Progress) != 6 || len(v.After.Progress) != 6 {
				t.Fatal(v)
			}
			c, cc, w := worldFixture(t)
			p := v.Before.Progress
			w.Army.Gold = uint64(p[3])
			w.Army.Leadership = uint64(p[4])
			w.Army.RecruitRank = uint32(p[0])
			w.Progress = WorldProgress{Rank: uint32(p[0]), Merit: uint64(p[1]), Legacy04F6: uint64(p[2]), Legacy04FC: uint64(p[5]), Thresholds: [6]uint64{0, 100, 100, 100, 100, 100}}
			e := w.Encounters["test"]
			e.Enemy[0].Count = 1
			w.Encounters["test"] = e
			// A one-unit reference fixture isolates precisely the recorded reward values.
			unit := c.Profiles[len(c.Profiles)-1]
			unit.ID = "openkb:reward-control"
			unit.NativeKind = 0
			unit.Gold = v.RewardGold
			unit.Command = max(uint64(1), v.RewardMerit*2)
			c.Profiles = append(c.Profiles, unit)
			cc.Profiles[unit.ID] = game.OwnedCombatProfile{ID: unit.ID, Attack: 1, HP: 1}
			e.Enemy[0].Unit = unit.ID
			w.Encounters["test"] = e
			w.Battle.State.Initial[1][0] = game.OwnedCombatStack{Unit: unit.ID, Count: 1}
			w.Battle.State.Rows[1][0] = game.OwnedCombatStack{Unit: unit.ID, Count: 0}
			w.Battle.State.CatalogSHA = cc.Digest()
			w.Battle.State.ArmySHA = worldDigest(w.Army)
			w.Battle.StartSHA = w.baseDigest()
			n, _, err := w.settleVictory(c, cc)
			if err != nil {
				t.Fatal(err)
			}
			actual := []uint64{uint64(n.Progress.Rank), n.Progress.Merit, n.Progress.Legacy04F6, n.Army.Gold, n.Army.Leadership, n.Progress.Legacy04FC}
			for i, x := range v.After.Progress {
				if actual[i] != uint64(x) {
					t.Fatal("original mismatch", actual, v.After.Progress)
				}
			}
		})
	}
}
func TestWorldSaveBindingsAndMalformed(t *testing.T) {
	c, cc, w := worldFixture(t)
	dir := t.TempDir()
	base := make([]byte, 2987)
	if err := os.WriteFile(filepath.Join(dir, "gamedata.ay"), base, 0600); err != nil {
		t.Fatal(err)
	}
	if err := saveWorld(dir, c, cc, w, ""); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(dir, "gamedata.ay.army.json")
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	read, err := loadWorld(dir, c, cc)
	if err != nil || !reflect.DeepEqual(read, w) {
		t.Fatal(err)
	}
	if err = saveWorld(dir, c, cc, w, ""); err == nil {
		t.Fatal("stale writer")
	}
	if err = os.Mkdir(filepath.Join(dir, ".owned-world.lock"), 0700); err != nil {
		t.Fatal(err)
	}
	if err = saveWorld(dir, c, cc, w, contentSHA(raw)); err == nil {
		t.Fatal("locked writer")
	}
	os.Remove(filepath.Join(dir, ".owned-world.lock"))
	for _, name := range []string{"missing-world-field", "null-revision", "short-thresholds", "null-threshold", "short-enemy", "short-battle", "unknown-version", "trailing", "duplicate"} {
		t.Run(name, func(t *testing.T) {
			var object map[string]any
			if err = json.Unmarshal(raw, &object); err != nil {
				t.Fatal(err)
			}
			world := object["world"].(map[string]any)
			switch name {
			case "missing-world-field":
				delete(world, "revision")
			case "null-revision":
				world["revision"] = nil
			case "short-thresholds":
				world["progress"].(map[string]any)["thresholds"] = []any{0, 100}
			case "null-threshold":
				world["progress"].(map[string]any)["thresholds"].([]any)[0] = nil
			case "short-enemy":
				world["encounters"].(map[string]any)["test"].(map[string]any)["enemy"] = []any{}
			case "short-battle":
				world["battle"].(map[string]any)["state"].(map[string]any)["rows"] = []any{}
			case "unknown-version":
				object["schema"] = "unknown"
			}
			bad, _ := json.Marshal(object)
			if name == "trailing" {
				bad = append(bad, []byte(" {}")...)
			}
			if name == "duplicate" {
				bad = []byte(`{"schema":"x","schema":"y"}`)
			}
			if err = os.WriteFile(path, bad, 0600); err != nil {
				t.Fatal(err)
			}
			if _, err = loadWorld(dir, c, cc); err == nil {
				t.Fatal("malformed world accepted")
			}
		})
	}
	os.WriteFile(path, raw, 0600)
	base[0] = 1
	os.WriteFile(filepath.Join(dir, "gamedata.ay"), base, 0600)
	if _, err = loadWorld(dir, c, cc); err == nil {
		t.Fatal("wrong base save")
	}
}
