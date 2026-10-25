package eightsword

import "image"

func renderOwnedSceneReference(s *ownedScene, fonts *Assets, art *GraphicsAssets, palette *presentationPalette) *image.RGBA {
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	groups := map[drawGroup]bool{}
	sidebar := false
	for _, c := range s.Pixels[s.Start : s.Start+16000*8] {
		if g := s.Glyphs[c.Text.ID]; g != nil && g.Source == 990 {
			sidebar = true
			break
		}
	}
	for y := 0; y < 200; y++ {
		for x := 0; x < 640; x++ {
			c := s.Pixels[s.Start+y*640+x]
			color := canonicalEGA[c.Color&15]
			if c.Effect.ID != 0 {
				color = canonicalEGA[c.EffectBase&15]
			}
			if palette != nil && sidebar {
				if next, ok := palette.backdrop(c.Color&15, x, y, c.Text, s.Glyphs[c.Text.ID], true); ok {
					color = next
				}
			}
			for dy := 0; dy < 6; dy++ {
				for dx := 0; dx < 3; dx++ {
					at := (y*6+dy)*out.Stride + (x*3+dx)*4
					copy(out.Pix[at:at+3], color[:])
					out.Pix[at+3] = 255
					if art != nil {
						for _, layer := range []struct {
							c     graphicCell
							tiles map[uint16]*graphicMaterial
							blend bool
						}{{c.Material, art.Materials, false}, {c.Actor, art.Actors, true}} {
							m := layer.tiles[layer.c.ID]
							if m == nil || layer.c.Local >= uint32(m.NativeWidth*m.NativeHeight) {
								continue
							}
							sx, sy := int(layer.c.Local)%m.NativeWidth, int(layer.c.Local)/m.NativeWidth
							src := (sy*6+dy)*m.Tile.Stride + (sx*3+dx)*4
							if !layer.blend {
								copy(out.Pix[at:at+4], m.Tile.Pix[src:src+4])
								continue
							}
							a := uint32(m.Tile.Pix[src+3])
							for ch := 0; ch < 3; ch++ {
								out.Pix[at+ch] = uint8(min(255, uint32(m.Tile.Pix[src+ch])+(uint32(out.Pix[at+ch])*(255-a)+127)/255))
							}
						}
					}
					if fx := s.Effects[c.Effect.ID]; fx != nil {
						sx, sy := int(c.Effect.Local)%88, int(c.Effect.Local)/88
						src := (sy*6+dy)*fx.Stride + (sx*3+dx)*4
						a := uint32(fx.Pix[src+3])
						for ch := 0; ch < 3; ch++ {
							out.Pix[at+ch] = uint8(min(255, uint32(fx.Pix[src+ch])+(uint32(out.Pix[at+ch])*(255-a)+127)/255))
						}
					}
				}
			}
			if g := s.Glyphs[c.Text.ID]; g != nil {
				groups[drawGroup{g.ID, x - int(c.Text.Local)%g.Width, y - int(c.Text.Local)/g.Width}] = true
			}
		}
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
	return out
}
