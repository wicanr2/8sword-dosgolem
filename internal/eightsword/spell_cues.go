// Spec030 READY: additive HD cast cues; guest outcomes and clocks remain original.
package eightsword

import (
	"bytes"
	"github.com/wicanr2/dosgolem/oracle"
	"image"
)

type SpellCueInfo struct {
	Bound, Active                                   bool
	Kind                                            int
	Anchor                                          [2]int
	Started, Completed, Duplicates, Skipped, Frames uint64
	Map                                             [8]uint64
	Battle                                          [2]uint64
}
type spellCues struct {
	SpellCueInfo
	load, data, battle                        uint16
	mapBody, battleBody                       []byte
	mapPending, battlePending                 bool
	mapSP, battleSP                           uint16
	mapSequence, battleSequence, seenSequence uint64
	seenKind, seenOrdinal                     int
	start                                     uint64
	cachedBase, cached                        *image.RGBA
	sample                                    int
}

func (e *Engine) SpellCueStatus() SpellCueInfo {
	if e.spellCues == nil {
		return SpellCueInfo{}
	}
	return e.spellCues.SpellCueInfo
}
func (p *sourceAdapter) bindSpellCues(code []byte, load uint16) {
	v := &spellCues{SpellCueInfo: SpellCueInfo{Bound: true}, load: load, data: load + 0x1d78, battle: load + 0xe57, mapBody: append([]byte(nil), code[0x68ce:0x693c]...), battleBody: append([]byte(nil), code[0xe8a4:0xf265]...)}
	p.e.spellCues = v
	p.onCall(oracle.Addr{Seg: load, Off: 0x68ce}, func(o *oracle.Oracle) {
		r := o.Regs()
		if r.SS != v.data || r.DS != v.data || o.VideoMode() != 0x0e || !bytes.Equal(o.Bytes(oracle.Addr{Seg: load, Off: 0x68ce}, 110), v.mapBody) {
			return
		}
		if !v.mapPending || v.mapSP != r.SP {
			v.mapPending = true
			v.mapSP = r.SP
			v.mapSequence++
		}
	})
	p.onCall(oracle.Addr{Seg: load, Off: 0x68f0}, func(o *oracle.Oracle) { v.mapCue(o) })
	p.onCall(oracle.Addr{Seg: load, Off: 0x68fa}, func(o *oracle.Oracle) {
		if o.Regs().SP == v.mapSP {
			v.mapPending = false
		}
	})
	p.onCall(oracle.Addr{Seg: v.battle, Off: 0x334}, func(o *oracle.Oracle) {
		r := o.Regs()
		if r.SS != v.data || r.DS != v.data || !bytes.Equal(o.Bytes(oracle.Addr{Seg: v.battle, Off: 0x334}, len(v.battleBody)), v.battleBody) {
			return
		}
		if !v.battlePending || v.battleSP != r.SP {
			v.battlePending = true
			v.battleSP = r.SP
			v.battleSequence++
		}
	})
	for _, off := range []uint16{0x752, 0x906} {
		p.onCall(oracle.Addr{Seg: v.battle, Off: off}, func(o *oracle.Oracle) { v.battleCue(o, off) })
	}
	p.onCall(oracle.Addr{Seg: v.battle, Off: 0x1cfe}, func(o *oracle.Oracle) {
		if o.Regs().SP == v.battleSP+4 {
			v.battlePending = false
		}
	})
}
func (v *spellCues) activate(o *oracle.Oracle, kind int, anchor [2]int, seq uint64, ordinal int) {
	if v.Started > 0 && v.seenSequence == seq && v.seenKind == kind && v.seenOrdinal == ordinal {
		v.Duplicates++
		return
	}
	if v.Active {
		v.Completed++
	}
	v.seenSequence, v.seenKind, v.seenOrdinal = seq, kind, ordinal
	v.Kind, v.Anchor = kind, anchor
	v.Started++
	v.Active = true
	v.start = o.Cycles()
	v.cached = nil
	v.cachedBase = nil
	if kind < 8 {
		v.Map[kind]++
	} else {
		v.Battle[kind-8]++
	}
}
func (v *spellCues) mapCue(o *oracle.Oracle) {
	r := o.Regs()
	word := func(off uint16) uint16 { return o.Word(oracle.Addr{Seg: r.SS, Off: off}) }
	kind := int(word(r.BP + 6))
	if !v.mapPending || r.DS != v.data || r.SS != v.data || r.BP > 65527 || r.BP+2 != v.mapSP || r.SP != r.BP || o.VideoMode() != 0x0e || kind < 0 || kind > 7 || word(r.BP+2) != 0x6896 || word(r.BP+4) != v.load || !bytes.Equal(o.Bytes(oracle.Addr{Seg: v.load, Off: 0x68ce}, 110), v.mapBody) || o.Word(oracle.Addr{Seg: v.data, Off: 0x26aa}) == 0 || o.Word(oracle.Addr{Seg: v.data, Off: 0x2b28 + uint16(kind)*2}) == 0 {
		v.Skipped++
		return
	}
	v.activate(o, kind, [2]int{224, 92}, v.mapSequence, 0)
}
func (v *spellCues) battleCue(o *oracle.Oracle, entry uint16) {
	r := o.Regs()
	word := func(off uint16) uint16 { return o.Word(oracle.Addr{Seg: r.SS, Off: off}) }
	selector := word(r.BP - 4)
	if !v.battlePending || r.DS != v.data || r.SS != v.data || r.BP+2 != v.battleSP || r.BP < 20 || r.BP > 65527 || o.VideoMode() != 0x0e || word(r.BP+2) != 0x1cfe || word(r.BP+4) != v.battle || !bytes.Equal(o.Bytes(oracle.Addr{Seg: v.battle, Off: 0x334}, len(v.battleBody)), v.battleBody) || (entry == 0x752 && selector != 4) || (entry == 0x906 && selector != 6) || o.Word(oracle.Addr{Seg: v.data, Off: 0x26aa}) == 0 {
		v.Skipped++
		return
	}
	slot := word(r.BP + 6)
	if slot < 3 || slot >= 6 {
		v.Skipped++
		return
	}
	id := o.Word(oracle.Addr{Seg: v.data, Off: 0x6fb6 + slot*2})
	if id >= 6 {
		v.Skipped++
		return
	}
	casterKind := o.Word(oracle.Addr{Seg: v.data, Off: 0x56e8 + id*4})
	if (casterKind != 10 && casterKind != 12) || o.Word(oracle.Addr{Seg: v.data, Off: 0x56ea + id*4}) == 0 {
		v.Skipped++
		return
	}
	kind, ordinal := 8, 0
	if selector == 6 {
		slot = word(r.BP - 8)
		kind = 9
		ordinal = int(word(r.BP - 16))
	}
	if slot >= 6 {
		v.Skipped++
		return
	}
	packed := o.Word(oracle.Addr{Seg: v.data, Off: 0x703c + slot*2})
	anchor := [2]int{int(packed&255)*8 + 44, int(packed>>8) + 25}
	if anchor[0] < 44 || anchor[0] > 596 || anchor[1] < 25 || anchor[1] > 175 {
		v.Skipped++
		return
	}
	v.activate(o, kind, anchor, v.battleSequence, ordinal)
}
func (p *sourceAdapter) composeSpellCues(base *image.RGBA) *image.RGBA {
	v := p.e.spellCues
	if v == nil || !v.Active || p.cachedScene == nil {
		return base
	}
	o := p.e.Oracle
	if o.VideoMode() != 0x0e || o.Cycles() < v.start || o.Cycles()-v.start >= 1800000 {
		v.Active = false
		v.Completed++
		v.cached = nil
		return base
	}
	sample := int((o.Cycles() - v.start) * 120 / 1800000)
	if v.cached != nil && v.cachedBase == base && v.sample == sample {
		return v.cached
	}
	layer := drawSpellCue(v.Kind, float64(sample)/120, v.Anchor)
	if layer == nil {
		return base
	}
	pixels := p.cachedScene.Pixels[p.cachedScene.Start : p.cachedScene.Start+128000]
	out := compositeSpellCue(base, layer, pixels)
	v.Frames++
	v.cachedBase, v.cached, v.sample = base, out, sample
	return out
}
func compositeSpellCue(base, layer *image.RGBA, pixels []ownedPixel) *image.RGBA {
	if base == nil || base.Bounds() != image.Rect(0, 0, 1920, 1200) || layer == nil || len(pixels) != 128000 {
		return base
	}
	out := image.NewRGBA(base.Bounds())
	copy(out.Pix, base.Pix)
	clip := layer.Bounds().Intersect(image.Rect(12, 12, 1344, 1140))
	for y := clip.Min.Y; y < clip.Max.Y; y++ {
		for x := clip.Min.X; x < clip.Max.X; x++ {
			if pixels[y/6*640+x/3].Text.ID != 0 {
				continue
			}
			at := layer.PixOffset(x, y)
			a := uint32(layer.Pix[at+3])
			if a == 0 {
				continue
			}
			dst := out.PixOffset(x, y)
			for c := 0; c < 3; c++ {
				out.Pix[dst+c] = uint8(min(255, uint32(layer.Pix[at+c])+(uint32(out.Pix[dst+c])*(255-a)+127)/255))
			}
		}
	}
	return out
}
