// Spec 030 DRAFT: typed Go retreat/annihilation transition, no DOS memory access.
package ownedworld

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"math"
	"os"
	"path/filepath"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

type DefeatOrigin struct {
	Region string `json:"region"`
	X      uint16 `json:"x"`
	Y      uint16 `json:"y"`
	Facing uint8  `json:"facing"`
}
type DefeatInput struct {
	Reason string        `json:"reason"`
	Random *uint32       `json:"random"`
	Choice string        `json:"choice"`
	Origin *DefeatOrigin `json:"origin"`
}
type DefeatResolution struct {
	GoldLost       uint64        `json:"gold_lost"`
	Promoted       bool          `json:"promoted"`
	EnemySurvivors [6]ArmyStack  `json:"enemy_survivors"`
	NextOrigin     *DefeatOrigin `json:"next_origin"`
	WorldHandoff   string        `json:"world_handoff"`
}
type DefeatSession struct {
	Schema     string           `json:"schema"`
	Before     OwnedWorld       `json:"before"`
	After      OwnedWorld       `json:"after"`
	Input      DefeatInput      `json:"input"`
	Resolution DefeatResolution `json:"resolution"`
}

func retreatPenalty(gold uint64, random uint32) (uint64, error) {
	if random > 32767 {
		return 0, errors.New("random input outside original nonnegative 15-bit domain")
	}
	return gold / (uint64(random)/2730 + 3), nil
}
func compactExitRows(row [6]game.OwnedCombatStack) [6]ArmyStack {
	var result [6]ArmyStack
	j := 0
	for _, v := range row {
		if v.Count > 0 {
			result[j] = ArmyStack{Unit: v.Unit, Count: v.Count}
			j++
		}
	}
	return result
}
func (w OwnedWorld) resolveDefeat(c ArmyCatalog, combat game.OwnedCombatCatalog, in DefeatInput) (DefeatSession, error) {
	var empty DefeatSession
	if err := w.validate(c, combat); err != nil {
		return empty, err
	}
	if w.Battle == nil || w.Revision == math.MaxUint64 || w.Battle.State.Committed {
		return empty, errors.New("no pending battle")
	}
	state := w.Battle.State
	if state.Result == "win" || state.Result == "draw" {
		return empty, errors.New("victory/draw cannot enter defeat transition")
	}
	next := w
	next.Battle = nil
	next.Revision++
	next.Army.Slots = compactExitRows(state.Rows[0])
	result := DefeatResolution{EnemySurvivors: compactExitRows(state.Rows[1]), WorldHandoff: "pending"}
	alive := next.Army.Slots[0].Count > 0
	if alive {
		if in.Reason != "retreat" || in.Random == nil || in.Choice != "" || in.Origin != nil || state.Result != "" {
			return empty, errors.New("retreat requires one random input and surviving army")
		}
		lost, err := retreatPenalty(w.Army.Gold, *in.Random)
		if err != nil {
			return empty, err
		}
		result.GoldLost = lost
		next.Army.Gold -= lost
	} else {
		if in.Reason != "annihilation" || in.Random != nil || state.Result != "loss" {
			return empty, errors.New("annihilation requires an actual loss and no random input")
		}
		switch in.Choice {
		case "return-origin":
			if in.Origin == nil || in.Origin.Region != "native:00" || in.Origin.Facing != 3 {
				return empty, errors.New("verified original start destination required")
			}
			destination := *in.Origin
			result.NextOrigin = &destination
		case "roam":
			if in.Origin != nil {
				return empty, errors.New("roaming preserves the current destination")
			}
		default:
			return empty, errors.New("explicit annihilation choice required")
		}
	}
	// sub_11796 shares its promotion gate with surviving retreat. Both
	// annihilation choices return before it, even with merit above the threshold.
	if alive && next.Progress.Rank < 5 && next.Progress.Merit > next.Progress.Thresholds[next.Progress.Rank] {
		next.Progress.Rank++
		next.Army.RecruitRank = next.Progress.Rank
		result.Promoted = true
		next.Progress.Legacy04F6 = min(uint64(30000), next.Progress.Legacy04F6+100)
		next.Army.Leadership = min(uint64(30000), next.Army.Leadership+100)
		next.Progress.Legacy04FC = min(uint64(30000), next.Progress.Legacy04FC+uint64(next.Progress.Rank)*3)
	}
	if err := next.validate(c, combat); err != nil {
		return empty, err
	}
	session := DefeatSession{Schema: "eightsword-owned-defeat-session/1", Before: w, After: next, Input: in, Resolution: result}
	raw, err := json.Marshal(session)
	if err != nil {
		return empty, err
	}
	var detached DefeatSession
	if err = strictJSON(raw, &detached); err != nil {
		return empty, err
	}
	return detached, nil
}
func (s DefeatSession) validate(c ArmyCatalog, cc game.OwnedCombatCatalog) error {
	if s.Schema != "eightsword-owned-defeat-session/1" {
		return errors.New("defeat session schema")
	}
	expected, err := s.Before.resolveDefeat(c, cc, s.Input)
	if err != nil {
		return err
	}
	if worldDigest(s.After) != worldDigest(expected.After) || worldDigest(s.Resolution) != worldDigest(expected.Resolution) {
		return errors.New("defeat session result changed")
	}
	return nil
}

