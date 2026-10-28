// 053 READY. PAE source adaptation after the original overlay handoff.
package eightsword

import (
	"encoding/hex"
	"fmt"
	"image"
	"strings"

	"github.com/wicanr2/dosgolem/oracle"
)

func endingOverlay(o *oracle.Oracle) (uint16, bool) {
	overlays := o.Overlays()
	if len(overlays) == 0 {
		return 0, false
	}
	last := overlays[len(overlays)-1]
	return last.Seg, strings.EqualFold(last.Name, "PAE.AY")
}
func (e *Engine) inEndingPhase() bool { _, active := endingOverlay(e.Oracle); return active }

type endingAdapter struct {
	e            *Engine
	assets       *endingAssets
	scene        *endingScene
	bound        bool
	active       int
	load         uint16
	counts       map[string]uint64
	directCounts map[string]int
	cached       *image.RGBA
	cachedPage   *endingPage
	revision     uint64
	palette      [16][3]uint8
	fontID       string
	unsubscribe  func()
}

func (p *endingAdapter) reject(reason string) { p.e.sourceReject("ending", reason) }
func (p *endingAdapter) onCall(at oracle.Addr, fn func(*oracle.Oracle)) {
	p.e.Oracle.OnCall(at, func(o *oracle.Oracle) {
		if p.e.inEndingPhase() {
			p.e.sourceGuardCall(func() { fn(o) })
		}
	})
}
func (e *Engine) newSourceEnding() (func(), func() *image.RGBA, func()) {
	p := &endingAdapter{e: e, assets: e.endingAssets, scene: newEndingScene(), counts: map[string]uint64{}, directCounts: map[string]int{}}
	e.ending = p
	p.unsubscribe = e.sourceGuardObserver(PresentationObserver{
		ModeChange: func(v PresentationModeChange) {
			if !e.inEndingPhase() {
				return
			}
			p.scene = newEndingScene()
			p.scene.mode = v.Mode == 0xe
			p.cached = nil
			p.active = 0
			p.counts["mode"]++
		},
		Write: func(v PresentationWrite) {
			if e.inEndingPhase() && p.scene.mode && p.active == 0 {
				p.counts["unclassified-writes"]++
				e.sourceRejectAt("ending", "unclassified-video-write", v.Step, v.CS, v.IP, e.Oracle.VideoMode())
			}
		},
	})
	frame := func() *image.RGBA {
		if !e.inEndingPhase() {
			return nil
		}
		if !p.bound || !p.scene.mode || p.active != 0 {
			p.counts["held-frames"]++
			if e.sourceHeldFrame == nil {
				blank := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
				endingFill(blank, blank.Bounds(), endingPalette[0])
				return blank
			}
			return e.sourceHeldFrame
		}
		display, ok := e.Oracle.PlanarDisplay()
		if !ok || display.Width != 640 || display.Height != 200 || display.Pitch != 80 || int(display.Start) != p.scene.active*0x4000 {
			p.reject("display-layout-differs")
		}
		page := p.scene.pages[p.scene.active]
		if p.cached == nil || p.cachedPage != page || p.revision != page.revision || p.palette != display.Palette || p.fontID != e.FontID() {
			profile := p.assets.profile(e.FontID())
			if profile == nil {
				p.reject("missing-font-profile")
			}
			p.cached = renderEndingPage(page, display.Palette, p.assets.art, profile)
			p.cachedPage = page
			p.revision = page.revision
			p.palette = display.Palette
			p.fontID = e.FontID()
			p.counts["rendered-frames"]++
		}
		e.sourceMetadata = sourceFrameMetadata{Frame: p.cached, Kind: "ending-" + page.stage}
		return p.cached
	}
	return p.bind, frame, func() {
		if p.unsubscribe != nil {
			p.unsubscribe()
		}
	}
}
func (e *Engine) EndingStatus() map[string]any {
	if e.ending == nil {
		return map[string]any{"bound": false, "error": e.EndingError}
	}
	p := e.ending
	stage := ""
	if p.scene != nil {
		stage = p.scene.pages[p.scene.active].stage
	}
	counts := map[string]uint64{}
	for k, v := range p.counts {
		counts[k] = v
	}
	portrait := map[string]any{"loaded": false, "textures": 0, "error": ""}
	if p.assets != nil {
		portrait = map[string]any{"loaded": len(p.assets.art.portraits) == 5, "textures": len(p.assets.art.portraits), "error": p.assets.portraitError}
	}
	return map[string]any{"input_api": e.endingInputSupported, "input_step": e.endingInputStep, "input_discarded": e.endingInputDropped, "direct": p.directCounts, "bound": p.bound, "active": e.inEndingPhase(), "load_segment": p.load, "stage": stage, "pending": p.active, "counts": counts, "error": e.EndingError, "portrait": portrait}
}
func (p *endingAdapter) bind() {
	load, active := endingOverlay(p.e.Oracle)
	if !active || p.bound {
		return
	}
	if p.assets == nil {
		p.reject("missing-or-invalid-ending-assets")
	}
	overlays := p.e.Oracle.Overlays()
	last := overlays[len(overlays)-1]
	if load != 0x110 || last.Reloc != load {
		p.reject("unsupported-overlay-relocation")
	}
	p.load = load
	p.bound = true
	p.counts["overlay-bound"]++
	o := p.e.Oracle
	seg := load + 0x283
	fontSeg := load + 0x17e
	pageFor := func(ds uint16) *endingPage {
		if o.Word(oracle.Addr{Seg: ds, Off: 0x177a}) != 1 {
			p.reject("unsupported-source-mode")
		}
		dest := o.Word(oracle.Addr{Seg: ds, Off: 0x1780})
		if dest != 0xa000 && dest != 0xa400 {
			p.reject("unsupported-destination")
		}
		return p.scene.pages[int(dest-0xa000)/0x400]
	}
	bind := func(segment, entry, ret uint16, want string, prepare func() func()) {
		var apply func()
		var sp uint16
		p.onCall(oracle.Addr{Seg: segment, Off: entry}, func(q *oracle.Oracle) {
			if apply != nil {
				if sp == q.Regs().SP {
					p.counts["reobserved-entry"]++
					return
				}
				p.reject("nested-source-command")
			}
			if hash(q.Bytes(oracle.Addr{Seg: segment, Off: entry}, int(ret-entry)+1)) != want {
				p.reject("source-code-identity")
			}
			sp = q.Regs().SP
			apply = prepare()
			p.active++
		})
		p.onCall(oracle.Addr{Seg: segment, Off: ret}, func(q *oracle.Oracle) {
			if apply == nil {
				return
			}
			if q.Regs().SP != sp {
				p.reject("source-return-stack")
			}
			apply()
			apply = nil
			p.active--
		})
	}
	cache := map[string]*endingCommand{}
	for _, spec := range []struct {
		entry, ret uint16
		kind       int
		sha        string
	}{
		{0x4ec, 0x61f, 6, "85467a42c1b56b7eb880128fe34417adbe74fdf1bf42d857758908d8bbd79549"},
		{0x769, 0x84e, 5, "285723c100da394f2c125b5a1a293c0b24d4f18a8cf2276937ef4a47db4124bc"},
		{0x996, 0xa69, 4, "603833bfa266acbc8f7a3c8ecf3a30e9f15b5242211367534a7ca1145bb4cfad"},
	} {
		spec := spec
		bind(seg, spec.entry, spec.ret, spec.sha, func() func() {
			ptr := oracle.Addr{Seg: o.Arg(1), Off: o.Arg(0)}
			if !bitmapSourceInRAM(ptr, 4) {
				p.reject("source-header-bounds")
			}
			w, h := int(o.Word(ptr))*8, int(o.Word(oracle.Addr{Seg: ptr.Seg, Off: ptr.Off + 2}))
			if w < 8 || w > 640 || h < 1 || h > 200 || !bitmapSourceInRAM(ptr, 4+w/8*h*spec.kind) {
				p.reject("source-bitmap-bounds")
			}
			raw := o.Bytes(ptr, 4+w/8*h*spec.kind)
			key := hash(raw)
			command := cache[key]
			if command == nil {
				file := p.assets.manifest.Sources[key]
				if file == "" {
					p.reject("unclassified-source-bitmap")
				}
				pixels, mask := decodeEndingBitmap(raw, spec.kind, w, h)
				command = &endingCommand{Kind: "bitmap", W: w, H: h, Pixels: pixels, Mask: mask, SourceSHA: key, SourceFile: file}
				cache[key] = command
			}
			c := *command
			c.X, c.Y = int(o.Arg(2))*8, int(o.Arg(3))
			page := pageFor(o.Regs().DS)
			p.counts[fmt.Sprintf("bitmap-%d", spec.kind)]++
			return func() {
				page.apply(&c)
				if p.assets.art.completion[c.SourceSHA] != nil {
					p.counts["completion-source-commands"]++
					p.counts["completion-"+c.SourceSHA]++
				}
			}
		})
	}
	for _, spec := range []struct {
		segment, entry, ret uint16
		cjk                 bool
		sha                 string
	}{
		{fontSeg, 0xef0, 0x104f, true, "dc3197283e3434f6ca35e71592b0c604bc035efef450ed50afffff1309f01739"},
		{seg, 0xb80, 0xc7f, false, "5631f527e7a205f772c3c0f0b1c6521781a1264b669d487346dfa1671a5c1692"},
	} {
		spec := spec
		bind(spec.segment, spec.entry, spec.ret, spec.sha, func() func() {
			ds := o.Regs().DS
			page := pageFor(ds)
			index := int(o.Arg(0))
			width, kind, char := 8, "ascii", rune(index)
			bitsHex := ""
			ptr := oracle.Addr{Seg: ds, Off: uint16(0x548 + index*15)}
			if spec.cjk {
				if index%30 != 0 || index/30 >= 127 {
					p.reject("glyph-index")
				}
				index /= 30
				glyph := p.assets.manifest.CJK[index]
				char = []rune(glyph.Character)[0]
				bitsHex = glyph.Bits
				width, kind = 16, "cjk"
				ptr = oracle.Addr{Seg: fontSeg, Off: uint16(14 + index*30)}
			} else {
				if index > 255 {
					p.reject("glyph-index")
				}
				bitsHex = p.assets.manifest.ASCII[index]
			}
			bits := o.Bytes(ptr, width/8*15)
			if hex.EncodeToString(bits) != bitsHex {
				p.reject("glyph-source-identity")
			}
			mask := make([]byte, width*15)
			for at := range mask {
				mask[at] = bits[at/8] >> uint(7-at%8) & 1
			}
			c := &endingCommand{Kind: kind, Code: index, Char: char, X: int(o.Arg(1)) * 8, Y: int(o.Arg(2)), W: width, H: 15, FG: o.Byte(oracle.Addr{Seg: ds, Off: 0x1782}), BG: o.Byte(oracle.Addr{Seg: ds, Off: 0x1783}), Mask: mask}
			if c.FG > 15 || (c.BG > 15 && c.BG != 255) {
				p.reject("glyph-colors")
			}
			p.counts[kind]++
			return func() {
				if !page.apply(c) {
					p.counts["idempotent-or-empty-glyph"]++
				}
			}
		})
	}
	bind(seg, 0xd38, 0xd6e, "f64a64cc8b397aa4b1202678a1fb57a2e98f2e9e742091aee26839486238fa33", func() func() {
		ds := o.Regs().DS
		page := pageFor(ds)
		mask := o.Byte(oracle.Addr{Seg: ds, Off: 0x1782})
		if mask != 15 {
			p.reject("partial-clear-not-admitted")
		}
		p.counts["clear"]++
		return func() { clear(page.native); page.ops = nil; page.glyphs = 0; page.stage = ""; page.revision++ }
	})
	bind(seg, 0x3aa, 0x3de, "9c6604f617ce1421dd00d7f46e665e37416b00e822338f86dba879b13785aa36", func() func() {
		return func() {
			from, to := p.scene.pages[1], p.scene.pages[0]
			copy(to.native[:128000], from.native[:128000])
			to.ops = append([]*endingCommand(nil), from.ops...)
			to.stage, to.glyphs = from.stage, from.glyphs
			to.revision++
			p.counts["page-copy"]++
		}
	})
	bind(seg, 0x196, 0x1a3, "c764b97541e70a9e047ec2893ab0ce9bf3c51f36df6ad2a72ed7e27b46a31fc6", func() func() {
		page := o.Arg(0) & 255
		if page > 3 {
			p.reject("page-index")
		}
		return func() { p.scene.active = int(page); p.counts["select-page"]++ }
	})
	installEndingDirect(o, p.directCounts)
	installEndingMasked(o, p.directCounts)
	installEndingGlyphs(o, p.directCounts)
}
