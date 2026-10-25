//go:build ignore

// Spec 047 DRAFT. Copy into the disposable research package only.
package eightsword

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"os"
	"path/filepath"

	"github.com/wicanr2/dosgolem/oracle"
)

type ownedIntroGlyph struct {
	ID          uint32
	Rune        rune
	X, Y, Width int
	FG          byte
}

type ownedIntroPage struct {
	Kind   string
	Museum *museumPage
}
type ownedIntroScene struct {
	Native, Backing []byte
	Owners          []uint32
	Glyphs          map[uint32]ownedIntroGlyph
	Pages           map[int]ownedIntroPage
	Reveal          []bool
	Mode            byte
	Start           int
	Palette         [256][3]uint8
	Revision        uint64
	Next            uint32
	Prelude         bool
}
type ownedIntroArt struct {
	Font                                                                    *Assets
	PublisherInk, PublisherErase, IconArt, IconErase, Title, Story, Prelude image.Image
	MuseumArt                                                               *image.RGBA
	MuseumScenes                                                            map[string]*image.NRGBA
}

func newOwnedIntroScene(mode byte) *ownedIntroScene {
	return &ownedIntroScene{Native: make([]byte, 65536*8), Backing: make([]byte, 65536*8), Owners: make([]uint32, 65536*8),
		Glyphs: map[uint32]ownedIntroGlyph{}, Pages: map[int]ownedIntroPage{}, Reveal: make([]bool, 64000), Mode: mode}
}
func cloneOwnedIntroScene(s *ownedIntroScene) *ownedIntroScene {
	c := *s
	c.Native = append([]byte(nil), s.Native...)
	c.Backing = append([]byte(nil), s.Backing...)
	c.Owners = append([]uint32(nil), s.Owners...)
	c.Reveal = append([]bool(nil), s.Reveal...)
	c.Glyphs = map[uint32]ownedIntroGlyph{}
	c.Pages = map[int]ownedIntroPage{}
	for k, v := range s.Glyphs {
		c.Glyphs[k] = v
	}
	for k, v := range s.Pages {
		if v.Museum != nil {
			m := *v.Museum
			m.scene = cloneMuseumScene(v.Museum.scene)
			m.ink = image.NewRGBA(v.Museum.ink.Bounds())
			copy(m.ink.Pix, v.Museum.ink.Pix)
			v.Museum = &m
		}
		c.Pages[k] = v
	}
	return &c
}

