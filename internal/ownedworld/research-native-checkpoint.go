// Isolated checkpoint envelope. The formal WorldSave and Engine stay unchanged.
package ownedworld

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"math"
	"os"
	"path/filepath"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

const checkpointSchema = "eightsword-owned-world-save/2"
const checkpointIntent = "eightsword-pair-intent/2"

type checkpointSave struct {
	WorldSave
	Resume      *nativeResumeRef  `json:"native_resume,omitempty"`
	NativeFiles map[string][]byte `json:"native_files,omitempty"`
}

func checkNativeMaps(files map[string][]byte) error {
	if len(files) != 9 {
		return errors.New("checkpoint needs nine source-shaped maps")
	}
	for i := 0; i < 9; i++ {
		if len(files[fmt.Sprintf("map%02d.ay", i)]) != 5761 {
			return errors.New("checkpoint map name/size")
		}
	}
	return nil
}
func validCheckpointEnvelope(s checkpointSave, raw []byte) bool {
	if s.Schema == campSchema || s.Schema == legacyCampSchema {
		return validCampEnvelope(s)
	}
	if s.Schema == resumeSchema {
		return validResumeEnvelope(s)
	}
	if s.Resume != nil {
		return false
	}
	if s.Schema == "eightsword-owned-world-save/1" {
		var fields map[string]json.RawMessage
		return json.Unmarshal(raw, &fields) == nil && fields["native_files"] == nil
	}
	return s.Schema == checkpointSchema && checkNativeMaps(s.NativeFiles) == nil
}
func decodeCheckpointMaps(raw []byte) (map[string][]byte, error) {
	var s checkpointSave
	if e := pairStrictJSON(raw, &s); e != nil {
		return nil, e
	}
	if !validCheckpointEnvelope(s, raw) {
		return nil, errors.New("checkpoint envelope")
	}
	return s.NativeFiles, nil
}
func equalNativeMaps(a, b map[string][]byte) bool {
	if len(a) != len(b) {
		return false
	}
	for k, v := range a {
		if !bytes.Equal(v, b[k]) {
			return false
		}
	}
	return true
}
func buildCheckpointUpdate(before progressPairBytes, c ArmyCatalog, cc game.OwnedCombatCatalog, w OwnedWorld, native []byte, files map[string][]byte) (progressPairBytes, error) {
	var empty progressPairBytes
	maps, e := decodeCheckpointMaps(before.World)
	if e != nil {
		return empty, e
	}
	base := before.Native
	if native != nil {
		if e = checkNativeMaps(files); e != nil {
			return empty, e
		}
		v, x := decodeNativeResources(nativeProgressSource, native)
		if x != nil || v != pairWorldResources(w) || !bytes.Equal(native[12:36], before.Native[12:36]) {
			return empty, errors.New("checkpoint native resources/army")
		}
		base = native
		maps = files
	}
	out, e := buildProgressPair(base, c, cc, w)
	if e != nil {
		return empty, e
	}
	if maps == nil {
		return out, nil
	}
	s := checkpointSave{WorldSave: WorldSave{Schema: checkpointSchema, OriginalSHA: nativeSHA(out.Native), ArmyCatalogSHA: c.digest(), CombatCatalogSHA: cc.Digest(), World: w}, NativeFiles: maps}
	b, e := json.MarshalIndent(s, "", "  ")
	if e != nil || len(b)+1 > pairWorldLimit {
		return empty, errors.New("checkpoint world too large")
	}
	out.World = append(b, '\n')
	_, e = decodeProgressPair(out, c, cc)
	return out, e
}
func checkpointIntentSchema(b progressPairBytes) string {
	var s struct {
		Schema string `json:"schema"`
	}
	_ = json.Unmarshal(b.World, &s)
	if s.Schema == campSchema || s.Schema == legacyCampSchema {
		return campIntent
	}
	if s.Schema == resumeSchema {
		return resumeIntent
	}
	if s.Schema == checkpointSchema {
		return checkpointIntent
	}
	return "eightsword-pair-intent/1"
}
func checkCheckpointIntent(s *progressPairStore, i progressPairIntent) error {
	before, e := decodeProgressPair(i.Before, s.Catalog, s.Combat)
	if e != nil {
		return e
	}
	after, e := decodeProgressPair(i.After, s.Catalog, s.Combat)
	if e != nil {
		return e
	}
	if checkpointIntentSchema(i.After) != checkpointIntent {
		return errors.New("checkpoint intent requires v2 after")
	}
	maps, e := decodeCheckpointMaps(i.After.World)
	if e != nil {
		return e
	}
	// A normal Go army/resource commit must preserve the captured opaque state.
	expected, e := buildCheckpointUpdate(i.Before, s.Catalog, s.Combat, after.World, nil, nil)
	if e != nil {
		return e
	}
	if bytes.Equal(expected.Native, i.After.Native) && bytes.Equal(expected.World, i.After.World) {
		return nil
	}
	// A full native checkpoint changes no gameplay data in the Go world.
	w := after.World
	w.Revision = before.World.Revision
	if before.World.Battle != nil || after.World.Battle != nil || before.World.Revision == math.MaxUint64 || after.World.Revision != before.World.Revision+1 || worldDigest(w) != worldDigest(before.World) {
		return errors.New("checkpoint world transition")
	}
	expected, e = buildCheckpointUpdate(i.Before, s.Catalog, s.Combat, after.World, i.After.Native, maps)
	if e != nil {
		return e
	}
	if !bytes.Equal(expected.Native, i.After.Native) || !bytes.Equal(expected.World, i.After.World) {
		return errors.New("checkpoint serialization")
	}
	return nil
}
func (s *progressPairStore) Commit(expected string, w OwnedWorld) (progressPairSnapshot, error) {
	return s.commitCheckpointBytes(expected, w, nil, nil)
}
func (s *progressPairStore) CommitCheckpoint(expected string, native []byte, files map[string][]byte) (progressPairSnapshot, error) {
	before, e := s.Recover()
	if e != nil {
		return before, e
	}
	if expected == "" || expected != before.Token {
		return before, errors.New("stale checkpoint token")
	}
	if before.World.Battle != nil || before.World.Revision == math.MaxUint64 {
		return before, errors.New("checkpoint pending battle/revision")
	}
	if e = checkNativeMaps(files); e != nil {
		return before, e
	}
	maps, e := decodeCheckpointMaps(before.Bytes.World)
	if e != nil {
		return before, e
	}
	if r, _ := savedResume(before.Bytes.World); r == nil && bytes.Equal(native, before.Bytes.Native) && equalNativeMaps(maps, files) {
		return before, nil
	}
	w := before.World
	w.Revision++
	return s.commitCheckpointBytes(expected, w, native, files)
}

