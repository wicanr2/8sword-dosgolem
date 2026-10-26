package eightsword

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"image/png"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

func endingTestWrite(t *testing.T, path string, value any) {
	t.Helper()
	data, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(path, append(data, '\n'), 0644); err != nil {
		t.Fatal(err)
	}
}
func endingTestPaths(t *testing.T) (string, string, string) {
	t.Helper()
	root, assets, out := os.Getenv("EIGHTSWORD_TEST_ORIGINAL"), os.Getenv("EIGHTSWORD_TEST_ENDING_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ENDING_OUT")
	if root == "" || assets == "" || out == "" {
		t.Skip("ending fixture paths not supplied")
	}
	return root, assets, out
}

func TestEndingSourceRuntime(t *testing.T) {
	pairRequired := os.Getenv("EIGHTSWORD_TEST_ENDING_REQUIRE_PAIR") == "1"
	effectsOnly := os.Getenv("EIGHTSWORD_TEST_ENDING_EFFECTS_PREFIX") == "1"
	duelOnly := os.Getenv("EIGHTSWORD_TEST_ENDING_DUEL_PREFIX") == "1" || effectsOnly
	swordsOnly := os.Getenv("EIGHTSWORD_TEST_ENDING_SWORDS_PREFIX") == "1" || duelOnly
	root, assets, out := endingTestPaths(t)
	type result struct {
		state []byte
		pcm   string
		steps uint64
		files any
	}
	run := func(name string, hd, escape bool) result {
		dir := filepath.Join(out, name)
		if err := os.Mkdir(dir, 0755); err != nil {
			t.Fatal(err)
		}
		e, err := Open(Options{Root: root, Assets: assets, Saves: filepath.Join(dir, "scratch"), HD: hd})
		if err != nil {
			t.Fatal(err)
		}
		defer e.Close()
		if hd && (e.EndingError != "" || e.AssetError != "") {
			t.Fatalf("asset errors: %s / %s", e.EndingError, e.AssetError)
		}
		if hd {
			if pairRequired && (len(e.endingAssets.art.pair) != 4 || e.endingAssets.pairError != "") {
				t.Fatal("required END6 pair group not loaded")
			}
			if os.Getenv("EIGHTSWORD_TEST_ENDING_REQUIRE_PORTRAIT") == "1" && (len(e.endingAssets.art.portraits) != 5 || e.endingAssets.portraitError != "") {
				t.Fatal("required END5 portrait group not loaded")
			}
			for key, value := range e.Status() {
				if message, ok := value.(string); ok && strings.HasSuffix(key, "_error") && message != "" {
					t.Fatalf("candidate silently lost HD group %s: %s", key, message)
				}
			}
			if e.Music.LoadError != "" {
				t.Fatal(e.Music.LoadError)
			}
			toolbar, err := LoadPosterToolbar(assets, e.FontChoices())
			if err != nil || toolbar == nil || toolbar.Error != "" {
				t.Fatalf("poster group unavailable: %v / %v", toolbar, err)
			}
		}
		e.Oracle.SetClock(12, 0, 0, 0)
		e.EnableLiveClock(3000)
		audio := e.Oracle.NewAudio(48000)
		pcm := sha256.New()
		var scene string
		bound := false
		endingSamples := map[string]bool{}
		portraitSamples := map[string]bool{}
		var portraitSnapshots []map[string]any
		var snapshots []map[string]any
		var mutations []map[string]any
		var escaped bool
		must := func(err error) {
			if err != nil {
				t.Fatal(err)
			}
		}
		saveFrame := func(file string) {
			f, er := os.Create(filepath.Join(dir, file))
			must(er)
			must(png.Encode(f, e.Frame()))
			must(f.Close())
			if e.renderFault != nil {
				t.Fatal(e.renderFault)
			}
		}
		sample := func() {
			if !hd || e.ending == nil || !e.ending.bound || !e.ending.scene.mode || e.ending.active != 0 {
				return
			}
			p := e.ending
			page := p.scene.pages[p.scene.active]
			stage := page.stage
			if stage == "END5.AY" && len(p.assets.art.portraits) == 5 && page.glyphs > 0 {
				eye, mouth := 1, 4
				for _, command := range page.ops {
					if command.Kind != "bitmap" || command.SourceFile != "END5.AY" {
						continue
					}
					for i, source := range endingPortraitSources {
						if command.SourceSHA != source {
							continue
						}
						switch i {
						case 0:
							eye, mouth = 1, 4
						case 1, 2:
							eye = i
						case 3, 4:
							mouth = i
						}
					}
				}
				key := fmt.Sprintf("eye-%d-mouth-%d", eye, mouth)
				if !portraitSamples[key] {
					before := observerGuestState(t, e)
					saveFrame("portrait-" + key + ".png")
					if !bytes.Equal(before, observerGuestState(t, e)) {
						t.Fatal("portrait Frame changed guest")
					}
					display, ok := e.Oracle.PlanarDisplay()
					if !ok {
						t.Fatal("portrait display absent")
					}
					endingTestWrite(t, filepath.Join(dir, "portrait-"+key+".json"), map[string]any{"stage": stage, "pose": key, "font": e.FontID(), "step": e.Oracle.Steps(), "palette": display.Palette, "ops": page.ops, "pure": true})
					portraitSamples[key] = true
					portraitSnapshots = append(portraitSnapshots, map[string]any{"pose": key, "step": e.Oracle.Steps()})
				}
			}
			if swordsOnly {
				found := false
				for _, command := range page.ops {
					if command.SourceSHA == endingSwordsSource {
						found = true
					}
				}
				if effectsOnly && stage == "END2.AY" {
					found = false
					for _, command := range page.ops {
						if command.SourceSHA == endingEffectsSources[7] {
							found = true
						}
					}
					if !found {
						return
					}
					if len(p.assets.art.effects) != 11 || p.assets.effectsError != "" {
						t.Fatal("結局效果候選未載入")
					}
				} else if duelOnly && stage == "END1.AY" {
					found = false
					for _, command := range page.ops {
						if command.SourceSHA == endingDuelSource {
							found = true
						}
					}
					if !found || p.assets.art.duel == nil || p.assets.duelError != "" {
						t.Fatal("對峙人物候選未載入")
					}
				} else if stage != "END3.AY" || !found {
					return
				}
				if p.assets.art.swords == nil || p.assets.swordsError != "" {
					t.Fatal("八劍候選未載入")
				}
			} else if stage != "END5.AY" && stage != "END7.AY" && stage != "END8.AY" && stage != "END9.AY" && !(pairRequired && stage == "END6.AY") {
				return
			}
			if stage == "END6.AY" {
				found := false
				for _, command := range page.ops {
					found = found || p.assets.art.pair[command.SourceSHA] != nil
				}
				if !found {
					return
				}
			}
			if endingSamples[stage] || ((stage == "END5.AY" || stage == "END9.AY") && page.glyphs == 0) {
				return
			}
			endingSamples[stage] = true
			prefix := fmt.Sprintf("sample-%02d", len(endingSamples))
			before := filepath.Join(dir, prefix+"-before.state")
			after := filepath.Join(dir, prefix+"-after.state")
			must(e.Oracle.SaveStateFile(before))
			display, ok := e.Oracle.PlanarDisplay()
			if !ok {
				t.Fatal("missing display")
			}
			native := renderEndingPage(page, display.Palette, p.assets.art, nil)
			w, h, rgb := e.Oracle.ScreenRGB()
			if w != 640 || h != 200 {
				t.Fatal("native layout")
			}
			for y := 0; y < h; y++ {
				for x := 0; x < w; x++ {
					at := (y*w + x) * 3
					c := native.RGBAAt(x*3, y*6)
					if c.R != rgb[at] || c.G != rgb[at+1] || c.B != rgb[at+2] {
						t.Fatalf("native ending source differs %s %d,%d", stage, x, y)
					}
				}
			}
			f, er := os.Create(filepath.Join(dir, prefix+"-native.png"))
			must(er)
			must(png.Encode(f, native))
			must(f.Close())
			for _, font := range []string{"noto", "lishu", "caoshu"} {
				must(e.SetFont(font))
				saveFrame(prefix + "-" + font + ".png")
			}
			must(e.SetFont("noto"))
			must(e.Oracle.SaveStateFile(after))
			a, er := os.ReadFile(before)
			must(er)
			b, er := os.ReadFile(after)
			must(er)
			if !bytes.Equal(a, b) {
				t.Fatal("ending Frame changed guest")
			}
			endingTestWrite(t, filepath.Join(dir, prefix+".json"), map[string]any{"stage": stage, "step": e.Oracle.Steps(), "palette": display.Palette, "ops": page.ops, "glyphs": page.glyphs, "pure": true})
			snapshots = append(snapshots, map[string]any{"stage": stage, "prefix": prefix, "step": e.Oracle.Steps()})
			t.Log(name, stage, e.Oracle.Steps())
		}
		fixture, er := loadEndingAssets(assets, root)
		must(er)
		observerBound := false
		lastStage, visibleStage := "", ""
		tick := 0
		advance := func(ms int) {
			for ; ms > 0 && !e.Exited; ms -= 10 {
				must(e.AdvanceCycles(30000))
				if e.Oracle.Steps() > 230000000 {
					t.Fatal("bounded ending path exceeded")
				}
				if !bound && e.PAMLoaded {
					bound = true
					load := e.Oracle.Overlays()[0].Seg
					e.Oracle.OnCall(oracle.Addr{Seg: load + 0x13c2, Off: 0xae3}, func(q *oracle.Oracle) {
						if e.inEndingPhase() {
							return
						}
						switch q.Arg(0) {
						case 158, 218, 278:
							scene = "main-menu"
						case 338, 398:
							scene = "new-game-confirm"
						case 990, 1010, 1030, 1050, 1070, 1090, 1110:
							scene = "map"
						case 1170, 1182, 1194, 1206, 1218, 1230, 1242:
							scene = "character"
						case 12742, 12762, 12782, 12802, 12822, 12842:
							scene = "system-menu"
						}
					})
					e.Oracle.OnCall(oracle.Addr{Seg: load, Off: 0x20e}, func(q *oracle.Oracle) {
						if e.inEndingPhase() || len(mutations) > 0 {
							return
						}
						r := q.Regs()
						at := oracle.Addr{Seg: r.DS, Off: 0x56e2}
						old := q.Word(at)
						q.WriteU16(at, 1)
						mutations = append(mutations, map[string]any{"step": q.Steps(), "address": at, "old": old, "new": 1})
					})
				}
				if !observerBound && e.inEndingPhase() {
					observerBound = true
					for _, spec := range []struct {
						entry, ret uint16
						planes     int
					}{{0x4ec, 0x61f, 6}, {0x769, 0x84e, 5}, {0x996, 0xa69, 4}} {
						spec := spec
						pending := ""
						e.Oracle.OnCall(oracle.Addr{Seg: 0x393, Off: spec.entry}, func(q *oracle.Oracle) {
							ptr := oracle.Addr{Seg: q.Arg(1), Off: q.Arg(0)}
							w, h := int(q.Word(ptr)), int(q.Word(oracle.Addr{Seg: ptr.Seg, Off: ptr.Off + 2}))
							if w < 1 || w > 80 || h < 1 || h > 200 {
								t.Fatal("observer source bounds")
							}
							pending = fixture.manifest.Sources[hash(q.Bytes(ptr, 4+w*h*spec.planes))]
						})
						e.Oracle.OnCall(oracle.Addr{Seg: 0x393, Off: spec.ret}, func(*oracle.Oracle) {
							if pending != "" {
								lastStage = pending
								pending = ""
							}
						})
					}
					e.Oracle.OnCall(oracle.Addr{Seg: 0x393, Off: 0x1a3}, func(*oracle.Oracle) { visibleStage = lastStage })
				}
				_ = e.RenderAudio()
				samples := audio.Render()
				raw := make([]byte, len(samples)*2)
				for i, v := range samples {
					raw[i*2], raw[i*2+1] = byte(v), byte(uint16(v)>>8)
				}
				pcm.Write(raw)
				tick++
				if tick%10 == 0 && hd {
					_ = e.Frame()
					if e.renderFault != nil {
						t.Fatal(e.renderFault)
					}
					sample()
				}
				if escape && !escaped && visibleStage == "END5.AY" {
					must(e.Oracle.SaveStateFile(filepath.Join(dir, "escape-before.state")))
					must(e.Key(1, true))
					must(e.Key(1, false))
					escaped = true
				}
			}
		}
		press := func(scan uint8) { must(e.Key(scan, true)); advance(100); must(e.Key(scan, false)); advance(150) }
		advance(200)
		press(2)
		press(2)
		advance(500)
		if !e.PAMLoaded {
			press(1)
		}
		for n := 0; n < 300 && scene != "main-menu"; n++ {
			advance(100)
		}
		if scene != "main-menu" {
			t.Fatal("main menu not reached")
		}
		advance(500)
		saveFrame("01-main-menu.png")
		press(0x50)
		press(0x1c)
		advance(500)
		press(0x1c)
		advance(3000)
		if scene != "map" {
			t.Fatal("map not reached")
		}
		saveFrame("02-map.png")
		press(0x3b)
		advance(500)
		saveFrame("03-character.png")
		press(1)
		advance(500)
		press(0x3c)
		advance(500)
		saveFrame("04-army.png")
		press(1)
		advance(500)
		press(0x41)
		advance(500)
		press(0x4d)
		press(0x1c)
		advance(500)
		press(0x1c)
		for n := 0; n < 12000 && !e.Exited && !(swordsOnly && visibleStage == "END4.AY"); n++ {
			advance(10)
		}
		if !swordsOnly && (!e.Exited || e.ExitCode != 0) {
			t.Fatal("original ending did not exit zero")
		}
		expectedPrefixSamples := 1
		if duelOnly {
			expectedPrefixSamples = 2
		}
		if effectsOnly {
			expectedPrefixSamples = 3
		}
		if hd && swordsOnly && len(endingSamples) != expectedPrefixSamples {
			t.Fatal("八劍代表缺席")
		}
		if swordsOnly && visibleStage != "END4.AY" {
			t.Fatal("未到前綴停止邊界")
		}
		expectedSamples := 4
		if pairRequired {
			expectedSamples = 5
		}
		if hd && !swordsOnly && !escape && len(endingSamples) != expectedSamples {
			t.Fatalf("ending samples missing %v", endingSamples)
		}
		if hd && !swordsOnly && !escape && os.Getenv("EIGHTSWORD_TEST_ENDING_REQUIRE_PORTRAIT") == "1" && len(portraitSamples) < 3 {
			t.Fatalf("END5 representative states absent: %v", portraitSamples)
		}
		if escape && !escaped {
			t.Fatal("Esc not sent")
		}
		if os.Getenv("EIGHTSWORD_TEST_ENDING_REQUIRE_DIRECT") == "1" {
			if !e.endingInputSupported {
				t.Fatal("input revision API not active")
			}
			if hd && (e.ending.directCounts["glyph-go-rows"] == 0 || e.ending.directCounts["masked-skipped-x86"] == 0 || e.ending.directCounts["direct-skipped-x86-instructions"] == 0) {
				t.Fatalf("actual ending Go work missing %v", e.ending.directCounts)
			}
		}
		stateFile := filepath.Join(dir, "final.state")
		must(e.Oracle.SaveStateFile(stateFile))
		state, er := os.ReadFile(stateFile)
		must(er)
		endingTestWrite(t, filepath.Join(dir, "runtime.json"), map[string]any{"hd": hd, "escape": escape, "steps": e.Oracle.Steps(), "state_sha256": hash(state), "native_pcm_sha256": fmt.Sprintf("%x", pcm.Sum(nil)), "mutations": mutations, "snapshots": snapshots, "portrait_snapshots": portraitSnapshots, "ending": e.EndingStatus(), "inputs": e.InputEvents, "overlays": e.Oracle.Overlays(), "file_ops": e.Oracle.FileOps(), "music": e.Music.Status(), "unimplemented": e.Oracle.Unimplemented()})
		return result{state: state, pcm: fmt.Sprintf("%x", pcm.Sum(nil)), steps: e.Oracle.Steps(), files: e.Oracle.FileOps()}
	}
	native := run("native", false, false)
	hd := run("hd", true, false)
	if !bytes.Equal(native.state, hd.state) || native.steps != hd.steps || native.pcm != hd.pcm {
		t.Fatalf("native/HD ending guest or native audio differs steps %d/%d pcm %s/%s", native.steps, hd.steps, native.pcm, hd.pcm)
	}
	if old := os.Getenv("EIGHTSWORD_TEST_ENDING_OLD_CONTROL"); old != "" {
		previous, err := os.ReadFile(old)
		if err != nil {
			t.Fatal(err)
		}
		if !bytes.Equal(previous, native.state) {
			t.Fatal("input retirement changed original guest state")
		}
	}
	if swordsOnly {
		return
	}
	nativeEsc := run("native-escape", false, true)
	hdEsc := run("hd-escape", true, true)
	if !bytes.Equal(nativeEsc.state, hdEsc.state) || nativeEsc.steps != hdEsc.steps || nativeEsc.pcm != hdEsc.pcm {
		t.Fatal("native/HD BIOS Esc differs")
	}
}

