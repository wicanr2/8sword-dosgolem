//go:build ignore

package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

const monthlyIntent = "eightsword-pair-intent/monthly-1"

var monthlySavePAM []byte

func setMonthlySavePAM(path string) error {
	b, e := os.ReadFile(path)
	if e != nil {
		return e
	}
	if _, e = worldArmyCode(b); e != nil {
		return e
	}
	monthlySavePAM = b
	return nil
}
func buildMonthlyPair(before progressPairSnapshot, c ArmyCatalog, cc game.OwnedCombatCatalog, native []byte, files map[string][]byte) (progressPairBytes, error) {
	var empty progressPairBytes
	w, _, refreshed, e := buildMonthlyWorld(before, c, monthlySavePAM)
	if e != nil {
		return empty, e
	}
	if len(native) != 2987 || !bytes.Equal(native[12:36], before.Bytes.Native[12:36]) {
		return empty, errors.New("monthly shadow army changed")
	}
	v, e := decodeNativeResources(nativeProgressSource, native)
	if e != nil || v != pairWorldResources(w) {
		return empty, errors.New("monthly native resources")
	}
	// The existing F7 contract admits current opaque world data. The new
	// producer additionally proves every camp identity and refreshed stock.
	for g := 0; g < 5; g++ {
		for row := 0; row < 24; row++ {
			a, e := decodeCampRecord(refreshed, g, row)
			if e != nil {
				return empty, e
			}
			b, e := decodeCampRecord(native, g, row)
			if e != nil || a != b {
				return empty, errors.New("monthly serialized camp mismatch")
			}
		}
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
		return empty, errors.New("monthly envelope size")
	}
	out.World = append(raw, '\n')
	_, e = decodeProgressPair(out, c, cc)
	return out, e
}
func checkMonthlyIntent(s *progressPairStore, i progressPairIntent) error {
	if i.Schema != monthlyIntent || !i.Monthly {
		return errors.New("monthly intent kind")
	}
	before, e := decodeProgressPair(i.Before, s.Catalog, s.Combat)
	if e != nil {
		return e
	}
	if e = validateCampBindings(before.Bytes.Native, before.World.Army); e != nil {
		return e
	}
	var after checkpointSave
	if e = pairStrictJSON(i.After.World, &after); e != nil {
		return e
	}
	if after.Schema != campSchema || after.Resume != nil {
		return errors.New("monthly requires full v4 checkpoint")
	}
	expected, e := buildMonthlyPair(before, s.Catalog, s.Combat, i.After.Native, after.NativeFiles)
	if e != nil {
		return e
	}
	if !bytes.Equal(expected.Native, i.After.Native) || !bytes.Equal(expected.World, i.After.World) {
		return errors.New("monthly intent transition")
	}
	return validateCampBindings(i.After.Native, after.World.Army)
}
func (s *progressPairStore) CommitMonthly(expected string, native []byte, files map[string][]byte) (progressPairSnapshot, error) {
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
	if expected == "" || before.Token != expected {
		return empty, errors.New("stale monthly token")
	}
	after, e := buildMonthlyPair(before, s.Catalog, s.Combat, native, files)
	if e != nil {
		return empty, e
	}
	i := progressPairIntent{Schema: monthlyIntent, SourceSHA: nativeProgressSource, CatalogSHA: s.Catalog.digest(), CombatSHA: s.Combat.Digest(), Before: b, After: after, Monthly: true}
	if e = s.checkIntent(i); e != nil {
		return empty, e
	}
	if e = s.checkpoint("before-intent"); e != nil {
		return empty, e
	}
	raw, e := json.Marshal(i)
	if e != nil || len(raw) > 1<<20 {
		return empty, errors.New("monthly intent size")
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
