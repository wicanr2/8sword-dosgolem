//go:build ignore

package eightsword

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"image/png"
	"os"
	"path/filepath"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

// Same ordinary key/cycle schedule before and after the renderer change.
// Never wait on a renderer-dependent scene label to choose the next input.
func TestResearchOwnedGraphicsGroupFailure(t *testing.T) {
	root := os.Getenv("EIGHTSWORD_TEST_ORIG")
	assets, out := os.Getenv("EIGHTSWORD_TEST_OWNED_FALLBACK_ASSETS"), os.Getenv("EIGHTSWORD_TEST_OWNED_FALLBACK_OUT")
	control := os.Getenv("EIGHTSWORD_TEST_OWNED_FALLBACK_CONTROL") == "1"
	if root == "" || assets == "" || out == "" {
		t.Fatal("explicit original, fixed failure assets and new output required")
	}
	if err := os.Mkdir(out, 0755); err != nil {
		t.Fatal(err)
	}
	for _, kind := range []string{"missing", "corrupt"} {
		t.Run(kind, func(t *testing.T) {
			q := filepath.Join(out, kind)
			if err := os.Mkdir(q, 0755); err != nil {
				t.Fatal(err)
			}
			owned := filepath.Join(q, "owned")
			if err := os.Mkdir(owned, 0755); err != nil {
				t.Fatal(err)
			}
			if control {
				t.Setenv("EIGHTSWORD_RESEARCH_OWNED", "")
			} else {
				t.Setenv("EIGHTSWORD_RESEARCH_OWNED", owned)
			}
			e, err := Open(Options{Root: root, Assets: filepath.Join(assets, kind), Saves: filepath.Join(q, "scratch"), HD: true})
			if err != nil {
				t.Fatal(err)
			}
			t.Cleanup(e.Close)
			if !e.HD || e.Assets == nil || e.Tracker == nil || e.Tracker.graphics != nil || e.FontID() != "noto" {
				t.Fatal("wrong graphics failure fixture", e.Status())
			}
			if kind == "corrupt" && e.GraphicsError != "HD 圖像 grass-painted-r1.png SHA-256 不符" {
				t.Fatal("real SHA failure absent", e.GraphicsError)
			}
			if kind == "missing" && e.GraphicsError != "" {
				t.Fatal("missing optional graphics must remain optional", e.GraphicsError)
			}
			e.Oracle.SetClock(12, 0, 0, 0)
			e.EnableLiveClock(3000)
			readyMain := false
			readyStep := uint64(0)
			// Spec047: fixed-PAM 0110:055A is the completed main-menu read.
			// PREDELLA can use the same segment before the overlay is loaded.
			e.Oracle.OnCall(oracle.Addr{Seg: 0x110, Off: 0x55a}, func(*oracle.Oracle) {
				if !readyMain && e.PAMLoaded && e.Tracker.loadSegment == 0x110 {
					readyMain, readyStep = true, e.Oracle.Steps()
				}
			})
			pcm, err := os.OpenFile(filepath.Join(q, "audio.pcm"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
			if err != nil {
				t.Fatal(err)
			}
			t.Cleanup(func() {
				if err := pcm.Close(); err != nil {
					t.Error(err)
				}
			})
			advance := func(ms int) {
				for i := 0; i < ms; i += 10 {
					if err := e.AdvanceCycles(30000); err != nil {
						t.Fatal(err)
					}
					if err := binary.Write(pcm, binary.LittleEndian, e.RenderAudio()); err != nil {
						t.Fatal(err)
					}
					if i%100 == 0 {
						e.Frame()
					}
				}
			}
			press := func(scan byte, hold, gap int) {
				if err := e.Key(scan, true); err != nil {
					t.Fatal(err)
				}
				advance(hold)
				if err := e.Key(scan, false); err != nil {
					t.Fatal(err)
				}
				advance(gap)
			}
			captures := []map[string]any{}
			shot := func(name, scene string) {
				before := observerGuestState(t, e)
				im := e.Frame()
				after := observerGuestState(t, e)
				if !bytes.Equal(before, after) {
					t.Fatal("fallback Frame changed guest")
				}
				if !control && e.Tracker.VisibleScene != scene {
					data, _ := json.MarshalIndent(e.Status(), "", "  ")
					_ = os.WriteFile(filepath.Join(q, "failed-status.json"), data, 0644)
					t.Fatal("ordinary fixed schedule missed scene", name, e.Tracker.VisibleScene)
				}
				if !control && name == "03-army" && (!e.Tracker.HasVisibleSource(1330) || !e.Tracker.HasVisibleSource(1338) || !e.Tracker.HasVisibleSource(1346)) {
					t.Fatal("army source labels absent")
				}
				f, err := os.OpenFile(filepath.Join(q, name+".png"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
				if err != nil {
					t.Fatal(err)
				}
				if err := png.Encode(f, im); err != nil {
					t.Fatal(err)
				}
				if err := f.Close(); err != nil {
					t.Fatal(err)
				}
				captures = append(captures, map[string]any{"name": name, "scene": scene, "step": e.Oracle.Steps(), "rgba_sha256": hash(im.Pix), "frame_pure": true})
			}
			advance(1000)
			press(2, 100, 100)
			press(2, 100, 100)
			advance(1000)
			press(1, 100, 1000)
			for n := 0; !readyMain && n < 2000; n++ {
				advance(10)
			}
			if !readyMain {
				t.Fatal("original completed main-menu marker absent")
			}
			shot("01-main-menu", "main-menu")
			press(0x50, 100, 300)
			press(0x1c, 100, 500)
			press(0x1c, 100, 1400)
			press(0x3b, 100, 700)
			shot("02-character", "character")
			press(1, 100, 400)
			press(0x3c, 100, 700)
			shot("03-army", "map")
			press(1, 100, 400)
			shot("04-return-map", "map")
			if err := e.Oracle.SaveStateFile(filepath.Join(q, "final.state")); err != nil {
				t.Fatal(err)
			}
			report := map[string]any{"case": kind, "control": control, "graphics_error": e.GraphicsError, "font": e.FontID(), "pam_source_frames": e.researchDirectSourceFrames, "pam_legacy_rgb_frames": e.researchDirectLegacyFrames, "captures": captures, "status": e.Status(), "main_menu_ready_step": readyStep, "method": "ordinary fixed key/cycle schedule after original completed main-menu marker; no memory injection or emulator snapshot loading"}
			raw, err := json.MarshalIndent(report, "", "  ")
			if err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(filepath.Join(q, "receipt.json"), append(raw, 10), 0644); err != nil {
				t.Fatal(err)
			}
			if !control && (e.researchDirectSourceFrames == 0 || e.researchDirectLegacyFrames != 0) {
				t.Fatalf("graphics group loss disabled source renderer: source=%d legacy=%d", e.researchDirectSourceFrames, e.researchDirectLegacyFrames)
			}
		})
	}
}
