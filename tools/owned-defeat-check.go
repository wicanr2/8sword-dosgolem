//go:build ignore

// 030 DRAFT: actual Go combat -> defeat plan -> atomic save -> cold process.
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

func mustDefeat(e error) {
	if e != nil {
		panic(e)
	}
}
func writeDefeat(p string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	mustDefeat(e)
	mustDefeat(os.WriteFile(p, append(b, '\n'), 0600))
}
func main() {
	catalog := flag.String("catalog", "", "army catalog")
	combat := flag.String("combat", "", "combat catalog")
	controls := flag.String("controls", "", "recorded original controls")
	base := flag.String("base-save", "", "original 2987-byte save")
	out := flag.String("out", "", "new output")
	load := flag.String("load", "", "optional cold defeat save")
	flag.Parse()
	if os.Getuid() != 1000 || *out == "" {
		panic("explicit paths and UID1000")
	}
	if _, e := os.Stat(*out); !os.IsNotExist(e) {
		panic("output exists")
	}
	mustDefeat(os.Mkdir(*out, 0755))
	var c ArmyCatalog
	raw, e := os.ReadFile(*catalog)
	mustDefeat(e)
	mustDefeat(strictJSON(raw, &c))
	var cc game.OwnedCombatCatalog
	raw, e = os.ReadFile(*combat)
	mustDefeat(e)
	mustDefeat(strictJSON(raw, &cc))
	if *load != "" {
		session, err := loadDefeat(*load, c, cc)
		mustDefeat(err)
		writeDefeat(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-defeat-cold-load", "session": session, "player_path": false})
		return
	}
	var native struct {
		Rows []struct {
			Before struct {
				Origin []uint16 `json:"origin"`
			}
		} `json:"rows"`
	}
	raw, e = os.ReadFile(*controls)
	mustDefeat(e)
	mustDefeat(json.Unmarshal(raw, &native))
	if len(native.Rows) != 12 || len(native.Rows[0].Before.Origin) != 2 {
		panic("native source shape")
	}
	rows := []map[string]any{}
	for _, name := range []string{"retreat", "return-origin", "roam"} {
		count := uint32(30)
		enemy := ArmyStack{Unit: "openkb:skel", Count: 15}
		if name != "retreat" {
			count = 2
			enemy = ArmyStack{Unit: "openkb:drag", Count: 1}
		}
		army := OwnedArmy{Gold: 5000, Leadership: 1000, RecruitRank: 1, Rules: "tactics", Offers: map[string]ArmyOffer{"wolf-camp": {Unit: "openkb:wolf", Stock: 1000}}}
		army, _, e = army.recruit(c, "wolf-camp", count)
		mustDefeat(e)
		world := OwnedWorld{Schema: "eightsword-owned-world/1", Army: army, Progress: WorldProgress{Rank: 1, Thresholds: [6]uint64{0, 2000, 5000, 8000, 12000, 30000}}, Encounters: map[string]WorldEncounter{"enemy": {Enemy: [6]ArmyStack{enemy}}}}
		world, e = world.begin(c, cc, "enemy", game.OwnedCombatConfig{Rules: "tactics", Divisors: [2]uint32{5, 5}, Multipliers: [2]uint32{1, 1}})
		mustDefeat(e)
		decision, err := world.Battle.State.Choose(cc, 1, 0, "normal", 0, 0)
		mustDefeat(err)
		state, hit, err := world.Battle.State.Apply(cc, decision.Action)
		mustDefeat(err)
		world.Battle = &WorldBattle{Encounter: world.Battle.Encounter, StartSHA: world.Battle.StartSHA, State: state}
		input := DefeatInput{Reason: "annihilation", Choice: name}
		if name == "retreat" {
			random := uint32(2730)
			input = DefeatInput{Reason: "retreat", Random: &random}
		} else if name == "return-origin" {
			input.Origin = &DefeatOrigin{Region: "native:00", X: native.Rows[0].Before.Origin[0], Y: native.Rows[0].Before.Origin[1], Facing: 3}
		}
		session, err := world.resolveDefeat(c, cc, input)
		mustDefeat(err)
		if name == "retreat" {
			if session.After.Army.Slots[0].Count != 29 || session.After.Army.Gold != 2850 || session.Resolution.GoldLost != 950 {
				panic("retreat result")
			}
		} else if session.After.Army.Slots[0].Count != 0 || session.After.Army.Gold != 4920 || session.Resolution.GoldLost != 0 {
			panic("annihilation result")
		}
		if session.After.Battle != nil || session.After.Encounters["enemy"].Cleared || session.Resolution.WorldHandoff != "pending" {
			panic("incorrect handoff state")
		}
		if _, err = session.After.resolveDefeat(c, cc, input); err == nil {
			panic("duplicate defeat")
		}
		dir := filepath.Join(*out, name)
		mustDefeat(os.Mkdir(dir, 0700))
		raw, e = os.ReadFile(*base)
		mustDefeat(e)
		originalSHA := contentSHA(raw)
		mustDefeat(os.WriteFile(filepath.Join(dir, "gamedata.ay"), raw, 0600))
		mustDefeat(saveDefeat(dir, c, cc, session, ""))
		if err = saveDefeat(dir, c, cc, session, ""); err == nil {
			panic("stale defeat writer")
		}
		loaded, err := loadDefeat(dir, c, cc)
		mustDefeat(err)
		if !reflect.DeepEqual(loaded, session) {
			panic("defeat round trip")
		}
		if _, err = loadWorld(dir, c, cc); err == nil {
			panic("old loader discarded pending defeat")
		}
		if engine, err := game.Open(game.Options{Root: "/unmounted-original", Saves: dir, HD: true}); engine != nil || !errors.Is(err, game.ErrOwnedArmyHandoffPending) {
			panic("Engine did not guard defeat save")
		}
		raw, e = os.ReadFile(filepath.Join(dir, "gamedata.ay"))
		mustDefeat(e)
		if contentSHA(raw) != originalSHA {
			panic("base save changed")
		}
		rows = append(rows, map[string]any{"name": name, "hit": hit, "session": session, "original_sha256": originalSHA, "engine_guard": true})
	}
	writeDefeat(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-go-defeat-transitions", "rows": rows, "guest_instructions": 0, "player_path": false, "limits": []string{"Explicit Go combat fixtures; new-unit balance provisional.", "The complete pending world transition is saved; original map handoff and formal UI remain unconnected.", "Enemy survivors are returned as typed data; random/guarded encounter persistence is not guessed."}})
	fmt.Println("Go retreat and both annihilation choices passed; pending world state saved without DOS")
}
