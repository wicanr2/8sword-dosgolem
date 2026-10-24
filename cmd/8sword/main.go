package main

import (
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"image/png"
	"log"
	"os"
	"path/filepath"
	"runtime/pprof"
	"strings"
	"sync"
	"time"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/audio"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	"github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

type pcmQueue struct {
	sync.Mutex
	data                []byte
	Underflows, Dropped uint64
}

func (q *pcmQueue) Read(p []byte) (int, error) {
	q.Lock()
	defer q.Unlock()
	n := copy(p, q.data)
	q.data = q.data[n:]
	clear(p[n:])
	if n < len(p) {
		q.Underflows++
	}
	return len(p), nil
}
func (q *pcmQueue) push(samples []int16) {
	q.Lock()
	defer q.Unlock()
	for _, s := range samples {
		var sample [2]byte
		binary.LittleEndian.PutUint16(sample[:], uint16(s))
		q.data = append(q.data, sample[:]...)
	}
	if len(q.data) > 48000*4 {
		q.Dropped += uint64(len(q.data) - 48000*4)
		q.data = q.data[len(q.data)-48000*4:]
	}
}

type game struct {
	engine                                     *eightsword.Engine
	texture                                    *ebiten.Image
	frame                                      *image.RGBA
	capture                                    string
	updates, maxUpdates                        int
	cycles                                     uint64
	pcm                                        *pcmQueue
	audio                                      *audio.Player
	audioCapture                               *os.File
	audioFrames                                uint64
	recorder                                   *eightsword.FrameRecorder
	recordErr                                  error
	profile                                    map[string]float64
	recordMS                                   float64
	draws                                      uint64
	presentedScene                             string
	frameConsole                               string
	presentedConsole                           string
	frameIntro                                 string
	presentedIntro                             string
	frameFontID, presentedFontID               string
	frameStoryCalls, frameStoryPages           uint64
	frameCaptionSource, presentedCaptionSource uint16
	presentedStoryCalls, presentedStoryPages   uint64
	introDraw                                  *os.File
	recordedFrame                              *image.RGBA
	stageTotals                                map[string]*stageTiming
	started                                    time.Time
	startCycles                                uint64
	settings                                   string
	controlHeld                                bool
	titleSuffix                                string
	toolbar                                    *eightsword.PosterToolbar
	toolbarError                               string
	blocked                                    map[ebiten.Key]bool
	controlBlocked                             bool
}

type stageTiming struct {
	Count   uint64 `json:"count"`
	TotalNS int64  `json:"total_ns"`
	MaxNS   int64  `json:"max_ns"`
}

func (g *game) observe(stage string, duration time.Duration) {
	if g.capture == "" {
		return
	}
	if g.stageTotals == nil {
		g.stageTotals = map[string]*stageTiming{}
	}
	value := g.stageTotals[stage]
	if value == nil {
		value = &stageTiming{}
		g.stageTotals[stage] = value
	}
	value.Count++
	value.TotalNS += duration.Nanoseconds()
	value.MaxNS = max(value.MaxNS, duration.Nanoseconds())
}

func (g *game) status(closed bool) map[string]any {
	status := g.engine.Status()
	status["updates"], status["profile"] = g.updates, g.profile
	status["actual_fps"], status["actual_tps"] = ebiten.ActualFPS(), ebiten.ActualTPS()
	status["presented_frames"], status["presented_scene"] = g.draws, g.presentedScene
	status["presented_console"] = g.presentedConsole
	status["presented_intro"] = g.presentedIntro
	status["presented_font_id"] = g.presentedFontID
	status["presented_story_calls"], status["presented_story_pages"] = g.presentedStoryCalls, g.presentedStoryPages
	status["presented_caption_source"] = g.presentedCaptionSource
	status["stage_totals"] = g.stageTotals
	status["toolbar_error"] = g.toolbarError
	if g.toolbar != nil {
		status["poster_id"], status["toolbar_menu"] = g.toolbar.ID, g.toolbar.Menu
		status["poster_error"] = g.toolbar.Error
		status["presentation_size"] = []int{eightsword.PosterWidth, eightsword.PosterHeight}
	}
	if g.audioCapture != nil {
		status["captured_audio_frames"] = g.audioFrames
	}
	if !g.started.IsZero() {
		cycles := g.engine.Oracle.Cycles() - g.startCycles
		status["session"] = map[string]any{"wall_ms": float64(time.Since(g.started).Microseconds()) / 1000, "guest_cycles": cycles, "guest_ms": float64(cycles) / float64(g.cycles), "cycles_per_ms": g.cycles, "target_tps": 30, "muted": g.pcm == nil}
	}
	if g.recorder != nil {
		status["recorded_frames"] = g.recorder.Frames
		status["recorded_repeat_frames"] = g.recorder.RepeatedFrames
		status["recorded_compared_rows"] = g.recorder.ComparedRows
	}
	if closed {
		status["closed"] = true
	}
	return status
}

var keys = []struct {
	key  ebiten.Key
	scan uint8
}{
	{ebiten.KeyDigit1, 2}, {ebiten.KeyDigit2, 3}, {ebiten.KeyDigit3, 4},
	{ebiten.KeyEscape, 1}, {ebiten.KeyEnter, 0x1c}, {ebiten.KeySpace, 0x39},
	{ebiten.KeyV, 0x2f},
	{ebiten.KeyArrowUp, 0x48}, {ebiten.KeyArrowDown, 0x50}, {ebiten.KeyArrowLeft, 0x4b}, {ebiten.KeyArrowRight, 0x4d},
	{ebiten.KeyF1, 0x3b}, {ebiten.KeyF2, 0x3c}, {ebiten.KeyF3, 0x3d}, {ebiten.KeyF4, 0x3e}, {ebiten.KeyF5, 0x3f}, {ebiten.KeyF6, 0x40}, {ebiten.KeyF7, 0x41},
	{ebiten.KeyNumpad1, 0x4f}, {ebiten.KeyNumpad2, 0x50}, {ebiten.KeyNumpad3, 0x51}, {ebiten.KeyNumpad4, 0x4b}, {ebiten.KeyNumpad5, 0x4c}, {ebiten.KeyNumpad6, 0x4d}, {ebiten.KeyNumpad7, 0x47}, {ebiten.KeyNumpad8, 0x48}, {ebiten.KeyNumpad9, 0x49},
	{ebiten.KeyHome, 0x47}, {ebiten.KeyPageUp, 0x49}, {ebiten.KeyEnd, 0x4f}, {ebiten.KeyPageDown, 0x51},
}

func (g *game) Update() error {
	if g.started.IsZero() {
		g.started = time.Now()
		g.startCycles = g.engine.Oracle.Cycles()
	}
	if g.recordErr != nil {
		return g.recordErr
	}
	if (ebiten.IsKeyPressed(ebiten.KeyControlLeft) || ebiten.IsKeyPressed(ebiten.KeyControlRight)) && inpututil.IsKeyJustPressed(ebiten.KeyQ) {
		return ebiten.Termination
	}
	if !ebiten.IsFocused() {
		g.engine.ReleaseAll()
		g.controlHeld = false
		if g.toolbar != nil {
			g.toolbar.CloseMenu()
			g.blockHeld()
		}
	} else {
		consumed := false
		if g.toolbar != nil {
			x, y := ebiten.CursorPosition()
			key := ""
			for _, k := range []struct {
				key  ebiten.Key
				name string
			}{{ebiten.KeyArrowUp, "up"}, {ebiten.KeyArrowDown, "down"}, {ebiten.KeyEnter, "enter"}, {ebiten.KeyEscape, "escape"}} {
				if inpututil.IsKeyJustPressed(k.key) {
					key = k.name
					break
				}
			}
			previousMenu := g.toolbar.Menu
			a := g.toolbar.Input(x, y, inpututil.IsMouseButtonJustPressed(ebiten.MouseButtonLeft), key)
			consumed = a.Consumed
			if previousMenu != "" || consumed {
				g.engine.ReleaseAll()
				g.controlHeld = false
				g.blockHeld()
			}
			if a.Font != "" {
				g.selectFont(a.Font)
			}
			if a.Poster != "" {
				if err := g.toolbar.SetPoster(a.Poster, time.Now()); err != nil {
					log.Print(err)
				} else if err = eightsword.SavePosterPreference(g.settings+".poster.json", a.Poster); err != nil {
					log.Print(err)
				}
			}
		}
		if inpututil.IsKeyJustPressed(ebiten.KeyF10) && g.engine.HD {
			choices := g.engine.FontChoices()
			for i, choice := range choices {
				if choice.ID == g.engine.FontID() {
					next := choices[(i+1)%len(choices)].ID
					g.selectFont(next)
					break
				}
			}
			ebiten.SetWindowTitle("神州八劍 · " + g.engine.FontName() + " · F10 字型" + g.titleSuffix)
		}
		for _, k := range keys {
			if g.blocked[k.key] {
				if !ebiten.IsKeyPressed(k.key) {
					delete(g.blocked, k.key)
				}
				continue
			}
			if consumed {
				continue
			}
			if inpututil.IsKeyJustPressed(k.key) {
				if err := g.engine.Key(k.scan, true); err != nil {
					return err
				}
			}
			if inpututil.IsKeyJustReleased(k.key) {
				if err := g.engine.Key(k.scan, false); err != nil {
					return err
				}
			}
		}
		control := ebiten.IsKeyPressed(ebiten.KeyControlLeft) || ebiten.IsKeyPressed(ebiten.KeyControlRight)
		if g.controlBlocked {
			if !control {
				g.controlBlocked = false
			}
			control = false
		}
		if consumed {
			control = false
		}
		if control != g.controlHeld {
			if err := g.engine.Key(0x1d, control); err != nil {
				return err
			}
			g.controlHeld = control
		}
	}
	started := time.Now()
	if err := g.engine.AdvanceCycles(g.cycles * 1000 / 30); err != nil {
		return err
	}
	advanced := time.Now()
	samples := g.engine.RenderAudio()
	if g.audioCapture != nil {
		if err := binary.Write(g.audioCapture, binary.LittleEndian, samples); err != nil {
			return err
		}
		g.audioFrames += uint64(len(samples) / 2)
	}
	if g.pcm != nil {
		g.pcm.push(samples)
	}
	audioDone := time.Now()
	previous := g.frame
	g.frame = g.engine.Frame()
	if previous != g.frame {
		g.frameFontID = g.engine.FontID()
	}
	g.frameConsole = g.engine.ConsoleStage()
	g.frameIntro = g.engine.IntroFrameStage(g.frame)
	g.frameCaptionSource = 0
	if g.engine.Captions != nil && g.frameIntro == "captions-noto" {
		g.frameCaptionSource = g.engine.Captions.FrameSource(g.frame)
	}
	g.frameStoryCalls, g.frameStoryPages = 0, 0
	if g.engine.Story != nil && g.frameIntro != "" {
		g.frameStoryCalls, g.frameStoryPages = g.engine.Story.FrameInfo(g.frame)
	}
	if g.toolbar != nil {
		g.toolbar.SyncFont(g.engine.FontID())
		g.frame = g.toolbar.Frame(g.frame, time.Now())
	}
	composed := time.Now()
	if previous != g.frame {
		g.texture.WritePixels(g.frame.Pix)
	}
	uploaded := time.Now()
	g.observe("advance", advanced.Sub(started))
	g.observe("audio", audioDone.Sub(advanced))
	g.observe("compose", composed.Sub(audioDone))
	g.observe("upload", uploaded.Sub(composed))
	g.profile = map[string]float64{"advance_ms": float64(advanced.Sub(started).Microseconds()) / 1000, "audio_ms": float64(audioDone.Sub(advanced).Microseconds()) / 1000, "compose_ms": float64(composed.Sub(audioDone).Microseconds()) / 1000, "upload_ms": float64(uploaded.Sub(composed).Microseconds()) / 1000, "previous_record_ms": g.recordMS}
	g.updates++
	if g.capture != "" && (g.updates%5 == 0 || g.frameCaptionSource != 0) {
		status := g.status(false)
		b, err := json.MarshalIndent(status, "", "  ")
		if err != nil {
			return err
		}
		temp := filepath.Join(g.capture, "gui-state.json.tmp")
		if err = os.WriteFile(temp, append(b, '\n'), 0644); err != nil {
			return err
		}
		if err = os.Rename(temp, filepath.Join(g.capture, "gui-state.json")); err != nil {
			return err
		}
	}
	if g.capture != "" && inpututil.IsKeyJustPressed(ebiten.KeyF12) {
		if err := g.captureFrame(); err != nil {
			return err
		}
	}
	if g.engine.Exited || (g.maxUpdates > 0 && g.updates >= g.maxUpdates) {
		return ebiten.Termination
	}
	return nil
}
func (g *game) captureFrame() error {
	f, err := os.Create(filepath.Join(g.capture, fmt.Sprintf("presented-%06d.png", g.updates)))
	if err != nil {
		return err
	}
	defer f.Close()
	return png.Encode(f, g.frame)
}
func (g *game) Draw(screen *ebiten.Image) {
	screen.DrawImage(g.texture, nil)
	g.draws++
	g.presentedConsole = g.frameConsole
	g.presentedIntro = g.frameIntro
	g.presentedFontID = g.frameFontID
	g.presentedCaptionSource = g.frameCaptionSource
	g.presentedStoryCalls, g.presentedStoryPages = g.frameStoryCalls, g.frameStoryPages
	if g.introDraw != nil {
		if err := json.NewEncoder(g.introDraw).Encode(map[string]any{"draw": g.draws, "step": g.engine.Oracle.Steps(), "stage": g.frameIntro, "story_calls": g.frameStoryCalls, "story_pages": g.frameStoryPages, "caption_source": g.frameCaptionSource, "font_id": g.frameFontID}); err != nil {
			g.recordErr = err
		}
	}
	if g.engine.Tracker != nil {
		g.presentedScene = g.engine.Tracker.VisibleScene
	}
	if g.recorder != nil && g.frame != nil && g.recordErr == nil {
		started := time.Now()
		if g.recordedFrame == g.frame {
			g.recordErr = g.recorder.Repeat(g.engine.Oracle.Steps())
		} else {
			g.recordErr = g.recorder.Write(g.frame, g.engine.Oracle.Steps())
		}
		if g.recordErr == nil {
			g.recordedFrame = g.frame
		}
		g.recordMS = float64(time.Since(started).Microseconds()) / 1000
		g.observe("record", time.Since(started))
	}
}
func (g *game) blockHeld() {
	if g.blocked == nil {
		g.blocked = map[ebiten.Key]bool{}
	}
	for _, k := range keys {
		if ebiten.IsKeyPressed(k.key) {
			g.blocked[k.key] = true
		}
	}
	if ebiten.IsKeyPressed(ebiten.KeyControlLeft) || ebiten.IsKeyPressed(ebiten.KeyControlRight) {
		g.controlBlocked = true
	}
}
func (g *game) selectFont(id string) {
	if err := g.engine.SetFont(id); err != nil {
		log.Print(err)
	} else if err = eightsword.SaveFontPreference(g.settings, id); err != nil {
		log.Printf("字型偏好未儲存：%s", err)
	}
	ebiten.SetWindowTitle("神州八劍 · " + g.engine.FontName() + " · F10 字型" + g.titleSuffix)
}
func (g *game) Layout(int, int) (int, int) {
	if g.toolbar != nil {
		return eightsword.PosterWidth, eightsword.PosterHeight
	}
	return 1920, 1200
}
func main() {
	root := flag.String("root", "", "合法原版資料目錄")
	assets := flag.String("assets", "", "HD 字型、圖像與音樂素材目錄")
	font := flag.String("font", "", "字型：noto、lishu、caoshu；空白沿用偏好")
	poster := flag.String("poster", "", "海報：wings、cover、off；空白沿用偏好")
	settings := flag.String("settings", "", "字型偏好檔，預設為系統使用者設定目錄")
	saves := flag.String("saves", "", "可寫存檔目錄")
	capture := flag.String("capture-dir", "", "研究收據目錄，F12 抓圖")
	record := flag.Bool("record", false, "以無損列差分記錄每次呈現，需要 capture-dir")
	recordAudio := flag.Bool("record-audio", false, "記錄前端交錯雙聲道 PCM，需要 capture-dir")
	cpuProfile := flag.String("cpu-profile", "", "研究用 CPU profile 輸出檔案")
	vsync := flag.Bool("vsync", true, "同步視窗更新，研究環境可關閉比較")
	hd := flag.Bool("hd", true, "啟用 HD 文字、圖像與已提供的音樂")
	mute := flag.Bool("mute", false, "靜音，保留遊戲音訊時鐘")
	cycles := flag.Uint64("cycles", 20000, "DOSBox 相容 cycles/ms")
	limit := flag.Int("max-updates", 0, "研究執行上限，0 不限")
	flag.Parse()
	if *root == "" || *saves == "" || *cycles == 0 {
		log.Fatal("需要 -root、-saves 與正數 -cycles")
	}
	if *capture != "" {
		if err := os.MkdirAll(*capture, 0755); err != nil {
			log.Fatal(err)
		}
	}
	if *cpuProfile != "" {
		f, err := os.Create(*cpuProfile)
		if err != nil {
			log.Fatal(err)
		}
		defer f.Close()
		if err = pprof.StartCPUProfile(f); err != nil {
			log.Fatal(err)
		}
		defer pprof.StopCPUProfile()
	}
	engine, err := eightsword.Open(eightsword.Options{Root: *root, Assets: *assets, Saves: *saves, HD: *hd})
	if err != nil {
		log.Fatal(err)
	}
	defer engine.Close()
	engine.EnableLiveClock(*cycles)
	if *settings == "" {
		config, err := os.UserConfigDir()
		if err != nil {
			log.Fatal(err)
		}
		*settings = filepath.Join(config, "8sword", "settings.json")
	}
	selected := *font
	if selected == "" {
		var err error
		selected, err = eightsword.LoadFontPreference(*settings)
		if err != nil {
			log.Print(err)
		}
	}
	if engine.HD {
		if err := engine.SetFont(selected); err != nil {
			log.Printf("使用 Noto：%s", err)
		} else if *font != "" {
			if err := eightsword.SaveFontPreference(*settings, selected); err != nil {
				log.Printf("字型偏好未儲存：%s", err)
			}
		}
	}
	title := "神州八劍 · " + engine.FontName() + " · F10 字型"
	if !engine.HD {
		title = "神州八劍 · 原版文字"
	}
	if engine.AssetError != "" {
		title = "神州八劍 · 原版文字（HD 字型載入失敗）"
		log.Printf("HD 字型未載入，使用原版呈現：%s", engine.AssetError)
	}
	if engine.GraphicsError != "" {
		title += "（HD 圖像載入失敗）"
		log.Printf("HD 圖像未載入，保留原版圖像：%s", engine.GraphicsError)
	}
	if engine.BattleActorError != "" {
		title += "（HD 戰場部隊載入失敗）"
		log.Print(engine.BattleActorError)
	}
	if engine.BattleEffectError != "" {
		title += "（HD 戰場效果載入失敗）"
		log.Print(engine.BattleEffectError)
	}
	if engine.BattleMarkerError != "" {
		title += "（HD 陰陽圖案載入失敗）"
		log.Print(engine.BattleMarkerError)
	}
	if engine.PaletteError != "" {
		title += "（HD 修色已回退）"
		log.Print(engine.PaletteError)
	}
	if engine.Music != nil && engine.Music.LoadError != "" {
		title += "（HD 音樂載入失敗）"
		log.Printf("HD 音樂未載入，保留原版音訊：%s", engine.Music.LoadError)
	}
	if engine.IntroError != "" {
		title += "（HD 片頭載入失敗）"
		log.Printf("HD 片頭未載入，保留原版標題：%s", engine.IntroError)
	}
	if engine.PublisherError != "" {
		title += "（HD 發行商文字載入失敗）"
		log.Print(engine.PublisherError)
	}
	if engine.StoryError != "" {
		title += "（HD 故事文字載入失敗）"
		log.Printf("HD 故事字型未載入，保留原版文字：%s", engine.StoryError)
	}
	if engine.Story != nil && engine.Story.BackgroundError != "" {
		title += "（HD 故事背景載入失敗）"
		log.Printf("HD 故事背景未載入，保留原版背景：%s", engine.Story.BackgroundError)
	}
	if engine.FontError != "" {
		title += "（部分可選字型載入失敗）"
		log.Print(engine.FontError)
	}
	suffix := ""
	if i := strings.IndexRune(title, '（'); i >= 0 {
		suffix = title[i:]
	}
	g := &game{engine: engine, texture: ebiten.NewImage(1920, 1200), capture: *capture, cycles: *cycles, maxUpdates: *limit, settings: *settings, titleSuffix: suffix}
	if engine.HD {
		g.toolbar, err = eightsword.LoadPosterToolbar(*assets, engine.FontChoices())
		if err != nil {
			g.toolbarError = err.Error()
			log.Printf("海報工具列未載入：%s", err)
			title += "（海報工具列載入失敗）"
		}
		if g.toolbar != nil {
			selectedPoster := *poster
			if selectedPoster == "" {
				selectedPoster, err = eightsword.LoadPosterPreference(*settings + ".poster.json")
				if err != nil {
					log.Print(err)
				}
			}
			if err = g.toolbar.SetPoster(selectedPoster, time.Now()); err != nil {
				log.Print(err)
			} else if *poster != "" {
				if err = eightsword.SavePosterPreference(*settings+".poster.json", selectedPoster); err != nil {
					log.Print(err)
				}
			}
			if g.toolbar.Error != "" {
				log.Print(g.toolbar.Error)
				title += "（海報已關閉）"
			}
			g.texture.Dispose()
			g.texture = ebiten.NewImage(eightsword.PosterWidth, eightsword.PosterHeight)
		}
	}
	if i := strings.IndexRune(title, '（'); i >= 0 {
		g.titleSuffix = title[i:]
	}
	if *capture != "" {
		g.introDraw, err = os.Create(filepath.Join(*capture, "intro-draw.jsonl"))
		if err != nil {
			log.Fatal(err)
		}
		defer g.introDraw.Close()
	}
	if *recordAudio {
		if *capture == "" {
			log.Fatal("-record-audio 需要 -capture-dir")
		}
		g.audioCapture, err = os.Create(filepath.Join(*capture, "audio-s16le-stereo.pcm"))
		if err != nil {
			log.Fatal(err)
		}
		defer g.audioCapture.Close()
	}
	if *record {
		if *capture == "" {
			log.Fatal("-record 需要 -capture-dir")
		}
		w, h := g.Layout(0, 0)
		g.recorder, err = eightsword.NewFrameRecorder(filepath.Join(*capture, "presentation.frames.gz"), w, h)
		if err != nil {
			log.Fatal(err)
		}
	}
	if !*mute {
		context := audio.NewContext(48000)
		g.pcm = &pcmQueue{}
		g.audio, err = context.NewPlayer(g.pcm)
		if err != nil {
			log.Fatal(err)
		}
		defer g.audio.Close()
		g.audio.Play()
	}
	ebiten.SetWindowTitle(title)
	ebiten.SetWindowSize(1280, 800)
	if g.toolbar != nil {
		ebiten.SetWindowSize(1600, 687)
	}
	ebiten.SetWindowResizingMode(ebiten.WindowResizingModeEnabled)
	ebiten.SetTPS(30)
	ebiten.SetVsyncEnabled(*vsync)
	ebiten.SetRunnableOnUnfocused(true)
	if err = ebiten.RunGame(g); err != nil {
		log.Fatal(err)
	}
	if g.recorder != nil {
		if err = g.recorder.Close(); err != nil {
			log.Fatal(err)
		}
	}
	if *capture != "" {
		status := g.status(true)
		b, _ := json.MarshalIndent(status, "", "  ")
		if err = os.WriteFile(filepath.Join(*capture, "gui-final.json"), append(b, '\n'), 0644); err != nil {
			log.Fatal(err)
		}
		if err = engine.Oracle.SaveStateFile(filepath.Join(*capture, "gui-final.state")); err != nil {
			log.Fatal(err)
		}
	}
}
