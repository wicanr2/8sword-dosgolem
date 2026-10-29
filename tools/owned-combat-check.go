//go:build ignore

// 030 data-chain check: Go recruit -> Go battle -> Go survivors -> disk/cold load.
// No emulator, original memory address, or original combat executor is used here.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"reflect"

	"github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

func combatCheck(err error) {
	if err != nil {
		panic(err)
	}
}
func combatSave(path string, value any) {
	raw, e := json.MarshalIndent(value, "", "  ")
	combatCheck(e)
	combatCheck(os.WriteFile(path, append(raw, '\n'), 0644))
}
func main() {
	catalog := flag.String("catalog", "", "army catalog")
	combat := flag.String("combat", "", "Go combat profiles")
	base := flag.String("base-save", "", "read-only real original save used only as a SHA binding")
	out := flag.String("out", "", "new output directory")
	load := flag.String("load", "", "fresh-process load of prior complete data chain")
	flag.Parse()
	if os.Getuid() != 1000 || *out == "" {
		panic("UID1000 and explicit output required")
	}
	if _, e := os.Stat(*out); !os.IsNotExist(e) {
		panic("output exists")
	}
	combatCheck(os.Mkdir(*out, 0755))
	raw, e := os.ReadFile(*catalog)
	combatCheck(e)
	var c ArmyCatalog
	combatCheck(strictJSON(raw, &c))
	raw, e = os.ReadFile(*combat)
	combatCheck(e)
	var battleCatalog eightsword.OwnedCombatCatalog
	combatCheck(strictJSON(raw, &battleCatalog))
	combatCheck(battleCatalog.Validate())
	if *load != "" {
		a, e := loadArmy(*load, c)
		combatCheck(e)
		raw, e = os.ReadFile(filepath.Join(*load, "battle-final.json"))
		combatCheck(e)
		s, e := eightsword.DecodeOwnedCombatState(raw)
		combatCheck(e)
		combatCheck(s.Validate(battleCatalog))
		if !s.Committed || s.Result != "win" {
			panic("battle result not saved")
		}
		for i, v := range a.Slots {
			if v.Count != s.Rows[0][i].Count || (v.Count > 0 && v.Unit != s.Rows[0][i].Unit) {
				panic("saved survivors differ")
			}
		}
		combatSave(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-owned-combat-cold-load", "army": a, "battle": s, "guest_instructions": 0, "player_path": false})
		fmt.Println("Cold process restored Go battle survivors, resources, stock and rules")
		return
	}
	a := OwnedArmy{Gold: 5000, Leadership: 1000, RecruitRank: 6, Rules: "tactics", Offers: map[string]ArmyOffer{"wolf-camp": {Unit: "openkb:wolf", Stock: 1000}}}
	a, hire, e := a.recruit(c, "wolf-camp", 30)
	combatCheck(e)
	armyRaw, e := json.Marshal(a)
	combatCheck(e)
	var rows [2][6]eightsword.OwnedCombatStack
	for i, u := range a.Slots {
		rows[0][i] = eightsword.OwnedCombatStack{Unit: u.Unit, Count: u.Count}
	}
	rows[1][0] = eightsword.OwnedCombatStack{Unit: "openkb:skel", Count: 15}
	s, e := eightsword.NewOwnedCombat(battleCatalog, rows, eightsword.OwnedCombatConfig{Rules: a.Rules, Divisors: [2]uint32{5, 5}, Multipliers: [2]uint32{1, 1}}, contentSHA(armyRaw))
	combatCheck(e)
	start := s
	var events []eightsword.OwnedCombatOutcome
	for s.Result == "" && s.Round < 100 {
		for _, side := range []int{1, 0} {
			if s.Result != "" {
				break
			}
			choice, e := s.Choose(battleCatalog, side, 0, "normal", 0, 0)
			combatCheck(e)
			next, event, e := s.Apply(battleCatalog, choice.Action)
			combatCheck(e)
			s = next
			events = append(events, event)
			if len(events) == 1 {
				combatSave(filepath.Join(*out, "battle-checkpoint.json"), s)
				raw, e := os.ReadFile(filepath.Join(*out, "battle-checkpoint.json"))
				combatCheck(e)
				restored, e := eightsword.DecodeOwnedCombatState(raw)
				combatCheck(e)
				if !reflect.DeepEqual(restored, s) {
					panic("battle checkpoint lost a count, ID or action flag")
				}
				s = restored
				if _, _, err := s.Apply(battleCatalog, choice.Action); err == nil {
					panic("restored action flag allowed duplicate damage")
				}
			}
		}
		if s.Result == "" {
			s, e = s.NextRound(battleCatalog)
			combatCheck(e)
		}
	}
	if s.Result != "win" || s.Rows[0][0].Count != 29 {
		panic("controlled Go battle did not finish with 29 wolves")
	}
	committed, survivors, e := s.Commit(battleCatalog, contentSHA(armyRaw))
	combatCheck(e)
	if _, _, err := committed.Commit(battleCatalog, contentSHA(armyRaw)); err == nil {
		panic("duplicate survivor writeback accepted")
	}
	for i, u := range survivors {
		a.Slots[i] = ArmyStack{Unit: u.Unit, Count: u.Count}
	}
	combatCheck(a.validate(c))
	original, e := os.ReadFile(*base)
	combatCheck(e)
	if len(original) != 2987 {
		panic("original base save length")
	}
	combatCheck(os.WriteFile(filepath.Join(*out, "gamedata.ay"), original, 0600))
	combatCheck(saveArmy(*out, c, a))
	loaded, e := loadArmy(*out, c)
	combatCheck(e)
	if !reflect.DeepEqual(a, loaded) {
		panic("postbattle save roundtrip differs")
	}
	combatSave(filepath.Join(*out, "battle-final.json"), committed)
	strength, e := committed.Strength(battleCatalog, 0)
	combatCheck(e)
	combatSave(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-go-owned-combat-data-chain", "player_path": false, "production_combat_core": true, "guest_instructions": 0, "initial": start, "hire": hire, "events": events, "army": a, "battle": committed, "strength": strength, "original_sha256": contentSHA(original), "limits": []string{"Controlled economy and combat; no normal recruitment/battle UI handoff claim.", "OpenKB reference stats are disposable examples; abilities are inactive.", "No DOS combat or original fixed table handles the extended unit IDs.", "World rewards, all spells, accumulated injury display and complete save lifecycle are not integrated."}})
	fmt.Println("Go recruit/battle/survivors/save complete:", len(events), "actions; 30 -> 29 wolves; no DOS combat calls")
}
