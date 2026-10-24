package eightsword

import (
	"bytes"
	"encoding/binary"
	"github.com/wicanr2/dosgolem/oracle"
	"image"
)

type graphicCell struct {
	ID    uint16
	Local uint32
}
type bitmapCall struct {
	Kind            int
	Width, Height   int
	First           uint32
	Background      bool
	BackgroundFirst uint32
	Mask            []byte
	Material        uint16
	Actor           uint16
	ActorWrites     int
	Effect          uint16
	EffectWrites    int
}
type GraphicsStats struct {
	Bound                                                                                                          bool
	MaskedCalls, Opaque5Calls, Opaque4Calls, SourceMatches, HDSourceCalls                                          uint64
	MaskedWrites, CopiedBytes, InvalidatedPixels, AssignedPixels, CompositedFrames, PaintedNativePixels            uint64
	LastPaintedPixels, GeometryRejected, PaletteFallbackFrames                                                     uint64
	Errors                                                                                                         []string
	ActorCalls, ActorFallbackCalls, ActorAssignedPixels, ActorPaintedPixels, ActorCompletions                      uint64
	BackgroundMaskedCalls                                                                                          uint64
	BattleActorCalls, BattleActorCompletions, BattleActorFallbackCalls                                             uint64
	BitmapTransactions, BitmapTransactionCompletions, BitmapHeldFrames, BitmapTransactionFallbacks, BitmapMaxSteps uint64
	BitmapCompletionCaptures                                                                                       uint64
	BattleEffectCalls, BattleEffectCompletions, BattleEffectFallbackCalls, EffectPaintedPixels                     uint64
}
type Graphics struct {
	parent           *Tracker
	assets           *GraphicsAssets
	owners           []graphicCell
	actors           []graphicCell
	active           *bitmapCall
	pending          *battleBitmapTransaction
	captureAfterHold bool
	effects          []graphicCell
	effectBase       []uint8
	effectFrames     map[uint16]*battleEffectFrame
	effectDraft      *battleEffectDraft
	Stats            GraphicsStats
}

func newGraphics(t *Tracker, a *GraphicsAssets) *Graphics {
	g := &Graphics{parent: t, assets: a, owners: make([]graphicCell, 65536*8)}
	if len(a.Actors) > 0 {
		g.actors = make([]graphicCell, 65536*8)
	}
	if len(a.Effects) > 0 {
		g.effects = make([]graphicCell, 65536*8)
		g.effectBase = make([]uint8, 65536*8)
		g.effectFrames = map[uint16]*battleEffectFrame{}
	}
	return g
}
func (g *Graphics) bind() {
	t := g.parent
	for _, site := range []struct {
		ip         uint16
		file, kind int
	}{{0x4f2, 0x15582, 6}, {0x76f, 0x157ff, 5}, {0x99c, 0x15a2c, 4}, {0x626, 0x156b6, 6}, {0x423, 0x154b3, 1}} {
		if !bytes.Equal(t.o.Bytes(oracle.Addr{Seg: t.stringSeg, Off: site.ip}, 16), t.pam[site.file:site.file+16]) {
			g.Stats.Errors = append(g.Stats.Errors, "PAM 圖像入口 bytes 不符")
			return
		}
	}
	for _, ret := range []uint16{0x625, 0x76e, 0x4f1} {
		if t.o.Byte(oracle.Addr{Seg: t.stringSeg, Off: ret}) != 0xcb {
			g.Stats.Errors = append(g.Stats.Errors, "PAM 圖像返回 bytes 不符")
			return
		}
	}
	for _, site := range []struct {
		ip   uint16
		kind int
	}{{0x4f2, 6}, {0x76f, 5}, {0x99c, 4}} {
		site := site
		t.o.OnCall(oracle.Addr{Seg: t.stringSeg, Off: site.ip}, func(*oracle.Oracle) { g.begin(site.kind) })
	}
	t.o.OnCall(oracle.Addr{Seg: t.stringSeg, Off: 0x626}, func(*oracle.Oracle) { g.beginSource(6, true) })
	t.o.OnCall(oracle.Addr{Seg: t.stringSeg, Off: 0x423}, func(*oracle.Oracle) { g.beginBattleRestoreTransaction() })
	for _, site := range []struct{ entry, ret uint16 }{{0x4f2, 0x625}, {0x626, 0x76e}, {0x423, 0x4f1}} {
		site := site
		t.o.OnCall(oracle.Addr{Seg: t.stringSeg, Off: site.ret}, func(*oracle.Oracle) { g.finishBattleTransaction(site.entry) })
	}
	g.Stats.Bound = true
}
func (g *Graphics) clear() {
	g.abortBattleTransaction()
	clear(g.owners)
	clear(g.actors)
	clear(g.effects)
	clear(g.effectBase)
	clear(g.effectFrames)
	g.active = nil
}