// This renderer accepts our source-derived state and immutable art only.
func renderOwnedIntro(s *ownedIntroScene, a ownedIntroArt, hd bool) *image.RGBA {
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	width, scale := 640, 3
	if s.Mode == 0x13 {
		width, scale = 320, 6
	}
	for y := 0; y < 200; y++ {
		for x := 0; x < width; x++ {
			at := s.Start + y*width + x
			index := s.Native[at]
			if hd && s.Mode == 0xe && s.Owners[at] != 0 {
				if g, ok := s.Glyphs[s.Owners[at]]; ok && g.Rune != 0 && a.Font != nil {
					if _, known := a.Font.Glyphs[g.Rune]; known {
						index = s.Backing[at]
					}
				}
			}
			c := s.Palette[index]
			for dy := 0; dy < 6; dy++ {
				for dx := 0; dx < scale; dx++ {
					n := (y*6+dy)*out.Stride + (x*scale+dx)*4
					copy(out.Pix[n:n+3], c[:])
					out.Pix[n+3] = 255
				}
			}
		}
	}
	if !hd {
		return out
	}
	if s.Prelude && a.Prelude != nil {
		for pos, revealed := range s.Reveal {
			if !revealed {
				continue
			}
			x, y := pos%320, pos/320
			r := image.Rect(x*6, y*6, (x+1)*6, (y+1)*6)
			draw.Draw(out, r, a.Prelude, r.Min, draw.Src)
		}
		return out
	}
	p := s.Pages[s.Start]
	switch p.Kind {
	case "publisher":
		if a.PublisherErase != nil {
			draw.DrawMask(out, out.Bounds(), image.Black, image.Point{}, a.PublisherErase, image.Point{}, draw.Over)
		}
		if a.IconErase != nil {
			draw.DrawMask(out, out.Bounds(), image.Black, image.Point{}, a.IconErase, image.Point{}, draw.Over)
		}
		if a.IconArt != nil {
			draw.Draw(out, out.Bounds(), a.IconArt, image.Point{}, draw.Over)
		}
		if a.PublisherInk != nil {
			draw.Draw(out, out.Bounds(), a.PublisherInk, image.Point{}, draw.Over)
		}
	case "title":
		if a.Title != nil {
			r := image.Rect(48, 300, 1824, 870)
			draw.Draw(out, r, image.Black, image.Point{}, draw.Src)
			draw.Draw(out, r, a.Title, image.Point{}, draw.Over)
		}
	case "story":
		if a.Story != nil {
			draw.Draw(out, out.Bounds(), a.Story, a.Story.Bounds().Min, draw.Src)
		}
	case "museum":
		if p.Museum != nil && a.MuseumArt != nil {
			painter := &IntroMuseum{art: a.MuseumArt, sceneArts: a.MuseumScenes}
			copy(painter.palette[:], s.Palette[:16])
			band := painter.renderBand(p.Museum)
			draw.Draw(out, image.Rect(0, 120, 1920, 900), band, image.Point{}, draw.Over)
		}

	}
	if s.Mode != 0xe || a.Font == nil {
		return out
	}
	seen := map[uint32]bool{}
	for _, id := range s.Owners[s.Start : s.Start+128000] {
		if id != 0 {
			seen[id] = true
		}
	}
	for id := range seen {
		g := s.Glyphs[id]
		if g.Rune == 0 {
			continue
		}
		r := image.Rect(g.X*3, g.Y*6, (g.X+g.Width)*3, (g.Y+15)*6)

		c := s.Palette[g.FG]
		if p.Kind == "story" {
			c = [3]uint8{245, 207, 113}
		}
		fg, ok := a.Font.Glyphs[g.Rune]
		if !ok || g.Rune == ' ' {
			continue
		}
		iw, ih := fg.Ink[2], fg.Ink[3]
		if iw <= 0 || ih <= 0 {
			continue
		}
		dw, dh := min(iw, r.Dx()), min(ih, r.Dy())
		left, top := r.Min.X+(r.Dx()-dw)/2, r.Min.Y+(r.Dy()-dh)/2
		for y := 0; y < dh; y++ {
			for x := 0; x < dw; x++ {
				ox, oy := left+x, top+y
				if ox < 0 || ox >= 1920 || oy < 0 || oy >= 1200 || s.Owners[s.Start+(oy/6)*640+ox/3] != id {
					continue
				}
				_, _, _, alpha := a.Font.Atlas.At(fg.Ink[0]+x*iw/dw, fg.Ink[1]+y*ih/dh).RGBA()
				v := uint32(alpha >> 8)
				at := oy*out.Stride + ox*4
				for ch := 0; ch < 3; ch++ {
					out.Pix[at+ch] = uint8((uint32(c[ch])*v + uint32(out.Pix[at+ch])*(255-v) + 127) / 255)
				}
			}
		}

	}
	return out
}

type ownedIntroProbe struct {
	e                       *Engine
	scene, held             *ownedIntroScene
	bound, retired, started bool
	active                  int
	file                    *os.File
	log                     *json.Encoder
	counts                  map[string]uint64
	errors                  []string
	unsubscribe             func()
	source                  []byte
	order                   []uint32
	written                 int
	out                     string
	captures                map[string]bool
	lastNativeCheck         uint64
	cached                  *image.RGBA
	cachedScene             *ownedIntroScene
	revision                uint64
	font                    string
	storyPages              int
	pixelPending            *ownedIntroPixel
}
type ownedIntroPixel struct {
	At                     int
	Step                   uint64
	AX, ES, DS, BX, SP, SS uint16
}

