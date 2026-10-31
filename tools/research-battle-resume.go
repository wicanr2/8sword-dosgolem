//go:build ignore

// Isolated v3 suspend envelope. No changes to the formal engine/save codec.
package main

import (
	"bytes"
	"compress/gzip"
	"encoding/binary"
	"encoding/gob"
	"encoding/json"
	"errors"
	"io"
	"os"
	"path/filepath"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
	"golang.org/x/sys/unix"
)

const resumeSchema = "eightsword-owned-world-save/3"
const resumeIntent = "eightsword-pair-intent/3"
const resumeLimit = 2 << 20

type nativeResumeRef struct {
	SHA    string `json:"sha256"`
	Core   string `json:"core_sha256"`
	PAM    string `json:"pam_sha256"`
	Bytes  int    `json:"bytes"`
	Phase  string `json:"phase"`
	Start  string `json:"battle_start_sha256"`
	Result uint16 `json:"result"`
	Seed   uint32 `json:"return_seed"`
}
type resumeMachine struct {
	Magic         string
	Version       int
	Mem           []byte
	R             [8]uint16
	Seg           [4]uint16
	IP            uint16
	Steps, Cycles uint64
}
type resumeDOS struct {
	Magic        string
	Version      int
	Root         string
	RootDir, Dir string
	Handles      []struct {
		H          uint16
		Name, Path string
		Off, Size  int64
		PSP        uint16
	}
	Exited bool
}
type resumeImage struct {
	M resumeMachine
	D resumeDOS
}

func decodeResumeImage(raw []byte) (resumeImage, error) {
	var s resumeImage
	if len(raw) == 0 || len(raw) > resumeLimit {
		return s, errors.New("resume compressed size")
	}
	in := bytes.NewReader(raw)
	z, e := gzip.NewReader(in)
	if e != nil {
		return s, e
	}
	z.Multistream(false)
	b, e := io.ReadAll(io.LimitReader(z, (16<<20)+1))
	ce := z.Close()
	if e != nil || ce != nil || len(b) > 16<<20 || in.Len() != 0 {
		return s, errors.New("resume gzip boundary")
	}
	sections := [][]byte{}
	for i := 0; i < 2; i++ {
		if len(b) < 8 {
			return s, errors.New("resume section header")
		}
		n := binary.LittleEndian.Uint64(b)
		b = b[8:]
		if n == 0 || n > uint64(len(b)) {
			return s, errors.New("resume section bound")
		}
		sections = append(sections, b[:int(n)])
		b = b[int(n):]
	}
	if len(b) != 0 {
		return s, errors.New("resume trailing section")
	}
	for i, dst := range []any{&s.M, &s.D} {
		d := gob.NewDecoder(bytes.NewReader(sections[i]))
		if e = d.Decode(dst); e != nil {
			return s, e
		}
		var extra any
		if d.Decode(&extra) != io.EOF {
			return s, errors.New("resume trailing gob")
		}
	}
	m, d := s.M, s.D
	if m.Magic != "DOSGOLEM-M" || m.Version != 3 || len(m.Mem) != 1<<20 || d.Magic != "DOSGOLEM-D" || d.Version != 3 || d.Root != "/game" || d.Exited {
		return s, errors.New("resume codec/root")
	}
	// This cut admits no open file handles. The core codec does not retain
	// writable-open flags, so reopening a mutable shadow would be unsafe.
	if len(d.Handles) != 0 {
		return s, errors.New("resume requires closed DOS handles")
	}
	if m.Seg[1] != 0x110 || m.Seg[2] != 0x1e88 || m.Seg[3] != 0x1e88 || m.IP != 0x32e0 || m.R[4] < 32 || m.R[4] > 65520 || m.R[5] > 65520 {
		return s, errors.New("resume held frame")
	}
	word := func(off uint16) uint16 { return binary.LittleEndian.Uint16(m.Mem[0x1e880+int(off):]) }
	if word(m.R[4]) != 0x171d || word(m.R[4]+2) != 0x110 || word(m.R[5]+2) != 0xbd3 || word(m.R[5]+4) != 0x110 || word(0x8d6a) > 1 || word(0x56d6) > 7 {
		return s, errors.New("resume caller/modifier")
	}
	sig := append([]byte{}, m.Mem[0x1100+0x151c:0x1100+0x1796]...)
	sig = append(sig, m.Mem[0x1100+0x32e0:0x1100+0x3774]...)
	sig = append(sig, m.Mem[0x1100+0x1953e:0x1100+0x19566]...)
	if nativeSHA(sig) != resumeCodeSHA {
		return s, errors.New("resume source signature")
	}
	return s, nil
}
func resumeImageSeed(s resumeImage) uint32 { return binary.LittleEndian.Uint32(s.M.Mem[0x26a3c:]) }

