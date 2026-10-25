//go:build ignore

// 047 DRAFT. Method reference: MM3 direct-render-methodology.md,
// Wang Chun-Yu / wicanr2, https://github.com/wicanr2/mm3-dosgolem, RRSAL-1.0.
// The backend below accepts textures, rectangles and colors, never DOS state.
package eightsword

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"image"
	"os"
	"path/filepath"
	"time"
)

type ownedRenderOp struct {
	Texture     *image.RGBA
	Destination image.Rectangle
	Source      image.Point
	Color       [3]uint8
	Blend       bool
}
type ownedRenderStats struct {
	NativeRGBPixels, TextureCopyPixels, BlendedPixels int
	FillRectangles, CopyRectangles, BlendRectangles   int
}
type ownedRenderBatch struct {
	Operations []ownedRenderOp
	Stats      ownedRenderStats
}
type ownedRenderKey struct {
	Texture                  *image.RGBA
	X, Width, SourceX, Layer int
	Color                    [3]uint8
	Blend                    bool
}

func (b *ownedRenderBatch) append(op ownedRenderOp, layer int, last map[ownedRenderKey]int) {
	key := ownedRenderKey{op.Texture, op.Destination.Min.X, op.Destination.Dx(), op.Source.X, layer, op.Color, op.Blend}
	if i, ok := last[key]; ok {
		prior := &b.Operations[i]
		if prior.Destination.Max.Y == op.Destination.Min.Y && (op.Texture == nil || prior.Source.Y+prior.Destination.Dy() == op.Source.Y) {
			prior.Destination.Max.Y = op.Destination.Max.Y
			return
		}
	}
	last[key] = len(b.Operations)
	b.Operations = append(b.Operations, op)
}

func submitOwnedBatch(out *image.RGBA, b *ownedRenderBatch) error {
	if out == nil || out.Bounds() != image.Rect(0, 0, 1920, 1200) {
		return fmt.Errorf("owned batch target")
	}
	for _, op := range b.Operations {
		if op.Destination.Empty() || !op.Destination.In(out.Bounds()) {
			return fmt.Errorf("owned batch destination")
		}
		if op.Texture != nil && !(image.Rectangle{Min: op.Source, Max: op.Source.Add(op.Destination.Size())}).In(op.Texture.Bounds()) {
			return fmt.Errorf("owned batch texture")
		}
	}
	for _, op := range b.Operations {
		r := op.Destination
		if op.Texture == nil {
			first := out.Pix[r.Min.Y*out.Stride+r.Min.X*4 : r.Min.Y*out.Stride+r.Max.X*4]
			value := uint32(op.Color[0]) | uint32(op.Color[1])<<8 | uint32(op.Color[2])<<16 | 0xff000000
			for at := 0; at < len(first); at += 4 {
				binary.LittleEndian.PutUint32(first[at:], value)
			}
			for y := r.Min.Y + 1; y < r.Max.Y; y++ {
				copy(out.Pix[y*out.Stride+r.Min.X*4:y*out.Stride+r.Max.X*4], first)
			}
			continue
		}
		for row := 0; row < r.Dy(); row++ {
			source := (op.Source.Y+row)*op.Texture.Stride + op.Source.X*4
			destination := (r.Min.Y+row)*out.Stride + r.Min.X*4
			src := op.Texture.Pix[source : source+r.Dx()*4]
			dst := out.Pix[destination : destination+r.Dx()*4]
			if !op.Blend {
				copy(dst, src)
				continue
			}
			for at := 0; at < len(src); at += 4 {
				a := uint32(src[at+3])
				if a == 0 && src[at] == 0 && src[at+1] == 0 && src[at+2] == 0 {
					continue
				}
				if a == 255 {
					copy(dst[at:at+3], src[at:at+3])
					continue
				}
				for ch := 0; ch < 3; ch++ {
					dst[at+ch] = uint8(min(255, uint32(src[at+ch])+(uint32(dst[at+ch])*(255-a)+127)/255))
				}
			}
		}
	}
	return nil
}

