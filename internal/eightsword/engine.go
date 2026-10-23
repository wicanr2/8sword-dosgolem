package eightsword

import (
	"errors"
	"fmt"
	"image"
	"os"
	"path/filepath"
	"strings"

	"github.com/wicanr2/dosgolem/oracle"
)

type Options struct {
	Root, Assets, Saves string
	HD                  bool
}
type Engine struct {
	Oracle        *oracle.Oracle
	Tracker       *Tracker
	Assets        *Assets
	PAM           []byte
	HD            bool
	AssetError    string
	GraphicsError string
	Exited        bool
	ExitCode      uint8
	PAMLoaded     bool
	InputEvents   []InputEvent
	Sound         *oracle.Audio
	Music         *Music
}
type InputEvent struct {
	Step  uint64
	Scan  uint8
	Down  bool
	Route string
}

func Open(opt Options) (*Engine, error) {
	pam, err := os.ReadFile(filepath.Join(opt.Root, "PAM.AY"))
	if err != nil {
		return nil, err
	}
	if hash(pam) != PAMSHA {
		return nil, fmt.Errorf("未知 PAM.AY 來源版本")
	}
	exe := filepath.Join(opt.Root, "PREDELLA.EXE")
	original, err := os.ReadFile(exe)
	if err != nil {
		return nil, err
	}
	if hash(original) != "b9c7abdac7849711b68b6b6fd5861052e6f3d025b25af5f96d4605bf673cadaa" {
		return nil, fmt.Errorf("未知 PREDELLA.EXE 來源版本")
	}
	if err = os.MkdirAll(opt.Saves, 0755); err != nil {
		return nil, err
	}
	o, err := oracle.LoadWith(exe, opt.Root, oracle.Options{Adlib: true, ProgramPath: `C:\PREDELLA.EXE`})
	if err != nil {
		return nil, err
	}
	o.SetScratch(opt.Saves)
	e := &Engine{Oracle: o, PAM: pam, HD: opt.HD, Sound: o.NewAudio(48000)}
	if opt.HD {
		e.Assets, err = LoadAssets(opt.Assets, pam)
		if err != nil {
			e.AssetError = err.Error()
			e.HD = false
		} else {
			e.Tracker = NewTracker(o, e.Assets, pam)
			if _, statErr := os.Stat(filepath.Join(opt.Assets, "terrain.json")); !os.IsNotExist(statErr) {
				pmap, readErr := os.ReadFile(filepath.Join(opt.Root, "PMAP.AY"))
				if readErr != nil {
					e.GraphicsError = readErr.Error()
				} else {
					art, artErr := loadGraphicsAssets(opt.Assets, pmap)
					if artErr != nil {
						e.GraphicsError = artErr.Error()
					} else if art != nil {
						e.Tracker.graphics = newGraphics(e.Tracker, art)
					}
				}
			}
		}
	}
	e.Music = newMusic(o, pam, opt.Assets, e.HD)
	return e, nil
}
func (e *Engine) Close() {
	if e.Music != nil {
		e.Music.Close()
	}
	e.Oracle.Close()
}
func (e *Engine) RenderAudio() []int16 {
	if e.Music != nil {
		return e.Music.Render(e.Sound)
	}
	return stereoMono(e.Sound.Render())
}
func (e *Engine) EnableLiveClock(perMS uint64) { e.Oracle.SetDOSBoxCycles(perMS) }
func (e *Engine) AdvanceCycles(n uint64) error {
	for n > 0 && !e.Exited {
		count := n
		if count > 50000 {
			count = 50000
		}
		if err := e.Oracle.RunCycles(count); err != nil {
			var exit *oracle.ExitError
			if errors.As(err, &exit) {
				e.Exited = true
				e.ExitCode = exit.Code
				return nil
			}
			return err
		}
		for _, r := range e.Oracle.ExecLog() {
			if strings.EqualFold(r.Base, "PAM.AY") {
				e.PAMLoaded = true
			}
		}
		if e.Tracker != nil {
			e.Tracker.Bind()
		}
		if e.Music != nil {
			e.Music.Bind()
		}
		n -= count
	}
	return nil
}
func (e *Engine) Advance(n uint64) error {
	for n > 0 && !e.Exited {
		count := n
		if count > 50000 {
			count = 50000
		}
		err := e.Oracle.Run(count)
		if err != nil {
			var exit *oracle.ExitError
			if errors.As(err, &exit) {
				e.Exited = true
				e.ExitCode = exit.Code
				return nil
			}
			return err
		}
		for _, r := range e.Oracle.ExecLog() {
			if strings.EqualFold(r.Base, "PAM.AY") {
				e.PAMLoaded = true
			}
		}
		if e.Tracker != nil {
			e.Tracker.Bind()
		}
		if e.Music != nil {
			e.Music.Bind()
		}
		n -= count
	}
	return nil
}
func (e *Engine) Key(scan uint8, down bool) error {
	route := "bios"
	if e.PAMLoaded {
		route = "irq1"
	}
	e.InputEvents = append(e.InputEvents, InputEvent{e.Oracle.Steps(), scan, down, route})
	if e.PAMLoaded {
		if down {
			e.Oracle.KeyDown(scan)
		} else {
			e.Oracle.KeyUp(scan)
		}
		return nil
	}
	if !down {
		return nil
	}
	switch scan {
	case 0x02:
		return e.Oracle.TypeKeys("1")
	case 0x03:
		return e.Oracle.TypeKeys("2")
	case 0x04:
		return e.Oracle.TypeKeys("3")
	case 0x01:
		return e.Oracle.SendKeys("Esc")
	case 0x1c:
		return e.Oracle.SendKeys("Return")
	case 0x39:
		return e.Oracle.SendKeys("Space")
	case 0x48:
		return e.Oracle.SendKeys("Up")
	case 0x50:
		return e.Oracle.SendKeys("Down")
	}
	return nil
}
func (e *Engine) ReleaseAll() {
	for _, scan := range e.Oracle.HeldKeys() {
		_ = e.Key(scan, false)
	}
}
func (e *Engine) Frame() *image.RGBA {
	if e.Tracker != nil {
		if im := e.Tracker.Compose(); im != nil {
			return im
		}
	}
	if e.Oracle.VideoMode() == 3 {
		return e.consoleFrame()
	}
	w, h, rgb := e.Oracle.ScreenRGB()
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	if w <= 0 || h <= 0 {
		return out
	}
	for y := 0; y < 1200; y++ {
		sy := y * h / 1200
		for x := 0; x < 1920; x++ {
			sx := x * w / 1920
			src := (sy*w + sx) * 3
			dst := y*out.Stride + x*4
			copy(out.Pix[dst:dst+3], rgb[src:src+3])
			out.Pix[dst+3] = 255
		}
	}
	return out
}
func (e *Engine) Status() map[string]any {
	out := map[string]any{"steps": e.Oracle.Steps(), "mode": e.Oracle.VideoMode(), "pam_loaded": e.PAMLoaded, "hd": e.HD, "asset_error": e.AssetError, "graphics_error": e.GraphicsError, "exited": e.Exited, "exit_code": e.ExitCode, "bios_consumed": e.Oracle.KeysConsumed(), "irq1_delivered": e.Oracle.IRQ1Delivered(), "unimplemented": e.Oracle.Unimplemented(), "input_events": e.InputEvents, "exec_log": e.Oracle.ExecLog(), "file_ops": e.Oracle.FileOps()}
	view := e.bootConsole()
	out["console_stage"], out["console_source_sha256"] = view.stage, view.sha
	if e.Tracker != nil {
		out["text"] = e.Tracker.Stats
		out["scene"] = e.Tracker.Scene
		out["visible_scene"] = e.Tracker.VisibleScene
		out["strings"] = e.Tracker.Strings
		if e.Tracker.graphics != nil {
			out["graphics"] = e.Tracker.graphics.Stats
			out["graphics_materials"] = len(e.Tracker.graphics.assets.Materials)
			out["graphics_actor_materials"] = len(e.Tracker.graphics.assets.Actors)
		}
	}
	if e.Music != nil {
		out["music"] = e.Music.Status()
	}
	return out
}
