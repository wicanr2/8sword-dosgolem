package eightsword

import (
	"bytes"
	"encoding/binary"
	"os"
	"path/filepath"
	"sync"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

func observerGuestState(t *testing.T, e *Engine) []byte {
	t.Helper()
	path := filepath.Join(t.TempDir(), "guest.state")
	if err := e.Oracle.SaveStateFile(path); err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	return data
}

// A real guest program resets mode 0Eh twice and writes the same byte three times.
// It tests callback semantics independently of the game's chosen drawing paths.
func observerTestProgram(t *testing.T) (string, string) {
	t.Helper()
	code := []byte{0xb8, 0x0e, 0x00, 0xcd, 0x10, 0xb8, 0x0e, 0x00, 0xcd, 0x10, 0xb8, 0x00, 0xa0, 0x8e, 0xc0}
	for i := 0; i < 3; i++ {
		code = append(code, 0x26, 0xc6, 0x06, 0xa0, 0x0f, 0x55)
	}
	code = append(code, 0xb8, 0x00, 0x4c, 0xcd, 0x21)
	header := make([]byte, 32)
	word := func(at int, value uint16) { binary.LittleEndian.PutUint16(header[at:], value) }
	word(0, 0x5a4d)
	word(2, uint16(len(header)+len(code)))
	word(4, 1)
	word(8, 2)
	word(10, 0x1000)
	word(12, 0xffff)
	word(16, 0xfffe)
	word(24, 0x1c)
	dir := t.TempDir()
	path := filepath.Join(dir, "OBSERVE.EXE")
	if err := os.WriteFile(path, append(header, code...), 0644); err != nil {
		t.Fatal(err)
	}
	return path, dir
}

func openObserverTestEngine(t *testing.T, path, dir string) (*Engine, func()) {
	t.Helper()
	o, err := oracle.LoadWith(path, dir, oracle.Options{ProgramPath: `C:\OBSERVE.EXE`})
	if err != nil {
		t.Fatal(err)
	}
	e := &Engine{Oracle: o}
	var once sync.Once
	closeEngine := func() { once.Do(e.Close) }
	t.Cleanup(closeEngine)
	return e, closeEngine
}

func TestPresentationObserversSameValuePreWriteOrderAndIsolation(t *testing.T) {
	path, dir := observerTestProgram(t)
	control, _ := openObserverTestEngine(t, path, dir)
	e, closeEngine := openObserverTestEngine(t, path, dir)
	initial := observerGuestState(t, e)
	var latest PresentationWrite
	var before [][8]uint8
	modes, secondWrites := 0, 0
	bad := false
	cancelA := e.ObservePresentation(PresentationObserver{
		Write: func(v PresentationWrite) {
			latest = v
			pixels, ok := e.Oracle.PlanarBytePixels(v.Offset)
			bad = bad || !ok || v.Offset != 4000 || v.WriteMode != 0
			before = append(before, pixels)
		},
		ModeChange: func(v PresentationModeChange) {
			modes++
			bad = bad || v.Mode != 0x0e
		},
	})
	cancelB := e.ObservePresentation(PresentationObserver{Write: func(v PresentationWrite) {
		secondWrites++
		bad = bad || latest != v || len(before) != secondWrites
	}})
	if !bytes.Equal(initial, observerGuestState(t, e)) {
		t.Fatal("subscription changed guest state")
	}
	for _, instance := range []*Engine{control, e} {
		if err := instance.Advance(10000); err != nil {
			t.Fatal(err)
		}
		if !instance.Exited || instance.ExitCode != 0 {
			t.Fatal("probe did not normally exit")
		}
	}
	pattern := [8]uint8{0, 15, 0, 15, 0, 15, 0, 15}
	if bad || modes != 2 || len(before) != 3 || secondWrites != 3 || before[0] != [8]uint8{} || before[1] != pattern || before[2] != pattern {
		t.Fatalf("pre-write/order/same-value: bad=%v modes=%d before=%v second=%d", bad, modes, before, secondWrites)
	}
	if !bytes.Equal(observerGuestState(t, control), observerGuestState(t, e)) || !bytes.Equal(control.Frame().Pix, e.Frame().Pix) {
		t.Fatal("observer changed guest result or native frame")
	}
	closeEngine()
	cancelA()
	cancelB()
	if len(e.presentationObservers) != 0 {
		t.Fatal("cancellation after Close reattached subscriptions")
	}
}

func TestPresentationObserversCancellationDuringGuestWrite(t *testing.T) {
	path, dir := observerTestProgram(t)
	control, _ := openObserverTestEngine(t, path, dir)
	e, _ := openObserverTestEngine(t, path, dir)
	first, second := 0, 0
	var cancelA, cancelB func()
	cancelA = e.ObservePresentation(PresentationObserver{Write: func(PresentationWrite) {
		first++
		cancelA()
		cancelA()
	}})
	cancelB = e.ObservePresentation(PresentationObserver{Write: func(PresentationWrite) {
		second++
		if second == 2 {
			cancelB()
		}
	}})
	for _, instance := range []*Engine{control, e} {
		if err := instance.Advance(10000); err != nil {
			t.Fatal(err)
		}
	}
	if first != 1 || second != 2 || len(e.presentationObservers) != 0 || e.presentationDispatch != 0 {
		t.Fatalf("cancel lost following subscriber or retained dead slots: %d %d", first, second)
	}
	if !bytes.Equal(observerGuestState(t, control), observerGuestState(t, e)) {
		t.Fatal("cancelling callbacks changed the guest's remaining write")
	}
}

func TestPresentationObserversKeepNormalNotoAndPAM(t *testing.T) {
	assets := os.Getenv("EIGHTSWORD_TEST_PUBLISHER_ASSETS")
	if assets == "" {
		assets = os.Getenv("EIGHTSWORD_TEST_STORY_ASSETS")
	}
	control, e := storyEngine(t, assets), storyEngine(t, assets)
	writesA, writesB := 0, 0
	var latest PresentationWrite
	ordered := true
	firstActive := true
	cancelA := e.ObservePresentation(PresentationObserver{Write: func(v PresentationWrite) {
		writesA++
		latest = v
	}})
	cancelB := e.ObservePresentation(PresentationObserver{Write: func(v PresentationWrite) {
		writesB++
		if firstActive {
			ordered = ordered && latest == v && writesA == writesB
		}
	}})
	advance := func(ms int) {
		storyAdvance(t, control, ms)
		storyAdvance(t, e, ms)
	}
	press := func(scan byte) {
		storyPress(t, control, scan)
		storyPress(t, e, scan)
	}
	check := func() {
		t.Helper()
		if !bytes.Equal(control.Frame().Pix, e.Frame().Pix) || !bytes.Equal(observerGuestState(t, control), observerGuestState(t, e)) {
			t.Fatal("normal observed presentation differs from control")
		}
	}
	advance(1000)
	press(2)
	press(2)
	for i := 0; i < 140 && e.Captions.Stats.Composed == 0; i++ {
		advance(100)
		e.Frame()
	}
	if e.Captions.Stats.Composed == 0 || !ordered || writesA == 0 || writesA != writesB {
		t.Fatal("shared callbacks lost captions or subscriber order")
	}
	check()
	cancelA()
	firstActive = false
	frozen := writesA
	press(1)
	for i := 0; i < 150 && e.Tracker.VisibleScene != "main-menu"; i++ {
		advance(100)
		e.Frame()
	}
	if !e.PAMLoaded || e.Tracker.VisibleScene != "main-menu" || e.Tracker.Stats.RenderedGlyphs == 0 || writesA != frozen || writesB <= frozen {
		t.Fatal("unsubscribing one observer disabled PAM/Noto or its peer")
	}
	cancelB()
	advance(100)
	check()
	if len(e.presentationObservers) != 0 || len(e.Tracker.Stats.Errors) != 0 || len(e.Captions.Stats.Errors) != 0 {
		t.Fatal("observer lifecycle left state or presenter errors")
	}
}
