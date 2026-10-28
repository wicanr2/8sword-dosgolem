package eightsword

import (
	"bytes"
	"image"
	"image/color"
	"image/draw"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func testToolbar(t *testing.T) *PosterToolbar {
	t.Helper()
	dir := os.Getenv("EIGHTSWORD_TEST_POSTER_ASSETS")
	if dir == "" {
		t.Skip("需要真實海報素材")
	}
	v, err := LoadPosterToolbar(dir, []FontChoice{{ID: "noto"}, {ID: "lishu"}, {ID: "caoshu"}})
	if err != nil || v == nil || v.Error != "" {
		t.Fatalf("load: %v %#v", err, v)
	}
	v.SyncFont("noto")
	return v
}
func TestPosterCentralPixelsAndInterruptedFade(t *testing.T) {
	v := testToolbar(t)
	now := time.Unix(1000, 0)
	im := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	draw.Draw(im, im.Bounds(), image.NewUniform(color.RGBA{71, 83, 97, 255}), image.Point{}, draw.Src)
	check := func(f *image.RGBA) {
		t.Helper()
		for y := 0; y < 1200; y++ {
			i := f.PixOffset(512, 64+y)
			if !bytes.Equal(f.Pix[i:i+1920*4], im.Pix[y*im.Stride:y*im.Stride+1920*4]) {
				t.Fatal("海報改動中央遊戲")
			}
		}
	}
	first := v.Frame(im, now)
	check(first)
	if v.Frame(im, now) != first {
		t.Fatal("穩定畫面沒有快取")
	}
	copyFrame := image.NewRGBA(im.Bounds())
	copy(copyFrame.Pix, im.Pix)
	if v.Frame(copyFrame, now) != first || v.CachedPixels != 1 {
		t.Fatal("相同畫素的新原版緩衝區重複上傳")
	}
	copyFrame2 := image.NewRGBA(im.Bounds())
	copy(copyFrame2.Pix, im.Pix)
	copyFrame2.Pix[0]++
	if v.Frame(copyFrame2, now) == first {
		t.Fatal("真實畫素變更被快取吞掉")
	}
	if err := v.SetPoster("cover", now); err != nil {
		t.Fatal(err)
	}
	check(v.Frame(im, now))
	middle := v.panel(now.Add(200 * time.Millisecond))
	if bytes.Equal(middle.Pix, v.target.Pix) {
		t.Fatal("沒有中間淡入幀")
	}
	if err := v.SetPoster("off", now.Add(200*time.Millisecond)); err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(v.panel(now.Add(200*time.Millisecond)).Pix, middle.Pix) {
		t.Fatal("中斷淡入跳回舊圖")
	}
	check(v.Frame(im, now.Add(600*time.Millisecond)))
	if v.from != nil {
		t.Fatal("淡入沒有完成")
	}
}
func TestPosterToolbarConsumesMenusAndPreferences(t *testing.T) {
	v := testToolbar(t)
	a := v.Input(620, 24, true, "")
	if !a.Consumed || v.Menu != "font" {
		t.Fatal("字型選單未開啟")
	}
	a = v.Input(0, 0, false, "down")
	if !a.Consumed {
		t.Fatal("方向鍵未攔截")
	}
	a = v.Input(0, 0, false, "enter")
	if !a.Consumed || a.Font != "lishu" || v.Menu != "" {
		t.Fatal(a)
	}
	v.Input(1230, 24, true, "")
	v.Input(0, 0, false, "down")
	a = v.Input(0, 0, false, "escape")
	if !a.Consumed || a.Poster != "" || v.ID != "wings" {
		t.Fatal("取消改動海報")
	}
	v.Input(1230, 24, true, "")
	a = v.Input(1220, 190, true, "")
	if a.Poster != "off" || !a.Consumed {
		t.Fatal(a)
	}
	p := filepath.Join(t.TempDir(), "settings.json.poster.json")
	for _, id := range []string{"wings", "cover", "off"} {
		if err := SavePosterPreference(p, id); err != nil {
			t.Fatal(err)
		}
		got, err := LoadPosterPreference(p)
		if err != nil || got != id {
			t.Fatal(got, err)
		}
	}
	if SavePosterPreference(p, "../bad") == nil {
		t.Fatal("接受非法 ID")
	}
	os.WriteFile(p, []byte(`{"schema":1,"poster":"off","extra":true}`), 0600)
	if got, err := LoadPosterPreference(p); err == nil || got != "wings" {
		t.Fatal("壞設定未回退")
	}
}
func TestPosterRealCorruptionAndLegacyAssets(t *testing.T) {
	dir := os.Getenv("EIGHTSWORD_TEST_POSTER_ASSETS")
	if dir == "" {
		t.Skip("需要真實海報素材")
	}
	tmp := t.TempDir()
	for _, n := range []string{"poster-toolbar.json", "poster-toolbar-font.png", "poster-cover.png", "poster-wings.png"} {
		b, err := os.ReadFile(filepath.Join(dir, n))
		if err != nil {
			t.Fatal(err)
		}
		if err = os.WriteFile(filepath.Join(tmp, n), b, 0600); err != nil {
			t.Fatal(err)
		}
	}
	os.WriteFile(filepath.Join(tmp, "poster-cover.png"), []byte("broken real PNG"), 0600)
	v, err := LoadPosterToolbar(tmp, []FontChoice{{ID: "noto"}})
	if err != nil || v == nil || v.ID != "off" || v.Error == "" || v.panels["wings"] != nil {
		t.Fatal("海報損壞未整組關閉", err)
	}
	os.WriteFile(filepath.Join(tmp, "poster-toolbar-font.png"), []byte("broken atlas"), 0600)
	if _, err = LoadPosterToolbar(tmp, []FontChoice{{ID: "noto"}}); err == nil {
		t.Fatal("壞字集未拒用")
	}
	if v, err = LoadPosterToolbar(t.TempDir(), nil); err != nil || v != nil {
		t.Fatal("舊素材組不相容")
	}
}

func TestPosterBattleAISelectionAndPixels(t *testing.T) {
	v := testToolbar(t)
	im := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	base := v.Frame(im, time.Unix(1000, 0))
	v.SyncBattleAI("target")
	changed := v.Frame(im, time.Unix(1000, 0))
	if base == changed {
		t.Fatal("AI模式標示沒有更新")
	}
	for y := 0; y < PosterHeight; y++ {
		for x := 0; x < PosterWidth; x++ {
			if !image.Pt(x, y).In(image.Rect(1700, 8, 2076, 56)) && base.RGBAAt(x, y) != changed.RGBAAt(x, y) {
				t.Fatal("切換標示改到AI按鈕外", x, y)
			}
		}
	}
	if a := v.Input(1800, 24, true, ""); !a.Consumed || v.Menu != "ai" || v.Selected != 1 {
		t.Fatal("開啟未選中目前策略AI", a)
	}
	v.Input(0, 0, false, "down")
	if v.Selected != 0 {
		t.Fatal("兩選項循環越界")
	}
	a := v.Input(0, 0, false, "enter")
	if !a.Consumed || a.BattleAI != "native" || a.Font != "" || a.Poster != "" || v.Menu != "" {
		t.Fatal("確認未單獨輸出AI模式", a)
	}
	v.SyncBattleAI("native")
	v.Input(1800, 24, true, "")
	v.Input(0, 0, false, "down")
	if a := v.Input(0, 0, false, "escape"); !a.Consumed || a.BattleAI != "" || v.battleAI != "native" {
		t.Fatal("取消改動AI", a)
	}
	v.Input(1800, 24, true, "")
	if a := v.Input(1800, 140, true, ""); !a.Consumed || a.BattleAI != "target" {
		t.Fatal("滑鼠第二列未選中策略AI", a)
	}
	for _, mode := range []string{"native", "target"} {
		label := v.battleAILabel(mode) + "  v"
		x := 1720
		for _, c := range label {
			if _, ok := v.glyphs[c]; !ok {
				t.Fatalf("缺字 %q", c)
			}
			if c < 128 {
				x += 20
			} else {
				x += 34
			}
		}
		if x > 2076-20 {
			t.Fatal("AI標籤超出按鈕", mode)
		}
	}
}

func TestPosterRulesSelectionAndBattleLock(t *testing.T) {
	v := testToolbar(t)
	v.SyncBattleRules("formation", false)
	if a := v.Input(2400, 24, true, ""); !a.Consumed || v.Menu != "rules" || v.Selected != 1 {
		t.Fatal("rules menu", a)
	}
	v.Input(0, 0, false, "up")
	if a := v.Input(0, 0, false, "enter"); !a.Consumed || a.BattleRules != "native" || a.BattleAI != "" {
		t.Fatal("rules selection", a)
	}
	v.Input(2400, 24, true, "")
	v.SyncBattleRules("formation", true)
	if v.Menu != "" {
		t.Fatal("battle start left rules menu open")
	}
	if a := v.Input(2400, 24, true, ""); !a.Consumed || v.Menu != "" || a.BattleRules != "" {
		t.Fatal("locked rules changed", a)
	}
	v.Input(1800, 24, true, "")
	if v.Menu != "ai" {
		t.Fatal("battle lock blocked independent AI")
	}
	v.CloseMenu()
	v.SyncBattleRules("native", false)
	v.Input(2400, 24, true, "")
	if a := v.Input(2400, 140, true, ""); a.BattleRules != "formation" || !a.Consumed {
		t.Fatal(a)
	}
	for _, mode := range []string{"native", "formation"} {
		for _, locked := range []bool{false, true} {
			x := 2244
			for _, c := range v.rulesLabel(mode, locked) + "  v" {
				if _, ok := v.glyphs[c]; !ok {
					t.Fatalf("missing rule glyph %q", c)
				}
				if c < 128 {
					x += 20
				} else {
					x += 34
				}
			}
			if x > 2852 {
				t.Fatal("rule label exceeds button", mode, locked)
			}
		}
	}
}
