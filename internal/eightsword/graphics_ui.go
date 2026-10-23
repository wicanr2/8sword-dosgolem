package eightsword

import (
	"image"
	"image/color"
	"image/draw"
)

// Spec 005: fixed original fingerprints, not additional PMAP records.
func uiNativeSources() []nativeBitmap {
	return []nativeBitmap{
		{Index: 69, WidthBytes: 51, Height: 20, NativeSHA: "83f208ce4d25af7fee5e492367ad19e06838a6f66d78fbe37e0d081e41ffe8cb"},
		{Index: 70, WidthBytes: 56, Height: 75, NativeSHA: "20c0aa77c62fd139a730c314bc1e3b633a38a423c68eb3b5f87981f4c600b791"},
		{Index: 71, WidthBytes: 80, Height: 200, NativeSHA: "2df9ede8fd23ba02fbac60f635e81e504f6dd93bc2f143570ff97faccd573530"},
	}
}

var uiGold = color.RGBA{216, 174, 78, 255}
var uiLight = color.RGBA{255, 233, 159, 255}
var uiBronze = color.RGBA{105, 66, 25, 255}

func uiFill(out *image.RGBA, r image.Rectangle, c color.RGBA) {
	draw.Draw(out, r, &image.Uniform{C: c}, image.Point{}, draw.Src)
}

func uiOutline(out *image.RGBA, r image.Rectangle, width int, c color.RGBA) {
	uiFill(out, image.Rect(r.Min.X, r.Min.Y, r.Max.X, r.Min.Y+width), c)
	uiFill(out, image.Rect(r.Min.X, r.Max.Y-width, r.Max.X, r.Max.Y), c)
	uiFill(out, image.Rect(r.Min.X, r.Min.Y+width, r.Min.X+width, r.Max.Y-width), c)
	uiFill(out, image.Rect(r.Max.X-width, r.Min.Y+width, r.Max.X, r.Max.Y-width), c)
}

func uiJade(out *image.RGBA, r image.Rectangle, paper *image.RGBA) {
	r = r.Intersect(out.Bounds())
	for y := r.Min.Y; y < r.Max.Y; y++ {
		for x := r.Min.X; x < r.Max.X; x++ {
			c := paper.RGBAAt(x%paper.Bounds().Dx(), y%paper.Bounds().Dy())
			out.SetRGBA(x, y, color.RGBA{uint8(int(c.R)/2 + 4), uint8(int(c.G)*3/4 + 26), uint8(int(c.B)*3/4 + 18), 255})
		}
	}
}

// Rectilinear key ornament, drawn at physical resolution inside the gold band.
func uiKey(out *image.RGBA, x, y int) {
	uiOutline(out, image.Rect(x, y, x+16, y+16), 2, uiGold)
	uiFill(out, image.Rect(x+4, y+4, x+12, y+6), uiLight)
	uiFill(out, image.Rect(x+10, y+4, x+12, y+12), uiLight)
	uiFill(out, image.Rect(x+5, y+10, x+12, y+12), uiLight)
}

func uiBar(out *image.RGBA, r image.Rectangle, paper *image.RGBA, ornament bool) {
	uiFill(out, r, uiBronze)
	uiOutline(out, r.Inset(1), 2, uiLight)
	uiJade(out, r.Inset(4), paper)
	uiOutline(out, r.Inset(4), 1, uiGold)
	if ornament && r.Dx() > 80 && r.Dy() >= 24 {
		y := r.Min.Y + (r.Dy()-16)/2
		uiKey(out, r.Min.X+7, y)
		uiKey(out, r.Max.X-23, y)
	}
}

func uiLogical(r image.Rectangle) image.Rectangle {
	return image.Rect(r.Min.X*3, r.Min.Y*6, r.Max.X*3, r.Max.Y*6)
}

func makeUIBitmap(index int, paper *image.RGBA) *image.RGBA {
	w, h := 1224, 120
	if index == 70 {
		w, h = 1344, 450
	}
	if index == 71 {
		w, h = 1920, 1200
	}
	out := image.NewRGBA(image.Rect(0, 0, w, h))
	uiFill(out, out.Bounds(), color.RGBA{0, 0, 0, 255})
	if index == 69 {
		uiBar(out, out.Bounds(), paper, true)
		return out
	}
	if index == 70 {
		uiBar(out, out.Bounds(), paper, true)
		uiFill(out, image.Rect(18, 18, w-18, h-18), color.RGBA{85, 85, 85, 255})
		uiOutline(out, image.Rect(17, 17, w-17, h-17), 1, uiGold)
		return out
	}
	for _, r := range []image.Rectangle{
		image.Rect(0, 2, 8, 199), image.Rect(456, 2, 465, 199), image.Rect(632, 2, 640, 199),
		image.Rect(8, 2, 456, 12), image.Rect(8, 187, 456, 192),
	} {
		uiBar(out, uiLogical(r), paper, true)
	}
	for row := 0; row < 8; row++ {
		y := 2 + row*27
		uiBar(out, uiLogical(image.Rect(465, y, 632, y+7)), paper, true)
	}
	uiOutline(out, uiLogical(image.Rect(8, 191, 456, 198)), 3, uiGold)
	return out
}
