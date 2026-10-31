//go:build ignore

package main

import (
	"bytes"
	"errors"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"os"
	"path/filepath"
	"testing"
)

func TestNativeCheckpoint(t *testing.T) {
	input := os.Getenv("EIGHTSWORD_CHECKPOINT_INPUT")
	if input == "" {
		t.Fatal("real checkpoint inputs required")
	}
	c, cc, w, base := checkpointInputs(input)
	files := map[string][]byte{}
	for i := 0; i < 9; i++ {
		n := fmtCheckpointName(i)
		b, e := os.ReadFile(filepath.Join(input, "maps", n))
		if e != nil {
			t.Fatal(e)
		}
		files[n] = b
	}
	for _, phase := range []string{"", "native-durable", "world-durable"} {
		t.Run("payload-recovery-"+phase, func(t *testing.T) {
			d := filepath.Join(t.TempDir(), "pair")
			if e := initializeProgressPair(d, base, c, cc, w); e != nil {
				t.Fatal(e)
			}
			s, b, e := openProgressPair(d, c, cc)
			if e != nil {
				t.Fatal(e)
			}
			native := bytes.Clone(b.Bytes.Native)
			native[100] ^= 1
			if phase != "" {
				s.Fault = func(p string) error {
					if p == phase {
						return errors.New("controlled checkpoint interruption")
					}
					return nil
				}
			}
			n, e := s.CommitCheckpoint(b.Token, native, files)
			if phase == "" && e != nil {
				t.Fatal(e)
			}
			if phase != "" && e == nil {
				t.Fatal("missing interruption")
			}
			s.Close()
			s, n, e = openProgressPair(d, c, cc)
			if e != nil {
				t.Fatal(e)
			}
			defer s.Close()
			if !bytes.Equal(n.Bytes.Native, native) || n.World.Revision != w.Revision+1 {
				t.Fatal("whole checkpoint recovery")
			}
			stored, e := decodeCheckpointMaps(n.Bytes.World)
			if e != nil || !equalNativeMaps(files, stored) {
				t.Fatal("recovered maps")
			}
			next := n.World
			next.Revision++
			next.Army.Gold--
			after, e := s.Commit(n.Token, next)
			if e != nil {
				t.Fatal(e)
			}
			stored, e = decodeCheckpointMaps(after.Bytes.World)
			if e != nil || !equalNativeMaps(files, stored) || !bytes.Equal(after.Bytes.Native[12:], native[12:]) {
				t.Fatal("later resource commit discarded checkpoint")
			}
			prior, _ := s.readBytes()
			if _, e = s.CommitCheckpoint(b.Token, native, files); e == nil {
				t.Fatal("stale checkpoint accepted")
			}
			later, _ := s.readBytes()
			if !bytes.Equal(prior.Native, later.Native) || !bytes.Equal(prior.World, later.World) {
				t.Fatal("stale write changed files")
			}
		})
	}
	t.Run("map-shape", func(t *testing.T) {
		bad := map[string][]byte{}
		for k, v := range files {
			bad[k] = v
		}
		delete(bad, "map08.ay")
		bad["../map08.ay"] = files["map08.ay"]
		if checkNativeMaps(bad) == nil {
			t.Fatal("map traversal accepted")
		}
		bad = map[string][]byte{}
		for k, v := range files {
			bad[k] = v
		}
		bad["map08.ay"] = bad["map08.ay"][:5760]
		if checkNativeMaps(bad) == nil {
			t.Fatal("short map accepted")
		}
	})
}
func fmtCheckpointName(i int) string { return "map0" + string(rune('0'+i)) + ".ay" }

func TestCheckpointPendingWorld(t *testing.T) {
	input := os.Getenv("EIGHTSWORD_CHECKPOINT_INPUT")
	if input == "" {
		t.Fatal("real inputs required")
	}
	c, cc, w, base := checkpointInputs(input)
	files := map[string][]byte{}
	for i := 0; i < 9; i++ {
		n := fmtCheckpointName(i)
		b, e := os.ReadFile(filepath.Join(input, "maps", n))
		if e != nil {
			t.Fatal(e)
		}
		files[n] = b
	}
	d := filepath.Join(t.TempDir(), "pair")
	if e := initializeProgressPair(d, base, c, cc, w); e != nil {
		t.Fatal(e)
	}
	s, snap, e := openProgressPair(d, c, cc)
	if e != nil {
		t.Fatal(e)
	}
	snap, e = s.CommitCheckpoint(snap.Token, snap.Bytes.Native, files)
	if e != nil {
		t.Fatal(e)
	}
	next := snap.World
	enemy := [6]ArmyStack{}
	enemy[0] = ArmyStack{Unit: "openkb:wolf", Count: 1}
	next.Encounters = map[string]WorldEncounter{"random:resume-sample": {Enemy: enemy}}
	next, e = next.begin(c, cc, "random:resume-sample", game.OwnedCombatConfig{Rules: next.Army.Rules, Divisors: [2]uint32{5, 5}, Multipliers: [2]uint32{1, 1}})
	if e != nil {
		t.Fatal(e)
	}
	snap, e = s.Commit(snap.Token, next)
	if e != nil {
		t.Fatal(e)
	}
	s.Close()
	s, cold, e := openProgressPair(d, c, cc)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	if cold.World.Battle == nil || worldDigest(cold.World) != worldDigest(next) {
		t.Fatal("pending state lost during cold read")
	}
	legacy, e := buildProgressPair(cold.Bytes.Native, c, cc, cold.World)
	if e != nil {
		t.Fatal(e)
	}
	forged := progressPairIntent{Schema: "eightsword-pair-intent/1", SourceSHA: nativeProgressSource, CatalogSHA: c.digest(), CombatSHA: cc.Digest(), Before: cold.Bytes, After: legacy}
	if s.checkIntent(forged) == nil {
		t.Fatal("legacy intent discarded embedded maps")
	}
	shadow := filepath.Join(t.TempDir(), "native-shadow")
	if materializeNativeCheckpoint("unused", "unused", shadow, cold) == nil {
		t.Fatal("pending battle silently resumed as map")
	}
	if _, e = os.Lstat(shadow); !os.IsNotExist(e) {
		t.Fatal("pending rejection wrote a native shadow")
	}
	after, e := s.Recover()
	if e != nil || after.Token != snap.Token || !bytes.Equal(after.Bytes.Native, snap.Bytes.Native) || !bytes.Equal(after.Bytes.World, snap.Bytes.World) {
		t.Fatal("pending rejection changed saved progress")
	}
}
