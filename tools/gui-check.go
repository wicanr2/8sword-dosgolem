//go:build ignore

// 在 Docker/Xvfb 以 XTEST 真正送進視窗；不呼叫遊戲函式或注入 RAM。
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
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
	raw, err := os.ReadFile(filepath.Join(d.out, "gui-final.json"))
	if err != nil {
		raw, err = os.ReadFile(filepath.Join(d.out, "gui-state.json"))
	}
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
	if want == "character" {
		d.wait("人物頁或已出現的遭遇確認", 35, func(s map[string]any) bool {
			return s["presented_scene"] == want || s["presented_scene"] == "encounter-confirm"
		})
		if d.status()["presented_scene"] == "encounter-confirm" {
			d.shot("encounter-before-character")
			before := d.status()["steps"].(float64)
			d.press(114)
			d.wait("遭遇確認已選否", 20, func(s map[string]any) bool {
				for _, item := range s["strings"].([]any) {
					ev := item.(map[string]any)
					if ev["Step"].(float64) > before && strings.TrimSpace(ev["Text"].(string)) == "否" {
						return true
					}
				}
				return false
			})
			d.shot("encounter-selected-no")
			d.press(36)
			d.scene("map")
			d.press(67)
		}
	}
	d.wait(want, 35, func(s map[string]any) bool { return s["presented_scene"] == want })
	first := d.status()["presented_frames"].(float64)
	d.wait("畫面已持續呈現 "+want, 20, func(s map[string]any) bool {
		return s["presented_scene"] == want && s["presented_frames"].(float64) >= first+2
	})
}
func (d *driver) grab() *image.RGBA {
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
	return im
}
func (d *driver) shot(name string) {
	im := d.grab()
	f, err := os.Create(filepath.Join(d.out, name+".png"))
	check(err)
	check(png.Encode(f, im))
	check(f.Close())
	fmt.Println("captured", name, im.Bounds().Dx(), im.Bounds().Dy())
}

func (d *driver) confirmation(after float64) {
	d.wait("本次確認文字", 35, func(s map[string]any) bool {
		events, _ := s["strings"].([]any)
		for _, item := range events {
			ev := item.(map[string]any)
			if ev["Source"] == float64(0x3252) && ev["Step"].(float64) > after {
				return true
			}
		}
		return false
	})
}

func digest(path string) string {
	raw, err := os.ReadFile(path)
	check(err)
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:])
}

func (d *driver) receipt(flow string) {
	result := map[string]any{"status": "passed-input-path", "flow": flow, "method": "XTEST actual Ebiten window; X11 GetImage captures", "events": d.events, "final_status": d.status(), "warning": "visual, coverage and guest-isolation audits are separate"}
	raw, err := json.MarshalIndent(result, "", "  ")
	check(err)
	check(os.WriteFile(filepath.Join(d.out, "gui-input-receipt.json"), append(raw, '\n'), 0644))
}

func (d *driver) quit() {
	d.key(37, true)
	d.key(24, true)
	time.Sleep(300 * time.Millisecond)
	d.key(24, false)
	d.key(37, false)
}