// Complete the admitted pursuit opening before activating the save. A crash
// cannot leave half an opening or replay it after a later round.
func resumeOpening(w OwnedWorld, cc game.OwnedCombatCatalog, modifier uint16) (OwnedWorld, error) {
	if modifier == 0 {
		return w, nil
	}
	if modifier != 1 || w.Battle == nil {
		return w, errors.New("resume opening modifier")
	}
	b := *w.Battle
	for n := 0; n < 6 && b.State.Result == ""; n++ {
		found := false
		for i, row := range b.State.Rows[1] {
			if row.Count == 0 || b.State.Acted[1][i] || i >= 3 && !cc.Profiles[row.Unit].Ranged {
				continue
			}
			kind := "normal"
			if cc.Profiles[row.Unit].Ranged {
				kind = "ranged"
			}
			p, e := b.State.Choose(cc, 1, i, kind, 0, -1)
			if e != nil {
				w.Battle = &b
				return w, nil
			}
			state, _, e := b.State.Apply(cc, p.Action)
			if e != nil {
				return w, e
			}
			b.State = state
			found = true
			break
		}
		if !found {
			break
		}
	}
	w.Battle = &b
	return w, nil
}
func resumeRef(raw []byte, w OwnedWorld) (*nativeResumeRef, error) {
	s, e := decodeResumeImage(raw)
	if e != nil {
		return nil, e
	}
	if w.Battle == nil {
		return nil, errors.New("resume needs Go battle")
	}
	return &nativeResumeRef{SHA: nativeSHA(raw), Core: resumeCoreSHA, PAM: nativeProgressSource, Bytes: len(raw), Phase: "battle", Start: w.Battle.StartSHA, Seed: resumeImageSeed(s)}, nil
}
func validResumeEnvelope(s checkpointSave) bool {
	r := s.Resume
	if s.Schema != resumeSchema || checkNativeMaps(s.NativeFiles) != nil || r == nil || len(r.SHA) != 64 || len(r.Start) != 64 || r.Core != resumeCoreSHA || r.PAM != nativeProgressSource || r.Bytes <= 0 || r.Bytes > resumeLimit {
		return false
	}
	for _, c := range r.SHA + r.Start {
		if !(c >= '0' && c <= '9' || c >= 'a' && c <= 'f') {
			return false
		}
	}
	return r.Phase == "battle" && s.World.Battle != nil && r.Start == s.World.Battle.StartSHA && r.Result == 0 || r.Phase == "return" && s.World.Battle == nil && r.Result <= 1
}
func savedResume(raw []byte) (*nativeResumeRef, error) {
	var s checkpointSave
	if e := pairStrictJSON(raw, &s); e != nil {
		return nil, e
	}
	if !validCheckpointEnvelope(s, raw) {
		return nil, errors.New("resume envelope")
	}
	return s.Resume, nil
}
func resumeObjectPath(dir string, r *nativeResumeRef) string {
	return filepath.Join(dir, ".native-resume", r.SHA+".state")
}
func readResumeObject(dir string, p progressPairSnapshot) ([]byte, resumeImage, error) {
	var image resumeImage
	r, e := savedResume(p.Bytes.World)
	if e != nil || r == nil {
		return nil, image, e
	}
	st, e := os.Lstat(filepath.Join(dir, ".native-resume"))
	if e != nil || !st.IsDir() || st.Mode()&os.ModeSymlink != 0 {
		return nil, image, errors.New("resume object directory")
	}
	raw, e := pairRead(resumeObjectPath(dir, r), resumeLimit)
	if e != nil {
		return nil, image, e
	}
	if len(raw) != r.Bytes || nativeSHA(raw) != r.SHA {
		return nil, image, errors.New("resume object SHA/size")
	}
	image, e = decodeResumeImage(raw)
	if e != nil {
		return nil, image, e
	}
	m := image.M.Mem
	for i := 0; i < 12; i++ {
		off := 12 + i*2
		if binary.LittleEndian.Uint16(m[0x1edca+i*2:]) != binary.LittleEndian.Uint16(p.Bytes.Native[off:])-uint16(off+3) {
			return nil, image, errors.New("resume original army binding")
		}
	}
	if r.Phase == "battle" {
		if r.Seed != resumeImageSeed(image) {
			return nil, image, errors.New("resume seed binding")
		}
		for i, n := range pairWorldResources(p.World).words() {
			if uint64(binary.LittleEndian.Uint16(m[0x1ed72+i*2:])) != n {
				return nil, image, errors.New("resume resource binding")
			}
		}
	}
	return raw, image, nil
}

