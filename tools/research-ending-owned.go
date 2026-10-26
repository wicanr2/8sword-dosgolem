//go:build ignore

// 053 DRAFT. Source-owned PAE scene prototype; no production or CPU replacement.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"os"
	"path/filepath"

	"github.com/wicanr2/dosgolem/oracle"
)

var endingPalette = [16][3]uint8{{0, 0, 0}, {0, 0, 170}, {0, 170, 0}, {0, 170, 170}, {170, 0, 0}, {170, 0, 170}, {170, 85, 0}, {170, 170, 170}, {85, 85, 85}, {85, 85, 255}, {85, 255, 85}, {85, 255, 255}, {255, 85, 85}, {255, 85, 255}, {255, 255, 85}, {255, 255, 255}}

func check(err error) {
	if err != nil {
		panic(err)
	}
}
func sha(raw []byte) string   { return fmt.Sprintf("%x", sha256.Sum256(raw)) }
func read(path string) []byte { b, e := os.ReadFile(path); check(e); return b }
func save(path string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	check(e)
	check(os.WriteFile(path, append(b, '\n'), 0644))
}
func pngFile(path string, im image.Image) {
	f, e := os.Create(path)
	check(e)
	check(png.Encode(f, im))
	check(f.Close())
}

type fontGlyph struct {
	Character string
	Ink       [4]int
}
type fontProfile struct {
	ID, Atlas string
	Glyphs    []fontGlyph
	glyphs    map[rune]fontGlyph
	image     image.Image
}
type cjkGlyph struct {
	Index                 int
	Character, Code, Bits string
}
type inputs struct {
	CJK      []cjkGlyph
	ASCII    []string
	Profiles []fontProfile
	Files    map[string]string
}
type command struct {
	Kind                  string `json:"kind"`
	X, Y, W, H            int
	FG, BG                byte
	Code                  int
	Char                  rune
	SourceSHA, SourceFile string
	Pixels, Mask          []byte `json:"-"`
}
type page struct {
	native []byte
	ops    []*command
	stage  string
	glyphs int
}
type scene struct {
	pages  [4]*page
	active int
	mode   bool
}
type artSet struct {
	profiles []fontProfile
	end7     image.Image
	titles   map[string]image.Image
}

func newScene() *scene {
	s := &scene{}
	for i := range s.pages {
		s.pages[i] = &page{native: make([]byte, 0x4000*8)}
	}
	return s
}
func decodeBitmap(raw []byte, kind, w, h int) ([]byte, []byte) {
	area := w / 8 * h
	pixels, mask := make([]byte, w*h), make([]byte, w*h)
	for at := range pixels {
		b, bit := at/8, uint(7-at%8)
		for plane := 0; plane < 4; plane++ {
			pixels[at] |= (raw[4+plane*area+b] >> bit & 1) << uint(plane)
		}
		if kind != 6 || raw[4+5*area+b]>>bit&1 != 0 {
			mask[at] = 1
		}
	}
	return pixels, mask
}
func (p *page) apply(c *command) bool {
	if c.X < 0 || c.Y < 0 || c.X+c.W > 640 || c.Y+c.H > 200 {
		panic(fmt.Sprintf("source geometry %+v", c))
	}
	if c.Kind == "cjk" || c.Kind == "ascii" {
		if c.Char == ' ' && c.BG == 255 {
			empty := true
			for _, v := range c.Mask {
				if v != 0 {
					empty = false
					break
				}
			}
			if empty {
				return false
			}
		}
		r := image.Rect(c.X, c.Y, c.X+c.W, c.Y+c.H)
		for i := len(p.ops) - 1; i >= 0; i-- {
			prior := p.ops[i]
			if !r.Overlaps(image.Rect(prior.X, prior.Y, prior.X+prior.W, prior.Y+prior.H)) {
				continue
			}
			if prior.Kind == c.Kind && prior.Code == c.Code && prior.Char == c.Char && prior.X == c.X && prior.Y == c.Y && prior.W == c.W && prior.H == c.H && prior.FG == c.FG && prior.BG == c.BG {
				return false
			}
			break
		}
	}
	for y := 0; y < c.H; y++ {
		for x := 0; x < c.W; x++ {
			local, at := y*c.W+x, (c.Y+y)*640+c.X+x
			if c.Kind == "cjk" || c.Kind == "ascii" {
				if c.BG != 255 {
					p.native[at] = c.BG
				}
				if c.Mask[local] != 0 {
					p.native[at] = c.FG
				}
			} else if c.Mask[local] != 0 {
				p.native[at] = c.Pixels[local]
			}
		}
	}
	if c.X == 0 && c.Y == 0 && c.W == 640 && c.H == 200 && c.Kind != "cjk" && c.Kind != "ascii" {
		p.ops = nil
		p.glyphs = 0
	}
	p.ops = append(p.ops, c)
	if c.SourceFile != "" {
		p.stage = c.SourceFile
	}
	if c.Kind == "cjk" || c.Kind == "ascii" {
		p.glyphs++
	}
	return true
}
func fill(out *image.RGBA, r image.Rectangle, c [3]uint8) {
	draw.Draw(out, r, image.NewUniform(color.RGBA{c[0], c[1], c[2], 255}), image.Point{}, draw.Src)
}