func TestEndingInputHandoffGuard(t *testing.T) {
	root, _, out := endingTestPaths(t)
	e, err := Open(Options{Root: root, Saves: filepath.Join(out, "input-guard"), HD: false})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	api, ok := any(e.Oracle).(interface{ DiscardStalledKeyboardInput() (int, int, int, error) })
	if !ok {
		t.Skip("core input revision not installed")
	}
	o := e.Oracle
	before := hash(o.Bytes(oracle.Addr{}, 0xa0000))
	regs, step, cycles := o.Regs(), o.Steps(), o.Cycles()
	o.KeyDown(0x1c)
	queued, timed, held, err := api.DiscardStalledKeyboardInput()
	if err != nil || queued != 0 || timed != 1 || held != 1 {
		t.Fatalf("discard counts %d %d %d %v", queued, timed, held, err)
	}
	if o.Regs() != regs || o.Steps() != step || o.Cycles() != cycles || hash(o.Bytes(oracle.Addr{}, 0xa0000)) != before || len(o.HeldKeys()) != 0 {
		t.Fatal("discard changed guest or retained held input")
	}
	o.WriteU16(oracle.Addr{Off: 0x26}, 0x1234)
	o.KeyDown(0x1c)
	if _, _, _, err = api.DiscardStalledKeyboardInput(); err == nil || len(o.HeldKeys()) != 1 {
		t.Fatal("active IRQ1 consumer was not protected")
	}
	o.WriteU16(oracle.Addr{Off: 0x26}, 0x80)
	if _, timed, held, err = api.DiscardStalledKeyboardInput(); err != nil || timed != 1 || held != 1 {
		t.Fatal("rejected discard modified queues")
	}
}

