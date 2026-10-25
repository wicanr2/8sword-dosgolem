//go:build ignore

// Spec 047 DRAFT. Copy into a disposable eightsword package for research only.
// The renderer below has no Oracle, framebuffer, or VGA ownership input.
package eightsword

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"

	"github.com/wicanr2/dosgolem/oracle"
)

type ownedPixel struct {
	Color           uint8
	Material, Actor graphicCell
	Effect          graphicCell
	EffectBase      uint8
	Text            cell
}
type ownedScene struct {
	Pixels   []ownedPixel
	Glyphs   map[uint32]*glyph
	Next     uint32
	Revision uint64
	Start    int
	Effects  map[uint16]*image.RGBA
}
type ownedWriter struct {
	Count     uint64
	FirstStep uint64
	Offset    uint32
	Mode      uint8
	Registers any
	Stack     []uint16
}
type ownedProbe struct {
	e            *Engine
	scene        *ownedScene
	bound        bool
	commands     *json.Encoder
	file         *os.File
	counts       map[string]uint64
	writers      map[string]*ownedWriter
	active       int
	cached       *image.RGBA
	revision     uint64
	fontID       string
	stringActive bool
	stringSP     uint16
	stringGlyphs []func()
	out          string
	captures     map[string]bool
	unsubscribe  func()
}