// Validate the source rows with this store's catalogs, including initial enemy
// identity. The generic reader above never executes bytes from the snapshot.
func validateResumeObject(s *progressPairStore, p progressPairSnapshot) error {
	r, e := savedResume(p.Bytes.World)
	if e != nil || r == nil {
		return e
	}
	_, im, e := readResumeObject(s.Dir, p)
	if e != nil {
		return e
	}
	rows, e := decodeRuntimeEnemy(im.M.Mem[0x23f80:0x23f98], s.Catalog, s.Combat)
	if e != nil {
		return e
	}
	if p.World.Battle != nil {
		for i, a := range rows {
			b := p.World.Battle.State.Initial[1][i]
			if a.Unit != b.Unit || a.Count != b.Count {
				return errors.New("resume initial enemy binding")
			}
		}
	}
	return nil
}
func publishResumeObject(s *progressPairStore, raw []byte, r *nativeResumeRef) error {
	if len(raw) != r.Bytes || nativeSHA(raw) != r.SHA {
		return errors.New("resume publication SHA")
	}
	dir := filepath.Join(s.Dir, ".native-resume")
	if e := os.Mkdir(dir, 0700); e != nil && !os.IsExist(e) {
		return e
	}
	st, e := os.Lstat(dir)
	if e != nil || !st.IsDir() || st.Mode()&os.ModeSymlink != 0 {
		return errors.New("resume object directory")
	}
	if e = pairSyncDir(s.Dir); e != nil {
		return e
	}
	dst := resumeObjectPath(s.Dir, r)
	if old, e := pairRead(dst, resumeLimit); e == nil {
		if !bytes.Equal(old, raw) {
			return errors.New("immutable resume object changed")
		}
		return nil
	} else if !os.IsNotExist(e) {
		return e
	}
	f, e := os.CreateTemp(dir, ".resume-*.tmp")
	if e != nil {
		return e
	}
	tmp := f.Name()
	defer os.Remove(tmp)
	_, e = f.Write(raw)
	if e == nil {
		e = f.Sync()
	}
	ce := f.Close()
	if e != nil {
		return e
	}
	if ce != nil {
		return ce
	}
	if e = unix.Renameat2(unix.AT_FDCWD, tmp, unix.AT_FDCWD, dst, unix.RENAME_NOREPLACE); e != nil {
		return e
	}
	if e = pairSyncDir(dir); e != nil {
		return e
	}
	return s.checkpoint("resume-object-durable")
}
func marshalResumePair(base progressPairBytes, c ArmyCatalog, cc game.OwnedCombatCatalog, w OwnedWorld, files map[string][]byte, r *nativeResumeRef) (progressPairBytes, error) {
	out, e := buildProgressPair(base.Native, c, cc, w)
	if e != nil {
		return out, e
	}
	if e = checkNativeMaps(files); e != nil {
		return out, e
	}
	v := checkpointSave{WorldSave: WorldSave{Schema: resumeSchema, OriginalSHA: nativeSHA(out.Native), ArmyCatalogSHA: c.digest(), CombatCatalogSHA: cc.Digest(), World: w}, NativeFiles: files, Resume: r}
	raw, e := json.MarshalIndent(v, "", "  ")
	if e != nil || len(raw)+1 > pairWorldLimit {
		return out, errors.New("resume world size")
	}
	out.World = append(raw, '\n')
	_, e = decodeProgressPair(out, c, cc)
	return out, e
}
func resumeAfterSettlement(before OwnedWorld, w OwnedWorld, r *nativeResumeRef, c ArmyCatalog, cc game.OwnedCombatCatalog) (*nativeResumeRef, error) {
	if before.Battle == nil || r.Phase != "battle" || w.Battle != nil {
		return nil, errors.New("resume settlement phase")
	}
	next := *r
	var input DefeatInput
	if before.Battle.State.Result == "win" {
		next.Result = 0
	} else if before.Battle.State.Result == "" {
		plan := planOriginalRand(r.Seed)
		value := uint32(plan.Value)
		input = DefeatInput{Reason: "retreat", Random: &value}
		next.Result = 1
		next.Seed = plan.After
	} else {
		return nil, errors.New("resume unsupported battle result")
	}
	settled, e := before.resolveEncounter(c, cc, EncounterContext{Kind: "random"}, input)
	if e != nil || worldDigest(settled.After) != worldDigest(w) {
		return nil, errors.New("resume settlement mismatch")
	}
	next.Phase = "return"
	return &next, nil
}
func buildResumeUpdate(b progressPairBytes, c ArmyCatalog, cc game.OwnedCombatCatalog, w OwnedWorld, native []byte, files map[string][]byte, explicit *nativeResumeRef) (progressPairBytes, error) {
	var prev checkpointSave
	if e := pairStrictJSON(b.World, &prev); e != nil {
		return progressPairBytes{}, e
	}
	r := prev.Resume
	if explicit != nil {
		r = explicit
	}
	if r == nil {
		return buildCheckpointUpdate(b, c, cc, w, native, files)
	}
	if native != nil {
		if prev.Resume == nil || prev.Resume.Phase != "return" {
			return progressPairBytes{}, errors.New("cannot clear active resume")
		}
		return buildCheckpointUpdate(b, c, cc, w, native, files)
	}
	if explicit == nil && prev.World.Battle != nil && w.Battle == nil {
		var e error
		r, e = resumeAfterSettlement(prev.World, w, r, c, cc)
		if e != nil {
			return progressPairBytes{}, e
		}
	}
	if files == nil {
		files = prev.NativeFiles
	}
	return marshalResumePair(b, c, cc, w, files, r)
}
func checkResumeIntent(s *progressPairStore, i progressPairIntent) error {
	before, e := decodeProgressPair(i.Before, s.Catalog, s.Combat)
	if e != nil {
		return e
	}
	after, e := decodeProgressPair(i.After, s.Catalog, s.Combat)
	if e != nil {
		return e
	}
	// First accept an ordinary Go action or settlement retaining the anchor.
	expected, e := buildResumeUpdate(i.Before, s.Catalog, s.Combat, after.World, nil, nil, nil)
	if e == nil && bytes.Equal(expected.Native, i.After.Native) && bytes.Equal(expected.World, i.After.World) {
		return validateResumeObject(s, after)
	}
	r, e := savedResume(i.After.World)
	if e != nil {
		return e
	}
	if r != nil && r.Phase == "battle" && before.World.Battle == nil && after.World.Battle != nil {
		w := before.World
		w.Encounters = after.World.Encounters
		w, e = w.begin(s.Catalog, s.Combat, after.World.Battle.Encounter, after.World.Battle.State.Config)
		if e == nil {
			_, im, x := readResumeObject(s.Dir, after)
			if x != nil {
				return x
			}
			w, e = resumeOpening(w, s.Combat, binary.LittleEndian.Uint16(im.M.Mem[0x275ea:]))
		}
		if e != nil || worldDigest(w) != worldDigest(after.World) {
			return errors.New("resume begin transition")
		}
		var saved checkpointSave
		if e = pairStrictJSON(i.After.World, &saved); e != nil {
			return e
		}
		expected, e = buildResumeUpdate(i.Before, s.Catalog, s.Combat, w, nil, saved.NativeFiles, r)
		if e != nil || !bytes.Equal(expected.Native, i.After.Native) || !bytes.Equal(expected.World, i.After.World) {
			return errors.New("resume begin serialization")
		}
		return validateResumeObject(s, after)
	}
	// A normal F7 after return replaces the anchor with a full v2 checkpoint.
	old, e := savedResume(i.Before.World)
	if e != nil {
		return e
	}
	if old != nil && old.Phase == "return" && r == nil {
		w := after.World
		w.Revision = before.World.Revision
		if after.World.Revision != before.World.Revision+1 || worldDigest(w) != worldDigest(before.World) {
			return errors.New("resume clear needs full checkpoint")
		}
		return checkCheckpointIntent(s, i)
	}
	return errors.New("resume intent changes anchor")
}
func (s *progressPairStore) commitCheckpointBytes(expected string, w OwnedWorld, native []byte, files map[string][]byte) (progressPairSnapshot, error) {
	return s.commitResumeBytes(expected, w, native, files, nil)
}
func (s *progressPairStore) CommitSuspendedBattle(expected string, w OwnedWorld, raw []byte, files map[string][]byte) (progressPairSnapshot, error) {
	before, e := s.Recover()
	if e != nil {
		return before, e
	}
	if before.Token != expected || before.World.Battle != nil {
		return before, errors.New("resume stale/already pending")
	}
	r, e := resumeRef(raw, w)
	if e != nil {
		return before, e
	}
	// A durable orphan is harmless; only the paired journal activates it.
	if e = publishResumeObject(s, raw, r); e != nil {
		return before, e
	}
	return s.commitResumeBytes(expected, w, nil, files, r)
}
func loadResumeInto(o *oracle.Oracle, s *progressPairStore, p progressPairSnapshot, b *controlledBattle) (*nativeResumeRef, error) {
	r, e := savedResume(p.Bytes.World)
	if e != nil || r == nil {
		return r, e
	}
	if e = validateResumeObject(s, p); e != nil {
		return nil, e
	}
	_, im, e := readResumeObject(s.Dir, p)
	if e != nil {
		return nil, e
	}
	if e = o.LoadStateFile(resumeObjectPath(s.Dir, r)); e != nil {
		return nil, e
	}
	b.Current = p
	b.Pending = true
	b.SP = im.M.R[4]
	b.BP = im.M.R[5]
	for i := range b.BeforeResources {
		b.BeforeResources[i] = binary.LittleEndian.Uint16(im.M.Mem[0x1ed72+i*2:])
	}
	if r.Phase == "return" {
		b.Settled = true
		b.Result = r.Result
		writeOriginalSeed(o, r.Seed)
	}
	return r, nil
}
