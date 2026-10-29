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
	if kind < 8 {
		return drawMapSpellColor(kind, t, anchor)
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

// Saturated map cues use a colored floor and a bright rim to remain readable
// over sunlit grass. Actor/text protection is applied by the compositor.
func drawMapSpellColor(kind int, t float64, anchor [2]int) *image.RGBA {
	colors := [8][3]float64{{255, 145, 38}, {255, 204, 32}, {45, 219, 255}, {222, 65, 255}, {74, 116, 255}, {255, 216, 103}, {20, 169, 255}, {174, 56, 255}}
	col := colors[kind]
	hot := [3]float64{}
	for c := range hot {
		hot[c] = col[c]*.55 + 255*.45
	}
	cx, cy := float64(anchor[0]*3), float64(anchor[1]*6)
	floor := cy + 105
	out := image.NewRGBA(image.Rect(max(0, int(cx)-330), max(0, int(cy)-300), min(1920, int(cx)+331), min(1200, int(cy)+331)))
	fade := min(1, t/.12) * min(1, (1-t)/.28)
	paint := func(x, y int, color [3]float64, alpha float64) {
		if alpha < .004 || !image.Pt(x, y).In(out.Bounds()) {
			return
		}
		alpha = min(1, alpha*fade)
		at := out.PixOffset(x, y)
		for c := 0; c < 3; c++ {
			out.Pix[at+c] = uint8(min(255, color[c]*alpha+float64(out.Pix[at+c])*(1-alpha)))
		}
		out.Pix[at+3] = uint8(min(255, 255*alpha+float64(out.Pix[at+3])*(1-alpha)))
	}
	rx, ry := 150+35*math.Sin(math.Pi*t), 65+15*math.Sin(math.Pi*t)
	for y := out.Rect.Min.Y; y < out.Rect.Max.Y; y++ {
		for x := out.Rect.Min.X; x < out.Rect.Max.X; x++ {
			dx, dy := (float64(x)-cx)/rx, (float64(y)-floor)/ry
			d := math.Sqrt(dx*dx + dy*dy)
			if d < 1.3 {
				paint(x, y, [3]float64{9, 13, 36}, .22*math.Exp(-d*d))
			}
			if d < 1 {
				paint(x, y, col, .32*(1-.6*d*d))
			}
			edge := (d - 1) * ry
			if math.Abs(edge) < 14 {
				paint(x, y, col, .88*math.Exp(-edge*edge/38))
				paint(x, y, hot, .7*math.Exp(-edge*edge/3))
			}
			// Soft color rises behind the figure; its actual actor cells stay intact.
			beam := (floor - float64(y)) / 260
			if beam > 0 && beam < 1 {
				paint(x, y, col, .18*math.Sin(beam*math.Pi)*math.Exp(-math.Pow((float64(x)-cx)/52, 2)))
			}
		}
	}
	stroke := func(x, y float64) {
		for yy := -6; yy <= 6; yy++ {
			for xx := -6; xx <= 6; xx++ {
				d := float64(xx*xx + yy*yy)
				paint(int(x)+xx, int(y)+yy, col, .40*math.Exp(-d/16))
				if d < 5 {
					paint(int(x)+xx, int(y)+yy, hot, .60)
				}
			}
		}
	}
	ring := func(x, y, rx, ry float64) {
		for i := 0; i < 360; i++ {
			a := float64(i) * math.Pi / 180
			stroke(x+math.Cos(a)*rx, y+math.Sin(a)*ry)
		}
	}
	switch kind {
	case 0:
		for i := 0; i < 200; i++ {
			a := float64(i) * math.Pi / 199
			stroke(cx+math.Cos(a)*140, cy-35-math.Sin(a)*100)
		}
	case 1:
		ring(cx, cy-35, 92, 92)
	case 2:
		for j := -2; j <= 2; j++ {
			for i := 0; i < 90; i++ {
				stroke(cx+float64(j)*42, cy+55-float64(i)*2)
			}
		}
	case 3:
		ring(cx-60, cy-20, 95, 135)
		ring(cx+60, cy-20, 95, 135)
	case 4:
		ring(cx, cy-20, 125, 125)
		for j := 0; j < 6; j++ {
			a := float64(j)*math.Pi/3 + t*.4
			for i := 35; i < 116; i++ {
				stroke(cx+math.Cos(a)*float64(i), cy-20+math.Sin(a)*float64(i))
			}
		}
	case 5:
		for j := -2; j <= 2; j++ {
			for i := 0; i < 100; i++ {
				u := float64(i) / 99
				stroke(cx+float64(j)*38+math.Sin(u*math.Pi)*45, cy+45-u*210)
			}
		}
	case 6:
		ring(cx, floor-35, 135, 45)
		ring(cx, floor-75, 100, 33)
	case 7:
		ring(cx, cy-25, 130, 180)
		ring(cx, cy-25, 112, 161)
	}
	for j := 0; j < 18; j++ {
		a := float64(j)*2.399963 + t*3
		d := 75 + float64(j%5)*20
		stroke(cx+math.Cos(a)*d, cy+math.Sin(a)*d*.7-90*t)
	}
	return out
}