// Oracle.Bytes uses machine reads. Never touch VGA latches while observing a
// bitmap source; all verified source buffers are in conventional RAM.
func bitmapSourceInRAM(ptr oracle.Addr, length int) bool {
	return length > 0 && length <= 65536 && int(ptr.Off) <= 65536-length && ptr.Linear() < 0xa0000 && uint32(length) <= 0xa0000-ptr.Linear()
}

func (g *Graphics) begin(kind int) {
	g.beginSource(kind, false)
}

func (g *Graphics) beginSource(kind int, background bool) {
	g.abortBattleTransaction()
	t := g.parent
	o := t.o
	g.active = nil
	switch kind {
	case 6:
		g.Stats.MaskedCalls++
	case 5:
		g.Stats.Opaque5Calls++
	case 4:
		g.Stats.Opaque4Calls++
	}
	ptr := oracle.Addr{Seg: o.Arg(1), Off: o.Arg(0)}
	if !bitmapSourceInRAM(ptr, 4) {
		g.Stats.GeometryRejected++
		return
	}
	header := o.Bytes(ptr, 4)
	w, h := int(binary.LittleEndian.Uint16(header)), int(binary.LittleEndian.Uint16(header[2:]))
	x, y := int(o.Arg(2)), int(o.Arg(3))
	area := w * h
	n := 4 + area*kind
	ds := o.Regs().DS
	dest := o.Word(oracle.Addr{Seg: ds, Off: 0x748a})
	mode := o.Word(oracle.Addr{Seg: ds, Off: 0x7484})
	if w < 1 || w > 80 || h < 1 || h > 200 || x+w > 80 || y+h > 200 || !bitmapSourceInRAM(ptr, n) || (dest != 0xa000 && dest != 0xa400) || mode == 2 || mode == 3 {
		g.Stats.GeometryRejected++
		return
	}
	first := uint32(dest-0xa000)*16 + uint32(o.Word(oracle.Addr{Seg: t.stringSeg, Off: uint16(6 + y*2)})) + uint32(x)
	if first+uint32((h-1)*80+w) > 65536 {
		g.Stats.GeometryRejected++
		return
	}
	for row := 0; row < h; row++ {
		off := uint32(dest-0xa000)*16 + uint32(o.Word(oracle.Addr{Seg: t.stringSeg, Off: uint16(6 + (y+row)*2)})) + uint32(x)
		if off != first+uint32(row*80) {
			g.Stats.GeometryRejected++
			return
		}
	}
	backgroundFirst := uint32(0)
	if background {
		// Spec 021: this helper reads A400 latches instead of preserving
		// the old destination. Keep unverified page pairs native.
		if dest != 0xa000 || mode != 1 || o.Word(oracle.Addr{Seg: t.stringSeg, Off: 0x196}) != 0xa400 {
			g.Stats.GeometryRejected++
			return
		}
		backgroundFirst = first + 0x4000
		if backgroundFirst+uint32((h-1)*80+w) > 65536 {
			g.Stats.GeometryRejected++
			return
		}
		g.Stats.BackgroundMaskedCalls++
	}
	source := o.Bytes(ptr, n)
	id := g.assets.ByNative[hash(source[:4+area*4])]
	effectSource := id
	if id != 0 {
		g.Stats.SourceMatches++
	}
	actor := uint16(0)
	battleActor := g.assets.BattleActors[id]
	if g.assets.Actors[id] != nil && ((!background && !battleActor) || (background && battleActor)) {
		knownBackground := false
		if background {
			knownBackground = g.battleActorBackgroundKnown(backgroundFirst, w*8, h)
		} else {
			knownBackground = g.actorBackgroundKnown(first, w*8, h)
		}
		if g.heroRecordMatches(id, kind, source) && knownBackground {
			actor = id
			if battleActor {
				g.Stats.BattleActorCalls++
			} else {
				g.Stats.ActorCalls++
			}
		} else {
			if battleActor {
				g.Stats.BattleActorFallbackCalls++
			} else {
				g.Stats.ActorFallbackCalls++
			}
			// A rejected replacement must not leave the previous painted pose.
			for row := 0; row < h; row++ {
				for pixel := 0; pixel < w*8; pixel++ {
					g.setActor((first+uint32(row*80+pixel/8))*8+uint32(pixel%8), graphicCell{})
				}
			}
		}
	}
	if g.assets.Materials[id] != nil || actor != 0 {
		g.Stats.HDSourceCalls++
	}
	if g.assets.Materials[id] == nil {
		id = 0
	}
	call := &bitmapCall{Kind: kind, Width: w, Height: h, First: first, Material: id, Actor: actor, Background: background, BackgroundFirst: backgroundFirst}
	if kind == 6 {
		call.Mask = append([]byte(nil), source[4+area*5:4+area*6]...)
	}
	g.active = call
	if kind == 6 {
		entry := uint16(0x4f2)
		if background {
			entry = 0x626
		}
		g.startBattleTransaction(entry, first, w, h, dest, mode)
		if !background {
			g.prepareBattleEffect(effectSource, source)
		}
	}
}

