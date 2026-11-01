//go:build ignore

package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"os"
	"path/filepath"
)

const treasureIntent = "eightsword-pair-intent/treasure-1"

func buildTreasurePair(before progressPairSnapshot, c ArmyCatalog, cc game.OwnedCombatCatalog, a treasureAward, native []byte, files map[string][]byte) (progressPairBytes, error) {
	var empty progressPairBytes
	w, expected, e := buildTreasureWorld(before, a)
	if e != nil {
		return empty, e
	}
	if len(native) != 2987 || !bytes.Equal(native[12:36], before.Bytes.Native[12:36]) || !bytes.Equal(native[36:1236], before.Bytes.Native[36:1236]) || !bytes.Equal(native[1348:1508], expected[1348:1508]) {
		return empty, errors.New("treasure changed army/camp/other treasure")
	}
	v, e := decodeNativeResources(nativeProgressSource, native)
	if e != nil || v != pairWorldResources(w) {
		return empty, errors.New("treasure serialized resources")
	}
	if e = checkNativeMaps(files); e != nil {
		return empty, e
	}
	out, e := buildProgressPair(native, c, cc, w)
	if e != nil {
		return empty, e
	}
	saved := checkpointSave{WorldSave: WorldSave{Schema: campSchema, OriginalSHA: nativeSHA(out.Native), ArmyCatalogSHA: c.digest(), CombatCatalogSHA: cc.Digest(), World: w}, NativeFiles: files}
	raw, e := json.MarshalIndent(saved, "", "  ")
	if e != nil || len(raw)+1 > pairWorldLimit {
		return empty, errors.New("treasure envelope size")
	}
	out.World = append(raw, '\n')
	_, e = decodeProgressPair(out, c, cc)
	return out, e
}
func checkTreasureIntent(s *progressPairStore, i progressPairIntent) error {
	if i.Schema != treasureIntent || i.Treasure == nil || i.Monthly {
		return errors.New("treasure intent kind")
	}
	before, e := decodeProgressPair(i.Before, s.Catalog, s.Combat)
	if e != nil {
		return e
	}
	var after checkpointSave
	if e = pairStrictJSON(i.After.World, &after); e != nil {
		return e
	}
	if after.Schema != campSchema || after.Resume != nil {
		return errors.New("treasure requires full v4 checkpoint")
	}
	expected, e := buildTreasurePair(before, s.Catalog, s.Combat, *i.Treasure, i.After.Native, after.NativeFiles)
	if e != nil {
		return e
	}
	if !bytes.Equal(expected.Native, i.After.Native) || !bytes.Equal(expected.World, i.After.World) {
		return errors.New("treasure intent transition")
	}
	return validateCampBindings(i.After.Native, after.World.Army)
}
func (s *progressPairStore) CommitTreasure(token string, a treasureAward, native []byte, files map[string][]byte) (progressPairSnapshot, error) {
	var empty progressPairSnapshot
	if s.Lock == nil || s.Pending {
		return empty, errPairPending
	}
	if _, e := os.Lstat(filepath.Join(s.Dir, pairIntentName)); e == nil {
		return empty, errPairPending
	} else if !os.IsNotExist(e) {
		return empty, e
	}
	b, e := s.readBytes()
	if e != nil {
		return empty, e
	}
	before, e := decodeProgressPair(b, s.Catalog, s.Combat)
	if e != nil {
		return empty, e
	}
	if token == "" || token != before.Token {
		return empty, errors.New("stale treasure token")
	}
	after, e := buildTreasurePair(before, s.Catalog, s.Combat, a, native, files)
	if e != nil {
		return empty, e
	}
	i := progressPairIntent{Schema: treasureIntent, SourceSHA: nativeProgressSource, CatalogSHA: s.Catalog.digest(), CombatSHA: s.Combat.Digest(), Before: b, After: after, Treasure: &a}
	if e = s.checkIntent(i); e != nil {
		return empty, e
	}
	if e = s.checkpoint("before-intent"); e != nil {
		return empty, e
	}
	raw, e := json.Marshal(i)
	if e != nil || len(raw) > 1<<20 {
		return empty, errors.New("treasure intent size")
	}
	s.Pending = true
	if e = s.atomicFile(pairIntentName, append(raw, '\n'), "intent"); e == nil {
		e = s.finish(i)
	}
	if e != nil {
		return empty, fmt.Errorf("%w: %v", errPairPending, e)
	}
	s.Pending = false
	return decodeProgressPair(after, s.Catalog, s.Combat)
}