func materializeNativeCheckpoint(root, input, scratch string, s progressPairSnapshot) error {
	if s.World.Battle != nil {
		return errors.New("戰中進度尚未支援由地圖重開，存檔已保留")
	}
	files, e := decodeCheckpointMaps(s.Bytes.World)
	if e != nil {
		return e
	}
	if files == nil {
		files = map[string][]byte{}
		for i := 0; i < 9; i++ {
			n := fmt.Sprintf("map%02d.ay", i)
			p := filepath.Join(root, fmt.Sprintf("MAP%02d.AY", i))
			if i == 1 {
				p = filepath.Join(input, n)
			}
			b, x := pairRead(p, 5761)
			if x != nil {
				return x
			}
			files[n] = b
		}
	}
	if e = checkNativeMaps(files); e != nil {
		return e
	}
	if e = os.Mkdir(scratch, 0700); e != nil {
		return e
	}
	for n, b := range files {
		if e = os.WriteFile(filepath.Join(scratch, n), b, 0600); e != nil {
			return e
		}
	}
	return os.WriteFile(filepath.Join(scratch, "gamedata.ay"), s.Bytes.Native, 0600)
}
func readNativeCheckpointMaps(scratch string) (map[string][]byte, error) {
	files := map[string][]byte{}
	for i := 0; i < 9; i++ {
		n := fmt.Sprintf("map%02d.ay", i)
		b, e := pairRead(filepath.Join(scratch, n), 5761)
		if e != nil {
			return nil, e
		}
		files[n] = b
	}
	return files, checkNativeMaps(files)
}
