package eightsword

import (
	"image"
	"os"
	"path/filepath"

	"github.com/wicanr2/dosgolem/oracle"
)

// Spec 027: PON uses the destination-preserving 04F2 helper, not 0626.
const ponSourceSHA = "5fe52b534cccbcaab5265681c42f208751f69da1144161541f161d93b89b786e"

var ponSources = [4]battleActorSource{
	{"52ea2a2f814e481ae5009b8f853985db57f547730f182e7cfea598a320f04da0", "a69fc9dfe79641d9ac4d3eb8d1d543d74c521be9c957e9c926fd0e6c9bcca256"},
	{"3d66ffd805c84877ea3edbb36aff838178eafaeaf6a7d674b52e0547178b93db", "940308e27b760d7c09c4afae871556192d593682c8bc40a757382be41c9c766d"},
	{"9ce1e4b8560758a88ac1405ab30bee480f39dc32de94192dc875dd201d773472", "61a5081819badb113d7f199757a5a81e8a27a6f308f2b7f9952c9cffb744b42d"},
	{"db423b2b37e999194237c1ac07307bac207a6bd41de421c1e8551fd27fa005d2", "969a56a413cc4bcb87bf4f4ed4917045168ded8cc0d4237de8ca0fa8d09f82dc"},
}

var ponTargets = [4][4]int{{0, 0, 264, 300}, {33, 30, 225, 222}, {63, 66, 165, 174}, {90, 96, 114, 102}}

func loadBattleEffects(dir, root string, assets *GraphicsAssets) error {
	if _, err := os.Stat(filepath.Join(dir, "battle-pon.json")); os.IsNotExist(err) {
		return nil
	}
	// Reuse the four-image source/style/geometry validator, then commit to a
	// separate effect table. Existing actor maps are never mutated here.
	tmp := &GraphicsAssets{ByNative: map[string]uint16{}, Materials: assets.Materials, Actors: map[uint16]*graphicMaterial{}, ActorSHA: map[uint16]string{}}
	for h, id := range assets.ByNative {
		tmp.ByNative[h] = id
	}
	group := battleActorGroup{"battle-pon.json", "PON.EGG", ponSourceSHA, "battle-pon", 103, ponSources, ponTargets}
	if err := loadBattleActorGroup(dir, root, tmp, group); err != nil {
		return err
	}
	assets.Effects, assets.EffectSHA = tmp.Actors, tmp.ActorSHA
	for _, source := range ponSources {
		assets.ByNative[source.Native] = tmp.ByNative[source.Native]
	}
	return nil
}

// Frames are immutable while referenced by either VGA page. A new call uses a
// free slot, so changing the source page cannot change an earlier page copy.
const battleEffectSlots = 64

type battleEffectFrame struct {
	Tile   *image.RGBA
	Source uint16
	Refs   int
}

type battleEffectDraft struct {
	First uint32
	ID    uint16
	Frame *battleEffectFrame
	Base  []uint8
}

func (g *Graphics) setEffect(at uint32, value graphicCell, base uint8) {
	if len(g.effects) == 0 {
		return
	}
	if value.ID == 0 {
		base = 0
	}
	old := g.effects[at]
	if old == value && g.effectBase[at] == base {
		return
	}
	if old.ID != value.ID {
		if f := g.effectFrames[old.ID]; f != nil {
			f.Refs--
			if f.Refs == 0 {
				delete(g.effectFrames, old.ID)
			}
		}
		if f := g.effectFrames[value.ID]; f != nil {
			f.Refs++
		}
	}
	g.effects[at], g.effectBase[at] = value, base
	g.parent.revision++
}

func (g *Graphics) clearEffectByte(off uint32, mask uint8) {
	if len(g.effects) == 0 {
		return
	}
	for bit := 0; bit < 8; bit++ {
		if mask&(0x80>>uint(bit)) != 0 {
			g.setEffect(off*8+uint32(bit), graphicCell{}, 0)
		}
	}
}

func (g *Graphics) copyEffectByte(dst, src uint32) {
	if len(g.effects) == 0 {
		return
	}
	var cells [8]graphicCell
	var base [8]uint8
	copy(cells[:], g.effects[src*8:src*8+8])
	copy(base[:], g.effectBase[src*8:src*8+8])
	for bit, c := range cells {
		g.setEffect(dst*8+uint32(bit), c, base[bit])
	}
}

