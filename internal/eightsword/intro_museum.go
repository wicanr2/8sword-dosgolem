package eightsword

// Spec 017: source-identified museum presentation; guest state remains authoritative.
import (
	"fmt"
	"github.com/wicanr2/dosgolem/oracle"
	"image"
	"image/color"
	"image/draw"
	"os"
	"path/filepath"
)

func museumSHA(b []byte) string { return hash(b) }

type museumRecord struct {
	role                 string
	offset, w, h, blocks int
	raw                  []byte
}
type museumPage struct {
	scene       *museumScene
	role        string
	ink         *image.RGBA
	actor       *museumPlacedActor
	maskedCount int
}
type museumTX struct {
	invalidated bool
	at, end     uint16
	page        uint32
	start       uint64
	record      *museumRecord
	rows        []uint32
	clear, copy bool
	sourcePage  uint32
}
type IntroMuseum struct {
	title                                                                             *IntroTitle
	TitleHandoffFrames                                                                uint64
	drain                                                                             *museumDrain
	DrainFrames                                                                       uint64
	DrainStartStep, DrainStopStep                                                     uint64
	DrainStopReason                                                                   string
	sceneArts                                                                         map[string]*image.NRGBA
	sceneError                                                                        string
	SceneValidated                                                                    int
	RightComposed, PortraitComposed, BeamComposed                                     uint64
	stopObserving                                                                     func()
	ObserverWrites, ObserverBefore, ObserverAfterRetire                               uint64
	UnknownWrites, Invalidations, ModeInvalidations                                   uint64
	unknownSamples                                                                    []map[string]any
	actorSprites                                                                      map[string]*image.NRGBA
	actorRequested                                                                    bool
	actorError                                                                        string
	ActorValidated                                                                    int
	ActorAssignments, ActorRejected                                                   uint64
	o                                                                                 *oracle.Oracle
	variant                                                                           string
	records                                                                           map[string]*museumRecord
	pages                                                                             map[uint32]*museumPage
	tx                                                                                []museumTX
	last, hold                                                                        map[uint32]*image.RGBA
	holdVersion                                                                       map[uint32]uint64
	Events                                                                            []map[string]any
	art                                                                               *image.RGBA
	palette                                                                           [16][3]uint8
	paletteSet, active, retired, failed                                               bool
	version, cachedVersion                                                            uint64
	cachedBase, cachedFrame                                                           *image.RGBA
	cachedPage                                                                        uint32
	Stage                                                                             string
	final                                                                             *image.RGBA
	Starts, Opaque, Masked, Composed, Held, NativeCompared, BlackWrites, WrappedBytes uint64
	Copies, Clears                                                                    uint64
	Errors                                                                            []string
}

