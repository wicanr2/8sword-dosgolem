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
	Oracle                   *oracle.Oracle
	Tracker                  *Tracker
	Assets                   *Assets
	PAM                      []byte
	HD                       bool
	AssetError               string
	GraphicsError            string
	BattleBackgroundError    string
	RecruitmentBuildingError string
	MapEncounterError        string
	MapEncounter10Error      string
	MapEncounter7Error       string
	ArmyMan21Error           string
	BattleActorError         string
	BattleEffectError        string
	BattleMarkerError        string
	PaletteError             string
	Exited                   bool
	ExitCode                 uint8
	PAMLoaded                bool
	InputEvents              []InputEvent
	Sound                    *oracle.Audio
	Music                    *Music
	Intro                    *IntroTitle
	IntroError               string
	Publisher                *IntroTitle
	PublisherError           string
	Story                    *IntroStory
	StoryError               string
	Captions                 *IntroCaptions
	Heroine                  *IntroHeroine
	HeroineError             string
	Museum                   *IntroMuseum
	MuseumError              string
	fonts                    *fontChoices
	FontError                string
	presentationObservers    []*presentationSubscription
	presentationDispatch     int
	presentationSweep        bool
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
						if battleErr := loadBattleBackground(opt.Assets, opt.Root, art); battleErr != nil {
							e.BattleBackgroundError = battleErr.Error()
						}
						if actorErr := loadBattleActors(opt.Assets, opt.Root, art); actorErr != nil {
							e.BattleActorError = actorErr.Error()
						}
						if effectErr := loadBattleEffects(opt.Assets, opt.Root, art); effectErr != nil {
							e.BattleEffectError = effectErr.Error()
						}
						if markerErr := loadBattleMarkers(opt.Assets, opt.Root, art); markerErr != nil {
							e.BattleMarkerError = markerErr.Error()
						}
						if militiaErr := loadBattleMilitia(opt.Assets, opt.Root, art); militiaErr != nil {
							if e.BattleActorError != "" {
								e.BattleActorError += "；"
							}
							e.BattleActorError += "戰場民兵: " + militiaErr.Error()
						}
						if buildingErr := loadRecruitmentBuilding(opt.Assets, opt.Root, art); buildingErr != nil {
							e.RecruitmentBuildingError = buildingErr.Error()
						}
						if encounterErr := loadMapEncounter(opt.Assets, opt.Root, art); encounterErr != nil {
							e.MapEncounterError = encounterErr.Error()
						}
						if encounterErr := loadMapEncounter10(opt.Assets, opt.Root, art); encounterErr != nil {
							e.MapEncounter10Error = encounterErr.Error()
						}
						if encounterErr := loadMapEncounter7(opt.Assets, opt.Root, art); encounterErr != nil {
							e.MapEncounter7Error = encounterErr.Error()
						}
						if armyErr := loadArmyMan21(opt.Assets, opt.Root, art); armyErr != nil {
							e.ArmyMan21Error = armyErr.Error()
						}
						e.Tracker.graphics = newGraphics(e.Tracker, art)
					}
				}
			}
		}
	}
	if e.Tracker != nil {
		palette, paletteErr := loadPresentationPalette(opt.Assets, e.Tracker.graphics)
		if paletteErr != nil {
			e.PaletteError = paletteErr.Error()
		} else {
			e.Tracker.palette = palette
		}
	}
	e.Music = newMusic(o, pam, opt.Assets, e.HD)
	if e.HD {
		e.Intro, err = loadIntroTitle(o, opt.Assets, opt.Root)
		if err != nil {
			e.IntroError = err.Error()
		}
		e.Story, err = loadIntroStory(o, opt.Assets)
		if err != nil {
			e.StoryError = err.Error()
		}
		e.Captions = newIntroCaptions(o, e.Story)
		e.Publisher, err = loadIntroPublisher(o, opt.Assets, opt.Root)
		if err != nil {
			e.PublisherError = err.Error()
		}
		e.Museum, err = loadIntroMuseum(e, opt.Assets, opt.Root)
		if err != nil {
			e.MuseumError = err.Error()
		}
		if e.Museum == nil {
			e.Heroine, err = loadIntroHeroine(e, opt.Assets, opt.Root)
			if err != nil {
				e.HeroineError = err.Error()
			}
		}
	}
	e.loadFontChoices(opt.Assets)
	e.syncPresentationObservers()
	return e, nil
}
func (e *Engine) Close() {
	if e.Story != nil && e.Story.prelude != nil {
		e.Story.prelude.stop("close", false)
	}
	if e.Museum != nil {
		e.Museum.retireMuseum()
	}
	e.closePresentationObservers()
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
		if e.Intro != nil {
			e.Intro.Bind()
		}
		if e.Publisher != nil {
			e.Publisher.Bind()
		}
		if e.Story != nil {
			e.Story.Bind()
			e.Story.Tick()
		}
		if e.Captions != nil {
			e.Captions.Bind()
		}
		if e.Heroine != nil {
			e.Heroine.Tick()
		}
		if e.Museum != nil {
			e.Museum.Tick()
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
		if e.Intro != nil {
			e.Intro.Bind()
		}
		if e.Publisher != nil {
			e.Publisher.Bind()
		}
		if e.Story != nil {
			e.Story.Bind()
			e.Story.Tick()
		}
		if e.Captions != nil {
			e.Captions.Bind()
		}
		if e.Heroine != nil {
			e.Heroine.Tick()
		}
		if e.Museum != nil {
			e.Museum.Tick()
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
			return e.presentIntro(im)
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
	return e.presentIntro(out)
}
func (e *Engine) presentIntro(frame *image.RGBA) *image.RGBA {
	if !e.HD || (e.IntroStage() == "" && e.Heroine == nil && e.Museum == nil) {
		return frame
	}
	if (e.Intro != nil && e.Intro.active) || (e.Publisher != nil && e.Publisher.Stage() != "") || (e.Story != nil && e.Story.active) || (e.Captions != nil && e.Captions.Stage() != "") {
		// Tracker owns this cached frame. Intro overlays must not mutate it.
		copyFrame := image.NewRGBA(frame.Bounds())
		copy(copyFrame.Pix, frame.Pix)
		frame = copyFrame
	}
	if e.Intro != nil {
		frame = e.Intro.Compose(frame)
	}
	if e.Publisher != nil {
		frame = e.Publisher.Compose(frame)
	}
	if e.Story != nil {
		frame = e.Story.Compose(frame)
	}
	if e.Museum != nil {
		frame = e.Museum.Compose(frame)
	}
	if e.Heroine != nil {
		frame = e.Heroine.Compose(frame)
	}
	if e.Captions != nil {
		frame = e.Captions.Compose(frame)
	}
	if e.Museum != nil && e.Museum.Stage != "" {
		e.Museum.final = frame
	}
	if e.Heroine != nil && e.Heroine.used != 0 {
		e.Heroine.final = frame
	}
	return frame
}
func (e *Engine) IntroStage() string {
	if e.Publisher != nil && e.HD && e.Publisher.Stage() != "" {
		return e.Publisher.Stage()
	}
	if e.Captions != nil && e.HD && e.Captions.Stage() != "" {
		return e.Captions.Stage()
	}
	if e.Story != nil && e.HD && e.Story.Stage() != "" {
		return e.Story.Stage()
	}
	if e.Intro != nil && e.HD {
		return e.Intro.Stage()
	}
	return ""
}
func (e *Engine) IntroFrameStage(frame *image.RGBA) string {
	if e.Story != nil && e.HD && e.Story.prelude != nil {
		if stage := e.Story.prelude.FrameStage(frame); stage != "" {
			return stage
		}
	}
	if e.Publisher != nil && e.HD && frame != nil && (frame == e.Publisher.last || frame == e.Publisher.hold) {
		return e.Publisher.Stage()
	}
	if e.Captions != nil && e.HD && e.Captions.FrameSource(frame) != 0 {
		return "captions-noto"
	}
	if e.Museum != nil && e.HD && e.Museum.FrameStage(frame) != "" {
		return "museum-" + e.Museum.FrameStage(frame)
	}
	if e.Heroine != nil && e.HD && e.Heroine.FramePixels(frame) != 0 {
		return "heroine-hd"
	}
	if e.Story != nil && e.HD && frame != nil && (frame == e.Story.last || frame == e.Story.hold) {
		return e.Story.Stage()
	}
	if e.Intro != nil && e.HD && frame != nil && (frame == e.Intro.last || frame == e.Intro.hold) {
		return e.Intro.Stage()
	}
	return ""
}
func (e *Engine) Status() map[string]any {
	out := map[string]any{"steps": e.Oracle.Steps(), "mode": e.Oracle.VideoMode(), "pam_loaded": e.PAMLoaded, "hd": e.HD, "asset_error": e.AssetError, "graphics_error": e.GraphicsError, "exited": e.Exited, "exit_code": e.ExitCode, "bios_consumed": e.Oracle.KeysConsumed(), "irq1_delivered": e.Oracle.IRQ1Delivered(), "unimplemented": e.Oracle.Unimplemented(), "input_events": e.InputEvents, "exec_log": e.Oracle.ExecLog(), "file_ops": e.Oracle.FileOps()}
	out["font_id"], out["font_name"], out["font_error"], out["font_choices"] = e.FontID(), e.FontName(), e.FontError, e.FontChoices()
	out["battle_background_error"] = e.BattleBackgroundError
	out["recruitment_building_error"] = e.RecruitmentBuildingError
	out["map_encounter_error"] = e.MapEncounterError
	out["map_encounter_10_error"] = e.MapEncounter10Error
	out["map_encounter_7_error"] = e.MapEncounter7Error
	out["army_man21_error"] = e.ArmyMan21Error
	out["battle_actor_error"] = e.BattleActorError
	out["battle_effect_error"] = e.BattleEffectError
	out["battle_marker_error"] = e.BattleMarkerError
	out["heroine_error"], out["heroine"] = e.HeroineError, e.Heroine.Status()
	out["museum_error"], out["museum"] = e.MuseumError, e.Museum.Status()
	if e.Museum != nil {
		out["museum_transactions"] = e.Museum.Events
	}
	out["palette_error"], out["palette_style"] = e.PaletteError, ""
	if e.Tracker != nil && e.Tracker.palette != nil {
		out["palette_style"] = paletteStyle
	}
	view := e.bootConsole()
	out["console_stage"], out["console_source_sha256"] = view.stage, view.sha
	intro := map[string]any{"load_error": e.IntroError, "stage": e.IntroStage()}
	if e.Intro != nil {
		intro["stats"] = e.Intro.Stats
	}
	out["intro_title"] = intro
	pub := map[string]any{"load_error": e.PublisherError, "stage": ""}
	if e.Publisher != nil {
		pub["stats"], pub["stage"] = e.Publisher.Stats, e.Publisher.Stage()
		pub["icon"] = map[string]any{"loaded": e.Publisher.publisher.icon != nil, "load_error": e.Publisher.publisher.iconError}
	}
	out["intro_publisher"] = pub
	story := map[string]any{"load_error": e.StoryError, "stage": ""}
	if e.Story != nil {
		story["stats"] = e.Story.Stats
		story["stage"] = e.Story.Stage()
		story["background_error"] = e.Story.BackgroundError
		story["hd_background"] = e.Story.art != nil
		story["prelude_error"] = e.Story.PreludeError
		story["prelude"] = e.Story.prelude.Status()
	}
	out["intro_story"] = story
	if e.Captions != nil {
		out["intro_captions"] = map[string]any{"stage": e.Captions.Stage(), "stats": e.Captions.Stats}
	}
	if e.Tracker != nil {
		out["text"] = e.Tracker.Stats
		out["scene"] = e.Tracker.Scene
		out["visible_scene"] = e.Tracker.VisibleScene
		out["visible_sources"] = e.Tracker.VisibleSources()
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
