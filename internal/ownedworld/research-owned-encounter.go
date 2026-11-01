// 030 DRAFT: typed world enemy persistence, separate random/guard rewards.
package ownedworld

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"os"
	"path/filepath"
	"strings"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

type EncounterContext struct {
	Kind             string  `json:"kind"`
	Region           uint16  `json:"region"`
	Index            uint16  `json:"index"`
	Legacy26AA       uint16  `json:"legacy_26aa"`
	Boss             bool    `json:"boss"`
	EndingGuardAlive bool    `json:"ending_guard_alive"`
	Pieces           [8]bool `json:"pieces"`
}
type EncounterResult struct {
	Persistent   bool              `json:"persistent"`
	EnemyRows    [6]ArmyStack      `json:"enemy_rows"`
	Cleared      bool              `json:"cleared"`
	Pieces       [8]bool           `json:"pieces"`
	RandomReward WorldReward       `json:"random_reward"`
	GuardGain    [2]uint64         `json:"guard_gain"`
	Defeat       *DefeatResolution `json:"defeat"`
	WorldHandoff string            `json:"world_handoff"`
}
type EncounterSession struct {
	Schema  string           `json:"schema"`
	Before  OwnedWorld       `json:"before"`
	After   OwnedWorld       `json:"after"`
	Context EncounterContext `json:"context"`
	Input   DefeatInput      `json:"input"`
	Result  EncounterResult  `json:"result"`
}

func (w OwnedWorld) resolveEncounter(c ArmyCatalog, cc game.OwnedCombatCatalog, ctx EncounterContext, input DefeatInput) (EncounterSession, error) {
	var empty EncounterSession
	if err := w.validate(c, cc); err != nil {
		return empty, err
	}
	if w.Battle == nil || w.Revision == math.MaxUint64 {
		return empty, errors.New("no pending encounter")
	}
	id := w.Battle.Encounter
	switch ctx.Kind {
	case "random":
		if !strings.HasPrefix(id, "random:") || ctx.Region != 0 || ctx.Index != 0 || ctx.Boss || ctx.Legacy26AA != 0 || ctx.EndingGuardAlive {
			return empty, errors.New("random context shape")
		}
	case "guarded":
		if ctx.Region > 7 || ctx.Index > 11 || id != fmt.Sprintf("guarded:%02d:%02d", ctx.Region, ctx.Index) || !ctx.EndingGuardAlive {
			return empty, errors.New("guard identity or unresolved ending gate")
		}
	default:
		return empty, errors.New("unknown encounter source")
	}
	state := w.Battle.State
	if state.Result == "draw" {
		return empty, errors.New("draw world contract unresolved")
	}
	result := EncounterResult{Persistent: ctx.Kind == "guarded", EnemyRows: compactExitRows(state.Rows[1]), Pieces: ctx.Pieces, WorldHandoff: "pending"}
	next := w
	if ctx.Kind == "random" {
		if state.Result == "win" {
			if input.Reason != "" || input.Random != nil || input.Choice != "" || input.Origin != nil {
				return empty, errors.New("victory has no defeat input")
			}
			var err error
			next, result.RandomReward, err = w.settleVictory(c, cc)
			if err != nil {
				return empty, err
			}
		} else {
			s, err := w.resolveDefeat(c, cc, input)
			if err != nil {
				return empty, err
			}
			next = s.After
			result.Defeat = &s.Resolution
		}
	} else {
		next.Battle = nil
		next.Revision++
		next.Army.Slots = compactExitRows(state.Rows[0])
		if state.Result == "win" {
			if input.Reason != "" || input.Random != nil || input.Choice != "" || input.Origin != nil {
				return empty, errors.New("guard victory has no defeat input")
			}
			if _, _, err := state.Commit(cc, worldDigest(w.Army)); err != nil {
				return empty, err
			}
			next.Progress.Legacy04F6 = min(uint64(30000), w.Progress.Legacy04F6+20*(uint64(ctx.Region)+1))
			result.GuardGain[0] = next.Progress.Legacy04F6 - w.Progress.Legacy04F6
			if ctx.Legacy26AA == 1 {
				next.Progress.Legacy04FC = min(uint64(30000), w.Progress.Legacy04FC+uint64(ctx.Region)+1)
				result.GuardGain[1] = next.Progress.Legacy04FC - w.Progress.Legacy04FC
			}
			if ctx.Boss {
				result.Pieces[ctx.Region] = true
			}
		} else {
			d := DefeatResolution{EnemySurvivors: result.EnemyRows, WorldHandoff: "pending"}
			if next.Army.Slots[0].Count > 0 {
				if state.Result != "" || input.Reason != "retreat" || input.Random == nil || input.Choice != "" || input.Origin != nil {
					return empty, errors.New("guard retreat input")
				}
				lost, err := retreatPenalty(w.Army.Gold, *input.Random)
				if err != nil {
					return empty, err
				}
				d.GoldLost = lost
				next.Army.Gold -= lost
			} else {
				if state.Result != "loss" || input.Reason != "annihilation" || input.Random != nil {
					return empty, errors.New("guard annihilation input")
				}
				switch input.Choice {
				case "roam":
					if input.Origin != nil {
						return empty, errors.New("roaming destination")
					}
				case "return-origin":
					if input.Origin == nil || input.Origin.Region != "native:00" || input.Origin.Facing != 3 {
						return empty, errors.New("verified origin needed")
					}
					v := *input.Origin
					d.NextOrigin = &v
				default:
					return empty, errors.New("explicit loss choice required")
				}
			}
			// sub_11ABE never reaches sub_11796's rank promotion gate.
			result.Defeat = &d
		}
	}
	// Map cloning prevents commit plans from mutating the pre-battle record.
	next.Encounters = make(map[string]WorldEncounter, len(next.Encounters))
	for key, v := range w.Encounters {
		next.Encounters[key] = v
	}
	if ctx.Kind == "random" {
		delete(next.Encounters, id)
	} else {
		record := next.Encounters[id]
		result.Cleared = state.Result == "win"
		record.Cleared = result.Cleared
		if !result.Cleared {
			record.Enemy = result.EnemyRows
		}
		// Cleared records retain the original enemy as historical data. EnemyRows
		// is the authoritative empty current roster; Cleared prevents re-entry.
		next.Encounters[id] = record
	}
	if err := next.validate(c, cc); err != nil {
		return empty, err
	}
	session := EncounterSession{Schema: "eightsword-owned-encounter-session/1", Before: w, After: next, Context: ctx, Input: input, Result: result}
	raw, err := json.Marshal(session)
	if err != nil {
		return empty, err
	}
	var detached EncounterSession
	if err = strictJSON(raw, &detached); err != nil {
		return empty, err
	}
	return detached, nil
}

