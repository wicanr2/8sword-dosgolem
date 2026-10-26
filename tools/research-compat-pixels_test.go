//go:build ignore

// 047 DRAFT. Read-only inventory of actual CPU video writes on player paths.
package eightsword

import (
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

type compatPixelSite struct {
	Count     uint64
	FirstStep uint64
	Code      string
	Mode      byte
}

func TestResearchCompatibilityPixelInventory(t *testing.T) {
	root, assets, out := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS"), os.Getenv("EIGHTSWORD_COMPAT_PROBE_OUT")
	if root == "" || assets == "" || out == "" {
		t.Skip("需原版、正式素材及新JSON路徑")
	}
	e, err := Open(Options{Root: root, Assets: assets, Saves: filepath.Join(t.TempDir(), "scratch"), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(e.Close)
	e.Oracle.SetClock(12, 0, 0, 0)
	e.EnableLiveClock(3000)
	native, future := map[string]*compatPixelSite{}, map[string]uint64{}
	t.Cleanup(e.ObservePresentation(PresentationObserver{Write: func(w PresentationWrite) {
		key := fmt.Sprintf("%04x:%04x", w.CS, w.IP)
		if w.Step != e.Oracle.Steps() {
			future[key]++
			return
		}
		site := native[key]
		if site == nil {
			site = &compatPixelSite{FirstStep: w.Step, Code: hex.EncodeToString(e.Oracle.Bytes(oracle.Addr{Seg: w.CS, Off: w.IP}, 12)), Mode: e.Oracle.VideoMode()}
			native[key] = site
		}
		site.Count++
	}}))
	advance := func(ms int) {
		t.Helper()
		for elapsed := 0; elapsed < ms; elapsed += 100 {
			if err := e.AdvanceCycles(300000); err != nil {
				t.Fatal(err)
			}
			e.RenderAudio()
			if im := e.Frame(); im == nil {
				t.Fatal("source frame unavailable")
			}
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
		advance(100)
	}
	ready := false
	e.Oracle.OnCall(oracle.Addr{Seg: 0x110, Off: 0x55a}, func(*oracle.Oracle) { ready = e.PAMLoaded })
	advance(1000)
	press(2)
	press(2)
	for n := 0; !ready && n < 1200; n++ {
		advance(100)
	}
	if !ready {
		t.Fatal("ordinary natural intro/main menu not reached")
	}
	press(0x50)
	press(0x1c)
	advance(300)
	press(0x1c)
	advance(1400)
	press(0x3b)
	advance(700)
	press(1)
	advance(400)
	press(0x3c)
	advance(700)
	press(1)
	advance(400)
	for _, scan := range []byte{0x4d, 0x4b, 0x50, 0x48} {
		press(scan)
		advance(300)
	}
	if e.Tracker.VisibleScene != "map" {
		t.Fatal("ordinary map missing", e.Status())
	}
	if os.Getenv("EIGHTSWORD_COMPAT_REQUIRE_ZERO") == "1" && len(native) != 0 {
		t.Fatalf("original CPU pixel writes remain: %+v", native)
	}
	result := map[string]any{"schema": 1, "spec": "047", "status": "observed-remaining-CPU-pixel-writes", "production": false, "native_writes": native, "host_future_writes": future, "steps": e.Oracle.Steps(), "load_segment": e.Tracker.loadSegment, "string_segment": e.Tracker.stringSeg, "font_segment": e.Tracker.fontSeg, "engine": e.Status(), "limits": []string{"Read-only observer, no CPU/RAM injection or rendering replacement.", "Classification uses current fixed host batches whose write timestamps are strictly after their pre-commit machine step.", "No battle, ending or all-game coverage inferred."}}
	b, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	f, err := os.OpenFile(out, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = f.Write(append(b, '\n')); err != nil {
		t.Fatal(err)
	}
	if err = f.Close(); err != nil {
		t.Fatal(err)
	}
	t.Logf("actual CPU write sites=%d future host write sites=%d", len(native), len(future))
}
