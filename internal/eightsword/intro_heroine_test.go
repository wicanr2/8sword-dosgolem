package eightsword

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

func TestHeroineNormalOcclusionAndFramePurity(t *testing.T) {
	dir := os.Getenv("EIGHTSWORD_TEST_HEROINE_ASSETS")
	if dir == "" {
		t.Skip("需要女主角素材")
	}
	e := storyEngine(t, dir)
	if e.HeroineError != "" || e.Heroine == nil {
		t.Fatal(e.HeroineError)
	}
	storyAdvance(t, e, 1000)
	storyPress(t, e, 2)
	storyPress(t, e, 2)
	seen := false
	for i := 0; i < 900; i++ {
		storyAdvance(t, e, 10)
		frame := e.Frame()
		if e.Heroine.FramePixels(frame) > 0 {
			if n := e.Heroine.FramePixels(frame); n != 42034 {
				t.Fatalf("native occlusion differs: %d", n)
			}
			path := filepath.Join(t.TempDir(), "state")
			e.Oracle.SaveStateFile(path)
			before, _ := os.ReadFile(path)
			inputs := len(e.InputEvents)
			noto := append([]byte(nil), frame.Pix...)
			for _, id := range []string{"lishu", "caoshu", "noto"} {
				if err := e.SetFont(id); err != nil {
					t.Fatal(err)
				}
				e.Frame()
			}
			if !bytes.Equal(noto, e.Frame().Pix) {
				t.Fatal("字型切回改動特寫")
			}
			e.Oracle.SaveStateFile(path)
			after, _ := os.ReadFile(path)
			if !bytes.Equal(before, after) || len(e.InputEvents) != inputs {
				t.Fatal("特寫／字型修改客體")
			}
			seen = true
			break
		}
	}
	if !seen || len(e.Heroine.Stats.Errors) != 0 {
		t.Fatal("沒有正常近景", e.Heroine.Status())
	}
	// Exercise only host page bookkeeping from the real reached portrait state.
	m := e.Heroine
	if m.pages[0] == nil || m.pages[0].count != 42034 {
		t.Fatal("原版目的頁不符")
	}
	m.tx = []heroineTX{{at: 0x5d76, end: 0x5d8f, page: 0x4000, sourcePage: 0}}
	m.commit(0x5d8f)
	if m.pages[0x4000] == nil || m.pages[0x4000].count != 42034 {
		t.Fatal("複製未保存所有權")
	}
	m.pages[0x4000].bits[0] = false
	if !m.pages[0].bits[0] {
		t.Fatal("複製共用了可寫 mask")
	}
	m.tx = []heroineTX{{at: 0x5b0c, end: 0x5b42, page: 0x4000}}
	m.commit(0x5b42)
	if m.pages[0x4000] != nil || m.pages[0] == nil {
		t.Fatal("清頁影響另一頁")
	}
	// Metadata-only transaction and invalidation are diagnostic, not guest writes.
	statePath := filepath.Join(t.TempDir(), "diagnostic.state")
	if err := e.Oracle.SaveStateFile(statePath); err != nil {
		t.Fatal(err)
	}
	before, err := os.ReadFile(statePath)
	if err != nil {
		t.Fatal(err)
	}
	inputs := len(e.InputEvents)
	baseline := append([]byte(nil), e.Frame().Pix...)
	m.tx = []heroineTX{{at: 0x5d76, end: 0x5d8f, page: 0x4000, sourcePage: 0}}
	m.commit(0x5d8f)
	hold := m.nativeRect()
	m.paint(hold, m.pages[0], m.art.Bounds().Min)
	m.tx = []heroineTX{{at: 0x5d9c, end: 0x5db5, page: 0, sourcePage: 0x4000, start: m.o.Cycles(), hold: hold}}
	held := e.Frame()
	if m.FramePixels(held) != -1 || !bytes.Equal(baseline, held.Pix) {
		t.Fatal("可見頁交易沒有保留完整呈現")
	}
	m.observeWrite(PresentationWrite{Offset: 0x4000 + 20*80 + 14, CS: 0x123, IP: 0x456, WriteMode: 0})
	if m.pages[0] != nil || m.pages[0x4000] != nil || !m.tx[0].invalid || m.tx[0].hold != nil {
		t.Fatal("未知來源頁寫入沒有使複製交易失效")
	}
	m.commit(0x5db5)
	if m.pages[0] != nil || m.FramePixels(e.Frame()) != 0 {
		t.Fatal("失效的交易重新提交了近景")
	}
	if err = e.Oracle.SaveStateFile(statePath); err != nil {
		t.Fatal(err)
	}
	after, err := os.ReadFile(statePath)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(before, after) || len(e.InputEvents) != inputs {
		t.Fatal("呈現診斷修改了客體")
	}
}
func TestHeroineRealAssetFailureAndRAMBounds(t *testing.T) {
	dir := os.Getenv("EIGHTSWORD_TEST_HEROINE_ASSETS")
	if dir == "" {
		t.Skip("需要女主角素材")
	}
	tmp := t.TempDir()
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		b, err := os.ReadFile(filepath.Join(dir, entry.Name()))
		if err != nil {
			t.Fatal(err)
		}
		if entry.Name() == "intro-heroine.png" {
			b = append(b, 0)
		}
		if err = os.WriteFile(filepath.Join(tmp, entry.Name()), b, 0600); err != nil {
			t.Fatal(err)
		}
	}
	e := storyEngine(t, tmp)
	if e.Heroine != nil || e.HeroineError == "" || e.FontError != "" || e.PublisherError != "" || e.GraphicsError != "" || e.SetFont("lishu") != nil {
		t.Fatal("故障影響其他呈現", e.HeroineError)
	}
	goodPNG, err := os.ReadFile(filepath.Join(dir, "intro-heroine.png"))
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(tmp, "intro-heroine.png"), goodPNG, 0600); err != nil {
		t.Fatal(err)
	}
	manifest, err := os.ReadFile(filepath.Join(dir, "intro-heroine.json"))
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(tmp, "intro-heroine.json"), bytes.Replace(manifest, []byte(heroineArtSHA), []byte("unknown"), 1), 0600); err != nil {
		t.Fatal(err)
	}
	unknown := storyEngine(t, tmp)
	if unknown.Heroine != nil || unknown.HeroineError == "" {
		t.Fatal("未知來源被接受")
	}
	if err = os.WriteFile(filepath.Join(tmp, "intro-heroine.json"), manifest, 0600); err != nil {
		t.Fatal(err)
	}
	if err = os.Remove(filepath.Join(tmp, "intro-heroine.png")); err != nil {
		t.Fatal(err)
	}
	if err = os.Symlink(filepath.Join(dir, "intro-heroine.png"), filepath.Join(tmp, "intro-heroine.png")); err != nil {
		t.Fatal(err)
	}
	linked := storyEngine(t, tmp)
	if linked.Heroine != nil || linked.HeroineError == "" {
		t.Fatal("符號連結圖片被接受")
	}
	for _, v := range []struct {
		seg, off uint16
		n        int
		ok       bool
	}{{0x6000, 0, 21204, true}, {0, 0, 4, true}, {0x9fff, 15, 1, true}, {0x9fff, 16, 1, false}, {0x6000, 65535, 2, false}, {0x6000, 65535, 1, true}, {0xa000, 0, 1, false}, {0x6000, 0, 0, false}} {
		if heroineRAM(v.seg, v.off, v.n) != v.ok {
			t.Fatal(v)
		}
	}
}
