//go:build ignore

// Disposable Go-rendered animation study. No CPU, game state, RNG or live renderer.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"math"
	"os"
	"path/filepath"
)

func check(e error) {
	if e != nil {
		panic(e)
	}
}
func read(p string, v any) { b, e := os.ReadFile(p); check(e); check(json.Unmarshal(b, v)) }
func save(p string, m image.Image) {
	f, e := os.Create(p)
	check(e)
	check(png.Encode(f, m))
	check(f.Close())
}
func scale(p string, w, h int, mirror bool) *image.RGBA {
	f, e := os.Open(p)
	check(e)
	m, e := png.Decode(f)
	check(e)
	check(f.Close())
	out := image.NewRGBA(image.Rect(0, 0, w, h))
	b := m.Bounds()
	for y := 0; y < h; y++ {
		for x := 0; x < w; x++ {
			sx := x * b.Dx() / w
			if mirror {
				sx = b.Dx() - 1 - sx
			}
			out.Set(x, y, m.At(b.Min.X+sx, b.Min.Y+y*b.Dy()/h))
		}
	}
	return out
}
func blend(m *image.RGBA, x, y int, c color.RGBA) {
	if !image.Pt(x, y).In(m.Bounds()) {
		return
	}
	at := m.PixOffset(x, y)
	a := uint32(c.A)
	for ch, v := range []uint8{c.R, c.G, c.B} {
		m.Pix[at+ch] = uint8((uint32(v)*a + uint32(m.Pix[at+ch])*(255-a) + 127) / 255)
	}
	m.Pix[at+3] = uint8(a + (uint32(m.Pix[at+3])*(255-a)+127)/255)
}
func glow(m *image.RGBA, x, y, radius, alpha float64, c color.RGBA) {
	if radius <= 0 {
		return
	}
	for yy := int(y - radius); yy <= int(y+radius); yy++ {
		for xx := int(x - radius); xx <= int(x+radius); xx++ {
			d := math.Hypot(float64(xx)-x, float64(yy)-y) / radius
			if d >= 1 {
				continue
			}
			v := c
			v.A = uint8(math.Min(255, alpha*(1-d)*(1-d)))
			blend(m, xx, yy, v)
		}
	}
}
func stroke(m *image.RGBA, x1, y1, x2, y2, width, alpha float64, c color.RGBA) {
	n := max(1, int(math.Hypot(x2-x1, y2-y1)*1.3))
	for i := 0; i <= n; i++ {
		t := float64(i) / float64(n)
		glow(m, x1+(x2-x1)*t, y1+(y2-y1)*t, width, alpha, c)
	}
}

type event struct {
	EntryStep  uint64 `json:"entry_step"`
	ReturnStep uint64 `json:"return_step"`
	Entry      uint16 `json:"entry"`
	Native     string `json:"native_sha256"`
	File       string `json:"file"`
	Record     int    `json:"record"`
	XYWH       []int  `json:"xywh"`
	PNG        string `json:"png"`
}
type inputs struct {
	Background, Militia, Dwarf string
	Source, PON                []string
	Start, End                 uint64
	Events                     []event
}
type frame struct {
	Index      int
	Step       uint64
	SourcePose int
	PON        []int
	Native     string
	A, B       string
	ABox, BBox [4]int
}

