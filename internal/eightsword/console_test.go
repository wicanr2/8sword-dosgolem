package eightsword

import (
	"bytes"
	"image"
	"os"
	"path/filepath"
	"testing"
)

func TestBootConsoleNormalInputAndReadOnlyRendering(t *testing.T) {
	_, _, assets := realAssets(t)
	e, err := Open(Options{Root: os.Getenv("EIGHTSWORD_TEST_ORIG"), Assets: assets, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	e.EnableLiveClock(3000)
	advance := func(ms int) {
		t.Helper()
		for n := 0; n < ms; n += 10 {
			if err := e.AdvanceCycles(30000); err != nil {
				t.Fatal(err)
			}
			e.RenderAudio()
		}
	}
	press := func(scan byte) {
		t.Helper()
		if err := e.Key(scan, true); err != nil {
			t.Fatal(err)
		}
		advance(100)
		if err := e.Key(scan, false); err != nil {
			t.Fatal(err)
		}
		advance(500)
	}
	stateDir := t.TempDir()
	state := func(name string) []byte {
		t.Helper()
		path := filepath.Join(stateDir, name)
		if err := e.Oracle.SaveStateFile(path); err != nil {
			t.Fatal(err)
		}
		data, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		return data
	}
	check := func(stage string) {
		t.Helper()
		if e.ConsoleStage() != stage || e.Exited {
			t.Fatalf("expected %s: %+v", stage, e.Status())
		}
		before := state("before.state")
		hd := e.Frame()
		e.HD = false
		native := e.Frame()
		e.HD = true
		if !bytes.Equal(before, state("after.state")) {
			t.Fatal("rendering changed complete guest state")
		}
		if bytes.Equal(hd.Pix, native.Pix) {
			t.Fatal("real Noto and original font unexpectedly identical")
		}
		safe := image.Rect(18*24, 10*48, 63*24, 16*48)
		for _, frame := range []*image.RGBA{hd, native} {
			ink := 0
			for y := 0; y < frame.Bounds().Dy(); y++ {
				for x := 0; x < frame.Bounds().Dx(); x++ {
					at := y*frame.Stride + x*4
					if frame.Pix[at]|frame.Pix[at+1]|frame.Pix[at+2] != 0 {
						ink++
						if !image.Pt(x, y).In(safe) {
							t.Fatalf("boot ink outside source panel: %d,%d", x, y)
						}
					}
				}
			}
			if ink < 10000 {
				t.Fatalf("boot text missing: only %d ink pixels", ink)
			}
		}
		output := []byte(e.Oracle.Console())
		if readBootConsole(output[:len(output)-1]).stage != "" {
			t.Fatal("partial output accepted")
		}
		output[len(output)-3] ^= 1
		if readBootConsole(output).stage != "" {
			t.Fatal("unknown output accepted")
		}
	}
	advance(1000)
	check("display-config")
	press(0x1c)
	check("display-config")
	press(2)
	check("sound-config")
	press(0x1c)
	check("sound-config")
	press(2)
	if e.ConsoleStage() != "" || e.Oracle.VideoMode() == 3 {
		t.Fatal("boot text survived graphics transition")
	}
}
