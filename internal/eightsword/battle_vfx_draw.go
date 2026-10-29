// Spec 030 READY. Approved procedural B kernel, sampled at twice prototype resolution.
package eightsword

import (
	"image"
	"image/color"
	"math"
)

func vfxBlend(m *image.RGBA, x, y int, c color.RGBA) {
	if !image.Pt(x, y).In(m.Rect) {
		return
	}
	at := m.PixOffset(x, y)
	a := uint32(c.A)
	for ch, v := range []uint8{c.R, c.G, c.B} {
		m.Pix[at+ch] = uint8((uint32(v)*a + uint32(m.Pix[at+ch])*(255-a) + 127) / 255)
	}
	m.Pix[at+3] = uint8(a + (uint32(m.Pix[at+3])*(255-a)+127)/255)
}
func vfxGlow(m *image.RGBA, x, y, r, alpha float64, c color.RGBA) {
	if r <= 0 {
		return
	}
	for yy := int((y - r) * 2); yy <= int((y+r)*2); yy++ {
		for xx := int((x - r) * 2); xx <= int((x+r)*2); xx++ {
			d := math.Hypot(float64(xx)/2-x, float64(yy)/2-y) / r
			if d >= 1 {
				continue
			}
			v := c
			v.A = uint8(math.Min(255, alpha*(1-d)*(1-d)))
			vfxBlend(m, xx, yy, v)
		}
	}
}
func vfxStroke(m *image.RGBA, x1, y1, x2, y2, w, alpha float64, c color.RGBA) {
	n := max(1, int(math.Hypot(x2-x1, y2-y1)*1.3))
	for i := 0; i <= n; i++ {
		t := float64(i) / float64(n)
		vfxGlow(m, x1+(x2-x1)*t, y1+(y2-y1)*t, w, alpha, c)
	}
}
func drawBattleVFX(phase string, t float64, source, target [2]int) *image.RGBA {
	if t < 0 || t > 1 {
		return nil
	}
	cx, cy := float64(target[0]+44)*1.5, float64(target[1]+25)*3
	var out *image.RGBA
	if phase == "impact" {
		bounds := image.Rect(int((cx-145)*2), int((cy-145)*2), int((cx+145)*2)+1, int((cy+145)*2)+1).Intersect(image.Rect(0, 0, 1920, 1200))
		if bounds.Empty() {
			return nil
		}
		out = image.NewRGBA(bounds)
		strength := math.Sin(math.Pi * t)
		for k := 0; k < 96; k++ {
			angle := float64(k)*math.Pi/48 + t*.65
			r := 100 + 8*math.Sin(t*math.Pi)
			if k%12 < 8 {
				vfxGlow(out, cx+math.Cos(angle)*r, cy+math.Sin(angle)*r*.76, 6, strength*230, color.RGBA{255, 216, 112, 0})
			}
		}
		for k := 0; k < 8; k++ {
			angle := float64(k)*math.Pi/4 + t*.5
			r := 90.0
			vfxStroke(out, cx+math.Cos(angle)*r, cy+math.Sin(angle)*r*.76, cx+math.Cos(angle)*(r+19), cy+math.Sin(angle)*(r+19)*.76, 3.5, strength*130, color.RGBA{255, 216, 112, 0})
		}
		for k := 0; k < 24; k++ {
			angle := float64(k)*2.399963 + t*.6
			r := 55 + float64(k%7)*8 + t*22
			vfxGlow(out, cx+math.Cos(angle)*r, cy+math.Sin(angle)*r*.8, 5+float64(k%3), strength*220, color.RGBA{255, 106, 35, 0})
		}
	} else if phase == "flight" {
		if t <= 0 {
			return nil
		}
		sx, sy := float64(source[0]+44)*1.5, float64(source[1]+25)*3
		point := func(p float64) (float64, float64) { return sx + (cx-sx)*p, sy + (cy-sy)*p - 85*math.Sin(math.Pi*p) }
		bounds := image.Rectangle{}
		for k := 0; k <= 30; k++ {
			p := t - float64(k)*.008
			if p < 0 {
				continue
			}
			x, y := point(p)
			r := image.Rect(int((x-27)*2), int((y-27)*2), int((x+27)*2)+1, int((y+27)*2)+1)
			if bounds.Empty() {
				bounds = r
			} else {
				bounds = bounds.Union(r)
			}
		}
		bounds = bounds.Intersect(image.Rect(0, 0, 1920, 1200))
		if bounds.Empty() {
			return nil
		}
		out = image.NewRGBA(bounds)
		for k := 30; k >= 0; k-- {
			p := t - float64(k)*.008
			if p < 0 {
				continue
			}
			x, y := point(p)
			vfxGlow(out, x, y, 26*(1-float64(k)/35), 200*(1-float64(k)/34), color.RGBA{248, 77, 28, 0})
			vfxGlow(out, x, y, 11*(1-float64(k)/35), 255*(1-float64(k)/34), color.RGBA{255, 231, 154, 0})
		}
	}
	return out
}