func (p *ownedIntroProbe) record(kind string, data map[string]any) {
	p.counts[kind]++
	data["command"] = kind
	data["step"] = p.e.Oracle.Steps()
	if err := p.log.Encode(data); err != nil {
		panic(err)
	}
}
func (p *ownedIntroProbe) begin() {
	if p.active == 0 {
		p.held = cloneOwnedIntroScene(p.scene)
	}
	p.active++
}
func (p *ownedIntroProbe) end() {
	p.active--
	if p.active < 0 {
		panic("owned intro negative transaction")
	}
	if p.active == 0 {
		p.held = nil
	}
	p.scene.Revision++
}
func (p *ownedIntroProbe) write(at int, index byte) {
	if at < 0 || at >= len(p.scene.Native) {
		panic("owned intro destination bounds")
	}
	p.scene.Native[at], p.scene.Backing[at], p.scene.Owners[at] = index, index, 0
}
func (p *ownedIntroProbe) art() ownedIntroArt {
	e := p.e
	a := ownedIntroArt{}
	if e.Story != nil {
		a.Font = e.Story.font
		if e.Story.art != nil {
			a.Story = e.Story.art
		}
		if e.Story.prelude != nil && e.Story.prelude.art != nil {
			a.Prelude = e.Story.prelude.art
		}
	}
	if e.Intro != nil && e.Intro.ink != nil {
		a.Title = e.Intro.ink
	}
	if e.Publisher != nil {
		if e.Publisher.ink != nil {
			a.PublisherInk = e.Publisher.ink
		}
		if e.Publisher.publisher != nil {
			if e.Publisher.publisher.erase != nil {
				a.PublisherErase = e.Publisher.publisher.erase
			}
			if i := e.Publisher.publisher.icon; i != nil {
				if i.art != nil {
					a.IconArt = i.art
				}
				if i.erase != nil {
					a.IconErase = i.erase
				}
			}
		}
	}
	if e.Museum != nil {
		a.MuseumArt = e.Museum.art
		a.MuseumScenes = e.Museum.sceneArts
	}
	return a
}
func (p *ownedIntroProbe) bind() {
	if p.retired {
		return
	}
	o := p.e.Oracle
	if len(o.Overlays()) != 0 {
		p.retired = true
		return
	}
	if p.bound {
		return
	}
	if hash(o.Bytes(oracle.Far(0, 0x576a), 212)) != "88d6cfe05ddb19b00bd42cb4857a95cbcf9bdf764320ea21e503b9f202a947d8" {
		return
	}
	for _, g := range []struct{ at, end uint16 }{{0x576a, 0x583d}, {0x52c0, 0x53f3}, {0x5b0c, 0x5b42}, {0x510b, 0x513f}, {0x517e, 0x51b2}, {0x4c74, 0x4dd3}, {0x5954, 0x5a53}, {0x58b1, 0x590f}} {
		if o.Byte(oracle.Far(0, g.end)) != 0xcb {
			panic("owned intro return ABI")
		}
	}
	p.bound = true
	p.unsubscribe = p.e.ObservePresentation(PresentationObserver{Write: func(v PresentationWrite) {
		if p.retired {
			return
		}
		pc := uint32(v.CS)*16 + uint32(v.IP)
		if pc == 0xa486 && p.scene.Mode == 0x13 {
			command := p.pixelPending
			if command == nil || v.Offset != uint32(command.At) {
				panic("owned intro reveal commit without source command")
			}
			p.write(command.At, p.source[command.At])
			p.scene.Reveal[command.At] = true
			p.scene.Revision++
			p.written++
			p.counts["reveal-pixels"]++
			p.pixelPending = nil
			p.counts["reveal-writes"]++
			return
		}
		if p.active == 0 {
			p.counts["writes-outside-command"]++
			if p.counts["writes-outside-command"] <= 16 {
				p.record("outside-sample", map[string]any{"pc": pc, "offset": v.Offset})
			}
		}
	}, ModeChange: func(v PresentationModeChange) {
		if p.retired {
			return
		}
		old := p.scene
		bridge := old.Mode == 0x13 && old.Prelude && v.Mode == 0xe && p.written == 64000
		p.scene = newOwnedIntroScene(v.Mode)
		p.scene.Revision = old.Revision + 1
		if bridge {
			p.scene.Prelude = true
			copy(p.scene.Reveal, old.Reveal)
		}
		p.active = 0
		p.pixelPending = nil
		p.held = nil
		p.started = v.Mode == 0xe || v.Mode == 0x13
		p.record("mode", map[string]any{"mode": v.Mode, "prelude_bridge": bridge})
	}})
	for _, entry := range []struct {
		at, end uint16
		planes  int
	}{{0x576a, 0x583d, 4}, {0x52c0, 0x53f3, 6}} {
		entry := entry
		var apply func()
		var sp uint16
		o.OnCall(oracle.Far(0, entry.at), func(*oracle.Oracle) {
			if p.retired {
				return
			}
			if apply != nil && sp == o.Regs().SP {
				return
			}
			if apply != nil {
				panic("owned intro bitmap reentry")
			}
			sp = o.Regs().SP
			w, h := int(o.Word(oracle.Far(o.Arg(1), o.Arg(0)))), int(o.Word(oracle.Far(o.Arg(1), o.Arg(0)+2)))
			x, y := int(o.Arg(2)), int(o.Arg(3))
			sourceOffset := o.Arg(0)
			dest := o.Word(oracle.Far(0, 0xd208))
			if o.Word(oracle.Far(0, 0xd202)) != 1 || w < 1 || w > 80 || h < 1 || y+h > 200 || x > 79 || (dest != 0xa000 && dest != 0xa400) {
				panic("owned intro bitmap geometry")
			}
			raw := o.Bytes(oracle.Far(o.Arg(1), o.Arg(0)), 4+w*h*entry.planes)
			source := hash(raw)
			page := int(dest-0xa000) * 16 * 8
			rows := make([]int, h)
			for row := range rows {
				v := o.Word(oracle.Far(o.Regs().CS, 4+uint16((y+row)*2)))
				if int(v) != (y+row)*80 {
					panic("owned intro bitmap pitch")
				}
				rows[row] = int(v) + x
			}
			p.begin()
			apply = func() {
				for row := 0; row < h; row++ {
					for col := 0; col < w*8; col++ {
						local := row*w*8 + col
						bit := uint(7 - local%8)
						if entry.planes == 6 && raw[4+5*w*h+local/8]&(1<<bit) == 0 {
							continue
						}
						index := byte(0)
						for plane := 0; plane < 4; plane++ {
							index |= ((raw[4+plane*w*h+local/8] >> bit) & 1) << uint(plane)
						}
						p.write(page+rows[row]*8+col, index)
					}
				}
				previous := p.scene.Pages[page]
				if entry.planes == 4 {
					kind := ""
					switch source {
					case publisherDecodedSHA:
						kind = "publisher"
					case titleDecodedSHA:
						kind = "title"
					case storyBackgroundSHA:
						kind = "story"
						p.storyPages++
						p.scene.Prelude = false
					}
					p.scene.Pages[page] = ownedIntroPage{Kind: kind}
				}
				p.museum(source, sourceOffset, raw, page, rows, entry.planes, previous)
				p.record("bitmap", map[string]any{"entry": entry.at, "page_pixels": page, "source_sha256": source, "x_byte": x, "y": y, "width_bytes": w, "height": h, "planes": entry.planes})
				p.end()
			}
		})
		o.OnCall(oracle.Far(0, entry.end), func(*oracle.Oracle) {
			if apply != nil {
				apply()
				apply = nil
			}
		})
	}
	var clear func()
	o.OnCall(oracle.Far(0, 0x5b0c), func(*oracle.Oracle) {
		if p.retired || clear != nil {
			return
		}
		dest := o.Word(oracle.Far(0, 0xd208))
		mask := o.Byte(oracle.Far(0, 0xd20a)) & 15
		if o.Word(oracle.Far(0, 0xd202)) != 1 || (dest != 0xa000 && dest != 0xa400) {
			panic("owned intro clear ABI")
		}
		page := int(dest-0xa000) * 16 * 8
		p.begin()
		clear = func() {
			for i := page; i < page+0x4000*8; i++ {
				p.write(i, p.scene.Native[i]&^mask)
			}
			delete(p.scene.Pages, page)
			p.record("clear", map[string]any{"page_pixels": page, "mask": mask})
			p.end()
		}
	})
	o.OnCall(oracle.Far(0, 0x5b42), func(*oracle.Oracle) {
		if clear != nil {
			clear()
			clear = nil
		}
	})
	for _, site := range []struct {
		at, end  uint16
		from, to int
	}{{0x510b, 0x513f, 0, 0x4000 * 8}, {0x517e, 0x51b2, 0x4000 * 8, 0}} {
		site := site
		pending := false
		o.OnCall(oracle.Far(0, site.at), func(*oracle.Oracle) {
			if !p.retired && !pending {
				pending = true
				p.begin()
			}
		})
		o.OnCall(oracle.Far(0, site.end), func(*oracle.Oracle) {
			if !pending {
				return
			}
			copy(p.scene.Native[site.to:site.to+128000], p.scene.Native[site.from:site.from+128000])
			copy(p.scene.Backing[site.to:site.to+128000], p.scene.Backing[site.from:site.from+128000])
			copy(p.scene.Owners[site.to:site.to+128000], p.scene.Owners[site.from:site.from+128000])
			v := p.scene.Pages[site.from]
			if v.Museum != nil {
				m := *v.Museum
				m.scene = cloneMuseumScene(v.Museum.scene)
				m.ink = image.NewRGBA(v.Museum.ink.Bounds())
				copy(m.ink.Pix, v.Museum.ink.Pix)
				v.Museum = &m
			}
			p.scene.Pages[site.to] = v
			p.record("copy", map[string]any{"from": site.from, "to": site.to})
			pending = false
			p.end()
		})
	}
	for _, site := range []struct {
		at, end uint16
		width   int
	}{{0x4c74, 0x4dd3, 16}, {0x5954, 0x5a53, 8}} {
		site := site
		var apply func()
		var sp uint16
		o.OnCall(oracle.Far(0, site.at), func(*oracle.Oracle) {
			if p.retired {
				return
			}
			if apply != nil && sp == o.Regs().SP {
				return
			}
			if apply != nil {
				panic("owned intro glyph reentry")
			}
			sp = o.Regs().SP
			x, y := int(o.Arg(1))*8, int(o.Arg(2))
			dest := o.Word(oracle.Far(0, 0xd208))
			fg, bg := o.Byte(oracle.Far(0, 0xd20a)), o.Byte(oracle.Far(0, 0xd20b))
			code := o.Arg(0)
			if o.Word(oracle.Far(0, 0xd202)) != 1 || x+site.width > 640 || y+15 > 200 || (dest != 0xa000 && dest != 0xa400) {
				panic("owned intro glyph geometry")
			}
			var bits []byte
			var char rune
			if site.width == 16 {
				bits = o.Bytes(oracle.Far(o.Regs().CS, code+6), 30)
				if code%30 != 0 {
					panic("owned intro glyph offset")
				}
				pair := o.Word(oracle.Far(0, 0xbd0c+code/30*2))
				if p.e.Story != nil {
					char = p.e.Story.codes[pair]
				}
			} else {
				bits = o.Bytes(oracle.Far(0, 0xbfd0+code*15), 15)
				char = rune(code)
			}
			page := int(dest-0xa000) * 16 * 8
			p.begin()
			apply = func() {
				p.scene.Next++
				id := p.scene.Next
				p.scene.Glyphs[id] = ownedIntroGlyph{id, char, x, y, site.width, fg}
				if char == 0 {
					p.counts["unmapped-glyph"]++
				} else if char != ' ' && p.e.Story != nil {
					if _, ok := p.e.Story.font.Glyphs[char]; !ok {
						p.counts["missing-hd-glyph"]++
					}
				}
				for row := 0; row < 15; row++ {
					for col := 0; col < site.width; col++ {
						at := page + (y+row)*640 + x + col
						bit := bits[row*(site.width/8)+col/8] & (128 >> uint(col%8))
						if bg != 255 {
							p.scene.Native[at] = bg
							p.scene.Backing[at] = bg
						}
						if bit != 0 {
							p.scene.Native[at] = fg
						}
						p.scene.Owners[at] = id
					}
				}
				p.record("glyph", map[string]any{"rune": string(char), "code": code, "x": x, "y": y, "width": site.width, "fg": fg, "bg": bg})
				p.end()
			}
		})
		o.OnCall(oracle.Far(0, site.end), func(*oracle.Oracle) {
			if apply != nil {
				apply()
				apply = nil
			}
		})
	}
	stringActive := false
	o.OnCall(oracle.Far(0, 0x58b1), func(*oracle.Oracle) {
		if !p.retired {
			if stringActive {
				panic("owned intro string reentry")
			}
			stringActive = true
			p.begin()
		}
	})
	o.OnCall(oracle.Far(0, 0x590f), func(*oracle.Oracle) {
		if stringActive {
			stringActive = false
			p.record("string", map[string]any{})
			p.end()
		}
	})
	o.OnCall(oracle.Far(0, 0xa3d0), func(*oracle.Oracle) {
		if p.retired {
			return
		}
		raw := o.Bytes(oracle.Far(0x6000, 0), 64768)
		if hash(raw) != preludeSourceSHA {
			panic("owned intro prelude source")
		}
		p.source = append([]byte(nil), raw[768:]...)
		p.order = nil
		p.written = 0
		table := o.Bytes(oracle.Far(0, 0xa633), 3200)
		if hash(table) != preludeTableSHA {
			panic("owned intro prelude order")
		}
		for i := 1599; i >= 0; i-- {
			v := int(binary.LittleEndian.Uint16(table[i*2:]))
			for x := v % 40; x < 320; x += 40 {
				for y := v / 40; y < 200; y += 40 {
					p.order = append(p.order, uint32(y*320+x))
				}
			}
		}
		p.scene.Prelude = true
		p.record("reveal-begin", map[string]any{"pixels": len(p.order)})
	})
	o.OnCall(oracle.Far(0, 0xa486), func(*oracle.Oracle) {
		if p.retired {
			return
		}
		r := o.Regs()
		at := int(r.SI)
		if pending := p.pixelPending; pending != nil {
			if pending.At == at && pending.AX == r.AX && pending.ES == r.ES && pending.DS == r.DS && pending.BX == r.BX && pending.SP == r.SP && pending.SS == r.SS {
				p.counts["reveal-entry-repeats"]++
				if p.counts["reveal-entry-repeats"] <= 8 {
					p.record("reveal-entry-repeat", map[string]any{"source_step": pending.Step, "return_step": o.Steps(), "at": at, "ax": r.AX, "es": r.ES, "ds": r.DS, "bx": r.BX, "sp": r.SP, "ss": r.SS})
				}
				return
			}
			panic("owned intro reveal source reentry differs")
		}
		if p.scene.Mode != 0x13 || p.written >= 64000 || at != int(p.order[p.written]) || byte(r.AX) != p.source[at] || r.ES != 0xa000 {
			panic("owned intro reveal pixel ABI")
		}
		p.pixelPending = &ownedIntroPixel{At: at, Step: o.Steps(), AX: r.AX, ES: r.ES, DS: r.DS, BX: r.BX, SP: r.SP, SS: r.SS}
	})
	o.OnCall(oracle.Far(0, 0xa450), func(*oracle.Oracle) {
		if !p.retired {
			if p.written != 64000 {
				panic("owned intro incomplete reveal")
			}
			p.record("reveal-complete", map[string]any{"pixels": p.written})
		}
	})
}

