//go:build ignore

// 030 DRAFT: actual map -> native F2 dispatcher -> owned Go canvas -> map.
package main

import (
	"encoding/binary"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"sync"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/audio"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

type reviewPCM struct {
	sync.Mutex
	Data []byte
}

func (q *reviewPCM) Read(p []byte) (int, error) {
	q.Lock()
	defer q.Unlock()
	n := copy(p, q.Data)
	q.Data = q.Data[n:]
	clear(p[n:])
	return len(p), nil
}
func (q *reviewPCM) push(v []int16) {
	q.Lock()
	defer q.Unlock()
	for _, s := range v {
		var b [2]byte
		binary.LittleEndian.PutUint16(b[:], uint16(s))
		q.Data = append(q.Data, b[:]...)
	}
	if len(q.Data) > 192000 {
		q.Data = q.Data[len(q.Data)-192000:]
	}
}

type armyScreenExtra interface {
	IsActive() bool
	NoteKey(byte, bool)
	Click(int, int) (byte, error)
	Paint(*armyUIFonts, string) (*image.RGBA, []armyUIText)
	State() map[string]any
}

var armyReviewExtraFactory = func(*game.Engine, *worldArmyPort) (armyScreenExtra, error) { return nil, nil }
var armyReviewTitle = "神州八劍・軍隊試作・檢閱"

type armyReviewApp struct {
	Extra                                                                      armyScreenExtra
	Engine                                                                     *game.Engine
	Store                                                                      *progressPairStore
	Snapshot                                                                   progressPairSnapshot
	Port                                                                       *worldArmyPort
	Review                                                                     *armyReview
	Fonts                                                                      *armyUIFonts
	Owned                                                                      bool
	Bound                                                                      bool
	NativeActive                                                               bool
	NativeDrawCalls                                                            uint64
	Frame                                                                      *image.RGBA
	Texture                                                                    *ebiten.Image
	Texts                                                                      []armyUIText
	FrameSHA, PresentedSHA, FrameView, PresentedView, FrameFont, PresentedFont string
	Capture, Preference, LastCapture                                           string
	Updates, Draws, Captures                                                   uint64
	SyntheticRelease                                                           byte
	PCM                                                                        *reviewPCM
	AudioFrames                                                                uint64
}

var reviewKeys = []struct {
	Key  ebiten.Key
	Scan byte
}{
	{ebiten.KeyDigit1, 2}, {ebiten.KeyDigit2, 3}, {ebiten.KeyDigit3, 4}, {ebiten.KeyEnter, 0x1c}, {ebiten.KeyEscape, 1}, {ebiten.KeySpace, 0x39},
	{ebiten.KeyArrowLeft, 0x4b}, {ebiten.KeyArrowRight, 0x4d}, {ebiten.KeyArrowUp, 0x48}, {ebiten.KeyArrowDown, 0x50},
	{ebiten.KeyF1, 0x3b}, {ebiten.KeyF2, 0x3c}, {ebiten.KeyF3, 0x3d}, {ebiten.KeyF4, 0x3e}, {ebiten.KeyF5, 0x3f}, {ebiten.KeyF6, 0x40}, {ebiten.KeyF7, 0x41},
}

func (g *armyReviewApp) font(id string) error {
	if g.Fonts.Atlases[id] == nil {
		return errors.New("軍隊字型未提供")
	}
	if err := g.Engine.SetFont(id); err != nil {
		return err
	}
	return game.SaveFontPreference(g.Preference, id)
}
func (g *armyReviewApp) bind() error {
	if g.Bound || !g.Engine.PAMLoaded || g.Engine.Tracker == nil || g.Engine.Tracker.VisibleScene != "map" {
		return nil
	}
	for i, n := range pairWorldResources(g.Snapshot.World).words() {
		if uint64(g.Engine.Oracle.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
			return errors.New("讀入的原進度與Go資源不符")
		}
	}
	if g.Owned {
		p, e := installWorldArmyPort(g.Engine, g.Store, g.Snapshot)
		if e != nil {
			return e
		}
		g.Port = p
		g.Review, e = installArmyReview(g.Engine, p)
		if e != nil {
			return e
		}
		g.Extra, e = armyReviewExtraFactory(g.Engine, p)
		if e != nil {
			return e
		}
	}
	g.Bound = true
	return nil
}
func (g *armyReviewApp) view() string {
	if g.Extra != nil && g.Extra.IsActive() {
		return "dismiss"
	}
	if g.Review != nil && g.Review.Active {
		return "army"
	}
	if !g.Owned && g.NativeActive {
		return "army"
	}
	if g.Engine.Tracker != nil {
		return g.Engine.Tracker.VisibleScene
	}
	return "intro"
}
func (g *armyReviewApp) Update() error {
	if err := g.bind(); err != nil {
		return err
	}
	ctrl := ebiten.IsKeyPressed(ebiten.KeyControlLeft) || ebiten.IsKeyPressed(ebiten.KeyControlRight)
	if ctrl && inpututil.IsKeyJustPressed(ebiten.KeyQ) {
		return ebiten.Termination
	}
	if !ebiten.IsFocused() {
		g.Engine.ReleaseAll()
	} else {
		if inpututil.IsKeyJustPressed(ebiten.KeyF10) {
			ids := []string{"noto", "lishu", "caoshu"}
			for i, id := range ids {
				if id == g.Engine.FontID() {
					if e := g.font(ids[(i+1)%3]); e != nil {
						return e
					}
					break
				}
			}
		}
		if ((g.Review != nil && g.Review.Active) || (g.Extra != nil && g.Extra.IsActive())) && inpututil.IsMouseButtonJustPressed(ebiten.MouseButtonLeft) {
			x, y := ebiten.CursorPosition()
			pt := image.Pt(x, y)
			for _, id := range []string{"noto", "lishu", "caoshu"} {
				if pt.In(uiFontRect(id)) {
					if e := g.font(id); e != nil {
						return e
					}
				}
			}
			var scan byte
			if g.Extra != nil && g.Extra.IsActive() {
				var e error
				scan, e = g.Extra.Click(x, y)
				if e != nil {
					return e
				}
			} else if pt.In(reviewCloseRect) {
				scan = 1
			}
			if scan != 0 {
				if g.Extra != nil {
					g.Extra.NoteKey(scan, true)
				}
				if e := g.Engine.Key(scan, true); e != nil {
					return e
				}
				g.SyntheticRelease = scan
			}
		}
		for _, k := range reviewKeys {
			if inpututil.IsKeyJustPressed(k.Key) {
				if g.Extra != nil {
					g.Extra.NoteKey(k.Scan, true)
				}
				if e := g.Engine.Key(k.Scan, true); e != nil {
					return e
				}
			}
			if inpututil.IsKeyJustReleased(k.Key) {
				if g.Extra != nil {
					g.Extra.NoteKey(k.Scan, false)
				}
				if e := g.Engine.Key(k.Scan, false); e != nil {
					return e
				}
			}
		}
	}
	if e := catchWorldArmyFault(func() error { return g.Engine.AdvanceCycles(100000) }); e != nil {
		return e
	}
	pcm := g.Engine.RenderAudio()
	g.AudioFrames += uint64(len(pcm) / 2)
	if g.PCM != nil {
		g.PCM.push(pcm)
	}
	if g.SyntheticRelease != 0 {
		if e := g.Engine.Key(g.SyntheticRelease, false); e != nil {
			return e
		}
		g.SyntheticRelease = 0
	}
	if e := g.bind(); e != nil {
		return e
	}
	g.Texts = nil
	if g.Extra != nil && g.Extra.IsActive() {
		g.Frame, g.Texts = g.Extra.Paint(g.Fonts, g.Engine.FontID())
	} else if g.Review != nil && g.Review.Active {
		g.Frame, g.Texts = paintArmyReview(g.Review.Data, g.Fonts, g.Engine.FontID())
	} else {
		g.Frame = g.Engine.Frame()
	}
	if g.Frame == nil || g.Frame.Bounds() != image.Rect(0, 0, 1920, 1200) {
		return errors.New("軍隊畫布形狀不符")
	}
	g.FrameSHA = contentSHA(g.Frame.Pix)
	g.FrameView = g.view()
	g.FrameFont = g.Engine.FontID()
	g.Texture.WritePixels(g.Frame.Pix)
	if inpututil.IsKeyJustPressed(ebiten.KeyF12) && g.Capture != "" {
		g.Captures++
		g.LastCapture = fmt.Sprintf("frame-%03d-%s-%s.png", g.Captures, g.FrameView, g.FrameFont)
		f, e := os.OpenFile(filepath.Join(g.Capture, g.LastCapture), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
		if e != nil {
			return e
		}
		e = png.Encode(f, g.Frame)
		ce := f.Close()
		if e != nil {
			return e
		}
		if ce != nil {
			return ce
		}
	}
	g.Updates++
	if g.Capture != "" && g.Updates%3 == 0 {
		return g.writeStatus("ui-state.json")
	}
	return nil
}
func (g *armyReviewApp) Draw(s *ebiten.Image) {
	s.DrawImage(g.Texture, nil)
	g.Draws++
	g.PresentedSHA = g.FrameSHA
	g.PresentedView = g.FrameView
	g.PresentedFont = g.FrameFont
}
func (g *armyReviewApp) Layout(int, int) (int, int) { return 1920, 1200 }
func (g *armyReviewApp) status() map[string]any {
	state := map[string]any{"schema": 1, "prototype": true, "owned": g.Owned, "bound": g.Bound, "view": g.FrameView, "presented_view": g.PresentedView, "font_id": g.Engine.FontID(), "presented_font": g.PresentedFont, "canvas_sha256": g.FrameSHA, "presented_sha256": g.PresentedSHA, "last_capture": g.LastCapture, "updates": g.Updates, "draws": g.Draws, "native_row_draw_calls": g.NativeDrawCalls, "guest_steps": g.Engine.Oracle.Steps(), "audio_frames": g.AudioFrames, "pair_token": g.Snapshot.Token, "world": g.Snapshot.World, "font_sources": g.Fonts.Sources, "text_fields": g.Texts, "native_rows_hex": fmt.Sprintf("%x", g.Engine.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24))}
	if g.Bound {
		state["native_display_mode"] = g.Engine.Oracle.Word(oracle.Far(0x1e88, 0x7484))
	}
	if g.Port != nil {
		state["world"] = g.Port.Current.World
		state["pair_token"] = g.Port.Current.Token
	}
	if g.Extra != nil {
		for k, v := range g.Extra.State() {
			state[k] = v
		}
	}
	if g.Engine.Tracker != nil {
		state["native_scene"] = g.Engine.Tracker.VisibleScene
	}
	if g.Review != nil {
		state["review_opens"] = g.Review.Opens
		state["review_closes"] = g.Review.Closes
		state["review_skipped"] = g.Review.Skipped
		state["review_native_entries"] = g.Review.NativeEntries
		state["review_data"] = g.Review.Data
	}
	return state
}
func (g *armyReviewApp) writeStatus(name string) error {
	raw, e := json.MarshalIndent(g.status(), "", "  ")
	if e != nil {
		return e
	}
	p := filepath.Join(g.Capture, name)
	if e = os.WriteFile(p+".tmp", append(raw, '\n'), 0600); e != nil {
		return e
	}
	return os.Rename(p+".tmp", p)
}
func runArmyReview() error {
	root := flag.String("root", "", "唯讀原版")
	assets := flag.String("assets", "", "正式HD素材")
	input := flag.String("input", "", "固定資料與原地圖")
	session := flag.String("session", "", "Go成對存檔")
	scratch := flag.String("scratch", "", "新原版工作目錄")
	pack := flag.String("ui-assets", "", "軍隊字圖")
	capture := flag.String("capture-dir", "", "抽驗目錄")
	owned := flag.Bool("owned", true, "Go軍隊檢閱；false只作原版控制")
	mute := flag.Bool("mute", false, "不輸出裝置音訊")
	scale := flag.Float64("scale", 2.0/3, "視窗比例")
	flag.Parse()
	if os.Getuid() != 1000 || *scratch == "" || *scale < 0.5 || *scale > 2 {
		return errors.New("請指定有效的研究路徑與視窗比例")
	}
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	for _, v := range []struct {
		Name string
		Dst  any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}} {
		b, e := os.ReadFile(filepath.Join(*input, v.Name))
		if e != nil {
			return e
		}
		if e = pairStrictJSON(b, v.Dst); e != nil {
			return e
		}
	}
	store, snap, e := openProgressPair(*session, c, cc)
	if e != nil {
		return e
	}
	defer store.Close()
	fonts, e := loadArmyUIFonts(*pack)
	if e != nil {
		return e
	}
	raw, e := os.ReadFile(filepath.Join(*input, "army-catalog.json"))
	if e != nil {
		return e
	}
	if contentSHA(raw) != fonts.CatalogRawSHA {
		return errors.New("兵種與字圖版本不符")
	}
	// The adapter explicitly owns the sidecar and the guard. The original DOS
	// executor receives only a separate native shadow with the same opaque bytes.
	if e = os.Mkdir(*scratch, 0700); e != nil {
		return e
	}
	if e = os.WriteFile(filepath.Join(*scratch, "gamedata.ay"), snap.Bytes.Native, 0600); e != nil {
		return e
	}
	raw, e = os.ReadFile(filepath.Join(*input, "map01.ay"))
	if e != nil {
		return e
	}
	if e = os.WriteFile(filepath.Join(*scratch, "map01.ay"), raw, 0600); e != nil {
		return e
	}
	engine, e := game.Open(game.Options{Root: *root, Assets: *assets, Saves: *scratch, HD: true})
	if e != nil {
		return e
	}
	defer engine.Close()
	engine.Oracle.SetClock(12, 0, 0, 0)
	engine.EnableLiveClock(3000)
	pref := filepath.Join(*session, "font-preference.json")
	font, e := game.LoadFontPreference(pref)
	if e != nil {
		return e
	}
	if e = engine.SetFont(font); e != nil {
		return e
	}
	g := &armyReviewApp{Engine: engine, Store: store, Snapshot: snap, Fonts: fonts, Owned: *owned, Capture: *capture, Preference: pref, Texture: ebiten.NewImage(1920, 1200)}
	engine.Oracle.OnCall(oracle.Far(0x110, 0x3e92), func(o *oracle.Oracle) {
		if o.Regs().CS != 0x110 || o.Regs().DS != 0x1e88 {
			return
		}
		if o.Word(oracle.Far(0x1e88, 0x56bc)) == 1 {
			g.NativeActive = true
		}
	})
	engine.Oracle.OnCall(oracle.Far(0x110, 0x3ed8), func(o *oracle.Oracle) {
		if o.Regs().CS == 0x110 && o.Regs().DS == 0x1e88 {
			g.NativeActive = false
		}
	})
	engine.Oracle.OnCall(oracle.Far(0x110, 0x75c6), func(o *oracle.Oracle) {
		if o.Regs().CS != 0x110 || o.Regs().DS != 0x1e88 {
			return
		}
		g.NativeDrawCalls++
		if g.Owned && (!g.Bound || g.Review == nil || !g.Review.Active) {
			panic(&worldArmyPortFault{"army review not bound before native draw"})
		}
	})
	var player *audio.Player
	if !*mute {
		ctx := audio.NewContext(48000)
		g.PCM = &reviewPCM{}
		player, e = ctx.NewPlayer(g.PCM)
		if e != nil {
			return e
		}
		defer player.Close()
		player.Play()
	}
	ebiten.SetTPS(30)
	ebiten.SetWindowTitle(armyReviewTitle)
	ebiten.SetWindowSize(int(1920**scale), int(1200**scale))
	if e = ebiten.RunGame(g); e != nil {
		return e
	}
	if *capture != "" {
		return g.writeStatus("ui-final.json")
	}
	return nil
}
func main() {
	if e := runArmyReview(); e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(1)
	}
}
