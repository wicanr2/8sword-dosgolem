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
	c             *xgb.Conn
	root, window  xproto.Window
	out           string
	events        []map[string]any
	forcedBattles int
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
			d.encounterChoice("否")
			d.shot("encounter-selected-no")
			decisionStep := d.status()["steps"].(float64)
			d.press(36)
			forced := false
			d.wait("拒戰後返回地圖或原版強制戰鬥", 40, func(s map[string]any) bool {
				if s["presented_scene"] == "map" {
					return true
				}
				for _, item := range s["strings"].([]any) {
					e := item.(map[string]any)
					if e["Step"].(float64) > decisionStep && e["Source"] == float64(17860) && s["music"].(map[string]any)["cue"] == float64(3) {
						forced = true
						return true
					}
				}
				return false
			})
			if forced {
				d.retreatForcedEncounter(decisionStep)
			}
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

// A refusal can still enter battle. Follow the observed ordinary retreat path;
// do not wait for a map that the original game has not restored.
func (d *driver) retreatForcedEncounter(after float64) {
	d.forcedBattles++
	prefix := fmt.Sprintf("forced-battle-%02d", d.forcedBattles)
	shot := func(name string) {
		d.shot(prefix + "-" + name)
		raw, err := json.MarshalIndent(d.status(), "", "  ")
		check(err)
		check(os.WriteFile(filepath.Join(d.out, prefix+"-"+name+".json"), append(raw, '\n'), 0644))
	}
	d.wait("被迫戰鬥的原版兵力已出字", 45, func(s map[string]any) bool {
		for _, item := range s["strings"].([]any) {
			e := item.(map[string]any)
			if e["Source"] == float64(36000) && e["Step"].(float64) > after {
				return true
			}
		}
		return false
	})
	shot("ready")
	visibleCounts := func(s map[string]any) bool {
		for _, source := range s["visible_sources"].([]any) {
			if source == float64(36000) {
				return true
			}
		}
		return false
	}
	if visibleCounts(d.status()) {
		d.press(37)
		d.wait("原版兵力顯示已結束", 25, func(s map[string]any) bool { return !visibleCounts(s) })
	}
	d.press(9)
	d.scene("battle-result")
	shot("result")
	d.press(36)
	d.scene("map")
	shot("returned")
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

func (d *driver) toolbarClick(x, y int) {
	geo, err := xproto.GetGeometry(d.c, xproto.Drawable(d.window)).Reply()
	check(err)
	pos, err := xproto.TranslateCoordinates(d.c, d.window, d.root, 0, 0).Reply()
	check(err)
	xx := pos.DstX + int16(x*int(geo.Width)/2944)
	yy := pos.DstY + int16(y*int(geo.Height)/1264)
	check(xtest.FakeInputChecked(d.c, 6, 0, 0, d.root, xx, yy, 0).Check())
	before := d.status()["updates"].(float64)
	check(xtest.FakeInputChecked(d.c, 4, 1, 0, d.root, 0, 0, 0).Check())
	d.wait("工具列滑鼠按下", 15, func(s map[string]any) bool { return s["updates"].(float64) >= before+3 })
	check(xtest.FakeInputChecked(d.c, 5, 1, 0, d.root, 0, 0, 0).Check())
	d.events = append(d.events, map[string]any{"toolbar_click": []int{x, y}, "status": d.status()})
	before = d.status()["updates"].(float64)
	d.wait("工具列滑鼠放開", 15, func(s map[string]any) bool { return s["updates"].(float64) >= before+3 })
}
func (d *driver) toolbar() {
	before := len(d.status()["input_events"].([]any))
	for _, row := range []struct {
		id string
		y  int
	}{{"lishu", 145}, {"caoshu", 202}, {"noto", 88}, {"lishu", 145}} {
		d.toolbarClick(700, 28)
		d.wait("字型選單", 15, func(s map[string]any) bool { return s["toolbar_menu"] == "font" })
		d.shot("toolbar-font-menu-" + row.id)
		d.toolbarClick(700, row.y)
		d.wait("工具列字型已呈現", 15, func(s map[string]any) bool { return s["presented_font_id"] == row.id && s["toolbar_menu"] == "" })
		d.shot("toolbar-font-" + row.id)
	}
	for _, row := range []struct {
		id string
		y  int
	}{{"cover", 145}, {"off", 202}, {"wings", 88}, {"cover", 145}} {
		d.toolbarClick(1300, 28)
		d.toolbarClick(1300, row.y)
		d.wait("海報切換", 15, func(s map[string]any) bool { return s["poster_id"] == row.id && s["toolbar_menu"] == "" })
		time.Sleep(500 * time.Millisecond)
		d.shot("toolbar-poster-" + row.id)
	}
	d.toolbarClick(700, 28)
	d.press(116)
	d.press(9)
	if d.status()["font_id"] != "lishu" || d.status()["toolbar_menu"] != "" {
		panic("取消字型選單改動選擇")
	}
	d.toolbarClick(1300, 28)
	d.press(116)
	d.press(36)
	d.wait("鍵盤選海報", 15, func(s map[string]any) bool { return s["poster_id"] == "cover" && s["toolbar_menu"] == "" })
	d.toolbarClick(700, 28)
	check(xproto.SetInputFocusChecked(d.c, 1, d.root, 0).Check())
	d.wait("失焦關閉工具列", 15, func(s map[string]any) bool { return s["toolbar_menu"] == "" })
	check(xproto.SetInputFocusChecked(d.c, 1, d.window, 0).Check())
	if len(d.status()["input_events"].([]any)) != before {
		panic("工具列將按鍵送入 DOS")
	}
	d.shot("toolbar-final-selection")
}

func (d *driver) sceneAfterHeroine() {
	d.wait("女主角後完整開場自然交接", 180, func(s map[string]any) bool { return s["presented_scene"] == "main-menu" })
	if d.status()["presented_heroine_pixels"] != float64(0) {
		panic("離開片頭後殘留女主角")
	}
	d.shot("heroine-natural-main-menu")
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

func (d *driver) army(prefix string) {
	for _, visit := range []string{"first", "again"} {
		before := d.status()["steps"].(float64)
		d.press(68) // F2 through XTEST.
		d.wait("本次民兵頁文字完成", 35, func(s map[string]any) bool {
			seen := map[float64]bool{}
			for _, item := range s["strings"].([]any) {
				e := item.(map[string]any)
				if e["Step"].(float64) > before {
					seen[e["Source"].(float64)] = true
				}
			}
			return seen[1330] && seen[1338] && seen[1346] && seen[10380]
		})
		lastFull, lastHalf, stable := float64(-1), float64(-1), float64(0)
		d.wait("民兵頁持續 Draw", 25, func(s map[string]any) bool {
			t := s["text"].(map[string]any)
			f, h, frame := t["Full"].(float64), t["Half"].(float64), s["presented_frames"].(float64)
			if f != lastFull || h != lastHalf {
				lastFull, lastHalf, stable = f, h, frame
				return false
			}
			return frame >= stable+3
		})
		d.shot(prefix + "-army-" + visit)
		raw, err := json.MarshalIndent(d.status(), "", "  ")
		check(err)
		check(os.WriteFile(filepath.Join(d.out, prefix+"-army-"+visit+".json"), append(raw, '\n'), 0644))
		before = d.status()["steps"].(float64)
		d.press(9)
		d.wait("本次 F2 返回地圖", 25, func(s map[string]any) bool {
			for _, item := range s["strings"].([]any) {
				e := item.(map[string]any)
				if e["Step"].(float64) > before && e["Source"] == float64(1010) {
					return true
				}
			}
			return false
		})
		d.scene("map")
		d.press(67)
		d.scene("character")
		d.shot(prefix + "-character-" + visit)
		d.press(9)
		d.scene("map")
	}
}

func (d *driver) encounterChoice(want string) {
	selection := func(s map[string]any) (string, float64) {
		value, step := "", float64(0)
		for _, item := range s["strings"].([]any) {
			e := item.(map[string]any)
			if e["Y"] == float64(133) && (e["Source"] == float64(66) || e["Source"] == float64(72)) {
				value, step = strings.TrimSpace(e["Text"].(string)), e["Step"].(float64)
			}
		}
		return value, step
	}
	current, _ := selection(d.status())
	if current == want {
		return
	}
	if current != "是" && current != "否" {
		panic("遭遇目前選項未確認")
	}
	before := d.status()["steps"].(float64)
	d.press(113)
	d.wait("遭遇實際選項 "+want, 20, func(s map[string]any) bool {
		value, step := selection(s)
		return value == want && step > before
	})
}

func (d *driver) battle() {
	shot := func(name string) {
		d.shot(name)
		raw, err := json.MarshalIndent(d.status(), "", "  ")
		check(err)
		check(os.WriteFile(filepath.Join(d.out, name+".json"), append(raw, '\n'), 0644))
	}
	stableText := func() {
		lastFull, lastHalf, stable := float64(-1), float64(-1), float64(0)
		d.wait("戰鬥文字完成且持續 Draw", 25, func(s map[string]any) bool {
			t := s["text"].(map[string]any)
			f, h, frame := t["Full"].(float64), t["Half"].(float64), s["presented_frames"].(float64)
			if f != lastFull || h != lastHalf {
				lastFull, lastHalf, stable = f, h, frame
				return false
			}
			return frame >= stable+3
		})
	}
	for n := 0; n < 128 && d.status()["presented_scene"] != "encounter-confirm"; n++ {
		key := byte(114)
		if n%2 == 1 {
			key = 113
		}
		d.press(key)
	}
	d.scene("encounter-confirm")
	shot("battle-01-first-encounter")
	d.encounterChoice("是")
	shot("battle-02-selected-yes")
	before := d.status()["steps"].(float64)
	d.press(36)
	d.wait("正常戰場已印兵力", 45, func(s map[string]any) bool {
		for _, item := range s["strings"].([]any) {
			e := item.(map[string]any)
			if e["Step"].(float64) > before && e["Source"] == float64(36000) {
				return s["music"].(map[string]any)["cue"] == float64(3)
			}
		}
		return false
	})
	stableText()
	shot("battle-03-ready")
	before = d.status()["steps"].(float64)
	d.press(55) // V: original troop-count display.
	d.wait("V 重新印出兵力", 20, func(s map[string]any) bool {
		for _, item := range s["strings"].([]any) {
			e := item.(map[string]any)
			if e["Step"].(float64) > before && e["Source"] == float64(36000) {
				return true
			}
		}
		return false
	})
	stableText()
	shot("battle-04-counts")
	controlEvents := func() []map[string]any {
		var out []map[string]any
		for _, item := range d.status()["input_events"].([]any) {
			e := item.(map[string]any)
			if e["Scan"] == float64(0x1d) {
				out = append(out, e)
			}
		}
		return out
	}
	edge := func(key byte, down bool) {
		before := d.status()["updates"].(float64)
		d.key(key, down)
		d.wait("Ctrl 實際按鍵已處理", 15, func(s map[string]any) bool { return s["updates"].(float64) >= before+5 })
	}
	beforeControl := len(controlEvents())
	edge(37, true)
	edge(105, true)
	edge(37, false)
	control := controlEvents()
	if len(control) != beforeControl+1 || control[len(control)-1]["Down"] != true {
		panic("右 Ctrl 仍按住時提前送出 DOS 放開")
	}
	edge(105, false)
	control = controlEvents()
	if len(control) != beforeControl+2 || control[len(control)-1]["Down"] != false {
		panic("最後一個 Ctrl 放開沒有送達 DOS")
	}
	d.wait("兵力數字結束後可繼續操作", 25, func(s map[string]any) bool {
		for _, source := range s["visible_sources"].([]any) {
			if source == float64(36000) {
				return false
			}
		}
		return true
	})
	shot("battle-05-active-unit")
	d.press(9)
	d.scene("battle-result")
	stableText()
	shot("battle-06-result")
	d.press(36)
	d.scene("map")
	shot("battle-07-result-closed")
}

func main() {
	out := flag.String("out", "", "GUI receipt directory")
	flow := flag.String("flow", "inspect", "inspect, captions, captions-fallback, story, story-skip, story-fallback, intro, intro-skip, intro-fallback, boot, boot-fallback, save, reload, menus, music, fallback or art-fallback")
	actorWalk := flag.Bool("actor-walk", false, "save flow also walks four directions through normal input")
	armyCheck := flag.Bool("army-check", false, "visit F2 twice through F1 before save and after reload")
	battleCheck := flag.Bool("battle-check", false, "first natural encounter, V/Ctrl, retreat and acknowledge result before normal save")
	showTitle := flag.Bool("intro-title", false, "wait for actual Noto title before Esc, including save/reload flows")
	showPublisher := flag.Bool("intro-publisher", false, "wait for actual publisher wordmarks before Esc")
	publisherCycle := flag.Bool("publisher-font-cycle", false, "switch one actual F10 font while publisher is visible")
	showStory := flag.Bool("intro-story", false, "wait for actual Noto story before Esc, including save/reload flows")
	showCaptions := flag.Bool("intro-captions", false, "wait for actual museum Noto before Esc, including save/reload flows")
	showHeroine := flag.Bool("intro-heroine", false, "wait for actual HD heroine Draw and natural full intro")
	fontCycle := flag.Bool("font-cycle", false, "use real F10 to cycle fonts before normal save and verify preference on reload")
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
	if *showHeroine {
		d.wait("女主角 HD 已真正 Draw", 180, func(s map[string]any) bool {
			if n, ok := s["presented_heroine_pixels"].(float64); ok && n > 0 {
				return true
			}
			b, err := os.ReadFile(filepath.Join(d.out, "intro-draw.jsonl"))
			if err != nil {
				return false
			}
			for _, line := range bytes.Split(b, []byte{'\n'}) {
				var j struct {
					Pixels int `json:"heroine_pixels"`
				}
				if json.Unmarshal(line, &j) == nil && j.Pixels > 0 {
					return true
				}
			}
			return false
		})
		if n, _ := d.status()["presented_heroine_pixels"].(float64); n > 0 {
			d.shot("heroine-actual-visible")
		} else {
			fmt.Println("女主角特寫已在實際 Draw 日誌呈現，由完整逐幀串流擷取。")
		}
		d.sceneAfterHeroine()
	}
	if *flow == "publisher" || *flow == "publisher-skip" || *showPublisher {
		d.wait("發行商字圖已真正呈現", 35, func(s map[string]any) bool { return s["presented_intro"] == "publisher-noto" })
		d.shot("publisher-01-visible")
		if *publisherCycle {
			choices := d.status()["font_choices"].([]any)
			current := d.status()["font_id"].(string)
			next := ""
			for i, c := range choices {
				if c.(map[string]any)["id"] == current {
					next = choices[(i+1)%len(choices)].(map[string]any)["id"].(string)
				}
			}
			d.key(76, true)
			d.wait("發行商 F10 已處理", 15, func(s map[string]any) bool { return s["font_id"] == next })
			d.key(76, false)
			d.wait("發行商 F10 字型已呈現", 15, func(s map[string]any) bool {
				// 摘要每批更新可能漏掉短暫 Draw；逐幀紀錄才是這一幕的收據。
				lines, err := os.ReadFile(filepath.Join(d.out, "intro-draw.jsonl"))
				if err != nil {
					return false
				}
				for _, line := range bytes.Split(lines, []byte{'\n'}) {
					var frame struct{ Stage, FontID string }
					var record map[string]any
					if json.Unmarshal(line, &record) == nil {
						frame.Stage, _ = record["stage"].(string)
						frame.FontID, _ = record["font_id"].(string)
						if frame.Stage == "publisher-noto" && frame.FontID == next {
							return true
						}
					}
				}
				return false
			})
			d.shot("publisher-02-after-font-key")
		}
		if *flow == "publisher" {
			d.wait("發行商自然轉至標題", 35, func(s map[string]any) bool { return s["presented_intro"] == "title-noto" })
			d.shot("publisher-03-next-title")
		}
	}
	if *flow == "publisher-fallback" {
		if *nativeFrame == "" {
			panic("publisher fallback requires independent native PNG")
		}
		f, err := os.Open(*nativeFrame)
		check(err)
		source, err := png.Decode(f)
		check(err)
		check(f.Close())
		shape := d.grab().Bounds()
		expected := image.NewRGBA(shape)
		for y := 0; y < shape.Dy(); y++ {
			for x := 0; x < shape.Dx(); x++ {
				r, g, b, _ := source.At(x*640/shape.Dx(), y*200/shape.Dy()).RGBA()
				at := y*expected.Stride + x*4
				expected.Pix[at], expected.Pix[at+1], expected.Pix[at+2], expected.Pix[at+3] = uint8(r>>8), uint8(g>>8), uint8(b>>8), 255
			}
		}
		d.wait("真實壞字圖回原發行商畫面", 35, func(s map[string]any) bool {
			return s["intro_publisher"].(map[string]any)["load_error"] != "" && s["hd"] == true && bytes.Equal(expected.Pix, d.grab().Pix)
		})
		d.shot("publisher-native-fallback")
	}
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
	if *flow == "captions" || *showCaptions {
		sources := []uint16{0x42, 0x6a, 0x92, 0xba}
		if *showCaptions {
			sources = sources[:1]
		}
		for _, source := range sources {
			source := source
			d.wait(fmt.Sprintf("製作名單 %04X 已真正呈現", source), 80, func(s map[string]any) bool {
				if s["presented_intro"] == "captions-noto" && s["presented_caption_source"] == float64(source) {
					return true
				}
				// 摘要可能略過短暫 Draw。逐幀日誌只在真正 Draw 後記錄，
				// 不用「已請求字幕」或背景頁繪字代替已呈現的證據。
				lines, err := os.ReadFile(filepath.Join(d.out, "intro-draw.jsonl"))
				if err != nil {
					return false
				}
				for _, line := range bytes.Split(lines, []byte{'\n'}) {
					var frame struct {
						Stage         string `json:"stage"`
						CaptionSource uint16 `json:"caption_source"`
					}
					if json.Unmarshal(line, &frame) == nil && frame.Stage == "captions-noto" && frame.CaptionSource == source {
						return true
					}
				}
				return false
			})
			if s := d.status(); s["presented_intro"] == "captions-noto" && s["presented_caption_source"] == float64(source) {
				d.shot(fmt.Sprintf("captions-%04x", source))
			} else {
				fmt.Printf("製作名單 %04X 已在逐幀日誌呈現；目前已轉場，略過同名視窗截圖。\n", source)
			}
		}
		if *flow == "captions" {
			d.wait("博物館後續動畫與五頁故事自然結束", 180, func(s map[string]any) bool { return s["presented_scene"] == "main-menu" })
		}
	}
	if *flow == "captions-fallback" {
		if *nativeFrame == "" {
			panic("caption fallback requires independent native caption PNG")
		}
		f, err := os.Open(*nativeFrame)
		check(err)
		native, err := png.Decode(f)
		check(err)
		check(f.Close())
		d.wait("真實壞 atlas 回原版製作名單", 80, func(s map[string]any) bool {
			if s["hd"] != true || s["asset_error"] != "" || s["graphics_error"] != "" || s["intro_story"].(map[string]any)["load_error"] != "故事字型圖片 SHA-256 不符" {
				return false
			}
			im := d.grab()
			for y := im.Bounds().Dy() * 160 / 200; y < im.Bounds().Dy()*175/200; y++ {
				for x := 0; x < im.Bounds().Dx(); x++ {
					r, g, b, _ := native.At(x*640/im.Bounds().Dx(), y*200/im.Bounds().Dy()).RGBA()
					at := y*im.Stride + x*4
					if im.Pix[at] != uint8(r>>8) || im.Pix[at+1] != uint8(g>>8) || im.Pix[at+2] != uint8(b>>8) {
						return false
					}
				}
			}
			return true
		})
		d.shot("captions-native-fallback")
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
	if *flow != "story" && *flow != "captions" && !*showHeroine {
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
	if *flow == "heroine-fallback" {
		if d.status()["heroine_error"] == "" || d.status()["graphics_error"] != "" || d.status()["font_error"] != "" || d.status()["asset_error"] != "" || d.status()["presented_heroine_pixels"] != float64(0) {
			panic("女主角故障未隔離")
		}
		d.shot("heroine-real-corrupt-fallback")
		d.receipt(*flow)
		d.quit()
		return
	}
	if *flow == "toolbar-fallback" {
		if d.status()["poster_id"] != "off" || d.status()["poster_error"] == "" || d.status()["font_name"] != "教育部隸書" || d.status()["toolbar_error"] != "" {
			panic("海報故障未隔離")
		}
		d.shot("toolbar-real-corrupt-fallback")
		d.receipt(*flow)
		d.quit()
		return
	}
	if *flow == "toolbar-reload" {
		if d.status()["font_id"] != "lishu" || d.status()["font_name"] != "教育部隸書" || d.status()["poster_id"] != "cover" {
			panic("工具列偏好沒有恢復")
		}
		d.shot("toolbar-preferences-restored")
		d.receipt(*flow)
		d.quit()
		return
	}
	if *flow == "toolbar" {
		d.toolbar()
	}
	if *fontCycle {
		if *flow == "reload" {
			if d.status()["font_id"] != "caoshu" {
				panic("font preference was not retained on cold boot")
			}
			d.shot("font-restored-caoshu")
		} else {
			native := append([]byte(nil), d.grab().Pix...)
			for _, id := range []string{"lishu", "caoshu", "noto", "lishu", "caoshu"} {
				d.press(76)
				d.wait("F10 字型已呈現", 20, func(s map[string]any) bool { return s["font_id"] == id && s["presented_scene"] == "main-menu" })
				first := d.status()["presented_frames"].(float64)
				d.wait("F10 後完成 Draw", 15, func(s map[string]any) bool { return s["presented_frames"].(float64) >= first+2 })
				if id == "noto" && !bytes.Equal(native, d.grab().Pix) {
					panic("Noto menu did not restore exact visible pixels")
				}
				d.shot("font-" + id)
			}
			pref, err := os.ReadFile(filepath.Join(filepath.Dir(d.out), "settings.json"))
			check(err)
			if !bytes.Contains(pref, []byte("caoshu")) {
				panic("F10 preference not written")
			}
		}
	}
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
		if *armyCheck {
			d.army("loaded")
		}
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
	if *flow == "toolbar" {
		if d.status()["font_name"] != "教育部隸書" {
			panic("新字型來源未載入")
		}
		d.army("toolbar")
		d.press(67)
		d.scene("character")
		d.shot("toolbar-moe-character")
		d.press(9)
		d.scene("map")
		d.shot("toolbar-return-map")
		d.receipt(*flow)
		d.quit()
		return
	}
	if *battleCheck && *flow == "save" {
		d.battle()
	}
	if *armyCheck {
		d.army("new")
	}
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
