// Spec 030 READY: approved B presentation; no guest writes or gameplay decisions.
package eightsword

import (
	"bytes"
	"encoding/binary"
	"github.com/wicanr2/dosgolem/oracle"
	"image"
)

type BattleVFXInfo struct {
	Bound, Active                                                                                  bool
	Phase                                                                                          string
	Started, Completed, Cancelled, Skipped, SourceCommits, PONCommits, Frames, ProtectedTextPixels uint64
	LastSkip                                                                                       string
	Source, Target                                                                                 [2]int
	QuakePans, QuakeDuplicates                                                                     uint64
	Shift                                                                                          [2]int
}
type battleVFX struct {
	BattleVFXInfo
	code, data, ss, sp                               uint16
	body, playerBody                                 []byte
	player                                           bool
	running                                          bool
	start, lastStep, lastCycles, poseCycle, poseSpan uint64
	poses, pon                                       int
	cachedBase, cached                               *image.RGBA
	cachedPhase                                      string
	cachedSample                                     int
	quake                                            bool
	quakeBody                                        []byte
	quakeBP                                          uint16
	quakeLocal                                       int
	quakePoints                                      [6][2]int
}

func (e *Engine) BattleVFXStatus() BattleVFXInfo {
	if e.battleVFX == nil {
		return BattleVFXInfo{}
	}
	return e.battleVFX.BattleVFXInfo
}
func (v *battleVFX) hide() {
	v.Active = false
	v.Phase = ""
	v.Shift = [2]int{}
	v.cachedBase = nil
	v.cached = nil
}
func (v *battleVFX) cancel(reason string) {
	if v.running {
		v.Cancelled++
	}
	v.running = false
	v.LastSkip = reason
	v.hide()
}
func (v *battleVFX) skip(reason string) { v.Skipped++; v.LastSkip = reason }
func (p *sourceAdapter) bindBattleVFX() {
	e := p.e
	if e.battleVFX != nil {
		return
	}
	if hash(e.PAM) != PAMSHA || e.Tracker.loadSegment > 0xffff-0x1d78 {
		return
	}
	load := e.Tracker.loadSegment
	o := e.Oracle
	word := func(at int) uint16 { return binary.LittleEndian.Uint16(e.PAM[at:]) }
	code := append([]byte(nil), e.PAM[int(word(8))*16:]...)
	for i := 0; i < int(word(6)); i++ {
		at := int(word(24)) + i*4
		loc := int(word(at+2))*16 + int(word(at))
		binary.LittleEndian.PutUint16(code[loc:], binary.LittleEndian.Uint16(code[loc:])+load)
	}
	at := 0xe57*16 + 0x36c6
	v := &battleVFX{BattleVFXInfo: BattleVFXInfo{Bound: true}, code: load + 0xe57, data: load + 0x1d78, body: append([]byte(nil), code[at:at+518]...)}
	playerAt := 0xe57*16 + 0x345c
	v.playerBody = append([]byte(nil), code[playerAt:playerAt+518]...)
	e.battleVFX = v
	p.bindBattleQuake(v, code)
	p.onCall(oracle.Addr{Seg: v.code, Off: 0x36c6}, func(*oracle.Oracle) {
		if e.battleVFX != nil {
			e.battleVFX.begin(o)
		}
	})
	p.onCall(oracle.Addr{Seg: v.code, Off: 0x345c}, func(*oracle.Oracle) {
		if e.battleVFX != nil {
			e.battleVFX.beginFrom(o, true)
		}
	})
	for _, site := range []struct {
		off    uint16
		player bool
	}{{0x38cb, false}, {0x3661, true}} {
		p.onCall(oracle.Addr{Seg: v.code, Off: site.off}, func(*oracle.Oracle) {
			v := e.battleVFX
			if v == nil || !v.running || v.player != site.player {
				return
			}
			r := o.Regs()
			if r.SS != v.ss || r.SP != v.sp {
				v.cancel("return-stack")
				return
			}
			v.Completed++
			v.running = false
			v.hide()
		})
	}
}
func (v *battleVFX) begin(o *oracle.Oracle) {
	v.beginFrom(o, false)
}
func (v *battleVFX) beginFrom(o *oracle.Oracle, player bool) {
	if v.running {
		v.cancel("new-effect")
	}
	v.quake = false
	r := o.Regs()
	entry, caller, body := uint16(0x36c6), uint16(0xe0d), v.body
	if player {
		entry, caller, body = 0x345c, 0x74a, v.playerBody
	}
	if r.DS != v.data || r.SS != v.data || r.BP < 4 || r.SP > 65519 || r.SP > r.BP || o.VideoMode() != 0x0e || !bytes.Equal(o.Bytes(oracle.Addr{Seg: v.code, Off: entry}, 518), body) {
		v.skip("entry-context")
		return
	}
	word := func(off uint16) uint16 { return o.Word(oracle.Addr{Seg: v.data, Off: off}) }
	callerMatches := word(r.SP) == caller || (player && word(r.SP) == 0x516)
	if !callerMatches || word(r.SP+2) != v.code {
		v.skip("caller")
		return
	}
	selector := word(r.BP - 4)
	playerPair := ((selector == 0 || selector == 2 || selector == 3 || selector == 5) && word(r.SP) == 0x74a) || (selector == 1 && word(r.SP) == 0x516)
	if (player && !playerPair) || (!player && selector != 0 && selector != 2 && selector != 5) {
		v.skip("selector")
		return
	}
	args := [6]uint16{}
	for i := range args {
		args[i] = o.Arg(i)
	}
	for i := 0; i < 2; i++ {
		row, col := args[2+i*2], args[3+i*2]
		if args[i] >= 6 || row > 1 || col > 2 || args[i] != row*3+col {
			v.skip("position-arguments")
			return
		}
	}
	mapping, units, sourceTable, targetTable := uint16(0x6fc2), uint16(0x5700), uint16(0x701e), uint16(0x703c)
	if player {
		mapping, units, sourceTable, targetTable = 0x6fb6, 0x56e8, 0x703c, 0x701e
	}
	id := word(mapping + args[0]*2)
	if id >= 6 || word(units+id*4) == 0 || word(units+2+id*4) == 0 {
		v.skip("empty-source")
		return
	}
	if player && (args[0] < 3 || word(0x26aa) == 0 || (word(units+id*4) != 10 && word(units+id*4) != 12)) {
		v.skip("player-caster")
		return
	}
	point := func(base, row, col uint16) [2]int {
		at := base + row*6 + col*2
		return [2]int{int(o.Byte(oracle.Addr{Seg: v.data, Off: at})) * 8, int(o.Byte(oracle.Addr{Seg: v.data, Off: at + 1}))}
	}
	source, target := point(sourceTable, args[2], args[3]), point(targetTable, args[4], args[5])
	for _, p := range [][2]int{source, target} {
		if p[0] < 0 || p[0]+88 > 640 || p[1] < 0 || p[1]+50 > 200 {
			v.skip("position-table")
			return
		}
	}
	v.Started++
	v.Active = true
	v.Phase = "flight"
	v.Source = source
	v.Target = target
	v.running = true
	v.player = player
	v.ss, v.sp = r.SS, r.SP
	v.start = o.Steps()
	v.lastStep = o.Steps()
	v.lastCycles = o.Cycles()
	v.poseCycle = 0
	v.poseSpan = 0
	v.poses = 0
	v.pon = 0
	v.cachedBase = nil
	v.cached = nil
}
func (e *Engine) syncBattleVFX() {
	v := e.battleVFX
	if v == nil || !v.running {
		return
	}
	step, cycles := e.Oracle.Steps(), e.Oracle.Cycles()
	if step < v.lastStep || cycles < v.lastCycles {
		v.cancel("clock-rewind")
		return
	}
	if step-v.start > 10000000 {
		v.cancel("step-bound")
		return
	}
	if !e.HD || e.Exited || e.renderFault != nil || e.inEndingPhase() || e.Oracle.VideoMode() != 0x0e {
		v.cancel("scene-exit")
		return
	}
	v.lastStep = step
	v.lastCycles = cycles
}
func (p *sourceAdapter) battleVFXBitmap(entry uint16, raw []byte, x, y, w, h int, dest uint16) {
	v := p.e.battleVFX
	if v == nil || !v.running {
		return
	}
	if v.quake {
		v.quakeBitmap(entry, raw, x, y, w, h, dest)
		return
	}
	if dest != 0xa000 || w != 11 || h != 50 {
		return
	}
	xy := [2]int{x * 8, y}
	if entry == 0x626 && xy == v.Source && v.Phase == "flight" {
		v.SourceCommits++
		v.poses++
		now := p.e.Oracle.Cycles()
		if v.poseCycle != 0 {
			v.poseSpan = now - v.poseCycle
		}
		v.poseCycle = now
		if v.poses > 4 {
			v.cancel("source-order")
		}
		return
	}
	if entry == 0x4f2 && xy == v.Target {
		record := -1
		for i, s := range ponSources {
			if hash(raw) == s.Record {
				record = i
				break
			}
		}
		if record < 0 || v.pon >= 12 || record != []int{1, 2, 3, 0}[v.pon%4] {
			v.cancel("effect-source-order")
			return
		}
		v.pon++
		v.PONCommits++
		v.Active = true
		v.Phase = "impact"
		v.cachedBase = nil
		return
	}
	if (entry == 0x626 || entry == 0x423) && xy == v.Target && v.pon > 0 {
		v.hide()
	}
}
func (p *sourceAdapter) composeBattleVFX(base *image.RGBA) *image.RGBA {
	e := p.e
	e.syncBattleVFX()
	v := e.battleVFX
	if v == nil || !v.Active || v.Phase == "" {
		return base
	}
	if v.quake {
		return p.composeBattleQuake(base)
	}
	progress := 0.0
	if v.Phase == "flight" {
		if v.poses < 1 {
			return base
		}
		progress = float64(v.poses-1) / 4
		if v.poseSpan > 0 {
			elapsed := min(float64(e.Oracle.Cycles()-v.poseCycle)/float64(v.poseSpan), 1.0)
			progress += elapsed / 4
		}
		progress = min(progress, .95)
	} else {
		progress = (float64(v.pon) - .5) / 12
	}
	sample := int(progress * 120)
	if v.cached != nil && v.cachedBase == base && v.cachedPhase == v.Phase && v.cachedSample == sample {
		return v.cached
	}
	layer := drawBattleVFX(v.Phase, float64(sample)/120, v.Source, v.Target)
	if layer == nil {
		return base
	}
	out := image.NewRGBA(base.Bounds())
	copy(out.Pix, base.Pix)
	visible := p.cachedScene.Pixels[p.cachedScene.Start : p.cachedScene.Start+128000]
	for y := layer.Rect.Min.Y; y < layer.Rect.Max.Y; y++ {
		for x := layer.Rect.Min.X; x < layer.Rect.Max.X; x++ {
			at := layer.PixOffset(x, y)
			alpha := uint32(layer.Pix[at+3])
			if alpha == 0 {
				continue
			}
			if visible[y/6*640+x/3].Text.ID != 0 {
				v.ProtectedTextPixels++
				continue
			}
			dst := out.PixOffset(x, y)
			for c := 0; c < 3; c++ {
				out.Pix[dst+c] = uint8(min(255, uint32(layer.Pix[at+c])+(uint32(out.Pix[dst+c])*(255-alpha)+127)/255))
			}
		}
	}
	v.Frames++
	v.cachedBase = base
	v.cached = out
	v.cachedPhase = v.Phase
	v.cachedSample = sample
	return out
}
