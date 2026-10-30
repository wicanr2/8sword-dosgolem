//go:build ignore

// 030 DRAFT, Linux: recovery-atomic resource progress + existing WorldSave pair.
package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"golang.org/x/sys/unix"
	"io"
	"os"
	"path/filepath"
)

const pairWorldLimit = 256 << 10
const pairIntentName = ".owned-pair.intent.json"

var errPairPending = errors.New("paired save needs recovery; reopen the window")
var errPairBusy = errors.New("paired save already open")

type progressPairBytes struct {
	Native []byte `json:"native"`
	World  []byte `json:"world"`
}
type progressPairIntent struct {
	Schema     string            `json:"schema"`
	SourceSHA  string            `json:"source_sha256"`
	CatalogSHA string            `json:"catalog_sha256"`
	CombatSHA  string            `json:"combat_sha256"`
	Before     progressPairBytes `json:"before"`
	After      progressPairBytes `json:"after"`
}
type progressPairSnapshot struct {
	World     OwnedWorld        `json:"world"`
	NativeSHA string            `json:"native_sha256"`
	WorldSHA  string            `json:"world_sha256"`
	Token     string            `json:"token"`
	Bytes     progressPairBytes `json:"-"`
}
type progressPairStore struct {
	Dir     string
	Catalog ArmyCatalog
	Combat  game.OwnedCombatCatalog
	Lock    *os.File
	Pending bool
	Fault   func(string) error
}

