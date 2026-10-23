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
	engine              *eightsword.Engine
	texture             *ebiten.Image
	frame               *image.RGBA
	capture             string
	updates, maxUpdates int
	cycles              uint64
	pcm                 *pcmQueue
	audio               *audio.Player
	audioCapture        *os.File
	audioFrames         uint64
	recorder            *eightsword.FrameRecorder
	recordErr           error
	profile             map[string]float64
	recordMS            float64
	draws               uint64
	presentedScene      string
	recordedFrame       *image.RGBA
	stageTotals         map[string]*stageTiming
	started             time.Time
	startCycles         uint64
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
	status["stage_totals"] = g.stageTotals
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
	} else {
		for _, k := range keys {
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
	if g.capture != "" && g.updates%5 == 0 {
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
func (g *game) Layout(int, int) (int, int) { return 1920, 1200 }
func main() {
	root := flag.String("root", "", "合法原版資料目錄")
	assets := flag.String("assets", "", "HD 字型、圖像與音樂素材目錄")
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
	title := "神州八劍 · Noto Black 900"
	if !engine.HD {
		title = "神州八劍 · 原版文字"
	}
	if engine.AssetError != "" {
		title = "神州八劍 · 原版文字（HD 字型載入失敗）"
		log.Printf("HD 字型未載入，使用原版呈現：%s", engine.AssetError)
	}
	if engine.GraphicsError != "" {
		title = "神州八劍 · Noto Black 900（HD 圖像載入失敗）"
		log.Printf("HD 圖像未載入，保留原版圖像：%s", engine.GraphicsError)
	}
	if engine.Music != nil && engine.Music.LoadError != "" {
		title += "（HD 音樂載入失敗）"
		log.Printf("HD 音樂未載入，保留原版音訊：%s", engine.Music.LoadError)
	}
	g := &game{engine: engine, texture: ebiten.NewImage(1920, 1200), capture: *capture, cycles: *cycles, maxUpdates: *limit}
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
		g.recorder, err = eightsword.NewFrameRecorder(filepath.Join(*capture, "presentation.frames.gz"), 1920, 1200)
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