func cropSave(m *image.RGBA, path string) [4]int {
	box := image.Rectangle{}
	for y := 0; y < m.Rect.Dy(); y++ {
		for x := 0; x < m.Rect.Dx(); x++ {
			if m.Pix[m.PixOffset(x, y)+3] > 0 {
				r := image.Rect(x, y, x+1, y+1)
				if box.Empty() {
					box = r
				} else {
					box = box.Union(r)
				}
			}
		}
	}
	if box.Empty() {
		box = image.Rect(0, 0, 1, 1)
	}
	out := image.NewRGBA(image.Rect(0, 0, box.Dx(), box.Dy()))
	draw.Draw(out, out.Bounds(), m, box.Min, draw.Src)
	save(path, out)
	return [4]int{box.Min.X, box.Min.Y, box.Dx(), box.Dy()}
}
func main() {
	input := flag.String("inputs", "", "frozen presentation inputs")
	out := flag.String("out", "", "new render directory")
	flag.Parse()
	if _, e := os.Stat(*out); !os.IsNotExist(e) {
		panic("output exists")
	}
	check(os.Mkdir(*out, 0755))
	var in inputs
	read(*input, &in)
	bg := scale(in.Background, 960, 600, false)
	militia := scale(in.Militia, 132, 150, true)
	dwarf := scale(in.Dwarf, 132, 150, true)
	draw.Draw(bg, image.Rect(276, 150, 408, 300), militia, image.Point{}, draw.Over)
	draw.Draw(bg, image.Rect(276, 300, 408, 450), dwarf, image.Point{}, draw.Over)
	save(filepath.Join(*out, "base.png"), bg)
	for i, p := range in.Source {
		save(filepath.Join(*out, fmt.Sprintf("source-%d.png", i)), scale(p, 132, 150, false))
	}
	for i, p := range in.PON {
		save(filepath.Join(*out, fmt.Sprintf("pon-%d.png", i)), scale(p, 132, 150, false))
	}
	var pon []event
	for _, ev := range in.Events {
		if ev.File == "PON.EGG" {
			pon = append(pon, ev)
		}
	}
	if len(pon) != 12 {
		panic("reviewed 12-call effect prefix required")
	}
	impact, last := pon[0].ReturnStep, pon[len(pon)-1].ReturnStep
	frames := []frame{}
	for i := 0; i <= 60; i++ {
		step := in.Start + (in.End-in.Start)*uint64(i)/60
		f := frame{Index: i, Step: step, SourcePose: 0, PON: []int{}, Native: "before.png"}
		for _, ev := range in.Events {
			if ev.ReturnStep == 0 || ev.ReturnStep > step {
				continue
			}
			if ev.PNG != "" {
				f.Native = ev.PNG
			}
			if ev.File == "MAN17.EGG" {
				f.SourcePose = ev.Record
			}
			if ev.File == "PON.EGG" && step <= last+100000 {
				f.PON = append(f.PON, ev.Record)
			}
		}
		if step == in.End {
			f.Native = "after.png"
		}
		a := image.NewRGBA(image.Rect(0, 0, 960, 600))
		b := image.NewRGBA(a.Bounds())
		if step >= impact && step <= last+100000 {
			t := float64(step-impact) / float64(last+100000-impact)
			strength := math.Sin(math.Pi * t)
			cx, cy := 342.0, 375.0
			for k := 0; k < 96; k++ {
				angle := float64(k)*math.Pi/48 + t*.65
				r := 100.0 + 8*math.Sin(t*math.Pi)
				alpha := strength * 230
				if k%12 < 8 {
					glow(a, cx+math.Cos(angle)*r, cy+math.Sin(angle)*r*.76, 6, alpha, color.RGBA{255, 216, 112, 0})
				}
			}
			for k := 0; k < 8; k++ {
				angle := float64(k)*math.Pi/4 + t*.5
				r := 90.0
				stroke(a, cx+math.Cos(angle)*r, cy+math.Sin(angle)*r*.76, cx+math.Cos(angle)*(r+19), cy+math.Sin(angle)*(r+19)*.76, 3.5, strength*130, color.RGBA{255, 216, 112, 0})
			}
			for k := 0; k < 24; k++ {
				angle := float64(k)*2.399963 + t*.6
				r := 55 + float64(k%7)*8 + t*22
				glow(a, cx+math.Cos(angle)*r, cy+math.Sin(angle)*r*.8, 5+float64(k%3), strength*220, color.RGBA{255, 106, 35, 0})
			}
		}
		draw.Draw(b, b.Bounds(), a, image.Point{}, draw.Src)
		if step > in.Start && step < pon[0].EntryStep {
			t := float64(step-in.Start) / float64(pon[0].EntryStep-in.Start)
			point := func(p float64) (float64, float64) { return 750 - 408*p, 300 + 75*p - 85*math.Sin(math.Pi*p) }
			for k := 30; k >= 0; k-- {
				p := t - float64(k)*.008
				if p < 0 {
					continue
				}
				x, y := point(p)
				glow(b, x, y, 26*(1-float64(k)/35), 200*(1-float64(k)/34), color.RGBA{248, 77, 28, 0})
				glow(b, x, y, 11*(1-float64(k)/35), 255*(1-float64(k)/34), color.RGBA{255, 231, 154, 0})
			}
		}
		f.A = fmt.Sprintf("a-%02d.png", i)
		f.B = fmt.Sprintf("b-%02d.png", i)
		f.ABox = cropSave(a, filepath.Join(*out, f.A))
		f.BBox = cropSave(b, filepath.Join(*out, f.B))
		frames = append(frames, f)
	}
	raw, e := json.MarshalIndent(map[string]any{"schema": 1, "renderer": "native Go raster operations; browser only blits prepared textures", "width": 960, "height": 600, "normalized_duration_ms": 3000, "frames": frames, "limits": []string{"Presentation prototype, not a production frame or same-state HD reconstruction.", "Original steps preserve event order; 3-second demo is not original wall-clock.", "No gameplay changes, live hooks, spell names, extra resource or hit inference."}}, "", "  ")
	check(e)
	check(os.WriteFile(filepath.Join(*out, "frames.json"), append(raw, '\n'), 0644))
}