// Rebuild museum metadata from the same source commands as our native pixels.
func (p *ownedIntroProbe) museum(source string, offset uint16, raw []byte, page int, rows []int, planes int, previous ownedIntroPage) {
	asset := p.e.Museum
	if asset == nil {
		return
	}
	meta := asset.records[source]
	if meta == nil || meta.offset != int(offset) || meta.blocks != planes {
		return
	}
	record := *meta
	record.raw = append([]byte(nil), raw...)
	t := museumTX{record: &record, page: uint32(page / 8), rows: make([]uint32, len(rows))}
	for y, row := range rows {
		t.rows[y] = t.page + uint32(row)
	}
	painter := &IntroMuseum{pages: map[uint32]*museumPage{t.page: previous.Museum}, actorSprites: asset.actorSprites, sceneArts: asset.sceneArts}
	copy(painter.palette[:], p.scene.Palette[:16])
	if planes == 4 {
		if record.role == "portrait" {
			old := previous.Museum
			if old == nil || old.role != "right" || old.maskedCount != 0 || old.scene == nil || len(t.rows) != 100 || t.rows[0] != t.page+1614 {
				panic("owned museum portrait backing")
			}
		} else if record.w != 80 || record.h != 100 || len(t.rows) != 100 || t.rows[0] != t.page+4000 {
			panic("owned museum backdrop geometry")
		}
		painter.commitMuseumOpaque(t)
		p.scene.Pages[page] = ownedIntroPage{"museum", painter.pages[t.page]}
		return
	}
	backing := previous.Museum
	if backing == nil {
		return
	}
	if record.w == 24 {
		painter.assignMuseumBeam(backing, t)
	} else {
		painter.assignHDActor(backing, t)
	}
	area := record.w * record.h
	for y, row := range rows {
		for x := 0; x < record.w*8; x++ {
			local := y*record.w*8 + x
			bit := uint(7 - local%8)
			if raw[4+5*area+local/8]&(1<<bit) == 0 {
				continue
			}
			at := row*8 + x
			index := p.scene.Native[page+at]
			c := p.scene.Palette[index]
			backing.ink.SetRGBA(at%640, at/640, color.RGBA{c[0], c[1], c[2], 255})
		}
	}
	p.scene.Pages[page] = ownedIntroPage{"museum", backing}
}

