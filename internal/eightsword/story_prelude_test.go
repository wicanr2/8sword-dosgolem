package eightsword

import (
	"bytes"
	"encoding/json"
	"image"
	"os"
	"path/filepath"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

func preludeAssets(t *testing.T) string {
	t.Helper()
	dir := os.Getenv("EIGHTSWORD_TEST_STORY_PRELUDE_ASSETS")
	if dir == "" {
		t.Skip("requires selected local prelude pack")
	}
	return dir
}

func TestStoryPreludeNormalCoverageHandoffAndPurity(t *testing.T) {
	e := storyEngine(t, preludeAssets(t))
	p := e.Story.prelude
	if p == nil || e.Story.PreludeError != "" {
		t.Fatal("missing prelude", e.Story.PreludeError)
	}
	storyAdvance(t, e, 1000)
	storyPress(t, e, 2)
	storyPress(t, e, 2)
	storyAdvance(t, e, 13600) // Normal 15000 virtual ms; no entry injection.
	seen := map[string]bool{}
	var previous *image.RGBA
	var previousBytes []byte
	diagnosed := false
	for elapsed := 15010; elapsed <= 17600; elapsed += 10 {
		storyAdvance(t, e, 10)
		before := museumGuestState(t, e)
		im := e.Frame()
		if !bytes.Equal(before, museumGuestState(t, e)) {
			t.Fatal("prelude Frame changed guest")
		}
		if previous != nil && !bytes.Equal(previous.Pix, previousBytes) {
			t.Fatal("previous presented frame mutated")
		}
		stage := e.IntroFrameStage(im)
		seen[stage] = true
		if stage == "story-prelude" {
			if !diagnosed && p.written > 1000 && p.written < 63000 {
				probe := *p
				probe.source = append([]byte(nil), p.source...)
				next := p.order[p.written]
				original := probe.source[next]
				probe.source[next] ^= 1
				probe.observeWrite(oracle.VideoWrite{CS: 0xa3d, IP: 0xb6, Offset: next, Value: original})
				if probe.failure != "unknown-reveal-write" || !probe.retired || p.retired {
					t.Fatal("unknown source value not isolated")
				}
				for _, id := range []string{"lishu", "caoshu", "noto"} {
					if err := e.SetFont(id); err != nil {
						t.Fatal(err)
					}
					e.Frame()
				}
				if !bytes.Equal(im.Pix, e.Frame().Pix) || !bytes.Equal(before, museumGuestState(t, e)) {
					t.Fatal("font choice changed prelude or guest")
				}
				diagnosed = true
			}
			if p.written == 64000 && !bytes.Equal(im.Pix, p.art.Pix) {
				t.Fatal("complete reveal differs from approved art")
			}
			previous, previousBytes = im, append([]byte(nil), im.Pix...)
		}
		if stage == "story-prelude-handoff" && !bytes.Equal(im.Pix, p.art.Pix) {
			t.Fatal("incomplete handoff")
		}
	}
	for _, stage := range []string{"story-prelude", "story-prelude-handoff", "story-noto"} {
		if !seen[stage] {
			t.Fatal("normal stage missing", stage, p.Status())
		}
	}
	if !diagnosed || p.written != 64000 || p.black != 782 || !p.retired || p.stopReason != "story-background" || p.failure != "" || p.bridges == 0 || e.Story.Stats.Errors != nil {
		t.Fatal("normal reveal did not retire cleanly", p.Status(), e.Story.Stats)
	}
}

func TestStoryPreludeRejectedFilesAreAtomic(t *testing.T) {
	dir := preludeAssets(t)
	e := storyEngine(t, dir)
	before := museumGuestState(t, e)
	raw, err := os.ReadFile(filepath.Join(dir, "story-prelude.json"))
	if err != nil {
		t.Fatal(err)
	}
	png, err := os.ReadFile(filepath.Join(dir, "story-prelude.png"))
	if err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"bad-png", "missing-png", "symlink-png", "symlink-json", "trailing-json", "unknown-field", "schema", "shape", "path", "large-json", "large-png"} {
		t.Run(name, func(t *testing.T) {
			out := t.TempDir()
			mp := filepath.Join(out, "story-prelude.json")
			ip := filepath.Join(out, "story-prelude.png")
			if err := os.WriteFile(mp, raw, 0600); err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(ip, png, 0600); err != nil {
				t.Fatal(err)
			}
			var m map[string]any
			if err := json.Unmarshal(raw, &m); err != nil {
				t.Fatal(err)
			}
			switch name {
			case "bad-png":
				err = os.WriteFile(ip, append(append([]byte(nil), png...), 0), 0600)
			case "missing-png":
				err = os.Remove(ip)
			case "symlink-png":
				err = os.Remove(ip)
				if err == nil {
					err = os.Symlink(filepath.Join(dir, "story-prelude.png"), ip)
				}
			case "symlink-json":
				err = os.Remove(mp)
				if err == nil {
					err = os.Symlink(filepath.Join(dir, "story-prelude.json"), mp)
				}
			case "trailing-json":
				err = os.WriteFile(mp, append(append([]byte(nil), raw...), []byte(" {}")...), 0600)
			case "large-json":
				err = os.WriteFile(mp, make([]byte, 65537), 0600)
			case "large-png":
				err = os.WriteFile(ip, make([]byte, 8*1024*1024+1), 0600)
			default:
				switch name {
				case "unknown-field":
					m["unknown"] = true
				case "schema":
					m["schema"] = 2
				case "shape":
					m["width"] = 960
				case "path":
					m["image"] = "../story-prelude.png"
				}
				var b []byte
				b, err = json.Marshal(m)
				if err == nil {
					err = os.WriteFile(mp, b, 0600)
				}
			}
			if err != nil {
				t.Fatal(err)
			}
			if p, err := loadStoryPrelude(e.Story, out); err == nil || p != nil {
				t.Fatal("bad prelude published", p, err)
			}
		})
	}
	if p, err := loadStoryPrelude(e.Story, t.TempDir()); p != nil || err != nil {
		t.Fatal("missing optional prelude not compatible")
	}
	if !bytes.Equal(before, museumGuestState(t, e)) {
		t.Fatal("loader changed guest")
	}
}

