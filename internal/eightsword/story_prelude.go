package eightsword

// Spec 014: original write coverage reveals approved HD art; guest remains authoritative.
import (
	"encoding/binary"
	"image"
	"image/draw"

	"github.com/wicanr2/dosgolem/oracle"
)

const preludePaletteSHA = "70890576d92472f8e97e1b4f3995f000a1317db79ede39d066553bcd31813e86"
const preludeTableSHA = "607a192b8ed9cf7dcb8f5c83cb5b43b83e9f5dd473f68e91db5fda5a1c4055a6"

type StoryPrelude struct {
	owner                                       *IntroStory
	art, cache, presented                       *image.RGBA
	source                                      []byte
	order, pending                              []uint32
	phase, stopReason, failure                  string
	retired                                     bool
	written, black, composed, bridges           uint64
	startCycle, bridgeCycle                     uint64
	startStep, returnStep, bridgeStep, stopStep uint64
}

func (p *StoryPrelude) bind() {
	o := p.owner.o
	o.OnCall(oracle.Far(0, 0xa3d0), func(*oracle.Oracle) { p.begin() })
	o.OnCall(oracle.Far(0, 0xa450), func(*oracle.Oracle) {
		if p.phase != "reveal" {
			return
		}
		if p.written != 64000 || !p.paletteOK() {
			p.stop("incomplete-return", true)
			return
		}
		p.phase = "wait"
		p.returnStep = o.Steps()
	})
	o.OnCall(oracle.Far(0, 0x1322), func(*oracle.Oracle) { p.stop("escape", false) })
}

func (p *StoryPrelude) begin() {
	t, o := p.owner, p.owner.o
	if p.retired || p.phase != "" || !t.valid() || t.Stats.Started {
		return
	}
	r := o.Regs()
	w, h, screen := o.Screen()
	if o.VideoMode() != 0x13 || w != 320 || h != 200 || len(screen) != 64000 || r.DS != 0xb31 || o.Arg(0) != 0 || o.Arg(1) != 0x6000 || o.Arg(2) != 0x100 || o.Arg(3) != 0 || o.Word(oracle.Far(r.SS, r.SP)) != 0x1ab || o.Word(oracle.Far(r.SS, r.SP+2)) != 0x110 {
		p.stop("entry-contract", true)
		return
	}
	for _, v := range screen {
		if v != 0 {
			p.stop("entry-not-black", true)
			return
		}
	}
	for _, g := range []struct {
		at  uint16
		n   int
		sha string
	}{
		{0xa3d0, 129, "98a5ba68ea08bad1b5b0f9ac32124c4bb5e43198448900897e556b98a2ee6066"},
		{0xa451, 78, "98c6d7b7f41bf3b132b994d890ec7ae585696b5941e791b60dbb33657d7f2143"},
		{0xa633, 3200, preludeTableSHA},
	} {
		if hash(o.Bytes(oracle.Far(0, g.at), g.n)) != g.sha {
			p.stop("code-or-order", true)
			return
		}
	}
	source := o.Bytes(oracle.Far(0x6000, 0), 64768)
	if hash(source) != preludeSourceSHA {
		p.stop("source", true)
		return
	}
	p.source = append([]byte(nil), source[768:]...)
	table := o.Bytes(oracle.Far(0, 0xa633), 3200)
	for i := 1599; i >= 0; i-- {
		v := int(binary.LittleEndian.Uint16(table[i*2:]))
		for x := v % 40; x < 320; x += 40 {
			for y := v / 40; y < 200; y += 40 {
				p.order = append(p.order, uint32(y*320+x))
			}
		}
	}
	if len(p.order) != 64000 {
		p.stop("order-shape", true)
		return
	}
	p.phase, p.startCycle, p.startStep = "reveal", o.Cycles(), o.Steps()
}

func (p *StoryPrelude) paletteOK() bool {
	palette := p.owner.o.Palette()
	var raw [768]byte
	for i, c := range palette {
		copy(raw[i*3:], c[:])
	}
	return hash(raw[:]) == preludePaletteSHA
}

