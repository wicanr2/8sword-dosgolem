//go:build ignore

package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"errors"
	"flag"
	"os"
	"path/filepath"
	"syscall"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func originPackedInput() ([]byte, error) {
	f := flag.Lookup("input")
	if f == nil || f.Value.String() == "" {
		return nil, errors.New("origin input directory missing")
	}
	return os.ReadFile(filepath.Join(f.Value.String(), "origin-terrain-packed.ay"))
}
func originWorld(before progressPairSnapshot, s *progressPairStore) (OwnedWorld, *nativeResumeRef, error) {
	var empty OwnedWorld
	r, e := savedResume(before.Bytes.World)
	if e != nil || r == nil || r.Phase != "battle" || before.World.Battle == nil || before.World.Battle.State.Result != "loss" {
		return empty, nil, errors.New("origin needs saved total loss")
	}
	_, im, e := readResumeObject(s.Dir, before)
	if e != nil {
		return empty, nil, e
	}
	if binary.LittleEndian.Uint16(im.M.Mem[0x1ec3e:]) != 40 || binary.LittleEndian.Uint16(im.M.Mem[0x1ec40:]) != 40 {
		return empty, nil, errors.New("origin source coordinates")
	}
	out, e := before.World.resolveEncounter(s.Catalog, s.Combat, EncounterContext{Kind: "random"}, DefeatInput{Reason: "annihilation", Choice: "return-origin", Origin: &DefeatOrigin{Region: "native:00", X: 40, Y: 40, Facing: 3}})
	if e != nil {
		return empty, nil, e
	}
	next := *r
	next.Phase = "return"
	next.Result = 3
	return out.After, &next, nil
}
func verifyOriginIntent(s *progressPairStore, i progressPairIntent, before, after progressPairSnapshot) error {
	w, r, e := originWorld(before, s)
	if e != nil {
		return e
	}
	if worldDigest(w) != worldDigest(after.World) {
		return errors.New("origin settlement world")
	}
	expected, e := buildResumeUpdate(i.Before, s.Catalog, s.Combat, w, nil, nil, r)
	if e != nil || !bytes.Equal(expected.Native, i.After.Native) || !bytes.Equal(expected.World, i.After.World) {
		return errors.New("origin settlement reference/maps")
	}
	return validateResumeObject(s, after)
}
func settleRuntimeOrigin(b *controlledBattle, o *oracle.Oracle, packed []byte) error {
	if !b.Pending || b.Settled || b.Returned {
		return errors.New("origin not pending")
	}
	r := o.Regs()
	if r.CS != 0x110 || r.DS != 0x1e88 || r.SS != 0x1e88 || r.IP != 0x32e0 || r.SP != b.SP || r.BP != b.BP || o.Word(oracle.Far(r.SS, r.SP)) != 0x171d || o.Word(oracle.Far(r.SS, r.SP+2)) != 0x110 {
		return errors.New("origin held frame")
	}
	for _, span := range [][2]uint16{{0x151c, 0x1796}, {0x32e0, 0x3774}, {0x1975, 0x19be}} {
		if !bytes.Equal(b.Code[span[0]:span[1]], o.Bytes(oracle.Far(0x110, span[0]), int(span[1]-span[0]))) {
			return errors.New("origin source bytes")
		}
	}
	before, e := b.Store.Recover()
	if e != nil {
		return e
	}
	if before.Token != b.Current.Token {
		return errors.New("origin stale token")
	}
	for i, v := range b.BeforeResources {
		if o.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2))) != v {
			return errors.New("origin resource binding")
		}
	}
	maps, e := decodeCheckpointMaps(before.Bytes.World)
	if e != nil {
		return e
	}
	_, im, e := readResumeObject(b.Store.Dir, before)
	if e != nil {
		return e
	}
	anchor, e := planOriginMap(im.M.Mem, maps, packed)
	if e != nil {
		return e
	}
	live, e := planOriginMap(o.Bytes(oracle.Far(0, 0), 1<<20), maps, packed)
	if e != nil {
		return e
	}
	a, _ := json.Marshal(anchor)
	z, _ := json.Marshal(live)
	if !bytes.Equal(a, z) {
		return errors.New("origin map changed after anchor")
	}
	w, ref, e := originWorld(before, b.Store)
	if e != nil {
		return e
	}
	next, e := b.Store.commitResumeBytes(before.Token, w, nil, nil, ref)
	if e != nil {
		return e
	}
	b.Current = next
	b.Result = 3
	b.Settled = true
	return nil
}
func originWriteMap(dir string, p originMapPlan) error {
	st, e := os.Lstat(dir)
	if e != nil || !st.IsDir() || st.Mode()&os.ModeSymlink != 0 {
		return errors.New("origin scratch directory")
	}
	path := filepath.Join(dir, p.CurrentName)
	st, e = os.Lstat(path)
	if e != nil || !st.Mode().IsRegular() || st.Sys().(*syscall.Stat_t).Uid != uint32(os.Getuid()) {
		return errors.New("origin scratch map ownership")
	}
	f, e := os.CreateTemp(dir, ".origin-map-*")
	if e != nil {
		return e
	}
	name := f.Name()
	defer os.Remove(name)
	if _, e = f.Write(p.SavedMap); e != nil {
		f.Close()
		return e
	}
	if e = f.Sync(); e != nil {
		f.Close()
		return e
	}
	if e = f.Close(); e != nil {
		return e
	}
	if e = os.Rename(name, path); e != nil {
		return e
	}
	d, e := os.Open(dir)
	if e != nil {
		return e
	}
	defer d.Close()
	return d.Sync()
}
func applyOriginReturn(m *dg.Machine, b *controlledBattle) error {
	packed, e := originPackedInput()
	if e != nil {
		return e
	}
	maps, e := decodeCheckpointMaps(b.Current.Bytes.World)
	if e != nil {
		return e
	}
	p, e := planOriginMap(m.Mem, maps, packed)
	if e != nil {
		return e
	}
	f := flag.Lookup("scratch")
	if f == nil || f.Value.String() == "" {
		return errors.New("origin scratch missing")
	}
	// Durable intent remains available if file materialization fails. A cold
	// process restores the immutable pre-return anchor and retries this plan.
	if e = originWriteMap(f.Value.String(), p); e != nil {
		return e
	}
	for i, v := range p.Terrain {
		m.Write8(0x9a000+uint32(i), v)
	}
	for i, v := range p.LoadedMap {
		m.Write8(0x9c000+uint32(i), v)
	}
	for _, v := range p.Words {
		m.Write16(0x1e880+uint32(v.Offset), v.Value)
	}
	for _, v := range []struct {
		Off  uint32
		Name string
	}{{0x8d5c, "map1.ay\x00"}, {0x8e52, "map01.ay\x00"}} {
		for i, ch := range []byte(v.Name) {
			m.Write8(0x1e880+v.Off+uint32(i), ch)
		}
	}
	return nil
}
