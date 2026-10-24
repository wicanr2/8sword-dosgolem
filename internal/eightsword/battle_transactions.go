package eightsword

import (
	"encoding/binary"

	"github.com/wicanr2/dosgolem/oracle"
)

// Spec 022: presentation can retain a complete frame while DOS continues.
// Only a verified GRO02-backed rectangle is eligible. Native fallback groups
// and the existing map/army paths do not acquire this transaction.
type battleBitmapTransaction struct {
	Entry, Writer uint16
	Start         uint64
	First         uint32
	Width, Height int
	Writes, Want  uint64
}

const battleBitmapStepBound = uint64(100000)

func (g *Graphics) abortBattleTransaction() {
	g.captureAfterHold = false
	if g.pending != nil {
		g.Stats.BitmapTransactionFallbacks++
		g.pending = nil
	}
}

func (g *Graphics) startBattleTransaction(entry uint16, first uint32, w, h int, dest, mode uint16) {
	g.abortBattleTransaction()
	if w != 11 || h != 50 || dest != 0xa000 || mode != 1 || first+0x4000+uint32((h-1)*80+w) > 65536 {
		return
	}
	o := g.parent.o
	if o.Word(oracle.Addr{Seg: g.parent.stringSeg, Off: 0x196}) != 0xa400 {
		return
	}
	p, ok := o.PlanarDisplay()
	if !ok || p.Width != 640 || p.Height != 200 || p.Start != 0 || p.Pitch != 80 || p.LineCompare < 199 || p.Palette != canonicalEGA {
		return
	}
	m := g.assets.Materials[battleBackgroundID]
	if m == nil || m.NativeWidth != 640 || m.NativeHeight != 200 {
		return
	}
	for y := 0; y < h; y++ {
		for x := 0; x < w*8; x++ {
			c := g.owners[(first+0x4000+uint32(y*80+x/8))*8+uint32(x%8)]
			if c.ID != battleBackgroundID || c.Local >= 640*200 {
				return
			}
		}
	}
	writer, want := uint16(0), uint64(w*h*4)
	switch entry {
	case 0x4f2:
		writer = 0x57d
	case 0x626:
		writer = 0x6b8
	case 0x423:
		writer, want = 0x47f, uint64(w*h)
	default:
		return
	}
	g.pending = &battleBitmapTransaction{Entry: entry, Writer: writer, Start: o.Steps(), First: first, Width: w, Height: h, Want: want}
	g.Stats.BitmapTransactions++
}

func (g *Graphics) beginBattleRestoreTransaction() {
	g.abortBattleTransaction()
	g.active = nil
	o := g.parent.o
	ptr := oracle.Addr{Seg: o.Arg(1), Off: o.Arg(0)}
	if !bitmapSourceInRAM(ptr, 4) {
		return
	}
	raw := o.Bytes(ptr, 4)
	w, h := int(binary.LittleEndian.Uint16(raw)), int(binary.LittleEndian.Uint16(raw[2:]))
	x, y := int(o.Arg(2)), int(o.Arg(3))
	if w != 11 || h != 50 || x+w > 80 || y+h > 200 {
		return
	}
	for row := 0; row < h; row++ {
		if o.Word(oracle.Addr{Seg: g.parent.stringSeg, Off: uint16(6 + (y+row)*2)}) != uint16((y+row)*80) {
			return
		}
	}
	ds := o.Regs().DS
	g.startBattleTransaction(0x423, uint32(y*80+x), w, h,
		o.Word(oracle.Addr{Seg: ds, Off: 0x748a}), o.Word(oracle.Addr{Seg: ds, Off: 0x7484}))
}

func (g *Graphics) observeBattleTransactionWrite(w oracle.VideoWrite) {
	b := g.pending
	if b == nil {
		return
	}
	if w.CS != g.parent.stringSeg || w.IP != b.Writer || w.Offset < b.First || (b.Entry == 0x423 && w.WriteMode != 1) || (b.Entry != 0x423 && w.WriteMode != 0) {
		g.abortBattleTransaction()
		return
	}
	delta := w.Offset - b.First
	index := b.Writes % uint64(b.Width*b.Height)
	if int(delta/80) >= b.Height || int(delta%80) >= b.Width || delta != uint32(index/uint64(b.Width)*80+index%uint64(b.Width)) || b.Writes >= b.Want {
		g.abortBattleTransaction()
		return
	}
	b.Writes++
}

func (g *Graphics) finishBattleTransaction(entry uint16) {
	b := g.pending
	if b == nil {
		return
	}
	elapsed := g.parent.o.Steps() - b.Start
	g.Stats.BitmapMaxSteps = max(g.Stats.BitmapMaxSteps, elapsed)
	if b.Entry != entry || b.Writes != b.Want || elapsed > battleBitmapStepBound {
		g.abortBattleTransaction()
		return
	}
	g.pending = nil
	g.Stats.BitmapTransactionCompletions++
	if g.captureAfterHold {
		g.captureAfterHold = false
		g.parent.Compose()
		g.Stats.BitmapCompletionCaptures++
	}
}

func (g *Graphics) holdBattleFrame() bool {
	b := g.pending
	if b == nil {
		return false
	}
	elapsed := g.parent.o.Steps() - b.Start
	if elapsed > battleBitmapStepBound || g.parent.cachedFrame == nil {
		g.abortBattleTransaction()
		return false
	}
	g.Stats.BitmapHeldFrames++
	g.captureAfterHold = true
	return true
}