func TestStoryPreludeMetadataTimeoutModeAndClose(t *testing.T) {
	e := storyEngine(t, preludeAssets(t))
	before := museumGuestState(t, e)
	p := e.Story.prelude
	for _, phase := range []string{"reveal", "handoff"} {
		probe := *p
		probe.phase = phase
		probe.startCycle = e.Oracle.Cycles() - 20000001
		probe.bridgeCycle = e.Oracle.Cycles() - titleTransactionLimit - 1
		probe.tick()
		if !probe.retired || probe.failure == "" || probe.cache != nil || probe.pending != nil {
			t.Fatal("unbounded lifetime", phase, probe.Status())
		}
	}
	probe := *p
	probe.phase = "wait"
	probe.written = 64000
	probe.mode(oracle.VideoModeChange{Mode: 0xe, Step: e.Oracle.Steps()})
	if probe.phase != "handoff" || probe.retired {
		t.Fatal("known mode handoff not retained")
	}
	probe.mode(oracle.VideoModeChange{Mode: 0xe, Step: e.Oracle.Steps()})
	if !probe.retired || probe.failure != "mode-change" {
		t.Fatal("same mode did not invalidate")
	}
	probe = *p
	probe.phase = "handoff"
	knownOwner := *e.Story
	knownOwner.Stats.Bound, knownOwner.Stats.Started = true, true
	knownOwner.Stats.Pages = 1
	knownOwner.active, knownOwner.inDraw = true, true
	probe.owner = &knownOwner
	probe.observeWrite(oracle.VideoWrite{Offset: 0})
	if !probe.retired || probe.failure != "unknown-handoff-write" {
		t.Fatal("unknown handoff write retained")
	}
	probe = *p
	owner := *e.Story
	owner.Stats.Bound = true
	probe.owner = &owner
	probe.begin()
	if !probe.retired || probe.failure != "entry-contract" {
		t.Fatal("foreign entry accepted")
	}
	if !bytes.Equal(before, museumGuestState(t, e)) {
		t.Fatal("metadata diagnosis changed guest")
	}
	e.Close()
	if !p.retired || p.stopReason != "close" {
		t.Fatal("Close left prelude")
	}
}

func TestStoryPreludeNormalHandoffWithoutPriorFrame(t *testing.T) {
	e := storyEngine(t, preludeAssets(t))
	storyAdvance(t, e, 1000)
	storyPress(t, e, 2)
	storyPress(t, e, 2)
	storyAdvance(t, e, 16080) // Normal 17480 ms, no Frame throughout the reveal.
	p := e.Story.prelude
	if p == nil || p.phase != "handoff" || p.composed != 0 || p.written != 64000 || p.black != 782 {
		t.Fatal("no-Frame normal handoff missing", p.Status())
	}
	before := museumGuestState(t, e)
	im := e.Frame()
	if e.IntroFrameStage(im) != "story-prelude-handoff" || !bytes.Equal(im.Pix, p.art.Pix) || !bytes.Equal(before, museumGuestState(t, e)) {
		t.Fatal("handoff depends on earlier rendering")
	}
	storyAdvance(t, e, 80) // First background returns without another Frame.
	if !p.retired || p.stopReason != "story-background" || p.cache != nil || p.source != nil || p.order != nil || p.pending != nil {
		t.Fatal("no-Frame lifetime not collected", p.Status())
	}
}