func pairStrictJSON(raw []byte, dst any) error {
	if len(raw) > 1<<20 {
		return errors.New("paired JSON exceeds limit")
	}
	d := json.NewDecoder(bytes.NewReader(raw))
	d.UseNumber()
	var walk func(int) error
	walk = func(depth int) error {
		if depth > 32 {
			return errors.New("paired JSON nesting limit")
		}
		t, e := d.Token()
		if e != nil {
			return e
		}
		if delim, ok := t.(json.Delim); ok {
			switch delim {
			case '{':
				seen := map[string]bool{}
				for d.More() {
					key, e := d.Token()
					if e != nil {
						return e
					}
					name, ok := key.(string)
					if !ok || seen[name] {
						return errors.New("duplicate paired JSON key")
					}
					seen[name] = true
					if e = walk(depth + 1); e != nil {
						return e
					}
				}
			case '[':
				for d.More() {
					if e = walk(depth + 1); e != nil {
						return e
					}
				}
			default:
				return errors.New("invalid paired JSON delimiter")
			}
			_, e = d.Token()
			return e
		}
		return nil
	}
	if e := walk(0); e != nil {
		return e
	}
	d = json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if e := d.Decode(dst); e != nil {
		return e
	}
	if _, e := d.Token(); e != io.EOF {
		return errors.New("trailing paired JSON")
	}
	return nil
}
func pairRead(path string, limit int64) ([]byte, error) {
	fd, e := unix.Open(path, unix.O_RDONLY|unix.O_NOFOLLOW|unix.O_CLOEXEC|unix.O_NONBLOCK, 0)
	if e != nil {
		return nil, e
	}
	f := os.NewFile(uintptr(fd), path)
	defer f.Close()
	st, e := f.Stat()
	if e != nil || !st.Mode().IsRegular() || st.Size() > limit {
		return nil, errors.New("invalid paired file type or size")
	}
	raw, e := io.ReadAll(io.LimitReader(f, limit+1))
	if e != nil {
		return nil, e
	}
	if int64(len(raw)) > limit {
		return nil, errors.New("paired file grew")
	}
	return raw, nil
}
func pairSyncDir(dir string) error {
	f, e := os.Open(dir)
	if e != nil {
		return e
	}
	defer f.Close()
	return f.Sync()
}
func pairWorldResources(w OwnedWorld) NativeResources {
	return NativeResources{uint64(w.Progress.Rank), w.Progress.Merit, w.Progress.Legacy04F6, w.Army.Gold, w.Army.Leadership, w.Progress.Legacy04FC}
}
func decodeProgressPair(b progressPairBytes, c ArmyCatalog, cc game.OwnedCombatCatalog) (progressPairSnapshot, error) {
	var empty progressPairSnapshot
	values, e := decodeNativeResources(nativeProgressSource, b.Native)
	if e != nil {
		return empty, e
	}
	if len(b.World) > pairWorldLimit {
		return empty, errors.New("paired world exceeds research limit")
	}
	var saved WorldSave
	if e = pairStrictJSON(b.World, &saved); e != nil {
		return empty, e
	}
	var shape struct {
		World map[string]json.RawMessage `json:"world"`
	}
	if e = json.Unmarshal(b.World, &shape); e != nil {
		return empty, e
	}
	for _, key := range []string{"schema", "revision", "army", "progress", "encounters", "battle"} {
		v, ok := shape.World[key]
		if !ok || (key != "battle" && bytes.Equal(bytes.TrimSpace(v), []byte("null"))) {
			return empty, errors.New("missing paired world field")
		}
	}
	var progress map[string]json.RawMessage
	if e = json.Unmarshal(shape.World["progress"], &progress); e != nil {
		return empty, e
	}
	for _, key := range []string{"rank", "merit", "legacy_04f6", "legacy_04fc", "thresholds"} {
		v, ok := progress[key]
		if !ok || bytes.Equal(bytes.TrimSpace(v), []byte("null")) {
			return empty, errors.New("missing paired progress field")
		}
	}
	var thresholds []json.RawMessage
	if e = json.Unmarshal(progress["thresholds"], &thresholds); e != nil || len(thresholds) != 6 {
		return empty, errors.New("paired threshold shape")
	}
	for _, v := range thresholds {
		if bytes.Equal(bytes.TrimSpace(v), []byte("null")) {
			return empty, errors.New("null paired threshold")
		}
	}
	if saved.Schema != "eightsword-owned-world-save/1" || saved.OriginalSHA != nativeSHA(b.Native) || saved.ArmyCatalogSHA != c.digest() || saved.CombatCatalogSHA != cc.Digest() {
		return empty, errors.New("paired world source binding")
	}
	if e = saved.World.validate(c, cc); e != nil {
		return empty, e
	}
	if values != pairWorldResources(saved.World) {
		return empty, errors.New("paired resources disagree")
	}
	nh, wh := nativeSHA(b.Native), nativeSHA(b.World)
	return progressPairSnapshot{saved.World, nh, wh, nativeSHA([]byte(nh + ":" + wh)), b}, nil
}
func buildProgressPair(base []byte, c ArmyCatalog, cc game.OwnedCombatCatalog, w OwnedWorld) (progressPairBytes, error) {
	var empty progressPairBytes
	if e := w.validate(c, cc); e != nil {
		return empty, e
	}
	before, e := decodeNativeResources(nativeProgressSource, base)
	if e != nil {
		return empty, e
	}
	plan, e := planNativeResources(nativeProgressSource, base, before, pairWorldResources(w))
	if e != nil {
		return empty, e
	}
	native, e := applyNativeResources(base, plan)
	if e != nil {
		return empty, e
	}
	raw, e := json.MarshalIndent(WorldSave{Schema: "eightsword-owned-world-save/1", OriginalSHA: nativeSHA(native), ArmyCatalogSHA: c.digest(), CombatCatalogSHA: cc.Digest(), World: w}, "", "  ")
	if e != nil {
		return empty, e
	}
	out := progressPairBytes{native, append(raw, '\n')}
	_, e = decodeProgressPair(out, c, cc)
	return out, e
}
func openProgressPair(dir string, c ArmyCatalog, cc game.OwnedCombatCatalog) (*progressPairStore, progressPairSnapshot, error) {
	var empty progressPairSnapshot
	st, e := os.Lstat(dir)
	if e != nil || !st.IsDir() || st.Mode()&os.ModeSymlink != 0 {
		return nil, empty, errors.New("paired save directory missing or linked")
	}
	for _, name := range []string{".owned-world.lock", ".owned-battle-ui.lock", ".owned-army-ui.lock"} {
		if _, e = os.Lstat(filepath.Join(dir, name)); e == nil {
			return nil, empty, errors.New("legacy writer is active or locked")
		} else if !os.IsNotExist(e) {
			return nil, empty, e
		}
	}
	fd, e := unix.Open(filepath.Join(dir, ".owned-pair.lock"), unix.O_RDWR|unix.O_CREAT|unix.O_CLOEXEC|unix.O_NOFOLLOW|unix.O_NONBLOCK, 0600)
	if e != nil {
		return nil, empty, e
	}
	lock := os.NewFile(uintptr(fd), "paired lock")
	lockStat, e := lock.Stat()
	if e != nil || !lockStat.Mode().IsRegular() {
		lock.Close()
		return nil, empty, errors.New("invalid paired lock file")
	}
	if e = unix.Flock(fd, unix.LOCK_EX|unix.LOCK_NB); e != nil {
		lock.Close()
		return nil, empty, errPairBusy
	}
	s := &progressPairStore{Dir: dir, Catalog: c, Combat: cc, Lock: lock}
	snap, e := s.Recover()
	if e != nil {
		s.Close()
		return nil, empty, e
	}
	return s, snap, nil
}
func (s *progressPairStore) Close() {
	if s != nil && s.Lock != nil {
		unix.Flock(int(s.Lock.Fd()), unix.LOCK_UN)
		s.Lock.Close()
		s.Lock = nil
	}
}
func (s *progressPairStore) readBytes() (progressPairBytes, error) {
	var b progressPairBytes
	var e error
	b.Native, e = pairRead(filepath.Join(s.Dir, "gamedata.ay"), 2987)
	if e != nil {
		return b, e
	}
	b.World, e = pairRead(filepath.Join(s.Dir, "gamedata.ay.army.json"), pairWorldLimit)
	return b, e
}
func (s *progressPairStore) checkIntent(i progressPairIntent) error {
	if i.Schema != "eightsword-pair-intent/1" || i.SourceSHA != nativeProgressSource || i.CatalogSHA != s.Catalog.digest() || i.CombatSHA != s.Combat.Digest() {
		return errors.New("paired intent source or version")
	}
	before, e := decodeProgressPair(i.Before, s.Catalog, s.Combat)
	if e != nil {
		return e
	}
	after, e := decodeProgressPair(i.After, s.Catalog, s.Combat)
	if e != nil {
		return e
	}
	if after.World.Revision < before.World.Revision {
		return errors.New("paired revision went backwards")
	}
	expected, e := buildProgressPair(i.Before.Native, s.Catalog, s.Combat, after.World)
	if e != nil {
		return e
	}
	if !bytes.Equal(expected.Native, i.After.Native) || !bytes.Equal(expected.World, i.After.World) {
		return errors.New("paired intent changes opaque bytes or serialization")
	}
	return nil
}
func (s *progressPairStore) checkpoint(name string) error {
	if s.Fault != nil {
		return s.Fault(name)
	}
	return nil
}
func (s *progressPairStore) atomicFile(name string, raw []byte, phase string) error {
	f, e := os.CreateTemp(s.Dir, ".owned-pair-"+phase+"-*.tmp")
	if e != nil {
		return e
	}
	temp := f.Name()
	defer os.Remove(temp)
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
	if e = s.checkpoint(phase + "-temp"); e != nil {
		return e
	}
	if e = os.Rename(temp, filepath.Join(s.Dir, name)); e != nil {
		return e
	}
	if e = pairSyncDir(s.Dir); e != nil {
		return e
	}
	return s.checkpoint(phase + "-durable")
}
func (s *progressPairStore) finish(i progressPairIntent) error {
	current, e := s.readBytes()
	if e != nil {
		return e
	}
	known := func(actual, a, b []byte) bool { return bytes.Equal(actual, a) || bytes.Equal(actual, b) }
	if !known(current.Native, i.Before.Native, i.After.Native) || !known(current.World, i.Before.World, i.After.World) {
		return errors.New("paired recovery found external changes; files preserved")
	}
	if !bytes.Equal(current.Native, i.After.Native) {
		if e = s.atomicFile("gamedata.ay", i.After.Native, "native"); e != nil {
			return e
		}
	}
	// Recheck the other target before replacement; uncooperative writers are
	// detected and never silently overwritten by recovery.
	now, e := s.readBytes()
	if e != nil {
		return e
	}
	if !bytes.Equal(now.Native, i.After.Native) || !known(now.World, i.Before.World, i.After.World) {
		return errors.New("paired files changed during commit")
	}
	if !bytes.Equal(now.World, i.After.World) {
		if e = s.atomicFile("gamedata.ay.army.json", i.After.World, "world"); e != nil {
			return e
		}
	}
	final, e := s.readBytes()
	if e != nil {
		return e
	}
	if !bytes.Equal(final.Native, i.After.Native) || !bytes.Equal(final.World, i.After.World) {
		return errors.New("paired verification failed")
	}
	if e = os.Remove(filepath.Join(s.Dir, pairIntentName)); e != nil {
		return e
	}
	if e = pairSyncDir(s.Dir); e != nil {
		return e
	}
	return s.checkpoint("cleared")
}
func (s *progressPairStore) Recover() (progressPairSnapshot, error) {
	var empty progressPairSnapshot
	if s.Lock == nil {
		return empty, errors.New("paired store closed")
	}
	raw, e := pairRead(filepath.Join(s.Dir, pairIntentName), 1<<20)
	if e == nil {
		var i progressPairIntent
		if e = pairStrictJSON(raw, &i); e == nil {
			e = s.checkIntent(i)
		}
		if e == nil {
			e = s.finish(i)
		}
		if e != nil {
			s.Pending = true
			return empty, e
		}
	} else if !os.IsNotExist(e) {
		s.Pending = true
		return empty, e
	}
	b, e := s.readBytes()
	if e != nil {
		return empty, e
	}
	snap, e := decodeProgressPair(b, s.Catalog, s.Combat)
	if e == nil {
		s.Pending = false
	}
	return snap, e
}
func (s *progressPairStore) Commit(expected string, w OwnedWorld) (progressPairSnapshot, error) {
	var empty progressPairSnapshot
	if s.Lock == nil {
		return empty, errors.New("paired store closed")
	}
	if s.Pending {
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
	if expected == "" || expected != before.Token {
		return empty, errors.New("stale paired token")
	}
	after, e := buildProgressPair(b.Native, s.Catalog, s.Combat, w)
	if e != nil {
		return empty, e
	}
	i := progressPairIntent{"eightsword-pair-intent/1", nativeProgressSource, s.Catalog.digest(), s.Combat.Digest(), b, after}
	if e = s.checkIntent(i); e != nil {
		return empty, e
	}
	if bytes.Equal(b.Native, after.Native) && bytes.Equal(b.World, after.World) {
		return before, nil
	}
	if e = s.checkpoint("before-intent"); e != nil {
		return empty, e
	}
	raw, e := json.Marshal(i)
	if e != nil || len(raw) > 1<<20 {
		return empty, errors.New("paired intent too large")
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

// Publish a new, explicitly separate prototype directory. Existing progress is
// never replaced by initialization, including an existing empty directory.
func initializeProgressPair(dir string, base []byte, c ArmyCatalog, cc game.OwnedCombatCatalog, w OwnedWorld) error {
	b, e := buildProgressPair(base, c, cc, w)
	if e != nil {
		return e
	}
	parent := filepath.Dir(dir)
	tmp, e := os.MkdirTemp(parent, ".owned-pair-init-*")
	if e != nil {
		return e
	}
	defer os.RemoveAll(tmp)
	for name, raw := range map[string][]byte{"gamedata.ay": b.Native, "gamedata.ay.army.json": b.World} {
		f, e := os.OpenFile(filepath.Join(tmp, name), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
		if e != nil {
			return e
		}
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
	}
	if e = pairSyncDir(tmp); e != nil {
		return e
	}
	if e = unix.Renameat2(unix.AT_FDCWD, tmp, unix.AT_FDCWD, dir, unix.RENAME_NOREPLACE); e != nil {
		return e
	}
	return pairSyncDir(parent)
}
