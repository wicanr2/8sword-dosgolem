//go:build ignore

// Spec 030 DRAFT: transactional Go world handoff. No guest memory access.
package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"os"
	"path/filepath"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

// Unknown semantic labels keep their original DS displacement until proven.
type WorldProgress struct {
	Rank       uint32    `json:"rank"`
	Merit      uint64    `json:"merit"`
	Legacy04F6 uint64    `json:"legacy_04f6"`
	Legacy04FC uint64    `json:"legacy_04fc"`
	Thresholds [6]uint64 `json:"thresholds"`
}
type WorldEncounter struct {
	Enemy   [6]ArmyStack `json:"enemy"`
	Cleared bool         `json:"cleared"`
}

func (e *WorldEncounter) UnmarshalJSON(raw []byte) error {
	var v struct {
		Enemy   *[]ArmyStack `json:"enemy"`
		Cleared *bool        `json:"cleared"`
	}
	if err := strictJSON(raw, &v); err != nil {
		return err
	}
	if v.Enemy == nil || len(*v.Enemy) != 6 || v.Cleared == nil {
		return errors.New("encounter six-slot shape")
	}
	copy(e.Enemy[:], *v.Enemy)
	e.Cleared = *v.Cleared
	return nil
}

type WorldBattle struct {
	Encounter string                `json:"encounter"`
	StartSHA  string                `json:"start_sha256"`
	State     game.OwnedCombatState `json:"state"`
}

func (b *WorldBattle) UnmarshalJSON(raw []byte) error {
	var v struct {
		Encounter *string         `json:"encounter"`
		StartSHA  *string         `json:"start_sha256"`
		State     json.RawMessage `json:"state"`
	}
	if err := strictJSON(raw, &v); err != nil {
		return err
	}
	if v.Encounter == nil || v.StartSHA == nil {
		return errors.New("battle fields")
	}
	s, err := game.DecodeOwnedCombatState(v.State)
	if err != nil {
		return err
	}
	b.Encounter = *v.Encounter
	b.StartSHA = *v.StartSHA
	b.State = s
	return nil
}

type OwnedWorld struct {
	Schema     string                    `json:"schema"`
	Revision   uint64                    `json:"revision"`
	Army       OwnedArmy                 `json:"army"`
	Progress   WorldProgress             `json:"progress"`
	Encounters map[string]WorldEncounter `json:"encounters"`
	Battle     *WorldBattle              `json:"battle"`
}
type WorldReward struct {
	Gold     uint64 `json:"gold"`
	Merit    uint64 `json:"merit"`
	Promoted bool   `json:"promoted"`
}