type DefeatSave struct {
	Schema           string        `json:"schema"`
	OriginalSHA      string        `json:"original_sha256"`
	ArmyCatalogSHA   string        `json:"army_catalog_sha256"`
	CombatCatalogSHA string        `json:"combat_catalog_sha256"`
	Session          DefeatSession `json:"session"`
}

// The complete before/after transition and its pending world command form one
// atomic record. Existing world-save/1 is never silently overwritten or read.
func saveDefeat(dir string, c ArmyCatalog, cc game.OwnedCombatCatalog, s DefeatSession, expectedSHA string) error {
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
		return errors.New("defeat save locked")
	}
	defer os.Remove(lock)
	target := filepath.Join(dir, "gamedata.ay.army.json")
	if previous, e := os.ReadFile(target); e == nil {
		if expectedSHA == "" || contentSHA(previous) != expectedSHA {
			return errors.New("stale defeat writer")
		}
		var shape struct {
			Schema string `json:"schema"`
		}
		if json.Unmarshal(previous, &shape) != nil || shape.Schema != "eightsword-owned-world-defeat/1" {
			return errors.New("refuse overwrite of another save schema")
		}
	} else if !os.IsNotExist(e) {
		return e
	} else if expectedSHA != "" {
		return errors.New("defeat save disappeared")
	}
	envelope := DefeatSave{Schema: "eightsword-owned-world-defeat/1", OriginalSHA: contentSHA(base), ArmyCatalogSHA: c.digest(), CombatCatalogSHA: cc.Digest(), Session: s}
	raw, err := json.MarshalIndent(envelope, "", "  ")
	if err != nil {
		return err
	}
	if len(raw) > 1<<20 {
		return errors.New("defeat save size")
	}
	f, err := os.CreateTemp(dir, ".owned-defeat-*.tmp")
	if err != nil {
		return err
	}
	name := f.Name()
	defer os.Remove(name)
	if _, err = f.Write(append(raw, '\n')); err == nil {
		err = f.Sync()
	}
	closeErr := f.Close()
	if err != nil {
		return err
	}
	if closeErr != nil {
		return closeErr
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
	directory, err := os.Open(dir)
	if err != nil {
		return err
	}
	defer directory.Close()
	return directory.Sync()
}
func boundedDefeatJSON(raw []byte) error {
	if len(raw) > 1<<20 {
		return errors.New("defeat JSON size")
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	depth := 0
	for {
		v, err := decoder.Token()
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}
		if d, ok := v.(json.Delim); ok {
			switch d {
			case '{', '[':
				depth++
				if depth > 32 {
					return errors.New("defeat JSON nesting")
				}
			case '}', ']':
				depth--
			}
		}
	}
	return nil
}
func requiredDefeatFields(raw json.RawMessage, fields []string, nullable map[string]bool) error {
	var object map[string]json.RawMessage
	if err := json.Unmarshal(raw, &object); err != nil {
		return err
	}
	for _, key := range fields {
		value, ok := object[key]
		if !ok || (!nullable[key] && bytes.Equal(bytes.TrimSpace(value), []byte("null"))) {
			return errors.New("missing defeat field " + key)
		}
	}
	return nil
}
func decodeDefeatWorld(raw json.RawMessage) error {
	if err := requiredDefeatFields(raw, []string{"schema", "revision", "army", "progress", "encounters", "battle"}, map[string]bool{"battle": true}); err != nil {
		return err
	}
	var object map[string]json.RawMessage
	json.Unmarshal(raw, &object)
	if err := requiredDefeatFields(object["progress"], []string{"rank", "merit", "legacy_04f6", "legacy_04fc", "thresholds"}, nil); err != nil {
		return err
	}
	var progress map[string]json.RawMessage
	json.Unmarshal(object["progress"], &progress)
	var cells []json.RawMessage
	if err := json.Unmarshal(progress["thresholds"], &cells); err != nil || len(cells) != 6 {
		return errors.New("defeat threshold shape")
	}
	for _, cell := range cells {
		if bytes.Equal(bytes.TrimSpace(cell), []byte("null")) {
			return errors.New("null defeat threshold")
		}
	}
	return nil
}
func loadDefeat(dir string, c ArmyCatalog, cc game.OwnedCombatCatalog) (DefeatSession, error) {
	var empty DefeatSession
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
		return empty, errors.New("defeat save type/size")
	}
	raw, err := io.ReadAll(io.LimitReader(f, (1<<20)+1))
	if err != nil {
		return empty, err
	}
	if err = boundedDefeatJSON(raw); err != nil {
		return empty, err
	}
	var saved DefeatSave
	if err = strictJSON(raw, &saved); err != nil {
		return empty, err
	}
	var wire struct {
		Session struct {
			Before, After json.RawMessage
			Input         json.RawMessage
			Resolution    json.RawMessage
		} `json:"session"`
	}
	if err = json.Unmarshal(raw, &wire); err != nil {
		return empty, err
	}
	for _, world := range []json.RawMessage{wire.Session.Before, wire.Session.After} {
		if err = decodeDefeatWorld(world); err != nil {
			return empty, err
		}
	}
	if err = requiredDefeatFields(wire.Session.Input, []string{"reason", "random", "choice", "origin"}, map[string]bool{"random": true, "origin": true}); err != nil {
		return empty, err
	}
	if err = requiredDefeatFields(wire.Session.Resolution, []string{"gold_lost", "promoted", "enemy_survivors", "next_origin", "world_handoff"}, map[string]bool{"next_origin": true}); err != nil {
		return empty, err
	}
	var inputFields, resolutionFields map[string]json.RawMessage
	json.Unmarshal(wire.Session.Input, &inputFields)
	json.Unmarshal(wire.Session.Resolution, &resolutionFields)
	for _, origin := range []json.RawMessage{inputFields["origin"], resolutionFields["next_origin"]} {
		if !bytes.Equal(bytes.TrimSpace(origin), []byte("null")) {
			if err = requiredDefeatFields(origin, []string{"region", "x", "y", "facing"}, nil); err != nil {
				return empty, err
			}
		}
	}
	// Fixed-array decoding must not truncate or pad the outgoing enemy record.
	var resolution map[string]json.RawMessage
	if err = json.Unmarshal(wire.Session.Resolution, &resolution); err != nil {
		return empty, err
	}
	var enemy []ArmyStack
	if err = json.Unmarshal(resolution["enemy_survivors"], &enemy); err != nil || len(enemy) != 6 {
		return empty, errors.New("defeat enemy shape")
	}
	base, err := os.ReadFile(filepath.Join(dir, "gamedata.ay"))
	if err != nil {
		return empty, err
	}
	if len(base) != 2987 || saved.Schema != "eightsword-owned-world-defeat/1" || saved.OriginalSHA != contentSHA(base) || saved.ArmyCatalogSHA != c.digest() || saved.CombatCatalogSHA != cc.Digest() {
		return empty, errors.New("defeat save binding")
	}
	if err = saved.Session.validate(c, cc); err != nil {
		return empty, err
	}
	return saved.Session, nil
}