func (e *Engine) ResearchOwnedIntro(out string) (func(), func() *image.RGBA, func() error) {
	f, err := os.Create(filepath.Join(out, "owned-intro-commands.jsonl"))
	if err != nil {
		panic(err)
	}
	p := &ownedIntroProbe{e: e, scene: newOwnedIntroScene(3), file: f, log: json.NewEncoder(f), counts: map[string]uint64{}, out: out, captures: map[string]bool{}}
	frame := func() *image.RGBA {
		if !p.bound || !p.started || p.retired {
			return nil
		}
		o := e.Oracle
		palette := o.Palette()
		start := 0
		if p.scene.Mode == 0xe {
			if display, ok := o.PlanarDisplay(); ok {
				copy(palette[:16], display.Palette[:])
				start = int(display.Start) * 8
			}
		}
		if palette != p.scene.Palette || start != p.scene.Start {
			p.scene.Palette = palette
			p.scene.Start = start
			p.scene.Revision++
		}
		if p.active == 0 && p.lastNativeCheck != p.scene.Revision {
			w, h, original := o.Screen()
			width := 640
			if p.scene.Mode == 0x13 {
				width = 320
			}
			if w == width && h == 200 {
				n := 0
				for at, v := range original {
					if p.scene.Native[start+at] != v {
						n++
					}
				}
				p.counts["native-stable-checks"]++
				if n != 0 {
					p.counts["native-mismatch-checks"]++
					if p.counts["native-mismatch-checks"] <= 12 {
						p.record("native-mismatch", map[string]any{"pixels": n, "mode": p.scene.Mode})
					}
				}
			}
			p.lastNativeCheck = p.scene.Revision
		}
		state := p.scene
		if p.held != nil {
			state = p.held
			p.counts["staged-frames"]++
		}
		if p.cached == nil || p.cachedScene != state || p.revision != state.Revision || p.font != e.FontID() {
			p.cached = renderOwnedIntro(state, p.art(), true)
			p.cachedScene = state
			p.revision = state.Revision
			p.font = e.FontID()
		}
		kind := state.Pages[state.Start].Kind
		if state.Prelude {
			kind = "prelude-reveal"
			if p.written == 64000 {
				kind = "prelude-complete"
				if state.Mode == 0xe {
					kind = "prelude-handoff"
				}
			}
		}
		if kind == "story" {
			letters := map[uint32]bool{}
			for _, id := range state.Owners[state.Start : state.Start+128000] {
				if g := state.Glyphs[id]; g.Rune != 0 && g.Rune != ' ' {
					letters[id] = true
				}
			}
			kind = fmt.Sprintf("story-%d-start", p.storyPages)
			if len(letters) >= 32 {
				kind = fmt.Sprintf("story-%d-text", p.storyPages)
			}
		}
		if page := state.Pages[state.Start].Museum; page != nil {
			kind = "museum-" + page.role
			if page.scene != nil && page.scene.portrait != nil {
				kind = "museum-portrait"
			}
			if page.scene != nil && page.scene.beam != nil {
				kind = "museum-beam"
			}
		}
		if p.active == 0 && kind != "" && !p.captures[kind] {
			p.captures[kind] = true
			native := renderOwnedIntro(state, p.art(), false)
			for suffix, im := range map[string]*image.RGBA{"owned": p.cached, "native": native} {
				file, err := os.Create(filepath.Join(out, "intro-"+kind+"-"+suffix+".png"))
				if err != nil {
					panic(err)
				}
				if err = png.Encode(file, im); err != nil {
					panic(err)
				}
				if err = file.Close(); err != nil {
					panic(err)
				}
			}
			data := map[string]any{"kind": kind, "rgba_sha256": hash(p.cached.Pix), "native_rgba_sha256": hash(native.Pix)}
			if reference := e.researchOwnedReference; reference != nil {
				diff := 0
				for at := 0; at < len(reference.Pix); at += 4 {
					if !bytes.Equal(reference.Pix[at:at+4], p.cached.Pix[at:at+4]) {
						diff++
					}
				}
				file, err := os.Create(filepath.Join(out, fmt.Sprintf("intro-%s-legacy.png", kind)))
				if err != nil {
					panic(err)
				}
				if err = png.Encode(file, reference); err != nil {
					panic(err)
				}
				if err = file.Close(); err != nil {
					panic(err)
				}
				data["different_pixels"] = diff
				data["legacy_rgba_sha256"] = hash(reference.Pix)
			}
			p.record("capture", data)
		}
		return p.cached
	}
	finish := func() error {
		if p.unsubscribe != nil {
			p.unsubscribe()
		}
		data := map[string]any{"production": false, "bound": p.bound, "retired": p.retired, "active_at_end": p.active, "commands": p.counts, "renderer_reads_vga": false, "limits": "research source model; unknown operations, early cancellation and failure recovery still require verification"}
		raw, err := json.MarshalIndent(data, "", "  ")
		if err != nil {
			return err
		}
		if err = os.WriteFile(filepath.Join(out, "owned-intro-receipt.json"), append(raw, 10), 0644); err != nil {
			return err
		}
		return f.Close()
	}
	return p.bind, frame, finish
}

