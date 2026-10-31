//go:build ignore

// Isolated v4: source-keyed stock and Go purchases share the paired journal.
package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"math"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

const campSchema = "eightsword-owned-world-save/4"
const campIntent = "eightsword-pair-intent/4"

func validCampEnvelope(v checkpointSave) bool {
	if v.Schema != campSchema || checkNativeMaps(v.NativeFiles) != nil {
		return false
	}
	if v.Resume == nil {
		return v.World.Battle == nil
	}
	v.Schema = resumeSchema
	return validResumeEnvelope(v)
}
func cloneCampWorld(w OwnedWorld) OwnedWorld {
	b, _ := json.Marshal(w)
	var v OwnedWorld
	_ = json.Unmarshal(b, &v)
	return v
}
func buildCampUpdate(b progressPairBytes, c ArmyCatalog, cc game.OwnedCombatCatalog, w OwnedWorld, native []byte, files map[string][]byte, r *nativeResumeRef) (progressPairBytes, error) {
	var prev checkpointSave
	if e := pairStrictJSON(b.World, &prev); e != nil {
		return progressPairBytes{}, e
	}
	offers, e := campOffers(w.Army)
	if e != nil {
		return progressPairBytes{}, e
	}
	out, e := buildResumeUpdate(b, c, cc, w, native, files, r)
	if e != nil {
		return out, e
	}
	if prev.Schema != campSchema && len(offers) == 0 {
		return out, nil
	}
	// A native F7 must already agree. Never overwrite an unknown refresh.
	if native != nil {
		if e = validateCampBindings(native, w.Army); e != nil {
			return out, e
		}
	}
	out.Native, e = projectCampStocks(out.Native, w.Army)
	if e != nil {
		return out, e
	}
	var saved checkpointSave
	if e = pairStrictJSON(out.World, &saved); e != nil {
		return out, e
	}
	if files != nil {
		saved.NativeFiles = files
	}
	if e = checkNativeMaps(saved.NativeFiles); e != nil {
		return out, e
	}
	saved.Schema = campSchema
	saved.OriginalSHA = nativeSHA(out.Native)
	raw, e := json.MarshalIndent(saved, "", "  ")
	if e != nil || len(raw)+1 > pairWorldLimit {
		return out, errors.New("camp envelope size")
	}
	out.World = append(raw, '\n')
	_, e = decodeProgressPair(out, c, cc)
	return out, e
}
func checkCampTransition(b, a progressPairSnapshot, c ArmyCatalog) error {
	old, e := campOffers(b.World.Army)
	if e != nil {
		return e
	}
	next, e := campOffers(a.World.Army)
	if e != nil {
		return e
	}
	changed := ""
	binding := false
	for k, v := range old {
		n, ok := next[k]
		if !ok || n.Unit != v.Unit || n.Stock > v.Stock {
			return errors.New("camp removal/identity/refresh unsupported")
		}
		if n.Stock != v.Stock {
			if changed != "" {
				return errors.New("multiple camp transactions")
			}
			changed = k
		}
	}
	for k := range next {
		if _, ok := old[k]; !ok {
			if changed != "" {
				return errors.New("multiple camp bindings")
			}
			changed = k
			binding = true
		}
	}
	if changed == "" {
		return nil
	}
	if b.World.Battle != nil || a.World.Battle != nil || b.World.Revision == math.MaxUint64 || a.World.Revision != b.World.Revision+1 {
		return errors.New("camp battle/revision")
	}
	expected := cloneCampWorld(b.World)
	if binding {
		g, r, _ := parseCampKey(changed)
		rec, e := decodeCampRecord(b.Bytes.Native, g, r)
		if e != nil || rec.Words[3] == 0 || rec.unit() != next[changed].Unit || uint32(rec.Words[4]) != next[changed].Stock {
			return errors.New("camp binding not from original checkpoint")
		}
		if expected.Army.Offers == nil {
			expected.Army.Offers = map[string]ArmyOffer{}
		}
		expected.Army.Offers[changed] = next[changed]
	} else {
		expected.Army, _, e = expected.Army.recruit(c, changed, old[changed].Stock-next[changed].Stock)
		if e != nil {
			return e
		}
	}
	expected.Revision++
	if worldDigest(expected) != worldDigest(a.World) {
		return errors.New("camp purchase world mismatch")
	}
	return nil
}
func checkCampIntent(s *progressPairStore, i progressPairIntent) error {
	if i.Schema != campIntent || checkpointIntentSchema(i.After) != campIntent {
		return errors.New("camp envelope cannot be downgraded")
	}
	b, e := decodeProgressPair(i.Before, s.Catalog, s.Combat)
	if e != nil {
		return e
	}
	a, e := decodeProgressPair(i.After, s.Catalog, s.Combat)
	if e != nil {
		return e
	}
	if e = validateCampBindings(b.Bytes.Native, b.World.Army); e != nil {
		return e
	}
	if e = validateCampBindings(a.Bytes.Native, a.World.Army); e != nil {
		return e
	}
	if e = checkCampTransition(b, a, s.Catalog); e != nil {
		return e
	}
	var before, after checkpointSave
	if e = pairStrictJSON(i.Before.World, &before); e != nil {
		return e
	}
	if e = pairStrictJSON(i.After.World, &after); e != nil {
		return e
	}
	var firstMaps map[string][]byte
	if before.NativeFiles == nil {
		firstMaps = after.NativeFiles
	}
	expected, e := buildCampUpdate(i.Before, s.Catalog, s.Combat, a.World, nil, firstMaps, nil)
	if e == nil && bytes.Equal(expected.Native, i.After.Native) && bytes.Equal(expected.World, i.After.World) {
		return validateResumeObject(s, a)
	}
	// Full F7 is still restricted to an unchanged Go world plus one revision.
	w := a.World
	w.Revision = b.World.Revision
	if b.World.Battle == nil && a.World.Battle == nil && b.World.Revision != math.MaxUint64 && a.World.Revision == b.World.Revision+1 && worldDigest(w) == worldDigest(b.World) {
		expected, e = buildCampUpdate(i.Before, s.Catalog, s.Combat, a.World, i.After.Native, after.NativeFiles, nil)
		if e == nil && bytes.Equal(expected.Native, i.After.Native) && bytes.Equal(expected.World, i.After.World) {
			return nil
		}
	}
	// Reuse the proven suspend transition with only its envelope version
	// translated. Bound stock must be identical across this transition.
	ob, _ := campOffers(b.World.Army)
	oa, _ := campOffers(a.World.Army)
	x, _ := json.Marshal(ob)
	y, _ := json.Marshal(oa)
	if !bytes.Equal(x, y) {
		return errors.New("camp transition is not canonical")
	}
	legacy := func(p progressPairBytes) (progressPairBytes, error) {
		var v checkpointSave
		if e := pairStrictJSON(p.World, &v); e != nil {
			return p, e
		}
		if v.Schema == campSchema {
			v.Schema = checkpointSchema
			if v.Resume != nil {
				v.Schema = resumeSchema
			}
		}
		raw, e := json.MarshalIndent(v, "", "  ")
		p.World = append(raw, '\n')
		return p, e
	}
	old := i
	old.Schema = resumeIntent
	old.Before, e = legacy(i.Before)
	if e != nil {
		return e
	}
	old.After, e = legacy(i.After)
	if e != nil {
		return e
	}
	if after.Resume == nil {
		return errors.New("camp intent changes opaque checkpoint")
	}
	return checkResumeIntent(s, old)
}
func (s *progressPairStore) BindCamp(expected string, g, row int, files map[string][]byte) (progressPairSnapshot, error) {
	b, e := s.Recover()
	if e != nil {
		return b, e
	}
	if expected == "" || b.Token != expected || b.World.Battle != nil {
		return b, errors.New("camp bind stale/battle")
	}
	rec, e := decodeCampRecord(b.Bytes.Native, g, row)
	if e != nil || rec.Words[3] == 0 {
		return b, errors.New("camp source unavailable")
	}
	key := campKey(g, row)
	offer := ArmyOffer{rec.unit(), uint32(rec.Words[4])}
	if old, ok := b.World.Army.Offers[key]; ok {
		if old != offer {
			return b, errors.New("camp stock disagreement")
		}
		return b, nil
	}
	if b.World.Revision == math.MaxUint64 {
		return b, errors.New("camp revision overflow")
	}
	w := cloneCampWorld(b.World)
	if w.Army.Offers == nil {
		w.Army.Offers = map[string]ArmyOffer{}
	}
	w.Army.Offers[key] = offer
	w.Revision++
	return s.commitResumeBytes(expected, w, nil, files, nil)
}
func overlayCampStocks(o *oracle.Oracle, p progressPairSnapshot) error {
	offers, e := campOffers(p.World.Army)
	if e != nil {
		return e
	}
	// Validate all identities before writing even the first stock word.
	for k := range offers {
		g, r, _ := parseCampKey(k)
		rec, e := decodeCampRecord(p.Bytes.Native, g, r)
		if e != nil {
			return e
		}
		base := campDS(g, r)
		for f := 0; f < 4; f++ {
			if o.Word(oracle.Far(0x1e88, base+uint16(f*2))) != rec.Words[f] {
				return errors.New("resume camp identity changed")
			}
		}
	}
	for k, v := range offers {
		g, r, _ := parseCampKey(k)
		o.WriteU16(oracle.Far(0x1e88, campDS(g, r)+8), uint16(v.Stock))
	}
	return nil
}
