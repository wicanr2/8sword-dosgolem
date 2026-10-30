//go:build ignore

package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"image"
	"image/png"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
)

type battleApp struct {
	UI                                                         *battleUI
	Fonts                                                      *armyUIFonts
	Texture                                                    *ebiten.Image
	Frame                                                      *image.RGBA
	Texts                                                      []armyUIText
	FrameSHA, PresentedSHA, PresentedFont, Capture, JournalSHA string
	Updates, Draws, Captures, Commits                          uint64
	LastCapture                                                string
	Done                                                       <-chan struct{}
}

func (g *battleApp) setFont(id string) {
	if g.Fonts.Atlases[id] == nil {
		return
	}
	if e := game.SaveFontPreference(filepath.Join(g.UI.Dir, "font-preference.json"), id); e != nil {
		g.UI.Message = "字型偏好無法儲存。"
	} else {
		g.UI.Font = id
	}
	g.UI.Dirty = true
}
func (g *battleApp) Update() error {
	select {
	case <-g.Done:
		return ebiten.Termination
	default:
	}
	ctrl := ebiten.IsKeyPressed(ebiten.KeyControlLeft) || ebiten.IsKeyPressed(ebiten.KeyControlRight)
	if ctrl && inpututil.IsKeyJustPressed(ebiten.KeyQ) {
		return ebiten.Termination
	}
	capture := false
	if ebiten.IsFocused() {
		if inpututil.IsMouseButtonJustPressed(ebiten.MouseButtonLeft) {
			x, y := ebiten.CursorPosition()
			action := battleHit(g.UI, x, y)
			if strings.HasPrefix(action, "font:") {
				g.setFont(strings.TrimPrefix(action, "font:"))
			} else if strings.HasPrefix(action, "card:") {
				var side, slot int
				if _, e := fmt.Sscanf(action, "card:%d:%d", &side, &slot); e == nil {
					if side == 0 {
						g.UI.Source = slot
					} else {
						g.UI.Target = slot
					}
					g.UI.Dirty = true
				}
			} else if action != "" {
				g.UI.handle(action)
			}
		} else if inpututil.IsKeyJustPressed(ebiten.KeyF10) {
			ids := []string{"noto", "lishu", "caoshu"}
			for i, id := range ids {
				if id == g.UI.Font {
					g.setFont(ids[(i+1)%3])
					break
				}
			}
		}
		capture = inpututil.IsKeyJustPressed(ebiten.KeyF12)
	}
	if g.Capture != "" && g.JournalSHA != g.UI.SavedSHA {
		g.Commits++
		raw, e := armyUIRead(filepath.Join(g.UI.Dir, "gamedata.ay.army.json"), 1<<20)
		if e != nil {
			return e
		}
		if e = os.WriteFile(filepath.Join(g.Capture, fmt.Sprintf("commit-%03d.json", g.Commits)), raw, 0600); e != nil {
			return e
		}
		g.JournalSHA = g.UI.SavedSHA
	}
	if g.UI.Dirty || g.Frame == nil {
		g.Frame, g.Texts = paintBattleUI(g.UI, g.Fonts)
		g.FrameSHA = contentSHA(g.Frame.Pix)
		g.Texture.WritePixels(g.Frame.Pix)
		g.UI.Dirty = false
	}
	if capture && g.Capture != "" {
		g.Captures++
		g.LastCapture = fmt.Sprintf("frame-%03d-%s.png", g.Captures, g.UI.Font)
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
func (g *battleApp) Draw(screen *ebiten.Image) {
	screen.DrawImage(g.Texture, nil)
	g.Draws++
	g.PresentedSHA = g.FrameSHA
	g.PresentedFont = g.UI.Font
}
func (g *battleApp) Layout(int, int) (int, int) { return 1920, 1200 }
func (g *battleApp) writeStatus(name string) error {
	v := map[string]any{"prototype": true, "world": g.UI.World, "font_id": g.UI.Font, "presented_font": g.PresentedFont, "canvas_sha256": g.FrameSHA, "presented_sha256": g.PresentedSHA, "session_sha256": g.UI.SavedSHA, "source": g.UI.Source, "target": g.UI.Target, "message": g.UI.Message, "events": g.UI.Events, "updates": g.Updates, "draws": g.Draws, "commits": g.Commits, "last_capture": g.LastCapture, "text_fields": g.Texts, "guest_instructions": 0}
	raw, e := json.MarshalIndent(v, "", "  ")
	if e != nil {
		return e
	}
	p := filepath.Join(g.Capture, name)
	if e = os.WriteFile(p+".tmp", append(raw, '\n'), 0600); e != nil {
		return e
	}
	return os.Rename(p+".tmp", p)
}
func runBattleUI() error {
	catalog := flag.String("catalog", "", "招募資料")
	combat := flag.String("combat", "", "戰鬥資料")
	seed := flag.String("seed", "", "明示試作初值")
	pack := flag.String("ui-assets", "", "三字型字圖")
	session := flag.String("session", "", "獨立進度目錄")
	capture := flag.String("capture-dir", "", "驗證輸出")
	scale := flag.Float64("scale", 2.0/3, "視窗比例")
	flag.Parse()
	if os.Getuid() != 1000 || *session == "" || !(*scale >= .5 && *scale <= 2) {
		return fmt.Errorf("請指定獨立進度與有效比例")
	}
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	var w OwnedWorld
	for _, v := range []struct {
		Path  string
		Value any
	}{{*catalog, &c}, {*combat, &cc}, {*seed, &w}} {
		raw, e := armyUIRead(v.Path, 1<<20)
		if e != nil {
			return e
		}
		if e = strictJSON(raw, v.Value); e != nil {
			return e
		}
	}
	f, e := loadArmyUIFonts(*pack)
	if e != nil {
		return e
	}
	raw, e := armyUIRead(*catalog, 1<<20)
	if e != nil || contentSHA(raw) != f.CatalogRawSHA {
		return fmt.Errorf("字圖與兵種資料不符")
	}
	u, e := openBattleUI(*session, c, cc, w)
	if e != nil {
		return e
	}
	defer u.Close()
	u.Font, e = game.LoadFontPreference(filepath.Join(*session, "font-preference.json"))
	if e != nil {
		return e
	}
	if *capture != "" {
		st, e := os.Stat(*capture)
		if e != nil || !st.IsDir() {
			return fmt.Errorf("擷取目錄不存在")
		}
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	g := &battleApp{UI: u, Fonts: f, Texture: ebiten.NewImage(1920, 1200), Capture: *capture, Done: ctx.Done()}
	ebiten.SetWindowTitle("神州八劍・軍隊試作・戰鬥接管")
	ebiten.SetWindowSize(int(1920**scale), int(1200**scale))
	ebiten.SetTPS(30)
	if e = ebiten.RunGame(g); e != nil {
		return e
	}
	if g.Capture != "" {
		return g.writeStatus("ui-final.json")
	}
	return nil
}
func main() {
	if e := runBattleUI(); e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(1)
	}
}
