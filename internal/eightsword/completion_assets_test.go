package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/wicanr2/dosgolem/oracle"
	"image"
	"image/draw"
	"image/png"
	"os"
	"path/filepath"
	"testing"
)

func completionTestPaths(t *testing.T) (string, string, string) {
	t.Helper()
	project, assets, out := os.Getenv("EIGHTSWORD_GLYPH_PROJECT"), os.Getenv("EIGHTSWORD_TEST_COMPLETION_ASSETS"), os.Getenv("EIGHTSWORD_TEST_COMPLETION_OUT")
	if project == "" || assets == "" || out == "" {
		t.Skip("需054來源、候選與新輸出")
	}
	return project, assets, out
}

func TestCompletionSolidPalette(t *testing.T) {
	s := &ownedScene{Pixels: make([]ownedPixel, 65536*8), Glyphs: map[uint32]*glyph{1: {ID: 1, Width: 1, Source: 990}}}
	s.Pixels[0].Text.ID = 1
	tile := image.NewRGBA(image.Rect(0, 0, 24, 18))
	for at := 0; at < len(tile.Pix); at += 4 {
		tile.Pix[at+1], tile.Pix[at+3] = 170, 255
	}
	art := &GraphicsAssets{Materials: map[uint16]*graphicMaterial{67: {8, 3, tile}}}
	for y := 191; y < 199; y++ {
		for x := 0; x < 464; x++ {
			s.Pixels[y*640+x] = ownedPixel{Color: []uint8{2, 10, 14}[y%3], Material: graphicCell{ID: 67, Local: uint32((y%3)*8+x%8)}}
		}
	}
	for _, palette := range []*presentationPalette{nil, {}} {
		actual, _ := prepareOwnedBatch(s, art, palette)
		control, _ := prepareOwnedBatch(s, nil, palette)
		got, want := image.NewRGBA(image.Rect(0, 0, 1920, 1200)), image.NewRGBA(image.Rect(0, 0, 1920, 1200))
		if err := submitOwnedBatch(got, &actual); err != nil { t.Fatal(err) }
		if err := submitOwnedBatch(want, &control); err != nil { t.Fatal(err) }
		if !bytes.Equal(got.Pix, want.Pix) { t.Fatal("solid swatch changed source colors or approved status palette") }
	}
}
func TestCompletionLoadAndAtomicFallback(t *testing.T) {
	project, assets, _ := completionTestPaths(t)
	root := filepath.Join(project, "workplace/intake-20261023/sources/game/8sword")
	a, err := loadCompletionAssets(assets, root)
	if err != nil || a == nil || len(a.Records) != 62 || len(a.ending) != 8 {
		t.Fatal(err)
	}
	for _, kind := range []string{"legacy", "manifest", "last-archive-png", "source", "symlink"} {
		t.Run(kind, func(t *testing.T) {
			dir := t.TempDir()
			for _, r := range a.Records {
				data, err := os.ReadFile(filepath.Join(assets, r.Image))
				if err != nil {
					t.Fatal(err)
				}
				if err := os.WriteFile(filepath.Join(dir, r.Image), data, 0644); err != nil {
					t.Fatal(err)
				}
			}
			data, _ := os.ReadFile(filepath.Join(assets, "completion.json"))
			os.WriteFile(filepath.Join(dir, "completion.json"), data, 0644)
			src := root
			switch kind {
			case "legacy":
				os.Remove(filepath.Join(dir, "completion.json"))
			case "manifest":
				os.WriteFile(filepath.Join(dir, "completion.json"), []byte("bad"), 0644)
			case "last-archive-png":
				os.Remove(filepath.Join(dir, a.Records[len(a.Records)-1].Image))
			case "source":
				src = t.TempDir()
			case "symlink":
				os.Remove(filepath.Join(dir, a.Records[0].Image))
				os.Symlink(filepath.Join(assets, a.Records[0].Image), filepath.Join(dir, a.Records[0].Image))
			}
			got, err := loadCompletionAssets(dir, src)
			if got != nil || (err == nil) != (kind == "legacy") {
				t.Fatal("group fallback", kind, err)
			}
		})
	}
	e, err := Open(Options{Root: root, Assets: assets, Saves: t.TempDir(), HD: false})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	if e.completion != nil {
		t.Fatal("original mode loaded HD completion")
	}
}
func TestCompletionEndingSourceReplay(t *testing.T) {
	project, assets, out := completionTestPaths(t)
	root := filepath.Join(project, "workplace/intake-20261023/sources/game/8sword")
	e, err := Open(Options{Root: root, Assets: assets, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	if e.CompletionError != "" || e.endingAssets == nil || len(e.endingAssets.art.completion) != 8 {
		t.Fatal(e.Status())
	}
	a := e.endingAssets
	if err := os.MkdirAll(filepath.Join(out, "ending-controlled"), 0755); err != nil {
		t.Fatal(err)
	}
	for _, r := range e.completion.Records {
		if r.Route != "ending" {
			continue
		}
		t.Run(fmt.Sprintf("%s-%d", r.SourceFile, r.Record), func(t *testing.T) {
			raw, err := os.ReadFile(filepath.Join(project, "workplace/probe-20261023/graphics-first/all-graphics-integration-r1/sources-r1", fmt.Sprintf("%s-%02d.bin", replaceCompletionName(r.SourceFile), r.Record)))
			if err != nil || hash(raw) != r.SourceSHA {
				t.Fatal(err)
			}
			pixels, mask := decodeEndingBitmap(raw, r.Planes, r.NativeWidth, r.NativeHeight)
			p := newEndingScene().pages[0]
			base := &endingCommand{Kind: "bitmap", W: 640, H: 200, Pixels: make([]byte, 128000), Mask: make([]byte, 128000), SourceSHA: "base"}
			for i := range base.Pixels {
				base.Pixels[i] = 12
				base.Mask[i] = 1
			}
			p.apply(base)
			x := 8
			if r.NativeWidth == 640 {
				x = 0
			}
			c := &endingCommand{Kind: "bitmap", X: x, Y: 25, W: r.NativeWidth, H: r.NativeHeight, SourceFile: r.SourceFile, SourceSHA: r.SourceSHA, Pixels: pixels, Mask: mask}
			p.apply(c)
			before := append([]byte(nil), p.native...)
			for _, font := range []string{"noto", "lishu", "caoshu"} {
				frame := renderEndingPage(p, endingPalette, a.art, a.profile(font))
				p.apply(c)
				again := renderEndingPage(p, endingPalette, a.art, a.profile(font))
				if !bytes.Equal(frame.Pix, again.Pix) || !bytes.Equal(before, p.native) {
					t.Fatal("repeat or native state changed")
				}
				file := fmt.Sprintf("%s-%02d-%s.png", replaceCompletionName(r.SourceFile), r.Record, font)
				f, er := os.Create(filepath.Join(out, "ending-controlled", file))
				if er != nil {
					t.Fatal(er)
				}
				if er = png.Encode(f, frame); er != nil {
					t.Fatal(er)
				}
				f.Close()
			}
			legacy := a.art
			legacy.completion = nil
			if !bytes.Equal(renderEndingPage(p, endingPalette, legacy, nil).Pix, renderEndingPage(p, endingPalette, a.art, nil).Pix) {
				t.Fatal("native renderer changed")
			}
			meta := map[string]any{"stage": r.SourceFile, "ops": p.ops, "font": "noto", "palette": endingPalette, "record": r.Record}
			endingTestWrite(t, filepath.Join(out, "ending-controlled", fmt.Sprintf("%s-%02d.json", replaceCompletionName(r.SourceFile), r.Record)), meta)
		})
	}
}
func replaceCompletionName(s string) string {
	b := []byte(s)
	for i, c := range b {
		if c == '.' {
			b[i] = '-'
		} else if c >= 'A' && c <= 'Z' {
			b[i] = c + 32
		}
	}
	return string(b)
}

func TestCompletionControlledPAM(t *testing.T) {
	project, assets, out := completionTestPaths(t)
	root := filepath.Join(project, "workplace/intake-20261023/sources/game/8sword")
	var engines [2]*Engine
	for i := range engines {
		dir := assets
		if i == 1 {
			dir = filepath.Join(project, "workplace/player/assets-painted-r64")
		}
		e, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
		if err != nil {
			t.Fatal(err)
		}
		t.Cleanup(e.Close)
		e.Oracle.SetClock(12, 0, 0, 0)
		e.EnableLiveClock(3000)
		engines[i] = e
	}
	e, control := engines[0], engines[1]
	if e.CompletionError != "" || e.completion == nil {
		t.Fatal(e.Status())
	}
	advance := func(ms int) {
		t.Helper()
		for at := 0; at < ms; at += 10 {
			for _, v := range engines {
				if err := v.AdvanceCycles(30000); err != nil {
					t.Fatal(err)
				}
			}
			if !bytes.Equal(int16Bytes(e.RenderAudio()), int16Bytes(control.RenderAudio())) {
				t.Fatal("PCM changed")
			}
		}
		for _, v := range engines {
			before := observerGuestState(t, v)
			v.Frame()
			if !bytes.Equal(before, observerGuestState(t, v)) || v.renderFault != nil {
				t.Fatal("ordinary Frame changed state or fault", v.Status())
			}
		}
		if !bytes.Equal(observerGuestState(t, e), observerGuestState(t, control)) {
			t.Fatal("guest changed")
		}
	}
	press := func(scan byte) {
		for _, v := range engines {
			if err := v.Key(scan, true); err != nil {
				t.Fatal(err)
			}
		}
		advance(100)
		for _, v := range engines {
			if err := v.Key(scan, false); err != nil {
				t.Fatal(err)
			}
		}
		advance(100)
	}
	advance(1000)
	press(2)
	press(2)
	advance(1000)
	press(1)
	for n := 0; n < 300 && e.Tracker.VisibleScene != "main-menu"; n++ {
		advance(100)
	}
	if e.Tracker.VisibleScene != "main-menu" {
		t.Fatal(e.Status())
	}
	press(0x50)
	press(0x1c)
	press(0x1c)
	advance(1400)
	press(0x3b)
	advance(700)
	press(1)
	press(0x3c)
	advance(700)
	press(1)
	if e.Tracker.VisibleScene != "map" {
		t.Fatal(e.Status())
	}
	dir := filepath.Join(out, "pam-controlled")
	os.MkdirAll(dir, 0755)
	bg, err := os.ReadFile(filepath.Join(project, "workplace/probe-20261023/graphics-first/map-interaction-r1/buildings-registration-r1/gro02-native.bin"))
	if err != nil {
		t.Fatal(err)
	}
	buffer := oracle.Addr{Seg: 0x8000}
	mode, dest := oracle.Addr{Seg: 0x0aa8, Off: 0x7484}, oracle.Addr{Seg: 0x0aa8, Off: 0x748a}
	for _, v := range engines {
		v.Oracle.SetRegs(oracle.CallRegs{DS: 0x0aa8, SetDS: true})
		v.Oracle.WriteU16(mode, 1)
		v.Oracle.WriteU16(oracle.Addr{Seg: v.Tracker.stringSeg, Off: 0x196}, 0xa400)
	}
	call := func(entry uint16, raw []byte, x, y uint16) {
		t.Helper()
		for _, v := range engines {
			v.Oracle.WriteBytes(buffer, raw)
			if _, er := v.Oracle.CallBudget(500000, oracle.Addr{Seg: v.Tracker.stringSeg, Off: entry}, 0, 0x8000, x, y); er != nil {
				t.Fatal(er)
			}
		}
		if !bytes.Equal(observerGuestState(t, e), observerGuestState(t, control)) {
			t.Fatal("controlled guest changed")
		}
	}
	report := []map[string]any{}
	for _, r := range e.completion.Records {
		if r.Route != "material" && r.Route != "actor" {
			continue
		}
		if r.Route == "actor" && r.Record != 0 {
			continue
		}
		if r.SourceFile == "PMAP.AY" && r.Record != 66 {
			continue
		}
		raw, er := os.ReadFile(filepath.Join(project, "workplace/probe-20261023/graphics-first/all-graphics-integration-r1/sources-r1", fmt.Sprintf("%s-%02d.bin", replaceCompletionName(r.SourceFile), r.Record)))
		if er != nil {
			t.Fatal(er)
		}
		entries := []uint16{0x99c}
		if r.Planes == 5 {
			entries = []uint16{0x76f}
		}
		if r.Route == "actor" {
			entries = []uint16{0x4f2, 0x626}
		}
		for _, entry := range entries {
			for _, page := range []uint16{0xa400, 0xa000} {
				for _, v := range engines {
					v.Oracle.WriteU16(dest, page)
				}
				call(0x99c, bg, 0, 0)
			}
			background := e.Frame()
			want := image.NewRGBA(background.Bounds())
			copy(want.Pix, background.Pix)
			call(entry, raw, 1, 12)
			before := observerGuestState(t, e)
			actual := e.Frame()
			if !bytes.Equal(before, observerGuestState(t, e)) || e.renderFault != nil {
				t.Fatal("Frame mutated or fault", e.Status())
			}
			rect := image.Rect(24, 72, 24+r.Width, 72+r.Height)
			blend := draw.Src
			if r.Route == "actor" {
				blend = draw.Over
			}
			draw.Draw(want, rect, r.texture, image.Point{}, blend)
			if r.Route == "actor" {
				// 047 owned batches use rounded premultiplied alpha; image/draw truncates.
				copy(want.Pix, background.Pix)
				for y := 0; y < r.Height; y++ {
					for x := 0; x < r.Width; x++ {
						s := y*r.texture.Stride + x*4
						d := (72+y)*want.Stride + (24+x)*4
						a := uint32(r.texture.Pix[s+3])
						for ch := 0; ch < 3; ch++ {
							want.Pix[d+ch] = byte(min(255, uint32(r.texture.Pix[s+ch])+(uint32(want.Pix[d+ch])*(255-a)+127)/255))
						}
					}
				}
			}
			if !bytes.Equal(actual.Pix, want.Pix) {
				for label, im := range map[string]*image.RGBA{"actual": actual, "expected": want} {
					f, _ := os.Create(filepath.Join(dir, "mismatch-"+label+".png"))
					png.Encode(f, im)
					f.Close()
				}
				t.Fatalf("Go texture mismatch %s/%d/%x", r.SourceFile, r.Record, entry)
			}
			name := fmt.Sprintf("%s-%02d-%x", replaceCompletionName(r.SourceFile), r.Record, entry)
			f, er := os.Create(filepath.Join(dir, name+".png"))
			if er != nil {
				t.Fatal(er)
			}
			png.Encode(f, actual)
			f.Close()
			baseFile := filepath.Join(dir, name+"-base.png")
			f, er = os.Create(baseFile)
			if er != nil {
				t.Fatal(er)
			}
			png.Encode(f, background)
			f.Close()
			report = append(report, map[string]any{"source": r.SourceFile, "record": r.Record, "entry": entry, "rect": []int{24, 72, r.Width, r.Height}, "image": name + ".png", "base": name + "-base.png", "texture": r.Image, "blend": r.Route == "actor", "guest_equal": true, "Frame_pure": true})
		}
	}
	endingTestWrite(t, filepath.Join(dir, "receipt.json"), report)
}

func TestCompletionEndingRuntime(t *testing.T) {
	if os.Getenv("EIGHTSWORD_TEST_COMPLETION_ENDING") != "1" {
		t.Skip("限定完整結局抽驗")
	}
	project, assets, out := completionTestPaths(t)
	t.Setenv("EIGHTSWORD_TEST_ORIGINAL", filepath.Join(project, "workplace/intake-20261023/sources/game/8sword"))
	t.Setenv("EIGHTSWORD_TEST_ENDING_ASSETS", assets)
	t.Setenv("EIGHTSWORD_TEST_ENDING_OUT", out)
	t.Setenv("EIGHTSWORD_TEST_ENDING_REQUIRE_PAIR", "1")
	t.Setenv("EIGHTSWORD_TEST_ENDING_REQUIRE_DIRECT", "1")
	if err := os.MkdirAll(out, 0755); err != nil {
		t.Fatal(err)
	}
	TestEndingSourceRuntime(t)
	b, err := os.ReadFile(filepath.Join(out, "hd/runtime.json"))
	if err != nil {
		t.Fatal(err)
	}
	var result struct {
		Ending struct {
			Counts map[string]uint64 `json:"counts"`
		} `json:"ending"`
	}
	if err = json.Unmarshal(b, &result); err != nil {
		t.Fatal(err)
	}
	if result.Ending.Counts["completion-source-commands"] == 0 {
		t.Fatal("new ending sources not used")
	}
}
