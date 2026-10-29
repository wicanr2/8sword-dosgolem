// Spec030 READY: Go-owned displacement driven by original five-phase quake events.
package eightsword

import (
	"bytes"
	"image"

	"github.com/wicanr2/dosgolem/oracle"
)

var quakeValues = [5]uint16{0x500d, 0xf00d, 0xa00d, 0x500d, 0x000d}
var quakeShifts = [5]int{6, 18, 12, 6, 0}

func (p *sourceAdapter) bindBattleQuake(v *battleVFX, code []byte) {
	v.quakeBody = append([]byte(nil), code[0xe8a4:0xf265]...)
	p.onCall(oracle.Addr{Seg: v.code, Off: 0x960}, func(o *oracle.Oracle) { v.beginQuake(o) })
	for i, off := range []uint16{0xa05, 0xa6e, 0xad7, 0xb40, 0xba9} {
		p.onCall(oracle.Addr{Seg: v.code, Off: off}, func(o *oracle.Oracle) { v.quakePan(o, i) })
	}
}

func (v *battleVFX) beginQuake(o *oracle.Oracle) {
	r := o.Regs()
	word := func(off uint16) uint16 { return o.Word(oracle.Addr{Seg: r.SS, Off: off}) }
	if v.running && v.quake && v.quakeLocal == 0 && v.pon == 0 && r.SS == v.ss && r.DS == v.data && r.BP == v.quakeBP && word(r.BP-4) == 7 && word(r.BP+2) == 0x1cfe && word(r.BP+4) == v.code && o.VideoMode() == 0x0e && bytes.Equal(o.Bytes(oracle.Addr{Seg: v.code, Off: 0x334}, len(v.quakeBody)), v.quakeBody) {
		return
	}
	if v.running {
		v.cancel("new-effect")
	}
	if r.SS != v.data || r.DS != v.data || r.BP < 4 || r.BP > 65527 || r.SP > r.BP || o.VideoMode() != 0x0e || !bytes.Equal(o.Bytes(oracle.Addr{Seg: v.code, Off: 0x334}, len(v.quakeBody)), v.quakeBody) {
		v.skip("quake-context")
		return
	}
	if word(r.BP-4) != 7 || word(r.BP+2) != 0x1cfe || word(r.BP+4) != v.code {
		v.skip("quake-caller-selector")
		return
	}
	slot := word(r.BP + 6)
	if slot < 3 || slot >= 6 || word(0x26aa) == 0 {
		v.skip("quake-caster")
		return
	}
	id := word(0x6fb6 + slot*2)
	if id >= 6 || word(0x56ea+id*4) == 0 || (word(0x56e8+id*4) != 10 && word(0x56e8+id*4) != 12) {
		v.skip("quake-caster")
		return
	}
	for i := 0; i < 6; i++ {
		packed := word(0x701e + uint16(i*2))
		point := [2]int{int(packed&255) * 8, int(packed >> 8)}
		if point[0]+88 > 640 || point[1]+50 > 200 {
			v.skip("quake-geometry")
			return
		}
		v.quakePoints[i] = point
	}
	v.Started++
	v.Active = true
	v.Phase = "quake"
	v.quake = true
	v.running = true
	v.ss, v.quakeBP = r.SS, r.BP
	v.quakeLocal = 0
	v.pon = 0
	v.start = o.Steps()
	v.lastStep = o.Steps()
	v.lastCycles = o.Cycles()
	v.Shift = [2]int{}
	v.cachedBase = nil
	v.cached = nil
}

func (v *battleVFX) quakeBitmap(entry uint16, raw []byte, x, y, w, h int, dest uint16) {
	if entry != 0x4f2 {
		return
	}
	valid := false
	for _, src := range ponSources {
		if hash(raw) == src.Record {
			valid = true
			break
		}
	}
	pointValid := false
	for _, pt := range v.quakePoints {
		if pt == [2]int{x * 8, y} {
			pointValid = true
			break
		}
	}
	if !valid || !pointValid || w != 11 || h != 50 || dest != 0xa000 || v.pon >= 250 || v.pon != v.quakeLocal {
		v.cancel("quake-source-order")
		return
	}
	v.pon++
	v.PONCommits++
}

func (v *battleVFX) quakePan(o *oracle.Oracle, phase int) {
	if !v.running || !v.quake {
		return
	}
	r := o.Regs()
	word := func(off uint16) uint16 { return o.Word(oracle.Addr{Seg: r.SS, Off: off}) }
	if r.SS != v.ss || r.DS != v.data || r.BP != v.quakeBP || r.SP > 65533 || word(r.SP) != 0x3d4 || word(r.SP+2) != quakeValues[phase] {
		v.cancel("quake-pan-order")
		return
	}
	if v.quakeLocal > 0 && phase == (v.quakeLocal-1)%5 && v.pon == v.quakeLocal {
		v.QuakeDuplicates++
		return
	}
	if v.quakeLocal >= 250 || phase != v.quakeLocal%5 || v.pon != v.quakeLocal+1 {
		v.cancel("quake-pan-order")
		return
	}
	v.quakeLocal++
	v.QuakePans++
	v.Shift = [2]int{0, quakeShifts[phase]}
	v.cached = nil
	if v.quakeLocal == 250 {
		v.Completed++
		v.running = false
		v.hide()
	}
}

// Native Go row copies, with fixed text and clamped edge. No guest or VGA input.
func renderQuakeShift(base *image.RGBA, pixels []ownedPixel, shift int) *image.RGBA {
	if base == nil || base.Bounds() != image.Rect(0, 0, 1920, 1200) || len(pixels) != 128000 || (shift != 6 && shift != 12 && shift != 18) {
		return base
	}
	out := image.NewRGBA(base.Bounds())
	copy(out.Pix, base.Pix)
	for y := 0; y < 1200; y++ {
		src := base.PixOffset(0, min(y+shift, 1199))
		dst := out.PixOffset(0, y)
		copy(out.Pix[dst:dst+1920*4], base.Pix[src:src+1920*4])
	}
	for i, pixel := range pixels {
		if pixel.Text.ID == 0 {
			continue
		}
		x, y := i%640*3, i/640*6
		for _, top := range []int{y, y - shift} {
			for row := max(0, top); row < min(1200, top+6); row++ {
				at := base.PixOffset(x, row)
				copy(out.Pix[at:at+12], base.Pix[at:at+12])
			}
		}
		if y == 1194 {
			for row := 1200 - shift; row < 1200; row++ {
				at := base.PixOffset(x, row)
				copy(out.Pix[at:at+12], base.Pix[at:at+12])
			}
		}
	}
	return out
}

func (p *sourceAdapter) composeBattleQuake(base *image.RGBA) *image.RGBA {
	v := p.e.battleVFX
	if v.Shift[1] == 0 || p.cachedScene == nil {
		return base
	}
	sample := v.quakeLocal % 5
	if v.cached != nil && v.cachedBase == base && v.cachedPhase == "quake" && v.cachedSample == sample {
		return v.cached
	}
	visible := p.cachedScene.Pixels[p.cachedScene.Start : p.cachedScene.Start+128000]
	out := renderQuakeShift(base, visible, v.Shift[1])
	if out == base {
		v.cancel("quake-canvas")
		return base
	}
	v.Frames++
	v.cachedBase = base
	v.cached = out
	v.cachedPhase = "quake"
	v.cachedSample = sample
	return out
}
