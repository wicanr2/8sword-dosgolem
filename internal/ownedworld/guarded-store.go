package ownedworld

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

func projectGuardNPC(native []byte, g *guardedBinding, rows [6]ArmyStack) ([]byte, error) {
	if len(native) != 2987 || g == nil || int(g.Context.Region) >= len(guardedCoordinates) || int(g.Context.Index) >= len(guardedCoordinates[g.Context.Region]) {
		return nil, errors.New("guard projection identity")
	}
	out := bytes.Clone(native)
	ds := guardNPCAt(int(g.Context.Region), int(g.Context.Index))
	for i, v := range rows {
		kind := uint16(0)
		if v.Unit != "" || v.Count != 0 {
			var n int
			if _, e := fmt.Sscanf(v.Unit, "native:%02d", &n); e != nil || n < 1 || n > 25 || v.Unit != fmt.Sprintf("native:%02d", n) || v.Count == 0 || v.Count > 32767 {
				return nil, errors.New("guard projection native kind/count")
			}
			kind = uint16(n)
		}
		for j, value := range []uint16{kind, uint16(v.Count)} {
			at := guardedSaveBase + ds - 0x365e + i*4 + j*2
			binary.LittleEndian.PutUint16(out[at:], value+uint16(at+3))
		}
	}
	return out, nil
}
func guardSettledReference(before OwnedWorld, g *guardedBinding, old *nativeResumeRef, result uint16, c ArmyCatalog, cc game.OwnedCombatCatalog) (OwnedWorld, *nativeResumeRef, error) {
	var empty OwnedWorld
	if old == nil || old.Phase != "battle" || g == nil || before.Battle == nil || before.Battle.Encounter != g.key() || result > 3 {
		return empty, nil, errors.New("guard settlement phase")
	}
	input := DefeatInput{}
	r := *old
	r.Phase = "return"
	r.Result = result
	switch result {
	case 0:
		if before.Battle.State.Result != "win" {
			return empty, nil, errors.New("guard not won")
		}
	case 1:
		p := planOriginalRand(old.Seed)
		value := uint32(p.Value)
		input = DefeatInput{Reason: "retreat", Random: &value}
		r.Seed = p.After
	case 2:
		input = DefeatInput{Reason: "annihilation", Choice: "roam"}
	case 3:
		input = DefeatInput{Reason: "annihilation", Choice: "return-origin", Origin: &DefeatOrigin{Region: "native:00", X: 40, Y: 40, Facing: 3}}
	}
	s, e := before.resolveEncounter(c, cc, g.Context, input)
	if e != nil {
		return empty, nil, e
	}
	return s.After, &r, nil
}
func buildGuardReturnPair(base progressPairBytes, c ArmyCatalog, cc game.OwnedCombatCatalog, w OwnedWorld, files map[string][]byte, r *nativeResumeRef) (progressPairBytes, error) {
	var before checkpointSave
	if e := pairStrictJSON(base.World, &before); e != nil {
		return base, e
	}
	if before.World.Battle == nil {
		return base, errors.New("guard before battle missing")
	}
	var region, index int
	key := before.World.Battle.Encounter
	if _, e := fmt.Sscanf(key, "guarded:%02d:%02d", &region, &index); e != nil || region < 0 || region > 7 || index < 0 || index >= len(guardedCoordinates[region]) || key != fmt.Sprintf("guarded:%02d:%02d", region, index) {
		return base, errors.New("guard return key")
	}
	rec, ok := w.Encounters[key]
	if !ok {
		return base, errors.New("guard return record")
	}
	rows := rec.Enemy
	if rec.Cleared {
		rows = [6]ArmyStack{}
	}
	native, e := projectGuardNPC(base.Native, &guardedBinding{Context: EncounterContext{Region: uint16(region), Index: uint16(index)}}, rows)
	if e != nil {
		return base, e
	}
	native, e = projectSwords(native, region, index, r.Result)
	if e != nil {
		return base, e
	}
	base.Native = native
	if files == nil {
		files = before.NativeFiles
	}
	return marshalResumePair(base, c, cc, w, files, r)
}
func verifyGuardSettlement(s *progressPairStore, i progressPairIntent, before, after progressPairSnapshot) error {
	_, im, e := readResumeObject(s.Dir, before)
	if e != nil {
		return e
	}
	g, e := guardSourceFromImage(im, s)
	if e != nil || g == nil {
		return errors.New("guard settlement anchor")
	}
	old, e := savedResume(i.Before.World)
	if e != nil {
		return e
	}
	r, e := savedResume(i.After.World)
	if e != nil || r == nil {
		return errors.New("guard settlement reference")
	}
	w, ref, e := guardSettledReference(before.World, g, old, r.Result, s.Catalog, s.Combat)
	if e != nil || worldDigest(w) != worldDigest(after.World) {
		return errors.New("guard settlement world mismatch")
	}
	expected, e := buildGuardReturnPair(i.Before, s.Catalog, s.Combat, w, nil, ref)
	if e != nil || !bytes.Equal(expected.Native, i.After.Native) || !bytes.Equal(expected.World, i.After.World) {
		return errors.New("guard settlement native/reference mismatch")
	}
	return validateResumeObject(s, after)
}
func settleGuardRuntime(b *controlledBattle, o *oracle.Oracle, result uint16) error {
	if b.Guard == nil || !b.Pending || b.Settled || b.Returned {
		return errors.New("guard not pending")
	}
	r := o.Regs()
	if r.IP != 0x32e0 || r.CS != 0x110 || r.DS != 0x1e88 || r.SS != 0x1e88 || r.SP != b.SP || r.BP != b.BP || o.Word(oracle.Far(r.SS, r.SP)) != 0x309e || o.Word(oracle.Far(r.SS, r.SP+2)) != 0x110 || guardedSignature(o.Bytes(oracle.Far(0, 0), 1<<20)) != guardedCodeSHA {
		return errors.New("guard held caller")
	}
	current, e := b.Store.Recover()
	if e != nil {
		return e
	}
	if current.Token != b.Current.Token {
		return errors.New("guard stale token")
	}
	for j, v := range b.BeforeResources {
		if o.Word(oracle.Far(0x1e88, 0x4f2+uint16(j*2))) != v {
			return errors.New("guard resource binding")
		}
	}
	ref, e := savedResume(current.Bytes.World)
	if e != nil || ref == nil || ref.Seed != originalSeed(o) {
		return errors.New("guard seed binding")
	}
	w, next, e := guardSettledReference(current.World, b.Guard, ref, result, b.Store.Catalog, b.Store.Combat)
	if e != nil {
		return e
	}
	if result == 3 {
		packed, e := originPackedInput()
		if e != nil {
			return e
		}
		maps, e := decodeCheckpointMaps(current.Bytes.World)
		if e != nil {
			return e
		}
		if _, e = planOriginMap(o.Bytes(oracle.Far(0, 0), 1<<20), maps, packed); e != nil {
			return e
		}
	}
	s, e := b.Store.commitResumeBytes(current.Token, w, nil, nil, next)
	if e != nil {
		return e
	}
	b.Current = s
	b.Result = result
	b.Settled = true
	writeOriginalSeed(o, next.Seed)
	return nil
}
func guardedBeginResume(s *progressPairStore, before, after progressPairSnapshot, im resumeImage) (OwnedWorld, error) {
	var rows [6]ArmyStack
	var g *guardedBinding
	var e error
	if guardedFrame(im) {
		g, e = bindGuard(im.M.Mem, s.Catalog, s.Combat)
		if e != nil {
			return before.World, e
		}
		rows = g.Rows
	} else {
		rows, e = decodeRuntimeEnemy(im.M.Mem[0x23f80:0x23f98], s.Catalog, s.Combat)
		if e != nil {
			return before.World, e
		}
	}
	w, e := guardBeginWorld(before.World, s.Catalog, s.Combat, g, rows)
	if e != nil {
		return w, e
	}
	modifier := binary.LittleEndian.Uint16(im.M.Mem[0x275ea:])
	w, e = resumeOpening(w, s.Combat, modifier)
	if e != nil {
		return w, e
	}
	return w, nil
}