func addWorld(a, b uint64) (uint64, error) {
	if a > math.MaxUint64-b {
		return 0, errors.New("world arithmetic overflow")
	}
	return a + b, nil
}
func worldDigest(v any) string          { raw, _ := json.Marshal(v); return contentSHA(raw) }
func (w OwnedWorld) baseDigest() string { w.Battle = nil; return worldDigest(w) }
func (w OwnedWorld) validate(c ArmyCatalog, combat game.OwnedCombatCatalog) error {
	if err := w.Army.validate(c); err != nil {
		return err
	}
	if err := combat.Validate(); err != nil {
		return err
	}
	if w.Schema != "eightsword-owned-world/1" || w.Progress.Rank < 1 || w.Progress.Rank > 5 || w.Army.RecruitRank != w.Progress.Rank || w.Encounters == nil || len(w.Encounters) > 4096 {
		return errors.New("world schema/bounds")
	}
	for _, v := range []uint64{w.Army.Gold, w.Army.Leadership, w.Progress.Merit, w.Progress.Legacy04F6, w.Progress.Legacy04FC} {
		if v > 30000 {
			return errors.New("original strategic stat cap")
		}
	}
	for i := 1; i < 5; i++ {
		if w.Progress.Thresholds[i] == 0 {
			return errors.New("promotion thresholds missing")
		}
	}
	idx, _ := c.index()
	for id, p := range idx {
		v, ok := combat.Profiles[id]
		if !ok || p.NativeKind != v.NativeKind {
			return errors.New("army/combat catalog identity")
		}
	}
	for id, e := range w.Encounters {
		if id == "" || len(id) > 120 {
			return errors.New("encounter ID")
		}
		seen := map[string]bool{}
		alive := false
		for _, s := range e.Enemy {
			if s.Unit == "" && s.Count == 0 {
				continue
			}
			if _, ok := idx[s.Unit]; !ok || s.Count == 0 || seen[s.Unit] {
				return errors.New("encounter troops")
			}
			seen[s.Unit] = true
			alive = true
		}
		if !alive {
			return errors.New("encounter empty")
		}
	}
	if b := w.Battle; b != nil {
		e, ok := w.Encounters[b.Encounter]
		if !ok || e.Cleared || b.StartSHA != w.baseDigest() {
			return errors.New("stale battle/world")
		}
		if err := b.State.Validate(combat); err != nil {
			return err
		}
		if b.State.Committed || b.State.ArmySHA != worldDigest(w.Army) || b.State.Config.Rules != w.Army.Rules {
			return errors.New("battle binding")
		}
		for i := 0; i < 6; i++ {
			a, f := w.Army.Slots[i], b.State.Initial[0][i]
			n, g := e.Enemy[i], b.State.Initial[1][i]
			if a.Unit != f.Unit || a.Count != f.Count || n.Unit != g.Unit || n.Count != g.Count {
				return errors.New("initial armies differ")
			}
		}
	}
	return nil
}
func (w OwnedWorld) begin(c ArmyCatalog, combat game.OwnedCombatCatalog, id string, config game.OwnedCombatConfig) (OwnedWorld, error) {
	if err := w.validate(c, combat); err != nil {
		return w, err
	}
	e, ok := w.Encounters[id]
	if !ok || e.Cleared || w.Battle != nil || w.Revision == math.MaxUint64 {
		return w, errors.New("cannot start encounter")
	}
	if config.Rules != w.Army.Rules {
		return w, errors.New("world rule mismatch")
	}
	var rows [2][6]game.OwnedCombatStack
	for i := 0; i < 6; i++ {
		rows[0][i] = game.OwnedCombatStack{Unit: w.Army.Slots[i].Unit, Count: w.Army.Slots[i].Count}
		rows[1][i] = game.OwnedCombatStack{Unit: e.Enemy[i].Unit, Count: e.Enemy[i].Count}
	}
	state, err := game.NewOwnedCombat(combat, rows, config, worldDigest(w.Army))
	if err != nil {
		return w, err
	}
	next := w
	next.Revision++
	next.Battle = &WorldBattle{Encounter: id, StartSHA: next.baseDigest(), State: state}
	if err = next.validate(c, combat); err != nil {
		return w, err
	}
	return next, nil
}
func (w OwnedWorld) settleVictory(c ArmyCatalog, combat game.OwnedCombatCatalog) (OwnedWorld, WorldReward, error) {
	var reward WorldReward
	if err := w.validate(c, combat); err != nil {
		return w, reward, err
	}
	if w.Battle == nil || w.Battle.State.Result != "win" || w.Revision == math.MaxUint64 {
		return w, reward, errors.New("only completed victory is supported")
	}
	_, survivors, err := w.Battle.State.Commit(combat, worldDigest(w.Army))
	if err != nil {
		return w, reward, err
	}
	idx, _ := c.index()
	encounter := w.Encounters[w.Battle.Encounter]
	var command uint64
	for _, s := range encounter.Enemy {
		if s.Count == 0 {
			continue
		}
		p := idx[s.Unit]
		gold := uint64(s.Count) * p.Gold
		weight := uint64(s.Count) * p.Command
		reward.Gold, err = addWorld(reward.Gold, gold)
		if err != nil {
			return w, WorldReward{}, err
		}
		command, err = addWorld(command, weight)
		if err != nil {
			return w, WorldReward{}, err
		}
	}
	reward.Merit = command / 2
	next := w
	next.Battle = nil
	next.Revision++
	next.Army.Slots = [6]ArmyStack{}
	j := 0
	// Original sub_13774 stably compacts survivors before strategic copyback.
	for _, s := range survivors {
		if s.Count > 0 {
			next.Army.Slots[j] = ArmyStack{Unit: s.Unit, Count: s.Count}
			j++
		}
	}
	next.Army.Gold, err = addWorld(w.Army.Gold, reward.Gold)
	if err != nil {
		return w, WorldReward{}, err
	}
	next.Progress.Merit, err = addWorld(w.Progress.Merit, reward.Merit)
	if err != nil {
		return w, WorldReward{}, err
	}
	// sub_19856 clamps each strategic stat after additions. Go widens the
	// intermediate rather than reproducing the original signed-16-bit wrap.
	next.Army.Gold = min(next.Army.Gold, 30000)
	next.Progress.Merit = min(next.Progress.Merit, 30000)
	if next.Progress.Rank < 5 && next.Progress.Merit > next.Progress.Thresholds[next.Progress.Rank] {
		next.Progress.Rank++
		reward.Promoted = true
		next.Army.RecruitRank = next.Progress.Rank
		next.Progress.Legacy04F6, err = addWorld(w.Progress.Legacy04F6, 100)
		if err != nil {
			return w, WorldReward{}, err
		}
		next.Army.Leadership, err = addWorld(w.Army.Leadership, 100)
		if err != nil {
			return w, WorldReward{}, err
		}
		next.Progress.Legacy04FC, err = addWorld(w.Progress.Legacy04FC, uint64(next.Progress.Rank)*3)
		if err != nil {
			return w, WorldReward{}, err
		}
		next.Progress.Legacy04F6 = min(next.Progress.Legacy04F6, 30000)
		next.Army.Leadership = min(next.Army.Leadership, 30000)
		next.Progress.Legacy04FC = min(next.Progress.Legacy04FC, 30000)
	}
	next.Encounters = make(map[string]WorldEncounter, len(w.Encounters))
	for k, v := range w.Encounters {
		next.Encounters[k] = v
	}
	encounter.Cleared = true
	next.Encounters[w.Battle.Encounter] = encounter
	if err = next.validate(c, combat); err != nil {
		return w, WorldReward{}, err
	}
	return next, reward, nil
}