func main() {
	out := flag.String("out", "", "GUI receipt directory")
	flow := flag.String("flow", "inspect", "inspect, save, reload, fallback or art-fallback")
	actorWalk := flag.Bool("actor-walk", false, "save flow also walks four directions through normal input")
	saves := flag.String("saves", "", "save-cycle writable layer")
	nativeFrame := flag.String("native-frame", "", "fallback original reference PNG")
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
	if *flow == "fallback" || *flow == "art-fallback" {
		if *nativeFrame == "" {
			panic("fallback requires an independently captured native reference")
		}
		f, err := os.Open(*nativeFrame)
		check(err)
		expected, err := png.Decode(f)
		check(err)
		check(f.Close())
		failureTitle := "HD 字型載入失敗"
		if *flow == "art-fallback" {
			failureTitle = "HD 圖像載入失敗"
			d.wait("圖像回退且 Noto 保留", 35, func(s map[string]any) bool {
				return s["hd"] == true && s["asset_error"] == "" && s["graphics_error"] == "HD 圖像 grass-painted-r1.png SHA-256 不符" && s["pam_loaded"] == true
			})
			d.scene("main-menu")
		} else {
			d.wait("原版回退已載入", 35, func(s map[string]any) bool {
				return s["hd"] == false && s["asset_error"] == "字型圖片 SHA-256 不符" && s["pam_loaded"] == true
			})
		}
		shape := d.grab().Bounds()
		resized := image.NewRGBA(shape)
		for y := 0; y < shape.Dy(); y++ {
			for x := 0; x < shape.Dx(); x++ {
				r, g, b, _ := expected.At(x*expected.Bounds().Dx()/shape.Dx(), y*expected.Bounds().Dy()/shape.Dy()).RGBA()
				at := y*resized.Stride + x*4
				resized.Pix[at], resized.Pix[at+1], resized.Pix[at+2], resized.Pix[at+3] = uint8(r>>8), uint8(g>>8), uint8(b>>8), 255
			}
		}
		d.wait("真正回退主選單畫面", 35, func(map[string]any) bool { return bytes.Equal(d.grab().Pix, resized.Pix) })
		prop, err := xproto.GetProperty(c, false, d.window, titleAtom.Atom, 0, 0, 1024).Reply()
		check(err)
		if !strings.Contains(string(prop.Value), failureTitle) {
			panic("視窗標題未顯示回退原因")
		}
		d.shot("03-fallback-native-menu")
		d.receipt(*flow)
		d.quit()
		return
	}
	d.scene("main-menu")
	d.shot("03-main-menu")
	if *flow == "reload" {
		d.press(36) // 原版預設「繼續上次進度」。
		d.scene("map")
		d.shot("04-loaded-map")
		d.press(67)
		d.scene("character")
		d.shot("05-loaded-character")
		d.press(9)
		d.scene("map")
		d.shot("06-returned-map")
		d.receipt(*flow)
		d.quit()
		return
	}
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
	if *actorWalk && *flow == "save" {
		for _, direction := range []struct {
			name string
			key  byte
		}{{"left", 113}, {"up", 111}, {"down", 116}, {"right", 114}} {
			before := d.status()["graphics"].(map[string]any)["ActorCompletions"].(float64)
			d.press(direction.key)
			d.wait("主角四平面繪製完成或自然遭遇", 35, func(s map[string]any) bool {
				return s["graphics"].(map[string]any)["ActorCompletions"].(float64) > before || s["presented_scene"] == "encounter-confirm"
			})
			// The existing character path handles a real encounter by choosing
			// the original No option. Returning also checks actor restoration.
			d.press(67)
			d.scene("character")
			d.press(9)
			d.scene("map")
			d.shot("actor-direction-" + direction.name)
		}
	}
	if *flow == "save" {
		if *saves == "" {
			panic("save flow requires -saves")
		}
		d.press(73)
		d.scene("system-menu")
		before := d.status()["steps"].(float64)
		d.press(36)
		d.confirmation(before)
		d.shot("12-save-confirm")
		d.press(36)
		d.scene("map")
		path := filepath.Join(*saves, "gamedata.ay")
		d.wait("真正寫檔", 20, func(s map[string]any) bool {
			info, err := os.Stat(path)
			return err == nil && info.Size() == 2987
		})
		d.shot("13-saved-map")
		saved := map[string]any{"path": "scratch/gamedata.ay", "bytes": 2987, "sha256": digest(path), "status": d.status()}
		raw, err := json.MarshalIndent(saved, "", "  ")
		check(err)
		check(os.WriteFile(filepath.Join(d.out, "saved.json"), append(raw, '\n'), 0644))
		d.press(73)
		d.scene("system-menu")
		d.press(114)
		d.shot("14-quit-focused")
		before = d.status()["steps"].(float64)
		d.press(36)
		d.confirmation(before)
		d.shot("15-quit-confirm")
		d.key(36, true)
		d.wait("原版正常回 DOS", 35, func(s map[string]any) bool {
			return s["closed"] == true && s["exited"] == true && s["exit_code"] == float64(0)
		})
		d.receipt(*flow)
		return
	}
	d.receipt(*flow)
	d.quit()
}