func loadIntroMuseum(e *Engine, dir, root string) (*IntroMuseum, error) {
	info, err := os.Lstat(filepath.Join(dir, "museum.json"))
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() {
		return nil, fmt.Errorf("博物館清單不是一般檔案")
	}
	m := &IntroMuseum{o: e.Oracle, title: e.Intro, variant: "a-purple", records: map[string]*museumRecord{}, pages: map[uint32]*museumPage{}, last: map[uint32]*image.RGBA{}, hold: map[uint32]*image.RGBA{}, holdVersion: map[uint32]uint64{}}
	for i, source := range heroineRecords {
		role := "actor"
		if i == 0 {
			role = "left"
		}
		if i == 1 {
			role = "right"
		}
		if i == 14 {
			role = "portrait"
		}
		m.records[source.sha] = &museumRecord{role: role, offset: source.offset, w: source.w, h: source.h, blocks: source.blocks}
	}
	if err = m.loadMuseumGroup(dir, root); err != nil {
		return nil, err
	}
	if e.sourceEnabled {
		return m, nil
	}
	m.stopObserving = e.ObservePresentation(PresentationObserver{Write: m.observeMuseumWrite, ModeChange: m.observeMuseumMode})
	m.o.OnCall(oracle.Far(0, 0x1be2), func(o *oracle.Oracle) {
		if m.retired || len(o.Overlays()) != 0 {
			return
		}
		if museumSHA(o.Bytes(oracle.Far(0, 0x1be2), 1116)) != "792fc06dec03852fa5c88844dc0c11321e263454b9ced40b62521d016d2713f2" {
			return
		}
		if museumSHA(o.Bytes(oracle.Far(0, 0x52c0), 308)) != "c7c0315ee13ef29e26ea2b35098c3cae6453e4f4e5fcd34da6cee81ae57c4dd3" {
			m.fail("masked code differs")
			return
		}

		for _, guard := range []struct {
			at  uint16
			n   int
			sha string
		}{
			{0x576a, 212, "88d6cfe05ddb19b00bd42cb4857a95cbcf9bdf764320ea21e503b9f202a947d8"},
			{0x510b, 53, "faa92f6dfda7d9d587f9279dac67ec33897fe9cde2fa1c1a21d9aacc1c04fb2c"},
			{0x517e, 53, "9c6604f617ce1421dd00d7f46e665e37416b00e822338f86dba879b13785aa36"},
			{0x5b0c, 55, "9b2e2e5b7c9b878690e526de6705910ee57066806e3a44c3b51fdf853176c76f"},
			{0x5d76, 38, "908543eeb25cf60eb9dac835d484d3dc38cc53ac6b62e150272e988b0a2f5f07"},
			{0x5d9c, 38, "2ce8b80f1c0f969c41e341d89d62eebdba356a5f66d5d8b843b9530eb449e281"},
		} {
			if museumSHA(o.Bytes(oracle.Far(0, guard.at), guard.n)) != guard.sha {
				m.fail("page operation code differs")
				return
			}
		}
		m.active = true
		m.Starts++
	})
	for _, at := range []uint16{0x203c, 0x1322} {
		m.o.OnCall(oracle.Far(0, at), func(*oracle.Oracle) {
			if !m.retired && (m.active || (len(m.o.Overlays()) == 0 && museumSHA(m.o.Bytes(oracle.Far(0, 0x1be2), 1116)) == "792fc06dec03852fa5c88844dc0c11321e263454b9ced40b62521d016d2713f2")) {
				m.retireMuseumAt(at)
			}
		})
	}
	for _, pair := range [][2]uint16{{0x576a, 0x583d}, {0x52c0, 0x53f3}, {0x5b0c, 0x5b42}, {0x5d76, 0x5d8f}, {0x5d9c, 0x5db5}} {
		at, end := pair[0], pair[1]
		m.o.OnCall(oracle.Far(0, at), func(*oracle.Oracle) { m.begin(at, end) })
		m.o.OnCall(oracle.Far(0, end), func(*oracle.Oracle) { m.commit(end) })
	}
	return m, nil
}
func (m *IntroMuseum) fail(s string) {
	if len(m.Errors) < 8 {
		m.Errors = append(m.Errors, s)
	}
	m.failed = true
	m.tx = nil
	m.retireMuseum()
}
func (m *IntroMuseum) valid() bool {
	return m != nil && m.active && !m.retired && !m.failed && len(m.o.Overlays()) == 0
}
func (m *IntroMuseum) begin(at, end uint16) {
	if !m.valid() {
		return
	}
	state, ok := m.o.PlanarDisplay()
	if !ok || state.Width != 640 || state.Height != 200 || state.Pitch != 80 || m.o.Word(oracle.Far(0, 0xd202)) != 1 {
		m.fail("prototype geometry differs")
		return
	}
	if !m.paletteSet {
		m.palette = state.Palette
		m.paletteSet = true
	}
	if m.palette != state.Palette {
		m.fail("prototype palette changed")
		return
	}
	dest := m.o.Word(oracle.Far(0, 0xd208))
	if dest != 0xa000 && dest != 0xa400 {
		m.fail("unknown destination")
		return
	}
	page := uint32(dest-0xa000) * 16
	if len(m.tx) >= 4 {
		m.fail("nested transaction outside prototype bound")
		return
	}

	sourcePage := uint32(0)
	if at == 0x5d76 {
		page, sourcePage = 0x4000, 0
	}
	if at == 0x5d9c {
		page, sourcePage = 0, 0x4000
	}
	t := museumTX{at: at, end: end, page: page, sourcePage: sourcePage, start: m.o.Cycles(), clear: at == 0x5b0c, copy: at == 0x5d76 || at == 0x5d9c}
	if !t.clear && !t.copy {
		off, seg, x, y := m.o.Arg(0), m.o.Arg(1), m.o.Arg(2), m.o.Arg(3)

		if !museumSourceInRAM(seg, off, 4) {
			m.fail("source header outside RAM")
			return
		}
		w, h := int(m.o.Word(oracle.Far(seg, off))), int(m.o.Word(oracle.Far(seg, off+2)))
		blocks := 4
		if at == 0x52c0 {
			blocks = 6
		}
		if w < 1 || w > 80 || h < 1 || h > 200 {
			m.fail("source shape differs")
			return
		}

		if !museumSourceInRAM(seg, off, 4+w*h*blocks) {
			m.fail("source record outside RAM")
			return
		}
		b := m.o.Bytes(oracle.Far(seg, off), 4+w*h*blocks)
		r := m.records[museumSHA(b)]
		if r == nil || r.offset != int(off) || r.blocks != blocks {
			m.fail("source record not identified")
			return
		}
		if r.raw == nil {
			r.raw = append([]byte(nil), b...)
		}
		t.record = r
		t.rows = make([]uint32, h)
		if int(y)+h > 200 || int(x) > 79 {
			m.fail("museum destination row outside known geometry")
			return
		}
		cs := m.o.Regs().CS
		for yy := range t.rows {
			row := m.o.Word(oracle.Far(cs, 4+(y+uint16(yy))*2))
			if row != uint16((int(y)+yy)*80) {
				m.fail("row table differs")
				return
			}
			t.rows[yy] = page + uint32(row+x)
		}
	}
	if state.Start == page && m.hold[page] == nil {
		p := m.pages[page]
		m.hold[page] = museumRawBand(m.o)
		if m.sceneSupported(p) {
			draw.Draw(m.hold[page], m.hold[page].Bounds(), m.renderBand(p), image.Point{}, draw.Over)
		}
		m.holdVersion[page] = m.version
	}
	m.tx = append(m.tx, t)
}
func (m *IntroMuseum) commit(end uint16) {
	if !m.valid() || len(m.tx) == 0 {
		return
	}
	t := m.tx[len(m.tx)-1]
	if t.end != end {
		m.fail("prototype return differs")
		return
	}
	m.tx = m.tx[:len(m.tx)-1]
	if t.invalidated {
		m.forgetMuseumPage(t.page)
		if t.clear {
			m.Clears++
		} else if t.copy {
			m.Copies++
		} else if t.record.blocks == 4 {
			m.Opaque++
		} else {
			m.Masked++
		}
	} else if t.clear {
		m.Clears++
		delete(m.pages, t.page)
		delete(m.last, t.page)
	} else if t.copy {
		m.Copies++
		p := m.pages[t.sourcePage]
		if p == nil {
			delete(m.pages, t.page)
		} else {
			ink := image.NewRGBA(p.ink.Bounds())
			copy(ink.Pix, p.ink.Pix)
			m.pages[t.page] = &museumPage{role: p.role, ink: ink, actor: p.actor, maskedCount: p.maskedCount, scene: cloneMuseumScene(p.scene)}
		}
		delete(m.last, t.page)
	} else if t.record.blocks == 4 {
		m.Opaque++
		m.commitMuseumOpaque(t)
	} else {
		m.Masked++
		p := m.pages[t.page]
		r := t.record
		n := r.w * r.h
		if p != nil && (p.role == "left" || p.role == "right") {
			if r.w == 24 {
				m.assignMuseumBeam(p, t)
			} else {
				m.assignHDActor(p, t)
			}
			for y, row := range t.rows {
				for x := 0; x < r.w; x++ {
					i := y*r.w + x
					mask := r.raw[4+5*n+i]
					local := int(row-t.page) + x
					if local < 0 || local >= 16000 {
						m.fail("ink outside page")
						return
					}
					if local%80 < x {
						m.WrappedBytes++
					}
					for bit := 0; bit < 8; bit++ {
						if mask&(128>>bit) == 0 {
							continue
						}
						index := byte(0)
						for plane := 0; plane < 4; plane++ {
							index |= ((r.raw[4+plane*n+i] >> uint(7-bit)) & 1) << uint(plane)
						}
						px, py := (local%80)*8+bit, local/80
						if py < 50 || py >= 150 {
							m.fail("prototype ink outside known artwork band")
							return
						}
						c := m.palette[index]
						p.ink.SetRGBA(px, py, color.RGBA{c[0], c[1], c[2], 255})
						if index == 0 {
							m.BlackWrites++
						}
					}
				}
			}
		}
	}
	m.version++
	operation := "draw"
	if t.clear {
		operation = "clear"
	}
	if t.copy {
		operation = "copy"
	}
	event := map[string]any{"serial": m.version, "at": t.at, "operation": operation, "source_page": t.sourcePage, "page": t.page, "rows": t.rows, "clear": t.clear, "step": m.o.Steps()}
	if t.record != nil {
		event["source_sha256"] = museumSHA(t.record.raw)
		event["role"] = t.record.role
		event["blocks"] = t.record.blocks
	}
	if t.invalidated {
		event["invalidated"] = true
	}
	if len(m.Events) >= 512 {
		m.fail("museum event bound")
		return
	}
	m.Events = append(m.Events, event)
	keep := false
	for _, remaining := range m.tx {
		if remaining.page == t.page {
			keep = true
		}
	}
	if !keep {
		delete(m.hold, t.page)
		delete(m.holdVersion, t.page)
	}
}
func museumRawBand(o *oracle.Oracle) *image.RGBA {
	w, h, b := o.ScreenRGB()
	if w != 640 || h != 200 {
		return nil
	}
	im := image.NewRGBA(image.Rect(0, 0, 1920, 780))
	for y := 0; y < 780; y++ {
		for x := 0; x < 1920; x++ {
			at := y*im.Stride + x*4
			src := ((y/6+20)*640 + x/3) * 3
			copy(im.Pix[at:at+3], b[src:src+3])
			im.Pix[at+3] = 255
		}
	}
	return im
}
func (m *IntroMuseum) Compose(base *image.RGBA) *image.RGBA {
	if m == nil {
		return base
	}
	m.Stage = ""
	if m.drain != nil {
		return m.composeMuseumDrain(base)
	}
	if !m.valid() {
		return base
	}
	state, ok := m.o.PlanarDisplay()
	if !ok || state.Width != 640 || state.Height != 200 || state.Pitch != 80 || state.Palette != m.palette {
		return base
	}
	for _, t := range m.tx {
		if m.o.Cycles()-t.start > 2000000 {
			m.fail("prototype transaction timeout")
			return base
		}
		if t.page == state.Start && m.hold[t.page] != nil {
			// The title owns this fully composed hold until the first museum commit.
			if !m.sceneSupported(m.pages[t.page]) && m.title != nil && m.title.hold == base {
				m.TitleHandoffFrames++
				return base
			}
			m.Held++
			m.Stage = "hold"
			result := image.NewRGBA(base.Bounds())
			copy(result.Pix, base.Pix)
			draw.Draw(result, image.Rect(0, 120, 1920, 900), m.hold[t.page], image.Point{}, draw.Over)
			return result
		}
	}
	p := m.pages[state.Start]
	if !m.sceneSupported(p) {
		return base
	}
	if m.cachedBase == base && m.cachedVersion == m.version && m.cachedPage == state.Start {
		m.noteMuseumScene(p)
		m.Composed++
		return m.cachedFrame
	}
	result := image.NewRGBA(base.Bounds())
	copy(result.Pix, base.Pix)
	draw.Draw(result, image.Rect(0, 120, 1920, 900), m.renderBand(p), image.Point{}, draw.Over)

	m.noteMuseumScene(p)
	m.Composed++
	m.cachedBase, m.cachedFrame, m.cachedVersion, m.cachedPage = base, result, m.version, state.Start
	m.last[state.Start] = result
	return result
}
func (m *IntroMuseum) Status() map[string]any {
	if m == nil {
		return map[string]any{"variant": "off"}
	}
	page := uint32(0)
	if s, ok := m.o.PlanarDisplay(); ok {
		page = s.Start
	}
	return map[string]any{"variant": m.variant, "title_handoff_frames": m.TitleHandoffFrames, "revision": 8, "draining": m.drain != nil, "drain_frames": m.DrainFrames, "drain_start_step": m.DrainStartStep, "drain_stop_step": m.DrainStopStep, "drain_stop_reason": m.DrainStopReason, "scene_loaded": len(m.sceneArts), "scene_validated": m.SceneValidated, "scene_error": m.sceneError, "right_composed": m.RightComposed, "portrait_composed": m.PortraitComposed, "beam_composed": m.BeamComposed, "observer_writes": m.ObserverWrites, "observer_before": m.ObserverBefore, "observer_after_retire": m.ObserverAfterRetire, "unknown_writes": m.UnknownWrites, "invalidations": m.Invalidations, "mode_invalidations": m.ModeInvalidations, "unknown_samples": m.unknownSamples, "actor_requested": m.actorRequested, "actor_loaded": len(m.actorSprites), "actor_validated": m.ActorValidated, "actor_error": m.actorError, "actor_assignments": m.ActorAssignments, "actor_rejected": m.ActorRejected, "page_copies": m.Copies, "page_clears": m.Clears, "stage": m.Stage, "active": m.active, "retired": m.retired, "starts": m.Starts, "opaque": m.Opaque, "masked": m.Masked, "composed": m.Composed, "held": m.Held, "native_compared": m.NativeCompared, "black_writes": m.BlackWrites, "wrapped_bytes": m.WrappedBytes, "errors": m.Errors, "disposable": false, "serial": m.version, "page": page, "hold_version": m.holdVersion[page]}
}

func museumSourceInRAM(seg, off uint16, n int) bool {
	if n <= 0 || uint64(off)+uint64(n) > 65536 {
		return false
	}
	return uint64(seg)*16+uint64(off)+uint64(n) <= 0xa0000
}
