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
func (d *driver) console(want string) {
	d.wait("啟動提示已真正呈現 "+want, 30, func(s map[string]any) bool {
		return s["console_stage"] == want && s["presented_console"] == want
	})
	first := d.status()["presented_frames"].(float64)
	d.wait("啟動提示持續呈現 "+want, 20, func(s map[string]any) bool {
		return s["console_stage"] == want && s["presented_console"] == want && s["presented_frames"].(float64) >= first+2
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
	flow := flag.String("flow", "inspect", "inspect, story, story-skip, story-fallback, intro, intro-skip, intro-fallback, boot, boot-fallback, save, reload, menus, music, fallback or art-fallback")
	actorWalk := flag.Bool("actor-walk", false, "save flow also walks four directions through normal input")
	showTitle := flag.Bool("intro-title", false, "wait for actual Noto title before Esc, including save/reload flows")
	showStory := flag.Bool("intro-story", false, "wait for actual Noto story before Esc, including save/reload flows")
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
	d.console("display-config")
	d.shot("01-display")
	bootInvalid := func(stage, name string) {
		before := d.status()["bios_consumed"].(float64)
		d.press(36)
		d.wait("原版已消耗無效 Return", 20, func(s map[string]any) bool { return s["bios_consumed"].(float64) > before })
		d.console(stage)
		d.shot(name)
	}
	if *flow == "boot" || *flow == "boot-fallback" {
		bootInvalid("display-config", "boot-invalid-display")
	}
	d.press(10)
	d.console("sound-config")
	d.shot("02-sound")
	if *flow == "boot" || *flow == "boot-fallback" {
		bootInvalid("sound-config", "boot-invalid-sound")
		if *flow == "boot-fallback" {
			s := d.status()
			if s["hd"] != false || s["asset_error"] != "字型圖片 SHA-256 不符" {
				panic("未觸發真實字型回退")
			}
			d.receipt(*flow)
			d.quit()
			return
		}
	}
	d.press(10)
	d.wait("片頭", 20, func(s map[string]any) bool { return s["mode"] != float64(3) })
	if *flow == "intro" || *flow == "intro-skip" || *showTitle {
		d.wait("Noto 標題已真正呈現", 35, func(s map[string]any) bool {
			return s["presented_intro"] == "title-noto" && s["intro_title"].(map[string]any)["stage"] == "title-noto"
		})
		first := d.status()["presented_frames"].(float64)
		d.wait("Noto 標題已持續呈現", 20, func(s map[string]any) bool {
			return s["presented_intro"] == "title-noto" && s["presented_frames"].(float64) >= first+2
		})
		titlePixels := append([]byte(nil), d.grab().Pix...)
		d.shot("intro-01-title")
		if *flow == "intro" {
			d.wait("下一張原版美術已完成", 35, func(s map[string]any) bool {
				stats := s["intro_title"].(map[string]any)["stats"].(map[string]any)
				return stats["Transitions"].(float64) > 0 && s["presented_intro"] == "" && s["intro_title"].(map[string]any)["stage"] == "" && s["mode"] != float64(3)
			})
			first = d.status()["presented_frames"].(float64)
			d.wait("下一張美術實際取代標題", 20, func(s map[string]any) bool {
				return s["presented_intro"] == "" && s["presented_frames"].(float64) >= first+2 && !bytes.Equal(d.grab().Pix, titlePixels)
			})
			d.shot("intro-02-next-art")
		}
	}
	if *flow == "intro-fallback" {
		if *nativeFrame == "" {
			panic("intro fallback requires independent native title PNG")
		}
		f, err := os.Open(*nativeFrame)
		check(err)
		expected, err := png.Decode(f)
		check(err)
		check(f.Close())
		shape := d.grab().Bounds()
		resized := image.NewRGBA(shape)
		for y := 0; y < shape.Dy(); y++ {
			for x := 0; x < shape.Dx(); x++ {
				r, g, b, _ := expected.At(x*expected.Bounds().Dx()/shape.Dx(), y*expected.Bounds().Dy()/shape.Dy()).RGBA()
				at := y*resized.Stride + x*4
				resized.Pix[at], resized.Pix[at+1], resized.Pix[at+2], resized.Pix[at+3] = uint8(r>>8), uint8(g>>8), uint8(b>>8), 255
			}
		}
		d.wait("真實壞片頭回到原版標題", 35, func(s map[string]any) bool {
			return s["hd"] == true && s["asset_error"] == "" && s["graphics_error"] == "" &&
				s["intro_title"].(map[string]any)["load_error"] == "HD 片頭圖片 SHA-256 不符" && bytes.Equal(d.grab().Pix, resized.Pix)
		})
		prop, err := xproto.GetProperty(c, false, d.window, titleAtom.Atom, 0, 0, 1024).Reply()
		check(err)
		if !strings.Contains(string(prop.Value), "HD 片頭載入失敗") {
			panic("片頭回退未顯示原因")
		}
		d.shot("intro-01-native-fallback")
	}
	if *flow == "music" {
		d.wait("片頭 HD 已實際輸出兩秒", 30, func(s map[string]any) bool {
			m, _ := s["music"].(map[string]any)
			return m["intro_bound"] == true && m["mode"] == "hd" && m["hd_frames"].(float64) >= 96000
		})
		d.shot("music-00-intro")
	}
	if *flow == "story" || *flow == "story-skip" || *showStory {
		pages := 5
		if *flow == "story-skip" || *showStory {
			pages = 1
		}
		for page := 1; page <= pages; page++ {
			page := page
			limit := 45
			if page == 1 {
				limit = 120
			} // 完整正常片頭先於故事，軟體繪圖可能低於即時。
			d.wait(fmt.Sprintf("故事第 %d 頁已真正呈現", page), limit, func(s map[string]any) bool {
				return s["presented_intro"] == "story-noto" && s["presented_story_pages"] == float64(page) && s["presented_story_calls"].(float64) >= float64((page-1)*192+36)
			})
			d.shot(fmt.Sprintf("story-%02d-page", page))
		}
		if *flow == "story" {
			d.scene("main-menu")
			stats := d.status()["intro_story"].(map[string]any)["stats"].(map[string]any)
			if stats["Calls"] != float64(888) || stats["Pages"] != float64(5) || stats["Timeouts"] != float64(0) || stats["Errors"] != nil {
				panic("故事未完整自然交接")
			}
		}
	}
	if *flow == "story-fallback" {
		d.wait("故事字型故障且其他 HD 保留", 30, func(s map[string]any) bool {
			return s["intro_story"].(map[string]any)["load_error"] == "故事字型圖片 SHA-256 不符" && s["hd"] == true && s["asset_error"] == "" && s["graphics_error"] == ""
		})
		if *nativeFrame == "" {
			panic("story fallback requires independent TIT6X background PNG")
		}
		f, err := os.Open(*nativeFrame)
		check(err)
		background, err := png.Decode(f)
		check(err)
		check(f.Close())
		d.wait("真正原版故事文字與獨立背景", 120, func(map[string]any) bool {
			im := d.grab()
			yellow := 0
			for y := 0; y < im.Bounds().Dy(); y++ {
				for x := 0; x < im.Bounds().Dx(); x++ {
					nx, ny := x*640/im.Bounds().Dx(), y*200/im.Bounds().Dy()
					at := y*im.Stride + x*4
					r, g, b := im.Pix[at], im.Pix[at+1], im.Pix[at+2]
					textCell := nx < 616 && nx%40 < 16 && ny >= 4 && ny < 195 && (ny-4)%16 < 15
					if !textCell {
						br, bg, bb, _ := background.At(nx, ny).RGBA()
						if r != uint8(br>>8) || g != uint8(bg>>8) || b != uint8(bb>>8) {
							return false
						}
					}
					if !((r == 0 && g == 0 && (b == 0 || b == 170)) || (r == 255 && g == 255 && (b == 85 || b == 255))) {
						return false
					}
					if r == 255 && g == 255 {
						yellow++
					}
				}
			}
			return yellow > 100
		})
		prop, err := xproto.GetProperty(c, false, d.window, titleAtom.Atom, 0, 0, 1024).Reply()
		check(err)
		if !strings.Contains(string(prop.Value), "HD 故事文字載入失敗") {
			panic("故事回退沒有原因")
		}
		d.shot("story-native-fallback")
	}
	if *flow != "story" {
		d.press(9)
	} // 原版 Esc，未直接進入 PAM。
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
	if *flow == "music" {
		music := func(s map[string]any) map[string]any { m, _ := s["music"].(map[string]any); return m }
		d.press(116)
		d.press(116)
		d.press(36)
		d.wait("音樂欣賞文字已出現", 25, func(s map[string]any) bool {
			for _, item := range s["strings"].([]any) {
				if item.(map[string]any)["Source"] == float64(758) {
					return true
				}
			}
			return false
		})
		first := d.status()["presented_frames"].(float64)
		d.wait("音樂欣賞已實際呈現", 15, func(s map[string]any) bool { return s["presented_frames"].(float64) >= first+2 })
		d.shot("music-01-catalog")
		beforeHD := music(d.status())["hd_frames"].(float64)
		d.press(36)
		d.wait("HD 幻已輸出兩秒", 25, func(s map[string]any) bool {
			m := music(s)
			return m["mode"] == "hd" && m["cue"] == float64(1) && m["hd_frames"].(float64) >= beforeHD+96000
		})
		d.shot("music-02-first")
		starts := music(d.status())["starts"].(float64)
		d.press(36)
		d.wait("同曲正常重啟", 20, func(s map[string]any) bool { return music(s)["starts"].(float64) > starts && music(s)["mode"] == "hd" })
		d.shot("music-03-restarted")
		starts = music(d.status())["starts"].(float64)
		d.press(116)
		if m := music(d.status()); m["mode"] != "hd" || m["cue"] != float64(1) || m["starts"] != starts {
			panic("移動反白改變音樂")
		}
		d.shot("music-04-highlight")
		d.press(36)
		d.wait("缺 HD 的遨遊使用原版", 20, func(s map[string]any) bool { m := music(s); return m["mode"] == "native" && m["cue"] == float64(2) })
		d.shot("music-05-native")
		d.press(9)
		d.wait("Esc 停止音樂", 20, func(s map[string]any) bool { m := music(s); return m["mode"] == "native" && m["cue"] == float64(0) })
		d.scene("main-menu")
		d.shot("music-06-returned")
	}
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
	if *flow == "menus" {
		// Fixed new-game pages, verified by normal original input. F5 prints
		// its position label after drawing the map; side-menu text is earlier.
		for _, page := range []struct {
			name    string
			key     byte
			side    float64
			sources []float64
		}{
			{"f2-army", 68, 1010, []float64{1330, 1338, 1346, 10380}},
			{"f4-magic", 70, 1050, []float64{10786}},
			{"f5-map", 71, 1070, []float64{1278, 1304}},
		} {
			before := d.status()["steps"].(float64)
			d.press(page.key)
			d.wait("本次選單內容完成", 35, func(s map[string]any) bool {
				seen := map[float64]bool{}
				for _, item := range s["strings"].([]any) {
					e := item.(map[string]any)
					if e["Step"].(float64) > before {
						seen[e["Source"].(float64)] = true
					}
				}
				for _, source := range page.sources {
					if !seen[source] {
						return false
					}
				}
				return true
			})
			lastFull, lastHalf, stable := float64(-1), float64(-1), float64(0)
			d.wait("選單文字完成且已持續呈現", 25, func(s map[string]any) bool {
				t := s["text"].(map[string]any)
				f, h := t["Full"].(float64), t["Half"].(float64)
				frame := s["presented_frames"].(float64)
				if f != lastFull || h != lastHalf {
					lastFull, lastHalf, stable = f, h, frame
					return false
				}
				return frame >= stable+3
			})
			d.shot("menus-" + page.name)
			raw, err := json.MarshalIndent(d.status(), "", "  ")
			check(err)
			check(os.WriteFile(filepath.Join(d.out, "menus-"+page.name+".json"), append(raw, '\n'), 0644))
			before = d.status()["steps"].(float64)
			d.press(9)
			d.wait("返回本次地圖指令", 25, func(s map[string]any) bool {
				for _, item := range s["strings"].([]any) {
					e := item.(map[string]any)
					if e["Step"].(float64) > before && e["Source"] == page.side {
						return true
					}
				}
				return false
			})
			d.scene("map")
		}
	}
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
