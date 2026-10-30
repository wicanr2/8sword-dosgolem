//go:build ignore

// 030 DRAFT: Go combat, source-specific world update and one atomic save.
package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"os"
	"path/filepath"
	"reflect"
	"strings"
)

func mustEncounter(err error) {
	if err != nil {
		panic(err)
	}
}
func writeEncounter(path string, v any) {
	raw, e := json.MarshalIndent(v, "", "  ")
	mustEncounter(e)
	f, e := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	mustEncounter(e)
	_, e = f.Write(append(raw, '\n'))
	mustEncounter(e)
	mustEncounter(f.Close())
}
func newEncounterFixture(c ArmyCatalog, cc game.OwnedCombatCatalog, guarded, loss bool) (OwnedWorld, EncounterContext, error) {
	count := uint32(30)
	enemy := ArmyStack{Unit: "openkb:skel", Count: 15}
	if loss {
		count = 2
		enemy = ArmyStack{Unit: "openkb:drag", Count: 1}
	}
	army := OwnedArmy{Gold: 5000, Leadership: 1000, RecruitRank: 1, Rules: "tactics", Offers: map[string]ArmyOffer{"wolf-camp": {Unit: "openkb:wolf", Stock: 1000}}}
	var err error
	army, _, err = army.recruit(c, "wolf-camp", count)
	if err != nil {
		return OwnedWorld{}, EncounterContext{}, err
	}
	id := "random:sample"
	ctx := EncounterContext{Kind: "random"}
	if guarded {
		id = "guarded:01:00"
		ctx = EncounterContext{Kind: "guarded", Region: 1, EndingGuardAlive: true}
	}
	w := OwnedWorld{Schema: "eightsword-owned-world/1", Army: army, Progress: WorldProgress{Rank: 1, Merit: 10000, Legacy04F6: 100, Legacy04FC: 10, Thresholds: [6]uint64{0, 2000, 5000, 8000, 12000, 30000}}, Encounters: map[string]WorldEncounter{id: {Enemy: [6]ArmyStack{enemy}}, "guarded:07:03": {Enemy: [6]ArmyStack{{Unit: "native:01", Count: 1}}}}}
	w, err = w.begin(c, cc, id, game.OwnedCombatConfig{Rules: "tactics", Divisors: [2]uint32{5, 5}, Multipliers: [2]uint32{1, 1}})
	return w, ctx, err
}
func main() {
	army := flag.String("catalog", "", "army catalog")
	combat := flag.String("combat", "", "combat catalog")
	base := flag.String("base-save", "", "base original save")
	out := flag.String("out", "", "new output")
	load := flag.String("load", "", "optional cold load")
	flag.Parse()
	if os.Getuid() != 1000 || *out == "" {
		panic("explicit paths and UID1000")
	}
	if _, e := os.Stat(*out); !os.IsNotExist(e) {
		panic("output exists")
	}
	mustEncounter(os.Mkdir(*out, 0755))
	var c ArmyCatalog
	raw, e := os.ReadFile(*army)
	mustEncounter(e)
	mustEncounter(strictJSON(raw, &c))
	var cc game.OwnedCombatCatalog
	raw, e = os.ReadFile(*combat)
	mustEncounter(e)
	mustEncounter(strictJSON(raw, &cc))
	if *load != "" {
		s, e := loadEncounter(*load, c, cc)
		mustEncounter(e)
		writeEncounter(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-encounter-cold-load", "session": s})
		return
	}
	var rows []map[string]any
	for _, name := range []string{"random-victory", "guarded-victory", "random-retreat", "guarded-retreat", "guarded-loss", "guarded-boss-victory"} {
		guarded := strings.HasPrefix(name, "guarded")
		loss := name == "guarded-loss"
		victory := strings.HasSuffix(name, "victory")
		w, ctx, err := newEncounterFixture(c, cc, guarded, loss)
		mustEncounter(err)
		if name == "guarded-boss-victory" {
			ctx.Boss = true
			ctx.Legacy26AA = 1
		}
		var events []any
		for w.Battle.State.Result == "" && w.Battle.State.Round < 40 {
			for _, side := range []int{1, 0} {
				if w.Battle.State.Result != "" {
					break
				}
				decision, err := w.Battle.State.Choose(cc, side, 0, "normal", 0, 0)
				mustEncounter(err)
				state, event, err := w.Battle.State.Apply(cc, decision.Action)
				mustEncounter(err)
				w.Battle = &WorldBattle{Encounter: w.Battle.Encounter, StartSHA: w.Battle.StartSHA, State: state}
				events = append(events, event)
				if !victory {
					break
				}
			}
			if !victory {
				break
			}
			if w.Battle.State.Result == "" {
				state, err := w.Battle.State.NextRound(cc)
				mustEncounter(err)
				w.Battle = &WorldBattle{Encounter: w.Battle.Encounter, StartSHA: w.Battle.StartSHA, State: state}
			}
		}
		in := DefeatInput{}
		if !victory {
			random := uint32(2730)
			in = DefeatInput{Reason: "retreat", Random: &random}
			if loss {
				in = DefeatInput{Reason: "annihilation", Choice: "roam"}
			}
		}
		s, err := w.resolveEncounter(c, cc, ctx, in)
		mustEncounter(err)
		if !reflect.DeepEqual(s.After.Encounters["guarded:07:03"], w.Encounters["guarded:07:03"]) {
			panic("neighbor changed")
		}
		if _, err = s.After.resolveEncounter(c, cc, ctx, in); err == nil {
			panic("duplicate encounter commit")
		}
		dir := filepath.Join(*out, name)
		mustEncounter(os.Mkdir(dir, 0700))
		raw, e = os.ReadFile(*base)
		mustEncounter(e)
		baseSHA := contentSHA(raw)
		mustEncounter(os.WriteFile(filepath.Join(dir, "gamedata.ay"), raw, 0600))
		mustEncounter(saveEncounter(dir, c, cc, s, ""))
		loaded, err := loadEncounter(dir, c, cc)
		mustEncounter(err)
		if !reflect.DeepEqual(loaded, s) {
			panic("round trip")
		}
		if err = saveEncounter(dir, c, cc, s, ""); err == nil {
			panic("stale writer")
		}
		if _, err = loadWorld(dir, c, cc); err == nil {
			panic("old world loader accepted")
		}
		if _, err = loadDefeat(dir, c, cc); err == nil {
			panic("old defeat loader accepted")
		}
		if engine, err := game.Open(game.Options{Root: "/unmounted-original", Saves: dir, HD: true}); engine != nil || !errors.Is(err, game.ErrOwnedArmyHandoffPending) {
			panic("DOS guard")
		}
		raw, e = os.ReadFile(filepath.Join(dir, "gamedata.ay"))
		mustEncounter(e)
		if contentSHA(raw) != baseSHA {
			panic("original save changed")
		}
		rows = append(rows, map[string]any{"name": name, "session": s, "events": events, "original_sha256": baseSHA, "engine_guard": true})
	}
	writeEncounter(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-go-encounter-chain", "rows": rows, "guest_instructions": 0, "player_path": false, "limits": []string{"DRAFT typed world transition; no normal player UI or map handoff.", "Legacy04F6 is monthly pay and Legacy04FC is spell ability; serialized offset names are retained. Legacy26AA meaning remains unknown.", "Ending guard transitions are rejected; pending map and quest commands are saved together.", "Expanded unit IDs remain entirely in Go; no native array writeback."}})
	fmt.Println("six Go source-specific encounter chains passed")
}