func (p *StoryPrelude) observeWrite(v oracle.VideoWrite) {
	if p == nil || p.phase == "" {
		return
	}
	pc := uint32(v.CS)*16 + uint32(v.IP)
	if p.phase == "handoff" {
		t := p.owner
		if t.valid() && t.Stats.Started && t.Stats.Pages == 1 && t.inDraw && pc == 0x57ca && v.WriteMode == 0 && v.Offset < 16000 {
			return
		}
		p.stop("unknown-handoff-write", true)
		return
	}
	if p.phase != "reveal" || p.owner.o.VideoMode() != 0x13 || pc != 0xa486 || p.written >= 64000 || v.Offset != p.order[p.written] || v.Value != p.source[v.Offset] {
		p.stop("unknown-reveal-write", true)
		return
	}
	if p.written == 0 && !p.paletteOK() {
		p.stop("initial-palette", true)
		return
	}
	p.pending = append(p.pending, v.Offset)
	p.written++
	if v.Value == 0 {
		p.black++
	}
}

func (p *StoryPrelude) mode(v oracle.VideoModeChange) {
	if p == nil || p.phase == "" {
		return
	}
	// A mode callback must not read Palette.
	if v.Mode == 0xe && p.phase == "wait" && p.written == 64000 {
		p.phase, p.bridgeCycle, p.bridgeStep = "handoff", p.owner.o.Cycles(), v.Step
		return
	}
	p.stop("mode-change", true)
}

func (p *StoryPrelude) stop(reason string, failure bool) {
	if p == nil || p.retired {
		return
	}
	p.stopReason, p.stopStep = reason, p.owner.o.Steps()
	if failure {
		p.failure = reason
	}
	p.phase, p.retired = "", true
	p.cache, p.presented, p.source, p.order, p.pending = nil, nil, nil, nil, nil
}

func (p *StoryPrelude) tick() {
	if p == nil || p.retired {
		return
	}
	if p.owner.Stats.Retired || len(p.owner.o.Overlays()) != 0 || p.owner.failed {
		p.stop("story-retired", false)
		return
	}
	if p.phase == "" {
		return
	}
	if p.phase == "handoff" {
		if p.owner.o.Cycles()-p.bridgeCycle > titleTransactionLimit {
			p.stop("handoff-timeout", true)
		}
	} else if p.owner.o.Cycles()-p.startCycle > 20000000 {
		p.stop("reveal-timeout", true)
	}
}

func (p *StoryPrelude) compose(native *image.RGBA) (*image.RGBA, bool) {
	if p == nil {
		return native, false
	}
	p.presented = nil
	p.tick()
	if p.phase == "" {
		return native, false
	}
	o := p.owner.o
	if p.phase == "handoff" {
		if !p.owner.geometry() || hash(o.Bytes(oracle.Far(0x6000, 0), 64004)) != storyBackgroundSHA {
			p.stop("handoff-source", true)
			return native, false
		}
		p.bridges++
		p.presented = p.art
		return p.art, true
	}
	w, h := o.ScreenSize()
	if o.VideoMode() != 0x13 || w != 320 || h != 200 || (p.written != 0 && !p.paletteOK()) {
		p.stop("display-contract", true)
		return native, false
	}
	if p.cache == nil || len(p.pending) != 0 {
		next := image.NewRGBA(p.art.Bounds())
		if p.cache != nil {
			copy(next.Pix, p.cache.Pix)
		} else {
			for at := 3; at < len(next.Pix); at += 4 {
				next.Pix[at] = 255
			}
		}
		for _, offset := range p.pending {
			x, y := int(offset%320)*6, int(offset/320)*6
			r := image.Rect(x, y, x+6, y+6)
			draw.Draw(next, r, p.art, r.Min, draw.Src)
		}
		p.pending = nil
		p.cache = next
	}
	p.composed++
	p.presented = p.cache
	return p.cache, true
}

func (p *StoryPrelude) FrameStage(im *image.RGBA) string {
	if p != nil && im != nil && p.presented == im && p.phase != "" {
		if p.phase == "handoff" {
			return "story-prelude-handoff"
		}
		return "story-prelude"
	}
	return ""
}

func (p *StoryPrelude) Status() map[string]any {
	if p == nil {
		return map[string]any{"loaded": false}
	}
	return map[string]any{"loaded": true, "phase": p.phase, "retired": p.retired, "written": p.written, "black_writes": p.black, "composed": p.composed, "handoff_frames": p.bridges, "start_step": p.startStep, "return_step": p.returnStep, "handoff_step": p.bridgeStep, "stop_step": p.stopStep, "stop_reason": p.stopReason, "error": p.failure}
}