func prepareOwnedBatch(s *ownedScene, art *GraphicsAssets, palette *presentationPalette) (ownedRenderBatch, map[drawGroup]bool) {
	b := ownedRenderBatch{}
	groups := map[drawGroup]bool{}
	sidebar := false
	visible := s.Pixels[s.Start : s.Start+16000*8]
	for at, c := range visible {
		if g := s.Glyphs[c.Text.ID]; g != nil {
			if g.Source == 990 {
				sidebar = true
			}
			groups[drawGroup{g.ID, at%640 - int(c.Text.Local)%g.Width, at/640 - int(c.Text.Local)/g.Width}] = true
		}
	}
	var materials, actors map[uint16]*graphicMaterial
	if art != nil {
		materials, actors = art.Materials, art.Actors
	}
	valid := func(c graphicCell, tiles map[uint16]*graphicMaterial) *graphicMaterial {
		m := tiles[c.ID]
		if m == nil || c.Local >= uint32(m.NativeWidth*m.NativeHeight) {
			return nil
		}
		return m
	}
	baseColor := func(c ownedPixel, x, y int) [3]uint8 {
		color := canonicalEGA[c.Color&15]
		if c.Effect.ID != 0 {
			color = canonicalEGA[c.EffectBase&15]
		}
		if palette != nil && sidebar {
			if next, ok := palette.backdrop(c.Color&15, x, y, c.Text, s.Glyphs[c.Text.ID], true); ok {
				color = next
			}
		}
		return color
	}
	last := map[ownedRenderKey]int{}
	// Resolve replacement textures before generating any native RGB fill.
	for y := 0; y < 200; y++ {
		for x := 0; x < 640; {
			c := visible[y*640+x]
			m := valid(c.Material, materials)
			run := 1
			if m != nil {
				sx, sy := int(c.Material.Local)%m.NativeWidth, int(c.Material.Local)/m.NativeWidth
				for x+run < 640 && sx+run < m.NativeWidth {
					next := visible[y*640+x+run].Material
					if next.ID != c.Material.ID || next.Local != c.Material.Local+uint32(run) {
						break
					}
					run++
				}
				b.append(ownedRenderOp{Texture: m.Tile, Destination: image.Rect(x*3, y*6, (x+run)*3, (y+1)*6), Source: image.Pt(sx*3, sy*6)}, 0, last)
				b.Stats.TextureCopyPixels += run * 18
			} else {
				color := baseColor(c, x, y)
				for x+run < 640 {
					next := visible[y*640+x+run]
					if valid(next.Material, materials) != nil || baseColor(next, x+run, y) != color {
						break
					}
					run++
				}
				b.append(ownedRenderOp{Destination: image.Rect(x*3, y*6, (x+run)*3, (y+1)*6), Color: color}, 0, last)
				b.Stats.NativeRGBPixels += run * 18
			}
			x += run
		}
	}
	for layer := 1; layer <= 2; layer++ {
		for y := 0; y < 200; y++ {
			for x := 0; x < 640; {
				c := visible[y*640+x]
				cell := c.Actor
				var texture *image.RGBA
				width, height := 0, 0
				if layer == 1 {
					if m := valid(cell, actors); m != nil {
						texture, width, height = m.Tile, m.NativeWidth, m.NativeHeight
					}
				} else {
					cell = c.Effect
					texture = s.Effects[cell.ID]
					if texture != nil {
						width, height = texture.Bounds().Dx()/3, texture.Bounds().Dy()/6
					}
				}
				if texture == nil || width == 0 || cell.Local >= uint32(width*height) {
					x++
					continue
				}
				sx, sy := int(cell.Local)%width, int(cell.Local)/width
				run := 1
				for x+run < 640 && sx+run < width {
					next := visible[y*640+x+run].Actor
					if layer == 2 {
						next = visible[y*640+x+run].Effect
					}
					if next.ID != cell.ID || next.Local != cell.Local+uint32(run) {
						break
					}
					run++
				}
				b.append(ownedRenderOp{Texture: texture, Destination: image.Rect(x*3, y*6, (x+run)*3, (y+1)*6), Source: image.Pt(sx*3, sy*6), Blend: true}, layer, last)
				b.Stats.BlendedPixels += run * 18
				x += run
			}
		}
	}
	for _, op := range b.Operations {
		if op.Texture == nil {
			b.Stats.FillRectangles++
		} else if op.Blend {
			b.Stats.BlendRectangles++
		} else {
			b.Stats.CopyRectangles++
		}
	}
	if b.Stats.NativeRGBPixels+b.Stats.TextureCopyPixels != 1920*1200 {
		panic("owned batch base coverage")
	}
	return b, groups
}

