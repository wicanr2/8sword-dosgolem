package eightsword

import (
	"bytes"
	"image"
	"image/color"
	"image/draw"

	"github.com/wicanr2/dosgolem/oracle"
)

// Spec 010: these fingerprints identify actual DOS output, not key counts.
// Prompt bytes remain in the user's original PREDELLA.EXE.
const displayConsoleSHA = "c0d69f7b75f9457b2c1f191207340c522b813706969c8a96f463c6df7bc91179"
const soundConsoleSHA = "ed42cfa2eb548fe083c6b3670d142eef819c8bdec24a42ee1acc59fc57feca6c"

type bootConsole struct {
	stage, sha string
	lines      [][]byte
}

func readBootConsole(output []byte) bootConsole {
	if len(output) < 390 {
		return bootConsole{}
	}
	block := output[len(output)-390:]
	sha := hash(block)
	stage := ""
	switch sha {
	case displayConsoleSHA:
		stage = "display-config"
	case soundConsoleSHA:
		stage = "sound-config"
	default:
		return bootConsole{}
	}
	lines := bytes.Split(block, []byte{'\n', '\r'})
	if len(lines) != 7 || len(lines[6]) != 0 {
		return bootConsole{}
	}
	return bootConsole{stage, sha, lines[:6]}
}

func (e *Engine) bootConsole() bootConsole {
	if e.PAMLoaded || e.Exited || e.Oracle.VideoMode() != 3 ||
		e.Oracle.Word(oracle.Far(0, 0x44a)) != 80 || e.Oracle.Word(oracle.Far(0, 0x450)) != 0x0a00 {
		return bootConsole{}
	}
	return readBootConsole([]byte(e.Oracle.Console()))
}

func (e *Engine) ConsoleStage() string { return e.bootConsole().stage }

func (e *Engine) consoleFrame() *image.RGBA {
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	draw.Draw(out, out.Bounds(), image.Black, image.Point{}, draw.Src)
	if view := e.bootConsole(); view.stage != "" {
		for row, line := range view.lines {
			for col, ch := range line {
				e.consoleGlyph(out, col, row+10, ch)
			}
		}
		return out
	}
	for row, line := range e.Oracle.TextScreen() {
		for col, ch := range []byte(line) {
			if ch >= 32 && ch <= 126 {
				e.consoleGlyph(out, col, row, ch)
			}
		}
	}
	return out
}

func (e *Engine) consoleGlyph(out *image.RGBA, col, row int, ch byte) {
	cell := image.Rect(col*24, row*48, (col+1)*24, (row+1)*48)
	if ch >= 0x80 {
		consoleBox(out, cell.Min, ch)
		return
	}
	if ch == ' ' {
		return
	}
	if e.Assets != nil && e.HD {
		e.Assets.DrawRune(out, rune(ch), cell, [3]uint8{220, 224, 230})
		return
	}
	start := 0x24b38 + int(ch)*15
	if start+15 > len(e.PAM) {
		return
	}
	for y, bits := range e.PAM[start : start+15] {
		for x := 0; x < 8; x++ {
			if bits&(0x80>>uint(x)) != 0 {
				r := image.Rect(col*24+x*3, row*48+y*3, col*24+(x+1)*3, row*48+(y+1)*3)
				draw.Draw(out, r, consoleInk, image.Point{}, draw.Src)
			}
		}
	}
}

var consoleInk = image.NewUniform(color.RGBA{220, 224, 230, 255})

// Double-line CP437 frame cells; ASCII is drawn with the chosen font.
func consoleBox(out *image.RGBA, origin image.Point, ch byte) {
	line := func(x0, y0, x1, y1 int) {
		draw.Draw(out, image.Rect(x0, y0, x1, y1).Add(origin), consoleInk, image.Point{}, draw.Src)
	}
	switch ch {
	case 0xcd:
		line(0, 20, 24, 22)
		line(0, 27, 24, 29)
	case 0xba:
		line(8, 0, 10, 48)
		line(15, 0, 17, 48)
	case 0xc9:
		line(8, 20, 24, 22)
		line(15, 27, 24, 29)
		line(8, 20, 10, 48)
		line(15, 27, 17, 48)
	case 0xbb:
		line(0, 20, 17, 22)
		line(0, 27, 10, 29)
		line(15, 20, 17, 48)
		line(8, 27, 10, 48)
	case 0xc8:
		line(8, 27, 24, 29)
		line(15, 20, 24, 22)
		line(8, 0, 10, 29)
		line(15, 0, 17, 22)
	case 0xbc:
		line(0, 27, 17, 29)
		line(0, 20, 10, 22)
		line(15, 0, 17, 29)
		line(8, 0, 10, 22)
	}
}
