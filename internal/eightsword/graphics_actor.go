package eightsword

import (
	"fmt"
	"github.com/wicanr2/dosgolem/oracle"
	"image"
)

// Fixed MAN.AY records, file offset frame*1204. See spec 007.
var heroSources = [...]struct{ NativeSHA, RecordSHA string }{
	{NativeSHA: "7a9813a1d91f65bd8ce1ed6018bcaca8b3e054189bbd3999e8cc14da909c159a", RecordSHA: "605b2440785c7760dcdcd09f5723126c3542b881a29ff6758afbc8109dcdead0"},
	{NativeSHA: "6dbe64b90670ee1d111670428633f73f29972ef83a1f805090687ea3fb07c5fa", RecordSHA: "49692088d96e38514b0f1b5e12d40d7bf9825241434b4bfe5ab9035803c762f7"},
	{NativeSHA: "b3e8433fda80e99243a1f2e30ca15e65c678768c581e252b431e3aa8cc36879d", RecordSHA: "a648e1f15f22398d726963e2ab24daa8d342d34cd0dcc6d6093f43e28b2ae8a1"},
	{NativeSHA: "12d749f1129d92cefc51d75b5c323117ddbbab78144298bd44706449a2592519", RecordSHA: "dcc6660b3424dfc78b5e57cca34c077b0220164155b18bb8724bfb667fe23594"},
	{NativeSHA: "e4f43271223cdd65bc59a025e945a2b9b60126250d35a1ce9b334b722c4fa080", RecordSHA: "4c32210b8b10e3fe96cea0873cf1e3e7921bd0d5521616f925c6b3bb80fed5b4"},
	{NativeSHA: "2cde4803a48e5c7a7904ff13410c248ca901fc399a0b8a1331d60d7a9365ddfa", RecordSHA: "fc5859952a91c827eedfb5dcfafcb5e542170aec9c86bcf8cc9fb33d8d0c7159"},
	{NativeSHA: "d5b5f1b9b8f1e83fa268510976d92d5afab6404216cb86ffcae41698befa508e", RecordSHA: "8dbe5293b925fd95b493ab7416aef323de5c029a295c3ca3674028f9b4f80bbc"},
	{NativeSHA: "09472ee2b468d0db27d9c21c5f10e0db24641e938a39251d65b1811100036edb", RecordSHA: "550add966262b8c457200f91759cf97fadb3808f70b8e4e7a862bfc7b0f46436"},
	{NativeSHA: "6cd18a7e6d97e1be959e22a43f8041856b1314a369a984013870d301d1582b7e", RecordSHA: "2765921a02cefc47a83549540c688240bb435c99685c5916aedd31b4c91e5039"},
	{NativeSHA: "83cbbdd3a105a71d308f23c69c640734118463061c847dd8a3d4163fe1135bf5", RecordSHA: "4a123a3722005514bafafe0b36b543004b20518f4fa00df8d61698a295158698"},
	{NativeSHA: "42dc15c55c040a02a43ae41070a28121d7f9b4ffe95167c37c5f5023695f6a71", RecordSHA: "59eb969deabf701b6f47511778d42ef5b8284afb713bce8cd1a99e9053984094"},
	{NativeSHA: "7f9b5e2fe383517bbcdad4bfd6f0810950e71ffcd50ab25198775a6e11871b94", RecordSHA: "4c8522d8ec6d2228cd7020f072c82bc1f55d4a5ede5b94fb616dd9232ea435e7"},
}

func (g *Graphics) setActor(at uint32, value graphicCell) {
	if len(g.actors) != 0 && g.actors[at] != value {
		g.actors[at] = value
		g.parent.revision++
	}
}

func (g *Graphics) heroRecordMatches(id uint16, kind int, source []byte) bool {
	return kind == 6 && g.assets.Actors[id] != nil && hash(source) == g.assets.ActorSHA[id]
}