// Only source commands, colors and immutable textures enter this painter.
// It has no Oracle, VGA pixels or previous original RGB frame input.
func render(p *page, palette [16][3]uint8, art artSet, profile *fontProfile) *image.RGBA {
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	fill(out, out.Bounds(), palette[0])
	for _, c := range p.ops {
		r := image.Rect(c.X*3, c.Y*6, (c.X+c.W)*3, (c.Y+c.H)*6)
		if profile != nil && c.SourceFile == "END7.AY" {
			if palette != endingPalette {
				panic("unreviewed ending art palette")
			}
			draw.Draw(out, r, art.end7, image.Point{}, draw.Src)
			continue
		}
		if profile != nil && c.SourceFile == "END8.AY" {
			if palette != endingPalette {
				panic("unreviewed ending title palette")
			}
			fill(out, r, palette[0])
			draw.Draw(out, r, art.titles[profile.ID], image.Point{}, draw.Over)
			continue
		}
		if c.Kind == "cjk" || c.Kind == "ascii" {
			if c.BG != 255 {
				fill(out, r, palette[c.BG])
			}
			if profile != nil {
				if c.Char == ' ' {
					continue
				}
				g, ok := profile.glyphs[c.Char]
				if !ok {
					panic(fmt.Sprintf("HD ending glyph missing %U", c.Char))
				}
				iw, ih := g.Ink[2], g.Ink[3]
				dw, dh := min(iw, r.Dx()), min(ih, r.Dy())
				left, top := r.Min.X+(r.Dx()-dw)/2, r.Min.Y+(r.Dy()-dh)/2
				fg := palette[c.FG]
				for y := 0; y < dh; y++ {
					for x := 0; x < dw; x++ {
						_, _, _, alpha := profile.image.At(g.Ink[0]+x*iw/dw, g.Ink[1]+y*ih/dh).RGBA()
						a := uint32(alpha >> 8)
						at := (top+y)*out.Stride + (left+x)*4
						for k := 0; k < 3; k++ {
							out.Pix[at+k] = byte((uint32(fg[k])*a + uint32(out.Pix[at+k])*(255-a) + 127) / 255)
						}
					}
				}
				continue
			}
		}
		for y := 0; y < c.H; y++ {
			for x := 0; x < c.W; {
				at := y*c.W + x
				if c.Mask[at] == 0 {
					x++
					continue
				}
				index := c.FG
				if c.Kind != "cjk" && c.Kind != "ascii" {
					index = c.Pixels[at]
				}
				run := 1
				for x+run < c.W && c.Mask[at+run] != 0 {
					if c.Kind != "cjk" && c.Kind != "ascii" && c.Pixels[at+run] != index {
						break
					}
					run++
				}
				fill(out, image.Rect((c.X+x)*3, (c.Y+y)*6, (c.X+x+run)*3, (c.Y+y+1)*6), palette[index])
				x += run
			}
		}
	}
	return out
}