func renderOwnedScene(s *ownedScene, fonts *Assets, art *GraphicsAssets, palette *presentationPalette) *image.RGBA {
	out, _ := renderOwnedSceneBatch(s, fonts, art, palette)
	return out
}

func renderOwnedSceneBatch(s *ownedScene, fonts *Assets, art *GraphicsAssets, palette *presentationPalette) (*image.RGBA, ownedRenderStats) {
	b, groups := prepareOwnedBatch(s, art, palette)
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	if err := submitOwnedBatch(out, &b); err != nil {
		panic(err)
	}
	for _, k := range sortedGroups(groups) {
		g := s.Glyphs[k.ID]
		fg, ok := fonts.Glyphs[g.Rune]
		if !ok || g.Rune == ' ' {
			continue
		}
		iw, ih := fg.Ink[2], fg.Ink[3]
		dw, dh := min(iw, g.Width*3), min(ih, 90)
		if dw <= 0 || dh <= 0 {
			continue
		}
		left, top := k.X*3+(g.Width*3-dw)/2, k.Y*6+(90-dh)/2
		color := canonicalEGA[g.FG]
		if g.FG == 14 {
			color = [3]uint8{255, 241, 181}
		}
		color = palette.ink(g.FG, color)
		for yy := 0; yy < dh; yy++ {
			for xx := 0; xx < dw; xx++ {
				ox, oy := left+xx, top+yy
				if ox < 0 || ox >= 1920 || oy < 0 || oy >= 1200 {
					continue
				}
				c := s.Pixels[s.Start+(oy/6)*640+ox/3].Text
				if c.ID != g.ID || int(c.Local)%g.Width != ox/3-k.X || int(c.Local)/g.Width != oy/6-k.Y {
					continue
				}
				_, _, _, alpha := fonts.Atlas.At(fg.Ink[0]+xx*iw/dw, fg.Ink[1]+yy*ih/dh).RGBA()
				a := uint32(alpha >> 8)
				at := oy*out.Stride + ox*4
				for ch := 0; ch < 3; ch++ {
					out.Pix[at+ch] = uint8((uint32(color[ch])*a + uint32(out.Pix[at+ch])*(255-a) + 127) / 255)
				}
			}
		}
	}
	return out, b.Stats
}

// Full old/new RGB comparison is diagnostic only, outside the presented Frame.
func (p *ownedProbe) auditOwnedRenderer(kind string) {
	t := p.e.Tracker
	reference := renderOwnedSceneReference(p.scene, t.assets, p.graphicsAssets(), t.palette)
	batch, stats := renderOwnedSceneBatch(p.scene, t.assets, p.graphicsAssets(), t.palette)
	if !bytes.Equal(reference.Pix, batch.Pix) {
		panic("batched source renderer differs from frozen reference: " + kind)
	}
	var oldTimes, newTimes []int64
	if os.Getenv("EIGHTSWORD_RESEARCH_RENDER_BENCH") == "1" {
		for i := 0; i < 3; i++ {
			old := func() {
				start := time.Now()
				reference = renderOwnedSceneReference(p.scene, t.assets, p.graphicsAssets(), t.palette)
				oldTimes = append(oldTimes, time.Since(start).Nanoseconds())
			}
			modern := func() {
				start := time.Now()
				batch, _ = renderOwnedSceneBatch(p.scene, t.assets, p.graphicsAssets(), t.palette)
				newTimes = append(newTimes, time.Since(start).Nanoseconds())
			}
			if i%2 == 0 {
				old()
				modern()
			} else {
				modern()
				old()
			}
			if !bytes.Equal(reference.Pix, batch.Pix) {
				panic("render benchmark changed pixels")
			}
		}
	}
	row := map[string]any{"kind": kind, "step": p.e.Oracle.Steps(), "font": p.e.FontID(), "same_pixels": true, "reference_rgba_sha256": hash(reference.Pix), "batch_rgba_sha256": hash(batch.Pix), "batch": stats, "reference_ns": oldTimes, "batch_ns": newTimes, "scope": "CPU source-scene render including packet construction and glyphs; not game FPS"}
	f, err := os.OpenFile(filepath.Join(p.out, "render-batch-audit.jsonl"), os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		panic(err)
	}
	if err = json.NewEncoder(f).Encode(row); err != nil {
		f.Close()
		panic(err)
	}
	if err = f.Close(); err != nil {
		panic(err)
	}
}
