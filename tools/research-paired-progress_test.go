//go:build ignore

package main

import (
	"bytes"
	"encoding/json"
	"errors"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

var pairPhases = []string{"before-intent", "intent-temp", "intent-durable", "native-temp", "native-durable", "world-temp", "world-durable", "cleared"}

func pairFixture(t *testing.T) (ArmyCatalog, game.OwnedCombatCatalog, OwnedWorld, OwnedWorld, []byte) {
	t.Helper()
	root := os.Getenv("EIGHTSWORD_PAIR_INPUT")
	if root == "" {
		t.Fatal("real paired inputs required")
	}
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	var before, after OwnedWorld
	for _, v := range []struct {
		Name  string
		Value any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}, {"before-world.json", &before}, {"after-world.json", &after}} {
		raw, e := os.ReadFile(filepath.Join(root, v.Name))
		if e != nil {
			t.Fatal(e)
		}
		if e = pairStrictJSON(raw, v.Value); e != nil {
			t.Fatal(e)
		}
	}
	raw, e := os.ReadFile(filepath.Join(root, "original-save.ay"))
	if e != nil {
		t.Fatal(e)
	}
	return c, cc, before, after, raw
}
func TestPairedCrashChild(t *testing.T) {
	if os.Getenv("EIGHTSWORD_PAIR_CHILD") == "" {
		return
	}
	c, cc, _, after, _ := pairFixture(t)
	s, snap, e := openProgressPair(os.Getenv("EIGHTSWORD_PAIR_DIR"), c, cc)
	if os.Getenv("EIGHTSWORD_PAIR_CHILD") == "busy" {
		if e == nil {
			s.Close()
			t.Fatal("second process opened store")
		}
		if !errors.Is(e, errPairBusy) {
			t.Fatal(e)
		}
		return
	}
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	s.Fault = func(phase string) error {
		if phase == os.Getenv("EIGHTSWORD_PAIR_STOP") {
			os.Exit(91)
		}
		return nil
	}
	if _, e = s.Commit(snap.Token, after); e != nil {
		t.Fatal(e)
	}
	t.Fatal("crash phase not reached")
}
func TestPairedEightProcessCrashes(t *testing.T) {
	c, cc, before, after, base := pairFixture(t)
	for _, phase := range pairPhases {
		t.Run(phase, func(t *testing.T) {
			dir := filepath.Join(t.TempDir(), "save")
			if e := initializeProgressPair(dir, base, c, cc, before); e != nil {
				t.Fatal(e)
			}
			child := exec.Command(os.Args[0], "-test.run=^TestPairedCrashChild$")
			child.Env = append(os.Environ(), "EIGHTSWORD_PAIR_CHILD=crash", "EIGHTSWORD_PAIR_DIR="+dir, "EIGHTSWORD_PAIR_STOP="+phase)
			out, e := child.CombinedOutput()
			var exit *exec.ExitError
			if !errors.As(e, &exit) || exit.ExitCode() != 91 {
				t.Fatalf("child: %v %s", e, out)
			}
			s, snap, e := openProgressPair(dir, c, cc)
			if e != nil {
				t.Fatal(e)
			}
			defer s.Close()
			expected := after
			if phase == "before-intent" || phase == "intent-temp" {
				expected = before
			}
			if !reflect.DeepEqual(snap.World, expected) {
				t.Fatal("wrong recovered generation")
			}
			if !bytes.Equal(snap.Bytes.Native[12:], base[12:]) {
				t.Fatal("native army/opaque bytes changed")
			}
			if _, e = os.Lstat(filepath.Join(dir, pairIntentName)); !os.IsNotExist(e) {
				t.Fatal("intent not cleared")
			}
			if expected.Battle == nil {
				if _, _, e = expected.settleVictory(c, cc); e == nil {
					t.Fatal("reward repeated")
				}
			}
		})
	}
}
func TestPairedLockAndStaleWriter(t *testing.T) {
	c, cc, before, after, base := pairFixture(t)
	dir := filepath.Join(t.TempDir(), "save")
	if e := initializeProgressPair(dir, base, c, cc, before); e != nil {
		t.Fatal(e)
	}
	s, snap, e := openProgressPair(dir, c, cc)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	child := exec.Command(os.Args[0], "-test.run=^TestPairedCrashChild$")
	child.Env = append(os.Environ(), "EIGHTSWORD_PAIR_CHILD=busy", "EIGHTSWORD_PAIR_DIR="+dir)
	if out, e := child.CombinedOutput(); e != nil {
		t.Fatalf("busy child %v %s", e, out)
	}
	next, e := s.Commit(snap.Token, after)
	if e != nil {
		t.Fatal(e)
	}
	if next.Token == snap.Token {
		t.Fatal("token unchanged")
	}
	if _, e = s.Commit(snap.Token, after); e == nil {
		t.Fatal("stale accepted")
	}
	if _, e = s.Commit("", after); e == nil {
		t.Fatal("empty token")
	}
	same, e := s.Commit(next.Token, after)
	if e != nil || same.Token != next.Token {
		t.Fatal("idempotent no-op", e)
	}
	if engine, e := game.Open(game.Options{Root: "/unmounted-original", Saves: dir, HD: true}); engine != nil || !errors.Is(e, game.ErrOwnedArmyHandoffPending) {
		t.Fatal("DOS guard", e)
	}
}
func TestPairedRecoveryRefusesUnknownChanges(t *testing.T) {
	c, cc, before, after, base := pairFixture(t)
	for _, bad := range []string{"foreign-world", "foreign-native", "bad-intent", "unknown-intent", "linked-world", "missing-world"} {
		t.Run(bad, func(t *testing.T) {
			dir := filepath.Join(t.TempDir(), "save")
			if e := initializeProgressPair(dir, base, c, cc, before); e != nil {
				t.Fatal(e)
			}
			s, snap, e := openProgressPair(dir, c, cc)
			if e != nil {
				t.Fatal(e)
			}
			s.Fault = func(phase string) error {
				if phase == "native-durable" {
					return errors.New("injected I/O interruption")
				}
				return nil
			}
			if _, e = s.Commit(snap.Token, after); !errors.Is(e, errPairPending) {
				t.Fatal(e)
			}
			if _, e = s.Commit(snap.Token, after); !errors.Is(e, errPairPending) {
				t.Fatal("uncertain writer not fenced")
			}
			s.Close()
			target := filepath.Join(dir, "gamedata.ay.army.json")
			journal := filepath.Join(dir, pairIntentName)
			switch bad {
			case "foreign-world":
				b, _ := os.ReadFile(target)
				os.WriteFile(target, append(b, ' '), 0600)
			case "foreign-native":
				p := filepath.Join(dir, "gamedata.ay")
				b, _ := os.ReadFile(p)
				b[100] ^= 1
				os.WriteFile(p, b, 0600)
			case "bad-intent":
				os.WriteFile(journal, []byte("{"), 0600)
			case "unknown-intent":
				b, _ := os.ReadFile(journal)
				var v map[string]any
				json.Unmarshal(b, &v)
				v["schema"] = "other"
				b, _ = json.Marshal(v)
				os.WriteFile(journal, b, 0600)
			case "linked-world":
				os.Rename(target, target+".outside")
				os.Symlink(target+".outside", target)
			case "missing-world":
				os.Remove(target)
			}
			inventory := map[string]string{}
			for _, name := range []string{"gamedata.ay", "gamedata.ay.army.json", pairIntentName} {
				p := filepath.Join(dir, name)
				if b, e := os.ReadFile(p); e == nil {
					inventory[name] = nativeSHA(b)
				}
			}
			if opened, _, e := openProgressPair(dir, c, cc); e == nil {
				opened.Close()
				t.Fatal("unsafe recovery accepted")
			}
			for name, h := range inventory {
				b, e := os.ReadFile(filepath.Join(dir, name))
				if e != nil || nativeSHA(b) != h {
					t.Fatal("recovery overwrote external/invalid data", name)
				}
			}
		})
	}
}
func TestPairedStrictShapeAndInitialization(t *testing.T) {
	c, cc, before, _, base := pairFixture(t)
	root := t.TempDir()
	existing := filepath.Join(root, "existing")
	os.Mkdir(existing, 0700)
	if e := initializeProgressPair(existing, base, c, cc, before); e == nil {
		t.Fatal("replaced existing directory")
	}
	b, e := buildProgressPair(base, c, cc, before)
	if e != nil {
		t.Fatal(e)
	}
	for _, field := range []string{"revision", "battle"} {
		var v map[string]any
		json.Unmarshal(b.World, &v)
		delete(v["world"].(map[string]any), field)
		raw, _ := json.Marshal(v)
		bad := b
		bad.World = raw
		if _, e = decodeProgressPair(bad, c, cc); e == nil {
			t.Fatal("missing field", field)
		}
	}
	for _, raw := range []string{`{"x":1,"x":2}`, strings.Repeat("[", 40) + "0" + strings.Repeat("]", 40), `{} {}`} {
		var v any
		if e = pairStrictJSON([]byte(raw), &v); e == nil {
			t.Fatal("unsafe JSON accepted")
		}
	}
	broken := b
	broken.Native = append([]byte(nil), b.Native...)
	broken.Native[6] ^= 1
	if _, e = decodeProgressPair(broken, c, cc); e == nil {
		t.Fatal("native binding mismatch")
	}
}
