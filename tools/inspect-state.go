// 研究工具：在固定 dosgolem 模組的 cmd/eightsword-inspect/ 下編譯。
// 唯讀檢視原版快照的顯示頁；不修改遊戲 RAM、指令或顯示起點。
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"image/color"
	"image/png"
	"os"
	"path/filepath"

	"github.com/wicanr2/dosgolem/internal/cpu"
	"github.com/wicanr2/dosgolem/internal/dos"
	"github.com/wicanr2/dosgolem/internal/machine"
	"github.com/wicanr2/dosgolem/internal/state"
)

func check(err error) {
	if err != nil {
		panic(err)
	}
}

func main() {
	source := flag.String("state", "", "固定版本原版快照")
	root := flag.String("root", "", "原版資料唯讀目錄")
	out := flag.String("out", "", "研究輸出目錄")
	until := flag.Uint64("until", 0, "續跑至絕對步數，0 不執行")
	flag.Parse()
	m := machine.New()
	d := dos.New(m, *root)
	d.Install()
	check(state.Load(*source, m, d))
	prior := m.CPU.IntHook
	m.CPU.IntHook = func(c *cpu.CPU, n uint8) bool {
		if n == 0x10 && m.CPU.R[cpu.AX]>>8 == 5 {
			fmt.Printf("INT10-AH05 step=%d runtime-CS:decoded-IP=%04X:%04X AX=%04X BDA-page-size=%04X\n",
				m.Steps, m.CPU.Seg[cpu.CS], m.CPU.IP, m.CPU.R[cpu.AX], m.Read16(0x44c))
		}
		return prior(c, n)
	}
	for m.Steps < *until {
		check(m.Step())
	}
	check(os.MkdirAll(*out, 0755))
	pal := make(color.Palette, 16)
	rgb := m.Palette()
	for i := range pal {
		c := rgb[m.VGA.DACIndex(uint8(i))]
		pal[i] = color.RGBA{c[0], c[1], c[2], 255}
	}
	counts := map[string]int{}
	for _, offset := range []int{0, 0x4000, 0x8000, 0xc000} {
		px := m.VGA.PixelsFrom(offset, 640, 200)
		n := 0
		for _, v := range px {
			if v != 0 {
				n++
			}
		}
		name := fmt.Sprintf("plane-offset-%04x", offset)
		counts[name] = n
		im := image.NewPaletted(image.Rect(0, 0, 640, 200), pal)
		copy(im.Pix, px)
		f, err := os.Create(filepath.Join(*out, name+".png"))
		check(err)
		check(png.Encode(f, im))
		check(f.Close())
	}
	report := map[string]any{
		"steps": m.Steps, "mode": m.VideoMode(), "crtc_display_start": m.VGA.DisplayStart(),
		"bda_page_size_0040_004c":        m.Read16(0x44c),
		"bda_page_start_0040_004e":       m.Read16(0x44e),
		"bda_active_page_0040_0062":      m.Read8(0x462),
		"nonzero_pixels_by_plane_offset": counts,
		"warning":                        "Diagnostic plane views only; not the player's visible screen; geometry assumes mode 0Eh",
	}
	b, err := json.MarshalIndent(report, "", "  ")
	check(err)
	check(os.WriteFile(filepath.Join(*out, "pages.json"), append(b, '\n'), 0644))
	fmt.Println(string(b))
}