// Pure scene rendering. Source-command adaptation is kept below this function.
func renderOwnedScene(s *ownedScene, fonts *Assets, art *GraphicsAssets, palette *presentationPalette) *image.RGBA {
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

func (e *Engine) ResearchOwnedScene(out string) (func(), func() *image.RGBA, func() error) {
	f, err := os.Create(filepath.Join(out, "owned-commands.jsonl"))
	if err != nil {
		panic(err)
	}
	p := &ownedProbe{e: e, scene: &ownedScene{Pixels: make([]ownedPixel, 65536*8), Glyphs: map[uint32]*glyph{}, Effects: map[uint16]*image.RGBA{}}, commands: json.NewEncoder(f), file: f, counts: map[string]uint64{}, writers: map[string]*ownedWriter{}, out: out, captures: map[string]bool{}}
	install := func() { p.bind() }
	frame := func() *image.RGBA {
		if !p.bound {
			return nil
		}
		if p.cached == nil || p.revision != p.scene.Revision || p.fontID != e.FontID() {
			p.cached = renderOwnedScene(p.scene, e.Tracker.assets, e.Tracker.graphics.assets, e.Tracker.palette)
			p.revision = p.scene.Revision
			p.fontID = e.FontID()
		}
		return p.cached
	}
	finish := func() error {
		if p.unsubscribe != nil {
			p.unsubscribe()
		}
		d := map[string]any{"schema": "8sword-owned-live-prototype-r1", "commands": p.counts, "writers": p.writers, "active_at_end": p.active, "scene_revision": p.scene.Revision, "renderer_inputs": []string{"owned scene", "source decoded bitmaps", "validated HD art", "font atlas", "approved palette"}, "renderer_reads_vga": false, "production": false, "known_gap": "unknown raster primitives and effect accumulation are evidence gaps; no framebuffer fallback inside scene"}
		raw, err := json.MarshalIndent(d, "", "  ")
		if err != nil {
			return err
		}
		if err = os.WriteFile(filepath.Join(out, "owned-receipt.json"), append(raw, 10), 0644); err != nil {
			return err
		}
		return f.Close()
	}
	return install, frame, finish
}
func (p *ownedProbe) record(kind string, values map[string]any) {
	p.counts[kind]++
	values["command"] = kind
	values["step"] = p.e.Oracle.Steps()
	if err := p.commands.Encode(values); err != nil {
		panic(err)
	}
}
func (p *ownedProbe) bind() {
	t := p.e.Tracker
	if p.bound || t == nil || t.loadSegment == 0 || t.graphics == nil {
		return
	}
	p.bound = true
	o := p.e.Oracle
	seg := t.stringSeg
	for _, site := range []struct {
		seg, entry, ret uint16
		base            int
	}{{seg, 0x274, 0x322, 0x15090}, {seg, 0x19c, 0x1a9, 0x15090}, {seg, 0xae3, 0xb41, 0x15090}, {seg, 0xd3e, 0xd74, 0x15090}, {seg, 0x33d, 0x371, 0x15090}, {seg, 0x3b0, 0x3e4, 0x15090}, {seg, 0x4f2, 0x625, 0x15090}, {seg, 0x626, 0x76e, 0x15090}, {seg, 0x76f, 0x854, 0x15090}, {seg, 0x99c, 0xa6f, 0x15090}, {seg, 0x423, 0x4f1, 0x15090}, {seg, 0xb86, 0xc85, 0x15090}, {t.fontSeg, 0x4a98, 0x4bf7, 0xadf0}} {
		if !bytes.Equal(o.Bytes(oracle.Addr{Seg: site.seg, Off: site.entry}, 16), t.pam[site.base+int(site.entry):site.base+int(site.entry)+16]) || o.Byte(oracle.Addr{Seg: site.seg, Off: site.ret}) != 0xcb {
			panic("owned primitive ABI differs")
		}
	}
	var page uint16
	o.OnCall(oracle.Addr{Seg: seg, Off: 0x19c}, func(*oracle.Oracle) { page = o.Arg(0) & 255 })
	o.OnCall(oracle.Addr{Seg: seg, Off: 0x1a9}, func(*oracle.Oracle) {
		if page > 3 {
			panic("owned page out of range")
		}
		p.scene.Start = int(page) * 0x4000 * 8
		p.scene.Revision++
		p.record("select-page", map[string]any{"page": page})
	})
	o.OnCall(oracle.Addr{Seg: seg, Off: 0xae3}, func(*oracle.Oracle) {
		if p.stringActive && p.stringSP == o.Regs().SP {
			return
		}
		if p.stringActive {
			panic("owned string reentry")
		}
		p.stringActive = true
		p.stringSP = o.Regs().SP
		p.stringGlyphs = nil
		p.active++
	})
	o.OnCall(oracle.Addr{Seg: seg, Off: 0xb41}, func(*oracle.Oracle) {
		if !p.stringActive {
			return
		}
		for _, apply := range p.stringGlyphs {
			apply()
		}
		p.record("string", map[string]any{"glyphs": len(p.stringGlyphs)})
		p.stringGlyphs = nil
		p.stringActive = false
		p.active--
	})
	var clearApply func()
	o.OnCall(oracle.Addr{Seg: seg, Off: 0xd3e}, func(*oracle.Oracle) {
		ds := o.Regs().DS
		dest := o.Word(oracle.Addr{Seg: ds, Off: 0x748a})
		mode := o.Word(oracle.Addr{Seg: ds, Off: 0x7484})
		mask := o.Byte(oracle.Addr{Seg: ds, Off: 0x748c})
		if (dest != 0xa000 && dest != 0xa400) || mode != 1 {
			p.counts["rejected-clear"]++
			return
		}
		first := int(dest-0xa000) * 16 * 8
		if clearApply != nil {
			return
		}
		p.active++
		clearApply = func() {
			for i := first; i < first+0x4000*8; i++ {
				p.scene.Pixels[i] = ownedPixel{Color: p.scene.Pixels[i].Color & ^mask}
			}
			p.scene.Revision++
			p.record("clear-page", map[string]any{"dest": dest, "plane_mask": mask})
		}
	})
	o.OnCall(oracle.Addr{Seg: seg, Off: 0xd74}, func(*oracle.Oracle) {
		if clearApply != nil {
			clearApply()
			clearApply = nil
			p.active--
		}
	})
	var plotApply func()
	o.OnCall(oracle.Addr{Seg: seg, Off: 0x274}, func(*oracle.Oracle) {
		if plotApply != nil {
			return
		}
		ds := o.Regs().DS
		x, y := int(o.Arg(0)), int(o.Arg(1))
		dest := o.Word(oracle.Addr{Seg: ds, Off: 0x748a})
		mode := o.Word(oracle.Addr{Seg: ds, Off: 0x7484})
		fg := o.Byte(oracle.Addr{Seg: ds, Off: 0x748c})
		if x >= 640 || y >= 200 || (dest != 0xa000 && dest != 0xa400) || mode != 1 || fg > 15 {
			p.counts["rejected-plot"]++
			return
		}
		at := int(dest-0xa000)*16*8 + y*640 + x
		p.active++
		plotApply = func() {
			p.scene.Pixels[at] = ownedPixel{Color: fg}
			p.scene.Revision++
			p.counts["plot"]++
			if p.counts["plot"] <= 32 {
				p.record("plot-sample", map[string]any{"x": x, "y": y, "dest": dest, "fg": fg})
			}
		}
	})
	o.OnCall(oracle.Addr{Seg: seg, Off: 0x322}, func(*oracle.Oracle) {
		if plotApply != nil {
			plotApply()
			plotApply = nil
			p.active--
		}
	})
	// Video writes are diagnostic counts only. None are scene render inputs.
	p.unsubscribe = p.e.ObservePresentation(PresentationObserver{Write: func(w PresentationWrite) {
		if p.active == 0 {
			p.counts["writes-outside-command"]++
		}
		k := fmt.Sprintf("%04x:%04x", w.CS, w.IP)
		v := p.writers[k]
		if v == nil {
			r := o.Regs()
			stack := []uint16{}
			for i := 0; i < 12; i++ {
				stack = append(stack, o.Word(oracle.Addr{Seg: r.SS, Off: r.SP + uint16(i*2)}))
			}
			v = &ownedWriter{FirstStep: w.Step, Offset: w.Offset, Mode: w.WriteMode, Registers: r, Stack: stack}
			p.writers[k] = v
		}
		v.Count++
	}})
	for _, c := range []struct {
		entry, ret uint16
		kind       int
	}{{0x4f2, 0x625, 6}, {0x626, 0x76e, 6}, {0x76f, 0x854, 5}, {0x99c, 0xa6f, 4}, {0x423, 0x4f1, 0}} {
		c := c
		if o.Byte(oracle.Addr{Seg: seg, Off: c.ret}) != 0xcb {
			panic("owned bitmap return bytes differ")
		}
		var apply func()
		var sp uint16
		o.OnCall(oracle.Addr{Seg: seg, Off: c.entry}, func(o *oracle.Oracle) {
			if apply != nil && sp == o.Regs().SP {
				return
			}
			if apply != nil {
				panic("owned bitmap reentry")
			}
			sp = o.Regs().SP
			ptr := oracle.Addr{Seg: o.Arg(1), Off: o.Arg(0)}
			if !bitmapSourceInRAM(ptr, 4) {
				p.counts["rejected-bitmap"]++
				return
			}
			head := o.Bytes(ptr, 4)
			w, h := int(binary.LittleEndian.Uint16(head)), int(binary.LittleEndian.Uint16(head[2:]))
			x, y := int(o.Arg(2)), int(o.Arg(3))
			ds := o.Regs().DS
			dest := o.Word(oracle.Addr{Seg: ds, Off: 0x748a})
			mode := o.Word(oracle.Addr{Seg: ds, Off: 0x7484})
			if w < 1 || w > 80 || h < 1 || h > 200 || x+w > 80 || y+h > 200 || (dest != 0xa000 && dest != 0xa400) || mode != 1 || !bitmapSourceInRAM(ptr, 4+w*h*c.kind) {
				p.counts["rejected-bitmap"]++
				return
			}
			raw := o.Bytes(ptr, 4+w*h*c.kind)
			first := int(dest-0xa000)*16*8 + y*640 + x*8
			for row := 0; row < h; row++ {
				if o.Word(oracle.Addr{Seg: seg, Off: uint16(6 + (y+row)*2)}) != uint16((y+row)*80) {
					panic("owned bitmap pitch")
				}
			}
			id, actor := uint16(0), uint16(0)
			if c.kind > 0 {
				id = t.graphics.assets.ByNative[hash(raw[:4+w*h*4])]
				if c.entry == 0x626 {
					if id == 85 {
						id = 107
					}
					if id == 150 {
						id = 152
					}
				}
				if t.graphics.assets.ActorSHA[id] == hash(raw) {
					actor = id
				}
			}
			// Reuse the existing validated eligibility contract, using our scene.
			if actor != 0 {
				background := c.entry == 0x626
				known := true
				base := first
				if background {
					base += 0x4000 * 8
				}
				for row := 0; row < h && known; row++ {
					for col := 0; col < w*8; col++ {
						v := p.scene.Pixels[base+row*640+col].Material
						m := t.graphics.assets.Materials[v.ID]
						if m == nil || v.Local >= uint32(m.NativeWidth*m.NativeHeight) {
							known = false
							break
						}
					}
				}
				if !known || background != t.graphics.assets.BattleActors[actor] {
					actor = 0
				}
			}
			effect := uint16(0)
			if c.entry == 0x4f2 && w == 11 && h == 50 && dest == 0xa000 && t.graphics.assets.EffectSHA[id] == hash(raw) && t.graphics.assets.Effects[id] != nil {
				valid := true
				for row := 0; row < h && valid; row++ {
					for col := 0; col < w*8; col++ {
						v := p.scene.Pixels[first+row*640+col]
						if v.Text.ID != 0 || (isChoiSource(id) && v.Effect.ID != 0) || t.graphics.assets.Materials[v.Material.ID] == nil {
							valid = false
							break
						}
					}
				}
				if valid {
					effect = id
				}
			}
			entryStep := o.Steps()
			p.active++
			apply = func() {
				area := w * h
				fxID := uint16(0)
				if effect != 0 {
					fxID = p.effectFrame(first, t.graphics.assets.Effects[effect].Tile)
				}
				for row := 0; row < h; row++ {
					for col := 0; col < w*8; col++ {
						at := first + row*640 + col
						local := row*w*8 + col
						if c.kind == 0 || c.entry == 0x626 {
							p.scene.Pixels[at] = p.scene.Pixels[at+0x4000*8]
						}
						if c.kind == 0 {
							continue
						}
						pix := &p.scene.Pixels[at]
						bit := uint(7 - local%8)
						mask := c.kind != 6 || (raw[4+5*area+local/8]>>bit)&1 != 0
						if fxID != 0 {
							base := pix.Color
							if pix.Effect.ID != 0 {
								base = pix.EffectBase
							}
							pix.Effect = graphicCell{fxID, uint32(local)}
							pix.EffectBase = base
						} else if mask {
							pix.Effect = graphicCell{}
						}
						if fxID == 0 {
							if actor != 0 {
								pix.Actor = graphicCell{actor, uint32(local)}
							} else if mask {
								pix.Actor = graphicCell{}
							}
						}
						if !mask {
							continue
						}
						color := uint8(0)
						for plane := 0; plane < 4; plane++ {
							color |= ((raw[4+plane*area+local/8] >> bit) & 1) << uint(plane)
						}
						pix.Color = color
						pix.Text = cell{}
						if actor == 0 && fxID == 0 {
							pix.Material = graphicCell{id, uint32(local)}
						}
					}
				}
				p.scene.Revision++
				p.record("bitmap", map[string]any{"entry": c.entry, "entry_step": entryStep, "width_bytes": w, "height": h, "x_byte": x, "y": y, "dest": dest, "source_sha256": hash(raw), "material": id, "actor": actor, "effect": effect})
				if int(dest-0xa000)*16*8 == p.scene.Start {
					kind := ""
					if actor == 150 {
						kind = "army-complete"
					}
					if actor >= 152 && actor <= 155 {
						kind = "battle-actor-complete"
					}
					if effect != 0 {
						kind = "battle-effect-complete"
					}
					if kind != "" {
						p.capture(kind)
					}
				}
			}
		})
		o.OnCall(oracle.Addr{Seg: seg, Off: c.ret}, func(*oracle.Oracle) {
			if apply != nil {
				apply()
				apply = nil
				p.active--
			}
		})
	}
	for _, c := range []struct {
		entry, ret uint16
		to, from   int
	}{{0x33d, 0x371, 0x4000 * 8, 0}, {0x3b0, 0x3e4, 0, 0x4000 * 8}} {
		c := c
		pending := false
		o.OnCall(oracle.Addr{Seg: seg, Off: c.entry}, func(*oracle.Oracle) {
			if !pending {
				pending = true
				p.active++
			}
		})
		o.OnCall(oracle.Addr{Seg: seg, Off: c.ret}, func(*oracle.Oracle) {
			if pending {
				copy(p.scene.Pixels[c.to:c.to+16000*8], p.scene.Pixels[c.from:c.from+16000*8])
				p.scene.Revision++
				p.record("page-copy", map[string]any{"entry": c.entry, "from": c.from, "to": c.to, "bytes": 16000})
				pending = false
				p.active--
			}
		})
	}
	for _, c := range []struct {
		seg, entry, ret uint16
		full            bool
	}{{t.fontSeg, 0x4a98, 0x4bf7, true}, {seg, 0xb86, 0xc85, false}} {
		c := c
		var pending *glyph
		var sp uint16
		o.OnCall(oracle.Addr{Seg: c.seg, Off: c.entry}, func(*oracle.Oracle) {
			if pending != nil && sp == o.Regs().SP {
				return
			}
			if pending != nil {
				panic("owned glyph reentry")
			}
			sp = o.Regs().SP
			g := t.active
			if g == nil {
				return
			}
			cp := glyph{Rune: g.Rune, Source: g.Source, Width: g.Width, FG: g.FG, BG: g.BG, Rows: g.Rows}
			pending = &cp
			p.active++
		})
		o.OnCall(oracle.Addr{Seg: c.seg, Off: c.ret}, func(*oracle.Oracle) {
			if pending == nil {
				return
			}
			g := pending
			apply := func() {
				p.scene.Next++
				g.ID = p.scene.Next
				p.scene.Glyphs[g.ID] = g
				for y := 0; y < 15; y++ {
					for x := 0; x < g.Width; x++ {
						at := int(g.Rows[y])*8 + x
						if at >= len(p.scene.Pixels) {
							panic("owned glyph bounds")
						}
						v := &p.scene.Pixels[at]
						v.Effect = graphicCell{}
						if g.BG != 255 {
							v.Color = g.BG
							v.Material = graphicCell{}
							v.Actor = graphicCell{}
						}
						v.Text = cell{ID: g.ID, Local: uint16(y*g.Width + x)}
					}
				}
				p.scene.Revision++
				p.record("glyph", map[string]any{"rune": string(g.Rune), "source": g.Source, "rows": g.Rows, "width": g.Width, "fg": g.FG, "bg": g.BG})
			}
			if p.stringActive {
				p.stringGlyphs = append(p.stringGlyphs, apply)
			} else {
				apply()
			}
			pending = nil
			p.active--
		})
	}
}

func (p *ownedProbe) effectFrame(first int, source *image.RGBA) uint16 {
	used := map[uint16]bool{}
	for _, v := range p.scene.Pixels {
		used[v.Effect.ID] = true
	}
	id := uint16(0)
	for n := uint16(1); n <= 64; n++ {
		if !used[n] {
			id = n
			break
		}
	}
	if id == 0 {
		p.counts["effect-slot-rejected"]++
		return 0
	}
	for n := range p.scene.Effects {
		if !used[n] {
			delete(p.scene.Effects, n)
		}
	}
	f := image.NewRGBA(image.Rect(0, 0, 264, 300))
	for y := 0; y < 50; y++ {
		for x := 0; x < 88; x++ {
			c := p.scene.Pixels[first+y*640+x].Effect
			prior := p.scene.Effects[c.ID]
			if prior == nil {
				continue
			}
			sx, sy := int(c.Local)%88, int(c.Local)/88
			for dy := 0; dy < 6; dy++ {
				dst, src := (y*6+dy)*f.Stride+x*12, (sy*6+dy)*prior.Stride+sx*12
				copy(f.Pix[dst:dst+12], prior.Pix[src:src+12])
			}
		}
	}
	for at := 0; at < len(f.Pix); at += 4 {
		a := uint32(source.Pix[at+3])
		for c := 0; c < 4; c++ {
			f.Pix[at+c] = uint8(min(255, uint32(source.Pix[at+c])+(uint32(f.Pix[at+c])*(255-a)+127)/255))
		}
	}
	p.scene.Effects[id] = f
	return id
}

func (p *ownedProbe) capture(kind string) {
	if p.captures[kind] {
		return
	}
	p.captures[kind] = true
	own := renderOwnedScene(p.scene, p.e.Tracker.assets, p.e.Tracker.graphics.assets, p.e.Tracker.palette)
	legacy := p.e.Tracker.Compose()
	diff := 0
	for at := 0; at < len(own.Pix); at += 4 {
		if !bytes.Equal(own.Pix[at:at+4], legacy.Pix[at:at+4]) {
			diff++
		}
	}
	for suffix, im := range map[string]*image.RGBA{"owned": own, "legacy": legacy} {
		f, err := os.Create(filepath.Join(p.out, kind+"-"+suffix+".png"))
		if err != nil {
			panic(err)
		}
		if err = png.Encode(f, im); err != nil {
			panic(err)
		}
		if err = f.Close(); err != nil {
			panic(err)
		}
	}
	p.record("completed-capture", map[string]any{"kind": kind, "different_pixels": diff, "rgba_sha256": hash(own.Pix), "legacy_rgba_sha256": hash(legacy.Pix), "page_start_pixels": p.scene.Start})
}
