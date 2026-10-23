package eightsword

import (
	"fmt"
	"image"
)

// Static opaque source tiles already include their ground. New RGBA art can
// therefore be flattened over the checked HD grass before entering the tracker.
// This does not apply to the native masked actor path. See spec 006.
func compositeStaticObject(source image.Image, background *image.RGBA) (*image.RGBA, error) {
	if background.Bounds() != image.Rect(0, 0, 192, 150) {
		return nil, fmt.Errorf("HD 靜物草底尺寸不符")
	}
	bounds := source.Bounds()
	sw, sh := bounds.Dx(), bounds.Dy()
	hasZero, hasOpaque := false, false
alphaCheck:
	for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			_, _, _, a := source.At(x, y).RGBA()
			hasZero = hasZero || a == 0
			hasOpaque = hasOpaque || a == 65535
			if hasZero && hasOpaque {
				break alphaCheck
			}
		}
	}
	if !hasZero || !hasOpaque {
		return nil, fmt.Errorf("HD 靜物須有透明背景及不透明主體")
	}
	out := image.NewRGBA(background.Bounds())
	for y := 0; y < 150; y++ {
		for x := 0; x < 192; x++ {
			sx, sy := max(0, (float64(x)+0.5)*float64(sw)/192-0.5), max(0, (float64(y)+0.5)*float64(sh)/150-0.5)
			x0, y0 := int(sx), int(sy)
			x1, y1 := min(x0+1, sw-1), min(y0+1, sh-1)
			fx, fy := sx-float64(x0), sy-float64(y0)
			points := [4]image.Point{{x0, y0}, {x1, y0}, {x0, y1}, {x1, y1}}
			weights := [4]float64{(1 - fx) * (1 - fy), fx * (1 - fy), (1 - fx) * fy, fx * fy}
			sum := [4]float64{}
			for n, p := range points {
				r, g, b, a := source.At(bounds.Min.X+p.X, bounds.Min.Y+p.Y).RGBA()
				if a <= 3*257 {
					continue
				}
				for c, v := range [4]uint32{r, g, b, a} {
					sum[c] += float64(v) * weights[n]
				}
			}
			alpha := sum[3] / 65535
			at := y*out.Stride + x*4
			bg := y*background.Stride + x*4
			for c := 0; c < 3; c++ {
				out.Pix[at+c] = uint8(max(0, min(255, sum[c]/257+float64(background.Pix[bg+c])*(1-alpha))) + 0.5)
			}
			out.Pix[at+3] = 255
		}
	}
	return out, nil
}