// Background-backed writes replace even transparent destination pixels.
// Source ownership must be copied before the mask removes opaque pixels.
func (g *Graphics) backgroundSource(w oracle.VideoWrite) (uint32, bool) {
	b := g.active
	if b == nil || !b.Background || b.Kind != 6 || w.CS != g.parent.stringSeg || w.IP != 0x6b8 || w.WriteMode != 0 || w.Offset < b.First {
		return 0, false
	}
	delta := w.Offset - b.First
	if int(delta/80) >= b.Height || int(delta%80) >= b.Width {
		return 0, false
	}
	return b.BackgroundFirst + delta, true
}
func (g *Graphics) set(at uint32, value graphicCell) {
	if g.owners[at] != value {
		g.owners[at] = value
		g.parent.revision++
	}
}
func (g *Graphics) copyByte(destination, source uint32) {
	var saved [8]graphicCell
	copy(saved[:], g.owners[source*8:source*8+8])
	for bit, value := range saved {
		g.set(destination*8+uint32(bit), value)
	}
	if len(g.actors) != 0 {
		copy(saved[:], g.actors[source*8:source*8+8])
		for bit, value := range saved {
			g.setActor(destination*8+uint32(bit), value)
		}
	}
	g.Stats.CopiedBytes++
	g.copyEffectByte(destination, source)
}
func (g *Graphics) clearByte(offset uint32, mask uint8) {
	for bit := 0; bit < 8; bit++ {
		if mask&(0x80>>uint(bit)) != 0 {
			if g.owners[offset*8+uint32(bit)].ID != 0 {
				g.Stats.InvalidatedPixels++
			}
			g.set(offset*8+uint32(bit), graphicCell{})
			g.setActor(offset*8+uint32(bit), graphicCell{})
			g.setEffect(offset*8+uint32(bit), graphicCell{}, 0)
		}
	}
}

