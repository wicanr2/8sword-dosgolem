//go:build ignore

// 在 Docker/Xvfb 以 XTEST 真正送進視窗；不呼叫遊戲函式或注入 RAM。
package main

import (
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/jezek/xgb"
	"github.com/jezek/xgb/xproto"
	"github.com/jezek/xgb/xtest"
)

func check(err error) {
	if err != nil {
		panic(err)
	}
}

type driver struct {
	c            *xgb.Conn
	root, window xproto.Window
	out          string
	events       []map[string]any
}

func (d *driver) status() map[string]any {
	raw, err := os.ReadFile(filepath.Join(d.out, "gui-state.json"))
	if err != nil {
		return nil
	}
	var s map[string]any
	if json.Unmarshal(raw, &s) != nil {
		return nil
	}
	return s
}
func (d *driver) wait(label string, seconds int, predicate func(map[string]any) bool) {
	deadline := time.Now().Add(time.Duration(seconds) * time.Second)
	for time.Now().Before(deadline) {
		s := d.status()
		if s != nil && predicate(s) {
			return
		}
		time.Sleep(100 * time.Millisecond)
	}
	raw, _ := json.Marshal(d.status())
	panic(fmt.Sprintf("等待 %s 逾時：%s", label, raw))
}
func (d *driver) key(code byte, down bool) {
	kind := byte(3)
	if down {
		kind = 2
	}
	check(xtest.FakeInputChecked(d.c, kind, code, 0, d.root, 0, 0, 0).Check())
	d.events = append(d.events, map[string]any{"x11_keycode": code, "down": down, "at": time.Now().UTC().Format(time.RFC3339Nano), "status": d.status()})
}
func (d *driver) press(code byte) {
	before := d.status()["updates"].(float64)
	d.key(code, true)
	d.wait("按下鍵已處理", 15, func(s map[string]any) bool { return s["updates"].(float64) >= before+5 })
	before = d.status()["updates"].(float64)
	d.key(code, false)
	d.wait("放開鍵已處理", 15, func(s map[string]any) bool { return s["updates"].(float64) >= before+5 })
}
func (d *driver) scene(want string) {
	d.wait(want, 35, func(s map[string]any) bool { return s["scene"] == want })
	time.Sleep(250 * time.Millisecond)
}
func (d *driver) shot(name string) {
	d.c.Sync()
	geo, err := xproto.GetGeometry(d.c, xproto.Drawable(d.window)).Reply()
	check(err)
	reply, err := xproto.GetImage(d.c, 2, xproto.Drawable(d.window), 0, 0, geo.Width, geo.Height, 0xffffffff).Reply()
	check(err)
	if len(reply.Data) != int(geo.Width)*int(geo.Height)*4 {
		panic("Xvfb 回傳非預期 32bpp 格式")
	}
	im := image.NewRGBA(image.Rect(0, 0, int(geo.Width), int(geo.Height)))
	for i := 0; i < int(geo.Width)*int(geo.Height); i++ {
		v := binary.LittleEndian.Uint32(reply.Data[i*4 : i*4+4])
		im.Pix[i*4] = uint8(v >> 16)
		im.Pix[i*4+1] = uint8(v >> 8)
		im.Pix[i*4+2] = uint8(v)
		im.Pix[i*4+3] = 255
	}
	f, err := os.Create(filepath.Join(d.out, name+".png"))
	check(err)
	check(png.Encode(f, im))
	check(f.Close())
	fmt.Println("captured", name, geo.Width, geo.Height)
}
func main() {
	out := flag.String("out", "", "GUI receipt directory")
	flag.Parse()
	c, err := xgb.NewConn()
	check(err)
	defer c.Close()
	check(xtest.Init(c))
	setup := xproto.Setup(c)
	if setup.ImageByteOrder != 0 {
		panic("Xvfb 不是 little-endian")
	}
	root := setup.DefaultScreen(c).Root
	d := &driver{c: c, root: root, out: *out}
	titleAtom, err := xproto.InternAtom(c, false, uint16(len("_NET_WM_NAME")), "_NET_WM_NAME").Reply()
	check(err)
	deadline := time.Now().Add(30 * time.Second)
	for d.window == 0 && time.Now().Before(deadline) {
		tree, err := xproto.QueryTree(c, root).Reply()
		check(err)
		for _, w := range tree.Children {
			prop, err := xproto.GetProperty(c, false, w, titleAtom.Atom, 0, 0, 1024).Reply()
			if err == nil && strings.Contains(string(prop.Value), "神州八劍") {
				d.window = w
				break
			}
		}
		if d.window == 0 {
			time.Sleep(100 * time.Millisecond)
		}
	}
	if d.window == 0 {
		panic("找不到神州八劍視窗")
	}
	check(xproto.SetInputFocusChecked(c, 1, d.window, 0).Check())
	d.wait("顯示選擇", 30, func(s map[string]any) bool { return s["mode"] == float64(3) && s["bios_consumed"] == float64(0) })
	d.shot("01-display")
	d.press(10)
	d.wait("音效選擇", 20, func(s map[string]any) bool { return s["mode"] == float64(3) && s["bios_consumed"] == float64(1) })
	d.shot("02-sound")
	d.press(10)
	d.wait("片頭", 20, func(s map[string]any) bool { return s["mode"] != float64(3) })
	d.press(9) // 原版手冊允許以 Esc 略過片頭，未直接進入 PAM。
	d.scene("main-menu")
	d.shot("03-main-menu")
	d.press(116)
	d.press(36)
	d.scene("new-game-confirm")
	d.shot("04-confirm")
	d.press(36)
	d.scene("map")
	d.shot("05-map")
	d.press(67)
	d.scene("character")
	d.shot("06-character")
	d.press(9)
	d.scene("map")
	d.shot("07-return-map")
	d.press(73)
	d.scene("system-menu")
	d.shot("08-system-menu")
	d.press(9)
	d.scene("map")
	d.press(114)
	d.shot("09-moved")
	d.press(67)
	d.scene("character")
	d.shot("10-character-again")
	d.press(9)
	d.scene("map")
	d.shot("11-final-map")
	result := map[string]any{"status": "passed-input-path", "method": "XTEST actual Ebiten window; X11 GetImage captures", "events": d.events, "final_status": d.status(), "warning": "visual, coverage and guest-isolation audits are separate"}
	raw, err := json.MarshalIndent(result, "", "  ")
	check(err)
	check(os.WriteFile(filepath.Join(d.out, "gui-input-receipt.json"), append(raw, '\n'), 0644))
	d.key(37, true)
	d.key(24, true)
	time.Sleep(300 * time.Millisecond)
	d.key(24, false)
	d.key(37, false)
}
