package eightsword

import (
	"bytes"
	"encoding/json"
	"image"
	"os"
	"path/filepath"
	"testing"
)

func museumTestAssets(t *testing.T) string {
	t.Helper()
	dir := os.Getenv("EIGHTSWORD_TEST_MUSEUM_ASSETS")
	if dir == "" {
		t.Skip("需要完整博物館素材")
	}
	return dir
}

func museumGuestState(t *testing.T, e *Engine) []byte {
	t.Helper()
	p := filepath.Join(t.TempDir(), "guest.state")
	if err := e.Oracle.SaveStateFile(p); err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile(p)
	if err != nil {
		t.Fatal(err)
	}
	if err = os.Remove(p); err != nil {
		t.Fatal(err)
	}
	return b
}

func TestMuseumNormalScenesAndFramePurity(t *testing.T) {
	e := storyEngine(t, museumTestAssets(t))
	if e.Museum == nil || e.MuseumError != "" || e.Heroine != nil {
		t.Fatal("博物館未使用單一所有權", e.MuseumError)
	}
	storyAdvance(t, e, 1000)
	storyPress(t, e, 2)
	storyPress(t, e, 2)
	seen := map[string]bool{}
	for i := 0; i < 400; i++ {
		storyAdvance(t, e, 50)
		before := museumGuestState(t, e)
		im := e.Frame()
		if !bytes.Equal(before, museumGuestState(t, e)) {
			t.Fatal("博物館 Frame 改動客體")
		}
		stage := e.Museum.FrameStage(im)
		if stage == "left" && !seen[stage] {
			pixels := append([]byte(nil), im.Pix...)
			for _, id := range []string{"lishu", "caoshu", "noto"} {
				if err := e.SetFont(id); err != nil {
					t.Fatal(err)
				}
				e.Frame()
			}
			if !bytes.Equal(pixels, e.Frame().Pix) || !bytes.Equal(before, museumGuestState(t, e)) {
				t.Fatal("字型切換改動博物館或客體")
			}
		}
		seen[stage] = true
	}
	m := e.Museum
	for _, stage := range []string{"left", "right", "portrait", "beam", "hold", "drain"} {
		if !seen[stage] {
			t.Fatalf("正常片頭未到達 %s: %+v", stage, m.Status())
		}
	}
	actors := map[int]bool{}
	for _, event := range m.Events {
		if event["role"] == "actor" {
			for _, record := range heroineRecords[2:12] {
				if event["source_sha256"] == record.sha {
					actors[record.offset] = true
				}
			}
		}
	}
	if len(actors) != 10 || !m.retired || m.drain != nil || m.stopObserving != nil || len(m.Errors) != 0 || m.UnknownWrites != 0 {
		t.Fatal("正常來源或交接不完整", len(actors), m.Status())
	}
}