func TestEndingAssetsFaults(t *testing.T) {
	root, assets, _ := endingTestPaths(t)
	for _, name := range []string{"ending.json", "ending-font-noto.png", "ending-end7-r2.png", "ending-title-lishu.png", "ending-font-lishu.png"} {
		t.Run(name, func(t *testing.T) {
			dir := t.TempDir()
			entries, err := os.ReadDir(assets)
			if err != nil {
				t.Fatal(err)
			}
			for _, entry := range entries {
				data, readErr := os.ReadFile(filepath.Join(assets, entry.Name()))
				if readErr != nil {
					t.Fatal(readErr)
				}
				if err = os.WriteFile(filepath.Join(dir, entry.Name()), data, 0644); err != nil {
					t.Fatal(err)
				}
			}
			target := filepath.Join(dir, name)
			if err = os.Remove(target); err != nil {
				t.Fatal(err)
			}
			if err = os.WriteFile(target, []byte("broken ending fixture"), 0644); err != nil {
				t.Fatal(err)
			}
			required := name == "ending.json" || name == "ending-font-noto.png"
			fixture, loadErr := loadEndingAssets(dir, root)
			if required && loadErr == nil {
				t.Fatal("corrupt required ending data accepted")
			}
			if !required {
				if loadErr != nil || fixture == nil || len(fixture.fallbacks) == 0 {
					t.Fatal("optional ending image blocked source fallback")
				}
				if name == "ending-end7-r2.png" && fixture.art.end7 != nil {
					t.Fatal("broken END7 retained")
				}
				if name == "ending-title-lishu.png" && fixture.art.titles["lishu"] != nil {
					t.Fatal("broken title retained")
				}
				if name == "ending-font-lishu.png" && fixture.profile("lishu").ID != "noto" {
					t.Fatal("broken optional font did not fall back to Noto")
				}
			}
			e, err := Open(Options{Root: root, Assets: dir, Saves: filepath.Join(t.TempDir(), "saves"), HD: true})
			if err != nil {
				t.Fatal(err)
			}
			defer e.Close()
			if !e.HD || e.AssetError != "" || e.EndingError == "" {
				t.Fatal("ending fault leaked into PAM base assets")
			}
		})
	}
}
