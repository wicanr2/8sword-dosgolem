package eightsword

import (
	"bytes"
	"os"
	"strings"
	"testing"
)

// This covers presentation and ordinary keys, not combat or RNG rules. It
// takes the first natural encounter without guest-state or save injection.
func TestNormalRetreatResultAndCharacterReturn(t *testing.T) {
	e := storyEngine(t, os.Getenv("EIGHTSWORD_TEST_ARMY_ASSETS"))
	e.Oracle.SetClock(12, 0, 0, 0)
	advance := func(ms int) { storyAdvance(t, e, ms); e.Frame() }
	press := func(scan byte) { storyPress(t, e, scan); e.Frame() }
	wait := func(label string, predicate func() bool) {
		t.Helper()
		for n := 0; n < 300 && !predicate(); n++ {
			advance(100)
		}
		if !predicate() {
			t.Fatalf("%s not reached: %+v", label, e.Status())
		}
	}
	scene := func(want string) { wait(want, func() bool { return e.Tracker.VisibleScene == want }) }
	advance(1000)
	press(2)
	press(2)
	advance(1000)
	press(1)
	scene("main-menu")
	press(0x50)
	press(0x1c)
	scene("new-game-confirm")
	press(0x1c)
	scene("map")
	for n := 0; n < 128 && e.Tracker.VisibleScene != "encounter-confirm"; n++ {
		scan := byte(0x4d)
		if n%2 == 1 {
			scan = 0x4b
		}
		press(scan)
		advance(100)
	}
	if e.Tracker.VisibleScene != "encounter-confirm" {
		t.Fatal("bounded ordinary movement did not reach an encounter")
	}
	selection := func() string {
		value := ""
		for _, s := range e.Tracker.Strings {
			if s.Y == 133 && (s.Source == 66 || s.Source == 72) {
				value = strings.TrimSpace(s.Text)
			}
		}
		return value
	}
	if selection() == "否" {
		press(0x4b)
	}
	if selection() != "是" {
		t.Fatal("actual encounter Yes was not selected")
	}
	beforeBattle := e.Oracle.Steps()
	press(0x1c)
	wait("battle numbers", func() bool {
		for _, s := range e.Tracker.Strings {
			if s.Step > beforeBattle && s.Source == 36000 {
				return true
			}
		}
		return false
	})
	advance(500)
	beforeV := e.Oracle.Steps()
	press(0x2f)
	wait("ordinary V numbers", func() bool {
		for _, s := range e.Tracker.Strings {
			if s.Step > beforeV && s.Source == 36000 {
				return true
			}
		}
		return false
	})
	press(0x1d)
	wait("V display dismissed by ordinary Ctrl", func() bool { return !e.Tracker.HasVisibleSource(36000) })
	press(1)
	scene("battle-result")
	advance(300)
	before := observerGuestState(t, e)
	e.Frame()
	if !bytes.Equal(before, observerGuestState(t, e)) || e.Tracker.VisibleScene != "battle-result" {
		t.Fatal("result presentation changed guest or lost modal priority")
	}
	ids := e.Tracker.VisibleSources()
	header := false
	for i, id := range ids {
		if id == 18046 {
			header = true
			ids[i] = 0
		}
	}
	if !header || !e.Tracker.HasVisibleSource(18046) {
		t.Fatal("visible result sources missing or exposed as mutable state")
	}
	press(0x1c)
	scene("map")
	if e.Tracker.HasVisibleSource(18046) {
		t.Fatal("dismissed result left a visible source")
	}
	press(0x3b)
	scene("character")
	press(1)
	scene("map")
	beforeArmy := e.Oracle.Steps()
	press(0x3c)
	wait("F2 after retreat", func() bool {
		for _, s := range e.Tracker.Strings {
			if s.Step > beforeArmy && s.Source == 10380 {
				return true
			}
		}
		return false
	})
	advance(300)
	if e.Tracker.Stats.MissingGlyphs != 0 || len(e.Tracker.Stats.Errors) != 0 || len(e.Oracle.Unimplemented()) != 0 {
		t.Fatalf("normal retreat/Noto path: %+v", e.Status())
	}
}
