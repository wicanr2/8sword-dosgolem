package ownedworld

import (
	"errors"
	"flag"
	"os"
	"path/filepath"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

func captureBattleResume(x *encounterExtra) error {
	r := runtimeEnemyCurrent
	if r == nil || r.Stage != "held" || r.Staged == nil {
		return errors.New("resume missing staged enemy")
	}
	dir := x.Port.Store.Dir
	f, e := os.CreateTemp(dir, ".capture-*.state")
	if e != nil {
		return e
	}
	name := f.Name()
	if e = f.Close(); e != nil {
		return e
	}
	defer os.Remove(name)
	x.Engine.ReleaseAll()
	if e = x.Engine.Oracle.SaveStateFile(name); e != nil {
		return e
	}
	raw, e := pairRead(name, resumeLimit)
	if e != nil {
		return e
	}
	maps, e := readNativeCheckpointMaps(flag.Lookup("scratch").Value.String())
	if e != nil {
		return e
	}
	// The current map may have changed since the previous F7. Its live page is
	// part of this anchor, while the other eight maps come from the shadow.
	location := checkpointLocation(x.Engine.Oracle)
	n, ok := location["map_name"].(string)
	if !ok || len(maps[n]) != 5761 {
		return errors.New("resume current map")
	}
	maps[n] = append([]byte(nil), x.Engine.Oracle.Bytes(oracle.Far(0x9c00, 0), 5761)...)
	w, e := resumeOpening(*r.Staged, x.Port.Store.Combat, r.Modifier)
	if e != nil {
		return e
	}
	next, e := x.Port.Store.CommitSuspendedBattle(x.Bridge.Current.Token, w, raw, maps)
	if e != nil {
		return e
	}
	x.Bridge.Current = next
	x.Port.Current = next
	r.Staged = nil
	return nil
}
func restoreBattleResume(x *encounterExtra) error {
	r, e := loadResumeInto(x.Engine.Oracle, x.Port.Store, x.Port.Current, x.Bridge)
	if e != nil || r == nil {
		return e
	}
	_, im, e := readResumeObject(x.Port.Store.Dir, x.Port.Current)
	if e != nil {
		return e
	}
	rt := runtimeEnemyCurrent
	rt.Stage = "held"
	rt.EntrySP = x.Bridge.SP
	rt.EntryBP = x.Bridge.BP
	rt.Modifier = uint16(im.M.Mem[0x275ea]) | uint16(im.M.Mem[0x275eb])<<8
	rt.EnemyBytes = append([]byte(nil), im.M.Mem[0x23f80:0x23f98]...)
	rt.Rows, e = decodeRuntimeEnemy(rt.EnemyBytes, x.Port.Store.Catalog, x.Port.Store.Combat)
	if e != nil {
		return e
	}
	x.NativeRows = append([]byte(nil), im.M.Mem[0x1edca:0x1ede2]...)
	a := x.Presence
	a.Active = true
	a.HasArmy = true
	a.Prompt = false
	a.BP = x.Bridge.BP
	a.SP = x.Bridge.SP + 4
	a.Token = x.Port.Current.Token
	a.NativeRows = append([]byte(nil), x.NativeRows...)
	x.Sequence = 1
	x.Confirmed = true
	x.ColdResume = true
	if r.Phase == "return" {
		x.Opened = true
	}
	x.Engine.ReleaseAll()
	x.Events = append(x.Events, map[string]any{"command": "cold-resume", "phase": r.Phase, "object_sha256": r.SHA})
	return nil
}
func initializeLayer27() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		old, err := previous(e, p)
		if err != nil {
			return nil, err
		}
		if encounterCurrent == nil {
			return nil, errors.New("resume normal encounter missing")
		}
		if err = restoreBattleResume(encounterCurrent); err != nil {
			return nil, err
		}
		return old, nil
	}
	armyReviewTitle = "神州八劍・軍隊試作・戰中續接"
}

// Resolve the reference before any native shadow or DOS executor is created.
func materializeResumeCheckpoint(root, input, scratch string, s *progressPairStore, p progressPairSnapshot) error {
	r, e := savedResume(p.Bytes.World)
	if e != nil {
		return e
	}
	if r == nil {
		return materializeNativeCheckpoint(root, input, scratch, p)
	}
	if e = validateResumeObject(s, p); e != nil {
		return e
	}
	copy := p
	copy.World.Battle = nil
	// materializeNativeCheckpoint only uses World.Battle as an early guard;
	// the serialized envelope remains bound to the saved Go battle.
	return materializeNativeCheckpoint(root, input, filepath.Clean(scratch), copy)
}