func (s EncounterSession) validate(c ArmyCatalog, cc game.OwnedCombatCatalog) error {
	if s.Schema != "eightsword-owned-encounter-session/1" {
		return errors.New("encounter session schema")
	}
	expected, err := s.Before.resolveEncounter(c, cc, s.Context, s.Input)
	if err != nil {
		return err
	}
	if worldDigest(s.After) != worldDigest(expected.After) || worldDigest(s.Result) != worldDigest(expected.Result) {
		return errors.New("changed encounter transition")
	}
	return nil
}

type EncounterSave struct {
	Schema           string           `json:"schema"`
	OriginalSHA      string           `json:"original_sha256"`
	ArmyCatalogSHA   string           `json:"army_catalog_sha256"`
	CombatCatalogSHA string           `json:"combat_catalog_sha256"`
	Session          EncounterSession `json:"session"`
}

func saveEncounter(dir string, c ArmyCatalog, cc game.OwnedCombatCatalog, s EncounterSession, expectedSHA string) error {
	if err := s.validate(c, cc); err != nil {
		return err
	}
	basePath := filepath.Join(dir, "gamedata.ay")
	base, err := os.ReadFile(basePath)
	if err != nil {
		return err
	}
	if len(base) != 2987 {
		return errors.New("original save length")
	}
	lock := filepath.Join(dir, ".owned-world.lock")
	if err = os.Mkdir(lock, 0700); err != nil {
		return errors.New("encounter save locked")
	}
	defer os.Remove(lock)
	target := filepath.Join(dir, "gamedata.ay.army.json")
	if old, e := os.ReadFile(target); e == nil {
		if expectedSHA == "" || contentSHA(old) != expectedSHA {
			return errors.New("stale encounter writer")
		}
		var header struct {
			Schema string `json:"schema"`
		}
		if json.Unmarshal(old, &header) != nil || header.Schema != "eightsword-owned-encounter-save/1" {
			return errors.New("other save schema")
		}
	} else if !os.IsNotExist(e) {
		return e
	} else if expectedSHA != "" {
		return errors.New("previous save disappeared")
	}
	raw, err := json.MarshalIndent(EncounterSave{Schema: "eightsword-owned-encounter-save/1", OriginalSHA: contentSHA(base), ArmyCatalogSHA: c.digest(), CombatCatalogSHA: cc.Digest(), Session: s}, "", "  ")
	if err != nil {
		return err
	}
	if len(raw) > 1<<20 {
		return errors.New("encounter save size")
	}
	f, err := os.CreateTemp(dir, ".owned-encounter-*.tmp")
	if err != nil {
		return err
	}
	name := f.Name()
	defer os.Remove(name)
	if _, err = f.Write(append(raw, '\n')); err == nil {
		err = f.Sync()
	}
	ce := f.Close()
	if err != nil {
		return err
	}
	if ce != nil {
		return ce
	}
	current, err := os.ReadFile(basePath)
	if err != nil {
		return err
	}
	if !bytes.Equal(current, base) {
		return errors.New("original save changed")
	}
	if err = os.Rename(name, target); err != nil {
		return err
	}
	d, err := os.Open(dir)
	if err != nil {
		return err
	}
	defer d.Close()
	return d.Sync()
}
func loadEncounter(dir string, c ArmyCatalog, cc game.OwnedCombatCatalog) (EncounterSession, error) {
	var empty EncounterSession
	f, err := os.Open(filepath.Join(dir, "gamedata.ay.army.json"))
	if err != nil {
		return empty, err
	}
	defer f.Close()
	st, err := f.Stat()
	if err != nil {
		return empty, err
	}
	if !st.Mode().IsRegular() || st.Size() > 1<<20 {
		return empty, errors.New("encounter save type/size")
	}
	raw, err := io.ReadAll(io.LimitReader(f, (1<<20)+1))
	if err != nil {
		return empty, err
	}
	if err = boundedDefeatJSON(raw); err != nil {
		return empty, err
	}
	var saved EncounterSave
	if err = strictJSON(raw, &saved); err != nil {
		return empty, err
	}
	var wire struct {
		Session map[string]json.RawMessage `json:"session"`
	}
	if err = json.Unmarshal(raw, &wire); err != nil {
		return empty, err
	}
	for _, key := range []string{"before", "after"} {
		if err = decodeDefeatWorld(wire.Session[key]); err != nil {
			return empty, err
		}
	}
	ctx := wire.Session["context"]
	if err = requiredDefeatFields(ctx, []string{"kind", "region", "index", "legacy_26aa", "boss", "ending_guard_alive", "pieces"}, nil); err != nil {
		return empty, err
	}
	res := wire.Session["result"]
	if err = requiredDefeatFields(res, []string{"persistent", "enemy_rows", "cleared", "pieces", "random_reward", "guard_gain", "defeat", "world_handoff"}, map[string]bool{"defeat": true}); err != nil {
		return empty, err
	}
	if err = requiredDefeatFields(wire.Session["input"], []string{"reason", "random", "choice", "origin"}, map[string]bool{"random": true, "origin": true}); err != nil {
		return empty, err
	}
	for _, item := range []struct {
		raw  json.RawMessage
		key  string
		size int
	}{{ctx, "pieces", 8}, {res, "pieces", 8}, {res, "enemy_rows", 6}, {res, "guard_gain", 2}} {
		var obj map[string]json.RawMessage
		json.Unmarshal(item.raw, &obj)
		var cells []json.RawMessage
		if json.Unmarshal(obj[item.key], &cells) != nil || len(cells) != item.size {
			return empty, errors.New("encounter array shape")
		}
		for _, v := range cells {
			if bytes.Equal(bytes.TrimSpace(v), []byte("null")) {
				return empty, errors.New("null encounter cell")
			}
		}
	}
	// Validate nullable sub-records explicitly rather than letting absent zero
	// values silently become a legitimate no-reward or no-destination result.
	var resultFields, inputFields map[string]json.RawMessage
	json.Unmarshal(res, &resultFields)
	json.Unmarshal(wire.Session["input"], &inputFields)
	if err = requiredDefeatFields(resultFields["random_reward"], []string{"gold", "merit", "promoted"}, nil); err != nil {
		return empty, err
	}
	if !bytes.Equal(bytes.TrimSpace(inputFields["origin"]), []byte("null")) {
		if err = requiredDefeatFields(inputFields["origin"], []string{"region", "x", "y", "facing"}, nil); err != nil {
			return empty, err
		}
	}
	if !bytes.Equal(bytes.TrimSpace(resultFields["defeat"]), []byte("null")) {
		if err = requiredDefeatFields(resultFields["defeat"], []string{"gold_lost", "promoted", "enemy_survivors", "next_origin", "world_handoff"}, map[string]bool{"next_origin": true}); err != nil {
			return empty, err
		}
		var d map[string]json.RawMessage
		json.Unmarshal(resultFields["defeat"], &d)
		var enemy []ArmyStack
		if json.Unmarshal(d["enemy_survivors"], &enemy) != nil || len(enemy) != 6 {
			return empty, errors.New("defeat enemy shape")
		}
		if !bytes.Equal(bytes.TrimSpace(d["next_origin"]), []byte("null")) {
			if err = requiredDefeatFields(d["next_origin"], []string{"region", "x", "y", "facing"}, nil); err != nil {
				return empty, err
			}
		}
	}
	base, err := os.ReadFile(filepath.Join(dir, "gamedata.ay"))
	if err != nil {
		return empty, err
	}
	if len(base) != 2987 || saved.Schema != "eightsword-owned-encounter-save/1" || saved.OriginalSHA != contentSHA(base) || saved.ArmyCatalogSHA != c.digest() || saved.CombatCatalogSHA != cc.Digest() {
		return empty, errors.New("encounter save binding")
	}
	if err = saved.Session.validate(c, cc); err != nil {
		return empty, err
	}
	return saved.Session, nil
}
