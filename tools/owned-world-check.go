//go:build ignore

// 030 DRAFT: actual Go recruitment -> combat -> world settlement -> cold save.
package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"reflect"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

func mustWorld(err error) {
	if err != nil {
		panic(err)
	}
}
func writeWorld(path string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	mustWorld(e)
	mustWorld(os.WriteFile(path, append(b, '\n'), 0600))
}
func main() {
	catalog := flag.String("catalog", "", "army catalog")
	combatFile := flag.String("combat", "", "combat catalog")
	base := flag.String("base-save", "", "original base save")
	controls := flag.String("controls", "", "recorded original world thresholds")
	out := flag.String("out", "", "new output")
	load := flag.String("load", "", "optional cold-process source")
	flag.Parse()
	if os.Getuid() != 1000 || *catalog == "" || *out == "" {
		panic("UID1000 and explicit paths required")
	}
	if _, e := os.Stat(*out); !os.IsNotExist(e) {
		panic("output exists")
	}
	mustWorld(os.Mkdir(*out, 0755))
	var c ArmyCatalog
	raw, e := os.ReadFile(*catalog)
	mustWorld(e)
	mustWorld(strictJSON(raw, &c))
	var cc game.OwnedCombatCatalog
	raw, e = os.ReadFile(*combatFile)
	mustWorld(e)
	mustWorld(strictJSON(raw, &cc))
	if *load != "" {
		w, err := loadWorld(*load, c, cc)
		mustWorld(err)
		if w.Battle != nil {
			if _, _, err = w.Battle.State.Apply(cc, game.OwnedCombatAction{Side: 1, Source: 0, Target: 0, Kind: "normal"}); err == nil {
				panic("cold-loaded action repeated")
			}
		}
		writeWorld(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-owned-world-cold-load", "world": w, "player_path": false})
		return
	}
	a := OwnedArmy{Gold: 5000, Leadership: 1000, RecruitRank: 1, Rules: "tactics", Offers: map[string]ArmyOffer{"wolf-camp": {Unit: "openkb:wolf", Stock: 1000}}}
	a, hire, e := a.recruit(c, "wolf-camp", 30)
	mustWorld(e)
	var original struct {
		NormalWorld struct {
			Thresholds []uint64 `json:"rank_thresholds_05b2"`
		} `json:"normal_world"`
	}
	raw, e = os.ReadFile(*controls)
	mustWorld(e)
	mustWorld(json.Unmarshal(raw, &original))
	if len(original.NormalWorld.Thresholds) != 7 {
		panic("original threshold source")
	}
	var thresholds [6]uint64
	copy(thresholds[:], original.NormalWorld.Thresholds[:6])
	w := OwnedWorld{Schema: "eightsword-owned-world/1", Army: a, Progress: WorldProgress{Rank: 1, Merit: 1990, Legacy04F6: 100, Legacy04FC: 10, Thresholds: thresholds}, Encounters: map[string]WorldEncounter{"skeleton-patrol": {Enemy: [6]ArmyStack{{Unit: "openkb:skel", Count: 15}}}}}
	initial := w
	w, e = w.begin(c, cc, "skeleton-patrol", game.OwnedCombatConfig{Rules: "tactics", Divisors: [2]uint32{5, 5}, Multipliers: [2]uint32{1, 1}})
	mustWorld(e)
	start := w
	saveDir := filepath.Join(*out, "save")
	mustWorld(os.Mkdir(saveDir, 0700))
	raw, e = os.ReadFile(*base)
	mustWorld(e)
	mustWorld(os.WriteFile(filepath.Join(saveDir, "gamedata.ay"), raw, 0600))
	originalSHA := contentSHA(raw)
	events := []game.OwnedCombatOutcome{}
	midSaved := false
	for w.Battle.State.Result == "" && w.Battle.State.Round < 40 {
		for _, side := range []int{1, 0} {
			if w.Battle.State.Result != "" {
				break
			}
			decision, err := w.Battle.State.Choose(cc, side, 0, "normal", 0, 0)
			mustWorld(err)
			state, result, err := w.Battle.State.Apply(cc, decision.Action)
			mustWorld(err)
			w.Battle = &WorldBattle{Encounter: w.Battle.Encounter, StartSHA: w.Battle.StartSHA, State: state}
			events = append(events, result)
			if !midSaved {
				mustWorld(saveWorld(saveDir, c, cc, w, ""))
				restored, err := loadWorld(saveDir, c, cc)
				mustWorld(err)
				if !reflect.DeepEqual(restored, w) {
					panic("mid-battle save differs")
				}
				w = restored
				midSaved = true
				mid := filepath.Join(*out, "mid-save")
				mustWorld(os.Mkdir(mid, 0700))
				for _, name := range []string{"gamedata.ay", "gamedata.ay.army.json"} {
					b, err := os.ReadFile(filepath.Join(saveDir, name))
					mustWorld(err)
					mustWorld(os.WriteFile(filepath.Join(mid, name), b, 0600))
				}
				if _, _, err = w.Battle.State.Apply(cc, decision.Action); err == nil {
					panic("loaded action repeated")
				}
			}
		}
		if w.Battle.State.Result == "" {
			state, err := w.Battle.State.NextRound(cc)
			mustWorld(err)
			w.Battle = &WorldBattle{Encounter: w.Battle.Encounter, StartSHA: w.Battle.StartSHA, State: state}
		}
	}
	won := w
	settled, reward, e := w.settleVictory(c, cc)
	mustWorld(e)
	if settled.Army.Gold != 4400 || settled.Army.Slots[0].Count != 29 || settled.Progress.Merit != 2012 || settled.Progress.Rank != 2 || settled.Army.RecruitRank != 2 || settled.Army.Leadership != 1100 || !settled.Encounters["skeleton-patrol"].Cleared || settled.Battle != nil {
		panic("world settlement differs")
	}
	if _, _, err := settled.settleVictory(c, cc); err == nil {
		panic("repeat settlement")
	}
	if _, err := settled.begin(c, cc, "skeleton-patrol", start.Battle.State.Config); err == nil {
		panic("cleared enemy restarted")
	}
	previous, e := os.ReadFile(filepath.Join(saveDir, "gamedata.ay.army.json"))
	mustWorld(e)
	mustWorld(saveWorld(saveDir, c, cc, settled, contentSHA(previous)))
	if err := saveWorld(saveDir, c, cc, won, contentSHA(previous)); err == nil {
		panic("stale writer overwrote completed battle")
	}
	restored, e := loadWorld(saveDir, c, cc)
	mustWorld(e)
	if !reflect.DeepEqual(restored, settled) {
		panic("completed world save differs")
	}
	raw, e = os.ReadFile(filepath.Join(saveDir, "gamedata.ay"))
	mustWorld(e)
	if contentSHA(raw) != originalSHA {
		panic("original modified")
	}
	if engine, err := game.Open(game.Options{Root: "/unmounted-original", Saves: saveDir, HD: true}); engine != nil || !errors.Is(err, game.ErrOwnedArmyHandoffPending) {
		panic("Engine did not isolate world save before DOS load")
	}
	writeWorld(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-go-owned-world-data-chain", "initial": initial, "started": start, "won": won, "world": settled, "reward": reward, "hire": hire, "events": events, "original_sha256": originalSHA, "player_path": false, "guest_instructions": 0, "engine_guard": true, "limits": []string{"DRAFT world handoff; normal Engine UI and world map not yet connected.", "Only victory settlement; defeat/retreat penalties and quest rewards unsupported.", "Initial merit1990 is an explicit fixture, with thresholds read from the original normal path.", "New-unit balance values remain provisional; unknown legacy field labels unchanged."}})
	fmt.Println("Go world chain passed:", len(events), "actions; troops29 gold4400 merit2012 rank2; replay, stale-save and DOS handoff rejected")
}