func TestMuseumLateAssetFailurePreservesHeroine(t *testing.T) {
	dir := museumTestAssets(t)
	copyDir := t.TempDir()
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		b, err := os.ReadFile(filepath.Join(dir, entry.Name()))
		if err != nil {
			t.Fatal(err)
		}
		if err = os.WriteFile(filepath.Join(copyDir, entry.Name()), b, 0600); err != nil {
			t.Fatal(err)
		}
	}
	manifestPath := filepath.Join(copyDir, "museum.json")
	raw, err := os.ReadFile(manifestPath)
	if err != nil {
		t.Fatal(err)
	}
	beam := filepath.Join(copyDir, "museum-beam.png")
	beamBytes, err := os.ReadFile(beam)
	if err != nil {
		t.Fatal(err)
	}
	tests := []string{"bad-last-png", "missing-last-png", "symlink", "trailing-json", "foreign-portrait", "late-cache"}
	for _, test := range tests {
		t.Run(test, func(t *testing.T) {
			os.Remove(beam)
			if err := os.WriteFile(beam, beamBytes, 0600); err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(manifestPath, raw, 0600); err != nil {
				t.Fatal(err)
			}
			switch test {
			case "bad-last-png":
				err = os.WriteFile(beam, append(append([]byte(nil), beamBytes...), 0), 0600)
			case "missing-last-png":
				err = os.Remove(beam)
			case "symlink":
				err = os.Remove(beam)
				if err == nil {
					err = os.Symlink(filepath.Join(dir, "museum-beam.png"), beam)
				}
			case "trailing-json":
				err = os.WriteFile(manifestPath, append(append([]byte(nil), raw...), []byte(" {}")...), 0600)
			default:
				var list museumGroupManifest
				if err = json.Unmarshal(raw, &list); err != nil {
					t.Fatal(err)
				}
				for i := range list.Assets {
					if test == "foreign-portrait" && list.Assets[i].ID == "portrait" {
						list.Assets[i].SHA = "unapproved-portrait"
					}
					if test == "late-cache" && list.Assets[i].ID == "beam" {
						list.Assets[i].CacheSHA = "bad-cache"
					}
				}
				var modified []byte
				modified, err = json.Marshal(list)
				if err == nil {
					err = os.WriteFile(manifestPath, modified, 0600)
				}
			}
			if err != nil {
				t.Fatal(err)
			}
			e := storyEngine(t, copyDir)
			if e.Museum != nil || e.MuseumError == "" || e.Heroine == nil || e.HeroineError != "" || e.GraphicsError != "" || e.PublisherError != "" || e.SetFont("lishu") != nil {
				t.Fatal("博物館故障影響其他 HD", e.Status())
			}
		})
	}
}

func TestMuseumMetadataPageInvalidationAndBounds(t *testing.T) {
	e := storyEngine(t, museumTestAssets(t))
	m := e.Museum
	if m == nil {
		t.Fatal(e.MuseumError)
	}
	before := museumGuestState(t, e)
	inputs := len(e.InputEvents)
	// This is host metadata diagnosis, not a claim of naturally occurring writes.
	m.active = true
	m.pages[0] = &museumPage{role: "left", ink: image.NewRGBA(image.Rect(0, 0, 640, 200)), scene: &museumScene{}}
	m.tx = []museumTX{{at: 0x5d76, end: 0x5d8f, copy: true, sourcePage: 0, page: 0x4000}}
	m.commit(0x5d8f)
	if m.pages[0x4000] == nil || m.pages[0x4000].ink == m.pages[0].ink || m.pages[0x4000].scene == m.pages[0].scene {
		t.Fatal("複製共用可寫頁面")
	}
	m.tx = []museumTX{{at: 0x5b0c, end: 0x5b42, page: 0x4000, clear: true}}
	m.commit(0x5b42)
	if m.pages[0x4000] != nil || m.pages[0] == nil {
		t.Fatal("清頁改動其他頁")
	}
	m.tx = []museumTX{{at: 0x5d76, end: 0x5d8f, copy: true, sourcePage: 0, page: 0x4000}}
	m.hold[0x4000] = image.NewRGBA(image.Rect(0, 0, 1920, 780))
	m.observeMuseumWrite(PresentationWrite{Offset: 4000, CS: 0x123, IP: 0x456})
	if m.pages[0] != nil || !m.tx[0].invalidated || m.hold[0x4000] != nil {
		t.Fatal("未知來源頁寫入沒有使待複製頁失效")
	}
	m.commit(0x5d8f)
	if m.pages[0x4000] != nil {
		t.Fatal("失效的複製復活")
	}
	m.tx = []museumTX{{start: m.o.Cycles() - 2000001}}
	m.Tick()
	if !m.failed || !m.retired || m.stopObserving != nil || len(m.tx) != 0 {
		t.Fatal("超時沒有回收")
	}
	// A full diagnostic log must retire the presentation without growing it.
	capped := &IntroMuseum{o: e.Oracle, active: true, pages: map[uint32]*museumPage{}, Events: make([]map[string]any, 512)}
	capped.tx = []museumTX{{at: 0x5d76, end: 0x5d8f, copy: true, sourcePage: 0, page: 0x4000}}
	capped.commit(0x5d8f)
	if !capped.failed || !capped.retired || len(capped.Events) != 512 || len(capped.tx) != 0 {
		t.Fatal("事件上限沒有回收")
	}
	// A mode callback must retire a pending drain without querying VGA state.
	capped.drain = &museumDrain{}
	capped.observeMuseumMode(PresentationModeChange{Step: e.Oracle.Steps()})
	if capped.drain != nil || capped.DrainStopReason != "mode-change" {
		t.Fatal("模式回呼未停止交接帶")
	}
	if !bytes.Equal(before, museumGuestState(t, e)) || inputs != len(e.InputEvents) {
		t.Fatal("metadata 診斷改動客體")
	}
	for _, tc := range []struct {
		seg, off uint16
		length   int
		valid    bool
	}{
		{0, 0, 4, true}, {0, 65532, 4, true}, {0, 65533, 4, false},
		{0x9fff, 0, 16, true}, {0x9fff, 1, 16, false}, {0xa000, 0, 4, false},
		{0xffff, 0xffff, 4, false}, {0x6000, 0, 21204, true}, {0, 0, 0, false},
	} {
		if museumSourceInRAM(tc.seg, tc.off, tc.length) != tc.valid {
			t.Fatal("RAM 邊界不符", tc)
		}
	}
}