func (e *Engine) ResearchOwnedEverything(out string) (func(), func() *image.RGBA, func() error) {
	if os.Getenv("EIGHTSWORD_RESEARCH_INTRO_CONTROL") == "1" {
		return e.ResearchOwnedScene(out)
	}
	installPAM, framePAM, closePAM := e.ResearchOwnedScene(out)
	installIntro, frameIntro, closeIntro := e.ResearchOwnedIntro(out)
	counts := map[string]uint64{}
	return func() { installIntro(); installPAM() }, func() *image.RGBA {
			mode := e.Oracle.VideoMode()
			if im := framePAM(); im != nil {
				counts[fmt.Sprintf("pam-%02x", mode)]++
				return im
			}
			if im := frameIntro(); im != nil {
				counts[fmt.Sprintf("intro-%02x", mode)]++
				return im
			}
			counts[fmt.Sprintf("fallback-%02x", mode)]++
			return nil
		}, func() error {
			if err := closeIntro(); err != nil {
				return err
			}
			if err := closePAM(); err != nil {
				return err
			}
			raw, err := json.MarshalIndent(map[string]any{"counts": counts, "production": false}, "", "  ")
			if err != nil {
				return err
			}
			return os.WriteFile(filepath.Join(out, "owned-dispatch-receipt.json"), append(raw, 10), 0644)
		}
}