func main() {
	root := flag.String("root", "", "read-only original game")
	batch := flag.String("batch", "", "read-only ending-hd-r1")
	assets := flag.String("inputs", "", "read-only prepared owned-inputs-r1")
	out := flag.String("out", "", "new research output")
	flag.Parse()
	if *root == "" || *batch == "" || *assets == "" || *out == "" {
		panic("missing owned ending arguments")
	}
	check(os.Mkdir(*out, 0755))
	check(os.Mkdir(filepath.Join(*out, "sources"), 0755))
	raw := read(filepath.Join(*root, "PAE.AY"))
	if sha(raw) != "8ae11b4c89f0361ed0a2d5b1859bbb4750047d37f0e26885e6903e4feb721a0c" {
		panic("unknown PAE")
	}
	inputRaw := read(filepath.Join(*assets, "inputs.json"))
	if sha(inputRaw) != "19497ef75d6a1eb26c8e5e07b806f4a4ccc1ceada43fb1710a7e850fdd7a6ef2" {
		panic("unknown owned input pack")
	}
	var in inputs
	check(json.Unmarshal(inputRaw, &in))
	loadImage := func(name string) image.Image {
		b := read(filepath.Join(*assets, name))
		if sha(b) != in.Files[name] {
			panic("owned texture hash")
		}
		im, _, e := image.Decode(bytes.NewReader(b))
		check(e)
		return im
	}
	art := artSet{profiles: in.Profiles, end7: loadImage("end7.png"), titles: map[string]image.Image{}}
	for i := range art.profiles {
		p := &art.profiles[i]
		p.image = loadImage(p.Atlas)
		p.glyphs = map[rune]fontGlyph{}
		for _, g := range p.Glyphs {
			p.glyphs[[]rune(g.Character)[0]] = g
		}
		art.titles[p.ID] = loadImage("title-" + p.ID + ".png")
	}
	var catalog struct {
		Records []struct {
			File string `json:"source_file"`
			SHA  string `json:"record_sha256"`
		}
	}
	check(json.Unmarshal(read(filepath.Join(*batch, "source.json")), &catalog))
	known := map[string]string{}
	for _, r := range catalog.Records {
		known[r.SHA] = r.File
	}
	o, e := oracle.LoadWith(filepath.Join(*root, "PAE.AY"), *root, oracle.Options{Adlib: true, ProgramPath: `C:\PAE.AY`})
	check(e)
	o.SetScratch(filepath.Join(*out, "scratch"))
	o.SetClock(12, 0, 0, 0)
	o.SetCmdLine("v a y a n g")
	s := newScene()
	active, flips, samples, pure := 0, 0, 0, 0
	counts := map[string]int{}
	unknown := map[string]int{}
	seenStage := map[string]bool{}
	seenText := false
	var receipts []map[string]any
	pageFor := func(ds uint16) *page {
		if o.Word(oracle.Addr{Seg: ds, Off: 0x177a}) != 1 {
			panic("PAE mode differs")
		}
		dest := o.Word(oracle.Addr{Seg: ds, Off: 0x1780})
		if dest != 0xa000 && dest != 0xa400 {
			panic("PAE destination differs")
		}
		return s.pages[int(dest-0xa000)/0x400]
	}
	sample := func(force bool) {
		if !s.mode || active != 0 {
			return
		}
		d, ok := o.PlanarDisplay()
		if !ok || d.Width != 640 || d.Height != 200 || d.Pitch != 80 || int(d.Start) != s.active*0x4000 {
			panic("owned ending display differs")
		}
		p := s.pages[s.active]
		_, _, native := o.Screen()
		if !bytes.Equal(p.native[:128000], native) {
			diffs := []int{}
			for i, v := range native {
				if v != p.native[i] && len(diffs) < 20 {
					diffs = append(diffs, i)
				}
			}
			save(filepath.Join(*out, "mismatch.json"), map[string]any{"step": o.Steps(), "diffs": diffs, "unknown_writes": unknown, "counts": counts, "stage": p.stage, "ops": p.ops})
			panic(fmt.Sprintf("source ending scene differs at step%d positions%v", o.Steps(), diffs))
		}
		counts["native-full-frame-checked"]++
		want := force || (!seenStage[p.stage] && p.stage != "") || (p.glyphs > 0 && !seenText) || flips%32 == 0
		if !want {
			return
		}
		seenStage[p.stage] = true
		if p.glyphs > 0 {
			seenText = true
		}
		samples++
		name := fmt.Sprintf("sample-%03d", samples)
		before, after := filepath.Join(*out, "before.state"), filepath.Join(*out, "after.state")
		check(o.SaveStateFile(before))
		b := read(before)
		baseline := render(p, d.Palette, art, nil)
		_, _, rgb := o.ScreenRGB()
		for y := 0; y < 200; y++ {
			for x := 0; x < 640; x++ {
				at := y*640 + x
				got := baseline.RGBAAt(x*3, y*6)
				if got.R != rgb[at*3] || got.G != rgb[at*3+1] || got.B != rgb[at*3+2] {
					panic("source RGB differs")
				}
			}
		}
		pngFile(filepath.Join(*out, name+"-source-native.png"), baseline)
		for i := range art.profiles {
			im := render(p, d.Palette, art, &art.profiles[i])
			pngFile(filepath.Join(*out, name+"-"+art.profiles[i].ID+".png"), im)
		}
		check(o.SaveStateFile(after))
		if !bytes.Equal(b, read(after)) {
			panic("owned ending render changed guest")
		}
		pure++
		check(os.WriteFile(filepath.Join(*out, name+".idx"), native, 0644))
		snap := map[string]any{"sample": samples, "step": o.Steps(), "page": s.active, "stage": p.stage, "glyphs": p.glyphs, "palette": d.Palette, "ops": p.ops}
		save(filepath.Join(*out, name+".json"), snap)
		receipts = append(receipts, map[string]any{"sample": samples, "step": o.Steps(), "stage": p.stage, "glyphs": p.glyphs, "ops": len(p.ops), "scene": name + ".json"})
	}
	bind := func(seg, entry, ret uint16, expected string, prepare func() func()) {
		var apply func()
		var sp uint16
		o.OnCall(oracle.Addr{Seg: seg, Off: entry}, func(o *oracle.Oracle) {
			if apply != nil {
				panic("ending source nesting")
			}
			if expected != "" && sha(o.Bytes(oracle.Addr{Seg: seg, Off: entry}, int(ret-entry)+1)) != expected {
				panic(fmt.Sprintf("ending routine changed %04x:%04x", seg, entry))
			}
			sp = o.Regs().SP
			apply = prepare()
			active++
		})
		o.OnCall(oracle.Addr{Seg: seg, Off: ret}, func(o *oracle.Oracle) {
			if apply == nil {
				return
			}
			if sp != o.Regs().SP {
				panic("ending return stack differs")
			}
			apply()
			apply = nil
			active--
		})
	}
	cache := map[string]*command{}
	for _, v := range []struct {
		Entry, Return uint16
		Kind          int
		SHA           string
	}{
		{0x4ec, 0x61f, 6, "85467a42c1b56b7eb880128fe34417adbe74fdf1bf42d857758908d8bbd79549"},
		{0x769, 0x84e, 5, "285723c100da394f2c125b5a1a293c0b24d4f18a8cf2276937ef4a47db4124bc"},
		{0x996, 0xa69, 4, "603833bfa266acbc8f7a3c8ecf3a30e9f15b5242211367534a7ca1145bb4cfad"},
	} {
		v := v
		bind(0x393, v.Entry, v.Return, v.SHA, func() func() {
			ptr := oracle.Addr{Seg: o.Arg(1), Off: o.Arg(0)}
			w, h := int(o.Word(ptr))*8, int(o.Word(oracle.Addr{Seg: ptr.Seg, Off: ptr.Off + 2}))
			if w < 8 || w > 640 || h < 1 || h > 200 {
				panic("ending bitmap bounds")
			}
			raw := o.Bytes(ptr, 4+w/8*h*v.Kind)
			key := sha(raw)
			cached := cache[key]
			if cached == nil {
				file := known[key]
				if file == "" {
					panic("unclassified ending bitmap")
				}
				px, mask := decodeBitmap(raw, v.Kind, w, h)
				cached = &command{Kind: "bitmap", W: w, H: h, Pixels: px, Mask: mask, SourceSHA: key, SourceFile: file}
				cache[key] = cached
				check(os.WriteFile(filepath.Join(*out, "sources", key+".bin"), raw, 0644))
			}
			c := *cached
			c.X, c.Y = int(o.Arg(2))*8, int(o.Arg(3))
			p := pageFor(o.Regs().DS)
			counts[fmt.Sprintf("bitmap-%d", v.Kind)]++
			return func() { p.apply(&c) }
		})
	}
	for _, v := range []struct {
		Seg, Entry, Return uint16
		CJK                bool
		SHA                string
	}{
		{0x28e, 0xef0, 0x104f, true, "dc3197283e3434f6ca35e71592b0c604bc035efef450ed50afffff1309f01739"},
		{0x393, 0xb80, 0xc7f, false, "5631f527e7a205f772c3c0f0b1c6521781a1264b669d487346dfa1671a5c1692"},
	} {
		v := v
		bind(v.Seg, v.Entry, v.Return, v.SHA, func() func() {
			ds := o.Regs().DS
			p := pageFor(ds)
			index := int(o.Arg(0))
			w := 8
			kind := "ascii"
			char := rune(index)
			bitsHex := ""
			ptr := oracle.Addr{Seg: ds, Off: uint16(0x548 + index*15)}
			if v.CJK {
				if index%30 != 0 || index/30 >= len(in.CJK) {
					panic("ending CJK index")
				}
				index /= 30
				g := in.CJK[index]
				char = []rune(g.Character)[0]
				bitsHex = g.Bits
				w = 16
				kind = "cjk"
				ptr = oracle.Addr{Seg: 0x28e, Off: uint16(14 + index*30)}
			} else {
				if index > 255 {
					panic("ending ASCII index")
				}
				bitsHex = in.ASCII[index]
			}
			bits := o.Bytes(ptr, w/8*15)
			if hex.EncodeToString(bits) != bitsHex {
				panic("ending glyph bitmap differs")
			}
			mask := make([]byte, w*15)
			for at := range mask {
				mask[at] = bits[at/8] >> uint(7-at%8) & 1
			}
			c := &command{Kind: kind, Code: index, Char: char, X: int(o.Arg(1)) * 8, Y: int(o.Arg(2)), W: w, H: 15, FG: o.Byte(oracle.Addr{Seg: ds, Off: 0x1782}), BG: o.Byte(oracle.Addr{Seg: ds, Off: 0x1783}), Mask: mask}
			if c.FG > 15 || (c.BG > 15 && c.BG != 255) {
				panic("ending text colors")
			}
			counts[kind]++
			return func() {
				if !p.apply(c) {
					counts["idempotent-or-empty-glyph"]++
				}
			}
		})
	}
	bind(0x393, 0xd38, 0xd6e, "f64a64cc8b397aa4b1202678a1fb57a2e98f2e9e742091aee26839486238fa33", func() func() {
		ds := o.Regs().DS
		p := pageFor(ds)
		mask := o.Byte(oracle.Addr{Seg: ds, Off: 0x1782})
		counts[fmt.Sprintf("clear-%d", mask)]++
		if mask != 15 {
			panic(fmt.Sprintf("ending partial clear requires review: %d", mask))
		}
		return func() { clear(p.native); p.ops = nil; p.glyphs = 0; p.stage = "" }
	})
	bind(0x393, 0x3aa, 0x3de, "9c6604f617ce1421dd00d7f46e665e37416b00e822338f86dba879b13785aa36", func() func() {
		counts["copy-page-1-to-0"]++
		return func() {
			from, to := s.pages[1], s.pages[0]
			copy(to.native[:128000], from.native[:128000])
			to.ops = append([]*command(nil), from.ops...)
			to.stage, to.glyphs = from.stage, from.glyphs
		}
	})
	var requested uint16
	bind(0x393, 0x196, 0x1a3, "c764b97541e70a9e047ec2893ab0ce9bf3c51f36df6ad2a72ed7e27b46a31fc6", func() func() {
		requested = o.Arg(0) & 255
		if requested > 3 {
			panic("ending page index")
		}
		return func() { s.active = int(requested); flips++ }
	})
	// Registered after the source commit callback, so the scene is complete.
	o.OnCall(oracle.Addr{Seg: 0x393, Off: 0x1a3}, func(*oracle.Oracle) { sample(false) })
	for _, ret := range []uint16{0xa69, 0x3de} {
		o.OnCall(oracle.Addr{Seg: 0x393, Off: ret}, func(*oracle.Oracle) {
			if s.mode && active == 0 && s.pages[s.active].stage == "END7.AY" && !seenStage["END7.AY"] {
				sample(true)
			}
		})
	}
	o.ObserveVideoModeChanges(func(v oracle.VideoModeChange) {
		s.mode = v.Mode == 0xe
		for _, p := range s.pages {
			clear(p.native)
			p.ops = nil
			p.glyphs = 0
			p.stage = ""
		}
		s.active = 0
	})
	o.ObserveVideoWrites(func(v oracle.VideoWrite) {
		if s.mode && active == 0 {
			key := fmt.Sprintf("%04x:%04x", v.CS, v.IP)
			unknown[key]++
		}
	})
	err := o.Run(200000000)
	check(o.SaveStateFile(filepath.Join(*out, "final.state")))
	message := ""
	if err != nil {
		message = err.Error()
	}
	save(filepath.Join(*out, "owned-result.json"), map[string]any{"spec": "053", "status": "research-owned-ending-source-scene", "production": false, "source_sha256": sha(raw), "inputs_sha256": sha(inputRaw), "steps": o.Steps(), "run_error": message, "counts": counts, "flips": flips, "samples": receipts, "frame_purity": pure, "unknown_writes": unknown, "file_ops": o.FileOps(), "exec_log": o.ExecLog(), "unimplemented": o.Unimplemented(), "limits": []string{"Standalone diagnostic, not normal PAM handoff or natural completion.", "Source-only owned scene; original CPU pixel loops are still executed. Unconverted ending artwork remains source pixels.", "No GPU or FPS claim."}})
	fmt.Printf("owned ending steps=%d flips=%d samples=%d pure=%d unknown=%v error=%q\n", o.Steps(), flips, samples, pure, unknown, message)
}