func (g *Graphics) prepareBattleEffect(id uint16, raw []byte) {
	source := g.assets.Effects[id]
	if source == nil {
		return
	}
	b, o := g.active, g.parent.o
	p, ok := o.PlanarDisplay()
	valid := b != nil && b.Kind == 6 && !b.Background && b.Width == 11 && b.Height == 50 &&
		g.pending != nil && g.pending.Entry == 0x4f2 && hash(raw) == g.assets.EffectSHA[id] &&
		ok && p.Start == 0 && p.Palette == canonicalEGA
	if valid {
		for y := 0; y < 50 && valid; y++ {
			for x := 0; x < 88; x++ {
				if g.parent.owners[(b.First+uint32(y*80+x/8))*8+uint32(x%8)].ID != 0 {
					valid = false
					break
				}
			}
		}
	}
	if !valid {
		g.Stats.BattleEffectFallbackCalls++
		return
	}
	free := g.freeBattleEffectSlot()
	if free == 0 {
		g.Stats.BattleEffectFallbackCalls++
		return
	}
	f := &battleEffectFrame{Tile: image.NewRGBA(image.Rect(0, 0, 264, 300)), Source: id}
	d := &battleEffectDraft{First: b.First, ID: free, Frame: f, Base: make([]uint8, 4400)}
	for y := 0; y < 50; y++ {
		for col := 0; col < 11; col++ {
			off := b.First + uint32(y*80+col)
			native, available := o.PlanarBytePixels(off)
			if !available {
				g.Stats.BattleEffectFallbackCalls++
				return
			}
			for bit := 0; bit < 8; bit++ {
				x, at := col*8+bit, off*8+uint32(bit)
				d.Base[y*88+x] = native[bit]
				old := g.effects[at]
				prior := g.effectFrames[old.ID]
				if prior == nil {
					continue
				}
				d.Base[y*88+x] = g.effectBase[at]
				sx, sy := int(old.Local)%88, int(old.Local)/88
				for dy := 0; dy < 6; dy++ {
					dst, src := (y*6+dy)*f.Tile.Stride+x*12, (sy*6+dy)*prior.Tile.Stride+sx*12
					copy(f.Tile.Pix[dst:dst+12], prior.Tile.Pix[src:src+12])
				}
			}
		}
	}
	for at := 0; at < len(f.Tile.Pix); at += 4 {
		alpha := uint32(source.Tile.Pix[at+3])
		for c := 0; c < 4; c++ {
			f.Tile.Pix[at+c] = uint8(min(255, uint32(source.Tile.Pix[at+c])+(uint32(f.Tile.Pix[at+c])*(255-alpha)+127)/255))
		}
	}
	g.effectDraft, b.Effect = d, id
	g.Stats.HDSourceCalls++
	g.Stats.BattleEffectCalls++
}

func (g *Graphics) freeBattleEffectSlot() uint16 {
	for n := uint16(1); n <= battleEffectSlots; n++ {
		if g.effectFrames[n] == nil {
			return n
		}
	}
	return 0
}

func (g *Graphics) abortBattleEffect() {
	d := g.effectDraft
	if d == nil {
		return
	}
	g.effectDraft = nil
	if g.active != nil {
		g.active.Effect = 0
	}
	for y := 0; y < 50; y++ {
		for x := 0; x < 88; x++ {
			at := (d.First+uint32(y*80+x/8))*8 + uint32(x%8)
			g.setEffect(at, graphicCell{}, 0)
			g.set(at, graphicCell{})
			g.setActor(at, graphicCell{})
		}
	}
	g.Stats.BattleEffectFallbackCalls++
}

func (g *Graphics) commitBattleEffect() {
	d := g.effectDraft
	if d == nil {
		return
	}
	if g.active == nil || g.active.Effect == 0 || g.active.EffectWrites != 2200 {
		g.abortBattleEffect()
		return
	}
	g.effectDraft = nil
	g.effectFrames[d.ID] = d.Frame
	for y := 0; y < 50; y++ {
		for x := 0; x < 88; x++ {
			at, local := (d.First+uint32(y*80+x/8))*8+uint32(x%8), uint32(y*88+x)
			g.setEffect(at, graphicCell{d.ID, local}, d.Base[local])
		}
	}
	g.active.Effect = 0
	g.Stats.BattleEffectCompletions++
}

func (g *Graphics) restoreEffectBases(out *image.RGBA, p oracle.PlanarDisplay) {
	if len(g.effects) == 0 {
		return
	}
	for y := 0; y < 200; y++ {
		for x := 0; x < 640; x++ {
			at := ((p.Start+uint32(y*80+x/8))&65535)*8 + uint32(x%8)
			if g.effects[at].ID == 0 {
				continue
			}
			color := canonicalEGA[g.effectBase[at]]
			for dy := 0; dy < 6; dy++ {
				for dx := 0; dx < 3; dx++ {
					dst := (y*6+dy)*out.Stride + (x*3+dx)*4
					copy(out.Pix[dst:dst+3], color[:])
					out.Pix[dst+3] = 255
				}
			}
		}
	}
}

func (g *Graphics) paintEffects(out *image.RGBA, p oracle.PlanarDisplay) {
	if len(g.effects) == 0 {
		return
	}
	for y := 0; y < 200; y++ {
		for x := 0; x < 640; x++ {
			at := ((p.Start+uint32(y*80+x/8))&65535)*8 + uint32(x%8)
			cell := g.effects[at]
			f := g.effectFrames[cell.ID]
			if f == nil {
				continue
			}
			sx, sy := int(cell.Local)%88, int(cell.Local)/88
			for dy := 0; dy < 6; dy++ {
				for dx := 0; dx < 3; dx++ {
					dst, src := (y*6+dy)*out.Stride+(x*3+dx)*4, (sy*6+dy)*f.Tile.Stride+(sx*3+dx)*4
					alpha := uint32(f.Tile.Pix[src+3])
					for c := 0; c < 3; c++ {
						out.Pix[dst+c] = uint8(min(255, uint32(f.Tile.Pix[src+c])+(uint32(out.Pix[dst+c])*(255-alpha)+127)/255))
					}
					out.Pix[dst+3] = 255
				}
			}
			g.Stats.EffectPaintedPixels++
		}
	}
}