func (g *Graphics) actorBackgroundKnown(first uint32, width, height int) bool {
	if width != 64 || height != 25 || len(g.actors) == 0 {
		return false
	}
	for y := 0; y < height; y++ {
		for x := 0; x < width; x++ {
			c := g.owners[(first+uint32(y*80+x/8))*8+uint32(x%8)]
			m := g.assets.Materials[c.ID]
			if m == nil || c.Local >= uint32(m.NativeWidth*m.NativeHeight) {
				return false
			}
		}
	}
	return true
}

// The generated PNG is not edited. Cache values use premultiplied RGBA.
func sampleActor(source image.Image) (*image.RGBA, error) {
	bounds := source.Bounds()
	sw, sh := bounds.Dx(), bounds.Dy()
	hasZero, hasOpaque := false, false
	for y := bounds.Min.Y; y < bounds.Max.Y && !(hasZero && hasOpaque); y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			_, _, _, a := source.At(x, y).RGBA()
			hasZero = hasZero || a == 0
			hasOpaque = hasOpaque || a == 65535
			if hasZero && hasOpaque {
				break
			}
		}
	}
	if !hasZero || !hasOpaque {
		return nil, fmt.Errorf("HD 主角須有透明背景與不透明主體")
	}
	out := image.NewRGBA(image.Rect(0, 0, 192, 150))
	for y := 0; y < 150; y++ {
		for x := 0; x < 192; x++ {
			sx, sy := max(0, (float64(x)+0.5)*float64(sw)/192-0.5), max(0, (float64(y)+0.5)*float64(sh)/150-0.5)
			x0, y0 := int(sx), int(sy)
			x1, y1 := min(x0+1, sw-1), min(y0+1, sh-1)
			fx, fy := sx-float64(x0), sy-float64(y0)
			points := [4]image.Point{{x0, y0}, {x1, y0}, {x0, y1}, {x1, y1}}
			weights := [4]float64{(1 - fx) * (1 - fy), fx * (1 - fy), (1 - fx) * fy, fx * fy}
			sums := [4]float64{}
			for i, p := range points {
				r, g, b, a := source.At(bounds.Min.X+p.X, bounds.Min.Y+p.Y).RGBA()
				if a <= 3*257 {
					continue
				}
				for channel, v := range [4]uint32{r, g, b, a} {
					sums[channel] += weights[i] * float64(v)
				}
			}
			at := y*out.Stride + x*4
			for channel, v := range sums {
				out.Pix[at+channel] = uint8(min(255, v/257) + 0.5)
			}
		}
	}
	return out, nil
}

func (g *Graphics) paintActors(out *image.RGBA, p oracle.PlanarDisplay) {
	if len(g.actors) == 0 {
		return
	}
	for y := 0; y < 200; y++ {
		for x := 0; x < 640; x++ {
			off := (p.Start + uint32(y*p.Pitch+x/8)) & 65535
			cell := g.actors[off*8+uint32(x%8)]
			m := g.assets.Actors[cell.ID]
			if m == nil {
				continue
			}
			if cell.Local >= 1600 {
				g.setActor(off*8+uint32(x%8), graphicCell{})
				continue
			}
			sx, sy := int(cell.Local)%64, int(cell.Local)/64
			for dy := 0; dy < 6; dy++ {
				for dx := 0; dx < 3; dx++ {
					src := (sy*6+dy)*m.Tile.Stride + (sx*3+dx)*4
					dst := (y*6+dy)*out.Stride + (x*3+dx)*4
					a := uint32(m.Tile.Pix[src+3])
					for channel := 0; channel < 3; channel++ {
						value := uint32(m.Tile.Pix[src+channel]) + (uint32(out.Pix[dst+channel])*(255-a)+127)/255
						out.Pix[dst+channel] = uint8(min(255, value))
					}
				}
			}
			g.Stats.ActorPaintedPixels++
		}
	}
}