func TestMuseumPreservesRealUpstreamTitleHold(t *testing.T) {
	e := storyEngine(t, museumTestAssets(t))
	if e.Museum == nil || e.Intro == nil {
		t.Fatal("需要完整正常博物館與標題")
	}
	storyAdvance(t, e, 1000)
	storyPress(t, e, 2)
	storyPress(t, e, 2)
	matched := false
	// Observe the ordinary Frame after a real guest call is in progress.
	// No callback-order assumption, guest writes, or injected entry.
	for i := 0; i < 1600 && !matched; i++ {
		storyAdvance(t, e, 10)
		display, ok := e.Oracle.PlanarDisplay()
		candidate := ok && e.Museum.valid() && e.Intro.hold != nil && !e.Museum.sceneSupported(e.Museum.pages[display.Start])
		visible := false
		if candidate {
			for _, tx := range e.Museum.tx {
				if tx.page == display.Start {
					visible = true
				}
			}
		}
		if !visible {
			e.Frame()
			continue
		}
		expected := e.Intro.hold
		before := museumGuestState(t, e)
		actual := e.Frame()
		if actual != expected || !bytes.Equal(actual.Pix, expected.Pix) || e.Museum.FrameStage(actual) != "" || e.IntroFrameStage(actual) != "title-transition" {
			t.Fatal("博物館覆蓋了已驗 Noto 標題保留幀")
		}
		if !bytes.Equal(before, museumGuestState(t, e)) {
			t.Fatal("首交接 Frame 改動客體")
		}
		matched = true
	}
	if !matched || e.Museum.TitleHandoffFrames == 0 {
		t.Fatal("沒有到達真正首館景交易", e.Museum.Status())
	}
}

func TestMuseumUnknownRuntimeSourceRetiresPresentation(t *testing.T) {
	e := storyEngine(t, museumTestAssets(t))
	if e.Museum == nil {
		t.Fatal(e.MuseumError)
	}
	// Host-only registry fault. The DOS program still follows its ordinary boot
	// and supplies its actual unchanged source bytes to the production guard.
	e.Museum.records = map[string]*museumRecord{}
	storyAdvance(t, e, 1000)
	storyPress(t, e, 2)
	storyPress(t, e, 2)
	for i := 0; i < 1000 && !e.Museum.failed; i++ {
		storyAdvance(t, e, 10)
		e.Frame()
	}
	m := e.Museum
	if !m.failed || !m.retired || m.active || m.stopObserving != nil || len(m.Errors) == 0 || len(m.tx) != 0 || len(m.pages) != 0 {
		t.Fatal("未知執行期來源沒有安全退休", m.Status())
	}
	before := museumGuestState(t, e)
	inputs := len(e.InputEvents)
	e.Frame()
	if e.SetFont("lishu") != nil || !bytes.Equal(before, museumGuestState(t, e)) || len(e.InputEvents) != inputs || e.GraphicsError != "" || e.StoryError != "" {
		t.Fatal("來源回退改動客體或其他 HD")
	}
}
