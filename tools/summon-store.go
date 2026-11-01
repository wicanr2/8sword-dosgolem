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

const summonIntent = "eightsword-pair-intent/summon-1"

func buildSummonPair(before progressPairSnapshot, c ArmyCatalog, cc game.OwnedCombatCatalog, a summonAward, native []byte, files map[string][]byte) (progressPairBytes, error) {
	var empty progressPairBytes
	w, expected, _, e := buildSummonWorld(before, c, a)
	if e != nil {
		return empty, e
	}
	if len(native) != 2987 || !bytes.Equal(native[12:36], before.Bytes.Native[12:36]) || !bytes.Equal(native[36:1236], before.Bytes.Native[36:1236]) || !bytes.Equal(native[1348:1508], expected[1348:1508]) || !bytes.Equal(native[1256:1258], expected[1256:1258]) || !bytes.Equal(native[1316:1318], expected[1316:1318]) || !bytes.Equal(native[1328:1330], expected[1328:1330]) {
		return empty, errors.New("summon changed army/camp/other summon")
	}
	v, e := decodeNativeResources(nativeProgressSource, native)
	if e != nil || v != pairWorldResources(w) {
		return empty, errors.New("summon serialized resources")
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
		return empty, errors.New("summon envelope size")
	}
	out.World = append(raw, '\n')
	_, e = decodeProgressPair(out, c, cc)
	return out, e
}
func checkSummonIntent(s *progressPairStore, i progressPairIntent) error {
	if i.Schema != summonIntent || i.Summon == nil || i.Monthly || i.Treasure != nil || i.Alchemy != nil {
		return errors.New("summon intent kind")
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
		return errors.New("summon requires full v4 checkpoint")
	}
	expected, e := buildSummonPair(before, s.Catalog, s.Combat, *i.Summon, i.After.Native, after.NativeFiles)
	if e != nil {
		return e
	}
	if !bytes.Equal(expected.Native, i.After.Native) || !bytes.Equal(expected.World, i.After.World) {
		return errors.New("summon intent transition")
	}
	return validateCampBindings(i.After.Native, after.World.Army)
}
func (s *progressPairStore) CommitSummon(token string, a summonAward, native []byte, files map[string][]byte) (progressPairSnapshot, error) {
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
		return empty, errors.New("stale summon token")
	}
	after, e := buildSummonPair(before, s.Catalog, s.Combat, a, native, files)
	if e != nil {
		return empty, e
	}
	i := progressPairIntent{Schema: summonIntent, SourceSHA: nativeProgressSource, CatalogSHA: s.Catalog.digest(), CombatSHA: s.Combat.Digest(), Before: b, After: after, Summon: &a}
	if e = s.checkIntent(i); e != nil {
		return empty, e
	}
	if e = s.checkpoint("before-intent"); e != nil {
		return empty, e
	}
	raw, e := json.Marshal(i)
	if e != nil || len(raw) > 1<<20 {
		return empty, errors.New("summon intent size")
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