type WorldSave struct {
	Schema           string     `json:"schema"`
	OriginalSHA      string     `json:"original_sha256"`
	ArmyCatalogSHA   string     `json:"army_catalog_sha256"`
	CombatCatalogSHA string     `json:"combat_catalog_sha256"`
	World            OwnedWorld `json:"world"`
}

// A complete world and its in-flight battle are one atomic sidecar. The current
// Engine already refuses this filename before DOS runs, regardless of schema.
func saveWorld(dir string, c ArmyCatalog, combat game.OwnedCombatCatalog, w OwnedWorld, expectedSHA string) error {
	if err := w.validate(c, combat); err != nil {
		return err
	}
	path := filepath.Join(dir, "gamedata.ay")
	base, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	if len(base) != 2987 {
		return errors.New("base save length")
	}
	lock := filepath.Join(dir, ".owned-world.lock")
	if err = os.Mkdir(lock, 0700); err != nil {
		return errors.New("world save locked")
	}
	defer os.Remove(lock)
	target := filepath.Join(dir, "gamedata.ay.army.json")
	if old, err := os.ReadFile(target); err == nil {
		if expectedSHA == "" || contentSHA(old) != expectedSHA {
			return errors.New("stale world save")
		}
		var header struct {
			Schema string `json:"schema"`
		}
		if json.Unmarshal(old, &header) != nil || header.Schema != "eightsword-owned-world-save/1" {
			return errors.New("refuse overwrite of another save format")
		}
	} else if !os.IsNotExist(err) {
		return err
	} else if expectedSHA != "" {
		return errors.New("world save disappeared")
	}
	envelope := WorldSave{Schema: "eightsword-owned-world-save/1", OriginalSHA: contentSHA(base), ArmyCatalogSHA: c.digest(), CombatCatalogSHA: combat.Digest(), World: w}
	raw, err := json.MarshalIndent(envelope, "", "  ")
	if err != nil {
		return err
	}
	if len(raw) > 1<<20 {
		return errors.New("world save too large")
	}
	f, err := os.CreateTemp(dir, ".owned-world-*.tmp")
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
	current, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	if contentSHA(current) != contentSHA(base) {
		return errors.New("base save changed")
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
func loadWorld(dir string, c ArmyCatalog, combat game.OwnedCombatCatalog) (OwnedWorld, error) {
	var empty OwnedWorld
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
		return empty, errors.New("world save type/size")
	}
	raw, err := io.ReadAll(io.LimitReader(f, (1<<20)+1))
	if err != nil {
		return empty, err
	}
	if len(raw) > 1<<20 {
		return empty, errors.New("world save grew")
	}
	var saved WorldSave
	if err = strictJSON(raw, &saved); err != nil {
		return empty, err
	}
	var shape struct {
		World map[string]json.RawMessage `json:"world"`
	}
	if err = json.Unmarshal(raw, &shape); err != nil {
		return empty, err
	}
	for _, k := range []string{"schema", "revision", "army", "progress", "encounters", "battle"} {
		if v, ok := shape.World[k]; !ok || (k != "battle" && bytes.Equal(bytes.TrimSpace(v), []byte("null"))) {
			return empty, fmt.Errorf("world missing %s", k)
		}
	}
	var progress map[string]json.RawMessage
	if err = json.Unmarshal(shape.World["progress"], &progress); err != nil {
		return empty, err
	}
	for _, k := range []string{"rank", "merit", "legacy_04f6", "legacy_04fc", "thresholds"} {
		if v, ok := progress[k]; !ok || bytes.Equal(bytes.TrimSpace(v), []byte("null")) {
			return empty, errors.New("progress missing field")
		}
	}
	var thresholds []uint64
	if err = json.Unmarshal(progress["thresholds"], &thresholds); err != nil || len(thresholds) != 6 {
		return empty, errors.New("threshold shape")
	}
	var thresholdCells []json.RawMessage
	if err = json.Unmarshal(progress["thresholds"], &thresholdCells); err != nil {
		return empty, err
	}
	for _, cell := range thresholdCells {
		if bytes.Equal(bytes.TrimSpace(cell), []byte("null")) {
			return empty, errors.New("null threshold")
		}
	}
	base, err := os.ReadFile(filepath.Join(dir, "gamedata.ay"))
	if err != nil {
		return empty, err
	}
	if len(base) != 2987 || saved.Schema != "eightsword-owned-world-save/1" || saved.OriginalSHA != contentSHA(base) || saved.ArmyCatalogSHA != c.digest() || saved.CombatCatalogSHA != combat.Digest() {
		return empty, errors.New("world save binding")
	}
	if err = saved.World.validate(c, combat); err != nil {
		return empty, err
	}
	return saved.World, nil
}