// Returns the pixels actually affected by the observed known bitmap write.
// The caller applies the same mask to text ownership invalidation.
func (g *Graphics) write(w oracle.VideoWrite) uint8 {
	t := g.parent
	b := g.active
	kind := 0
	if w.CS == t.stringSeg {
		switch w.IP {
		case 0x57d, 0x6b8:
			kind = 6
		case 0x7cf:
			kind = 5
		case 0x9fc:
			kind = 4
		}
	}
	if kind != 0 && b != nil && b.Kind == kind && b.Background == (w.IP == 0x6b8) && w.WriteMode == 0 && w.Offset >= b.First {
		delta := w.Offset - b.First
		row, col := int(delta/80), int(delta%80)
		if row < b.Height && col < b.Width {
			mask := uint8(255)
			if kind == 6 {
				mask = b.Mask[row*b.Width+col]
				g.Stats.MaskedWrites++
			}
			if b.Effect != 0 {
				b.EffectWrites++
				return mask
			}
			g.clearEffectByte(w.Offset, mask)
			if b.Actor != 0 {
				b.ActorWrites++
				if b.ActorWrites == b.Width*b.Height*4 {
					if g.assets.BattleActors[b.Actor] {
						g.Stats.BattleActorCompletions++
					} else {
						g.Stats.ActorCompletions++
					}
				}
				for bit := 0; bit < 8; bit++ {
					g.setActor(w.Offset*8+uint32(bit), graphicCell{b.Actor, uint32(row*b.Width*8 + col*8 + bit)})
					g.Stats.ActorAssignedPixels++
				}
				return mask
			}
			for bit := 0; bit < 8; bit++ {
				if mask&(0x80>>uint(bit)) != 0 {
					g.setActor(w.Offset*8+uint32(bit), graphicCell{})
					value := graphicCell{}
					if b.Material != 0 {
						value = graphicCell{b.Material, uint32(row*b.Width*8 + col*8 + bit)}
						g.Stats.AssignedPixels++
					}
					g.set(w.Offset*8+uint32(bit), value)
				}
			}
			return mask
		}
	}
	font := false
	if w.CS == t.fontSeg {
		switch w.IP {
		case 0x4b4e, 0x4b74, 0x4ba8, 0x4bce, 0x4b80, 0x4bda:
			font = true
		}
	}
	if w.CS == t.stringSeg {
		switch w.IP {
		case 0xc43, 0xc68, 0xc71:
			font = true
		}
	}
	if font && t.active != nil && t.active.BG == 255 {
		g.clearEffectByte(w.Offset, 255)
		return 255
	}
	g.clearByte(w.Offset, 255)
	return 255
}

var canonicalEGA = [16][3]uint8{{0, 0, 0}, {0, 0, 170}, {0, 170, 0}, {0, 170, 170}, {170, 0, 0}, {170, 0, 170}, {170, 85, 0}, {170, 170, 170}, {85, 85, 85}, {85, 85, 255}, {85, 255, 85}, {85, 255, 255}, {255, 85, 85}, {255, 85, 255}, {255, 255, 85}, {255, 255, 255}}

func (g *Graphics) paint(out *image.RGBA, p oracle.PlanarDisplay) {
	g.Stats.LastPaintedPixels = 0
	if !g.Stats.Bound || p.Width != 640 || p.Height != 200 || p.Pitch != 80 || p.LineCompare < 199 || p.Palette != canonicalEGA {
		g.Stats.PaletteFallbackFrames++
		return
	}
	g.restoreEffectBases(out, p)
	for y := 0; y < 200; y++ {
		for x := 0; x < 640; {
			off := (p.Start + uint32(y*p.Pitch+x/8)) & 65535
			owner := g.owners[off*8+uint32(x%8)]
			material := g.assets.Materials[owner.ID]
			if material == nil {
				x++
				continue
			}
			sx, sy := int(owner.Local)%material.NativeWidth, int(owner.Local)/material.NativeWidth
			if sy >= material.NativeHeight {
				if len(g.Stats.Errors) < 8 {
					g.Stats.Errors = append(g.Stats.Errors, "圖像圖內座標越界，保留原版")
				}
				g.set(off*8+uint32(x%8), graphicCell{})
				x++
				continue
			}
			run := 1
			for x+run < 640 && sx+run < material.NativeWidth {
				nx := x + run
				noff := (p.Start + uint32(y*p.Pitch+nx/8)) & 65535
				next := g.owners[noff*8+uint32(nx%8)]
				if next.ID != owner.ID || int(next.Local) != int(owner.Local)+run {
					break
				}
				run++
			}
			for dy := 0; dy < 6; dy++ {
				dst := (y*6+dy)*out.Stride + x*12
				src := (sy*6+dy)*material.Tile.Stride + sx*12
				copy(out.Pix[dst:dst+run*12], material.Tile.Pix[src:src+run*12])
			}
			g.Stats.LastPaintedPixels += uint64(run)
			x += run
		}
	}
	g.Stats.CompositedFrames++
	g.Stats.PaintedNativePixels += g.Stats.LastPaintedPixels
	g.paintActors(out, p)
	g.paintEffects(out, p)
}
