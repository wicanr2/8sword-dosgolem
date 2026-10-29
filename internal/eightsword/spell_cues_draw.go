package eightsword

import (
	"image"
	"math"
)

// Premultiplied light on transparent pixels. No guest/framebuffer dependency.
func drawSpellCue(kind int, t float64, anchor [2]int) *image.RGBA {
	if kind < 0 || kind >= 10 || t < 0 || t >= 1 {
		return nil
	}
	palettes := [10][3]float64{{232, 175, 94}, {255, 212, 116}, {177, 225, 241}, {213, 169, 255}, {146, 184, 255}, {247, 227, 170}, {119, 204, 250}, {201, 151, 255}, {157, 221, 255}, {151, 240, 204}}
	col := palettes[kind]
	cx, cy := float64(anchor[0]*3), float64(anchor[1]*6)
	out := image.NewRGBA(image.Rect(max(0, int(cx)-360), max(0, int(cy)-330), min(1920, int(cx)+361), min(1200, int(cy)+331)))
	fade := math.Sin(math.Pi * t)
	radius := 90 + 110*t
	glow := func(x, y, strength float64) {
		for yy := -7; yy <= 7; yy++ {
			for xx := -7; xx <= 7; xx++ {
				px, py := int(x)+xx, int(y)+yy
				if !image.Pt(px, py).In(out.Bounds()) {
					continue
				}
				a := strength * math.Exp(-float64(xx*xx+yy*yy)/15) * fade
				if a < .008 {
					continue
				}
				at := out.PixOffset(px, py)
				alpha := min(255, int(a*255))
				for c := 0; c < 3; c++ {
					out.Pix[at+c] = uint8(min(255, int(out.Pix[at+c])+int(col[c]*a)))
				}
				out.Pix[at+3] = uint8(min(255, int(out.Pix[at+3])+alpha))
			}
		}
	}
	ring := func(rx, ry, offset float64) {
		for i := 0; i < 360; i++ {
			a := float64(i)*math.Pi/180 + offset
			strength := .10 + .12*math.Pow(math.Sin(a*6+t*8), 2)
			glow(cx+math.Cos(a)*rx, cy+math.Sin(a)*ry, strength)
		}
	}
	switch kind {
	case 0: // raised arch, warm stone sparks
		for i := 0; i < 240; i++ {
			a := float64(i) * math.Pi / 239
			glow(cx+math.Cos(a)*radius, cy-math.Sin(a)*radius*.7, .24)
		}
	case 3, 7, 9: // paired leap / portal / duplication rings
		ring(radius, .95*radius, t*2)
		old := cx
		cx -= 55
		ring(radius*.65, radius*.72, -t*2)
		cx = old
	case 4: // six spokes around the suspended time dial
		ring(radius, radius, t*.15)
		for i := 0; i < 6; i++ {
			a := float64(i) * math.Pi / 3
			for k := .35; k < .95; k += .02 {
				glow(cx+math.Cos(a)*radius*k, cy+math.Sin(a)*radius*k, .17)
			}
		}
	case 5: // rising feather curves
		for j := 0; j < 5; j++ {
			for i := 0; i < 140; i++ {
				u := float64(i) / 139
				glow(cx+(float64(j)-2)*40+math.Sin(u*math.Pi)*55, cy+80-u*(180+100*t), .20)
			}
		}
	case 6: // water ripples
		ring(radius, radius*.32, 0)
		ring(radius*.70, radius*.22, 0)
		ring(radius*.4, radius*.12, 0)
	case 8: // crystalline six-point ring
		ring(radius, radius*.8, -t)
		for i := 0; i < 6; i++ {
			a := float64(i) * math.Pi / 3
			for k := .65; k < 1.3; k += .02 {
				glow(cx+math.Cos(a)*radius*k, cy+math.Sin(a)*radius*.8*k, .21)
			}
		}
	default:
		ring(radius, radius*.5, t)
		ring(radius*.75, radius*.35, -t)
	}
	for i := 0; i < 22; i++ {
		a := float64(i)*2.399963229728653 + t*2
		dist := radius * (.4 + float64(i%7)/8)
		glow(cx+math.Cos(a)*dist, cy+math.Sin(a)*dist*.6-80*t, .35)
	}
	return out
}
