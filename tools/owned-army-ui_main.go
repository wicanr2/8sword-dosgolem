//go:build ignore

// 030 DRAFT: actual Ebiten input and presentation for the isolated army UI.
package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"strings"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

type armyUIApp struct {
	UI                                    *armyUI
	Fonts                                 *armyUIFonts
	Texture                               *ebiten.Image
	Frame                                 *image.RGBA
	Texts                                 []armyUIText
	FrameSHA, PresentedSHA, PresentedFont string
	Capture, Preference                   string
	Updates, Draws, Captures              uint64
	LastCapture                           string
	MaxUpdates                            uint64
}

func (g *armyUIApp) font(id string) {
	if g.Fonts.Atlases[id] == nil {
		return
	}
	if err := game.SaveFontPreference(g.Preference, id); err != nil {
		g.UI.Message = "字型偏好無法儲存。"
		g.UI.Dirty = true
		return
	}
	g.UI.Font = id
	g.UI.Dirty = true
}
func (g *armyUIApp) Update() error {
	ctrl := ebiten.IsKeyPressed(ebiten.KeyControlLeft) || ebiten.IsKeyPressed(ebiten.KeyControlRight)
	if ctrl && inpututil.IsKeyJustPressed(ebiten.KeyQ) {
		return ebiten.Termination
	}
	capture := false
	if ebiten.IsFocused() {
		if inpututil.IsMouseButtonJustPressed(ebiten.MouseButtonLeft) {
			x, y := ebiten.CursorPosition()
			action := uiHit(g.UI, x, y)
			if action != "quantity" {
				if g.UI.QtyFocused {
					g.UI.Dirty = true
				}
				g.UI.QtyFocused = false
			}
			if strings.HasPrefix(action, "font:") {
				g.font(strings.TrimPrefix(action, "font:"))
			} else if action != "" {
				g.UI.handle(action)
			}
		} else if inpututil.IsKeyJustPressed(ebiten.KeyF10) {
			ids := []string{"noto", "lishu", "caoshu"}
			for i, id := range ids {
				if id == g.UI.Font {
					g.font(ids[(i+1)%3])
					break
				}
			}
		} else if ctrl && inpututil.IsKeyJustPressed(ebiten.KeyA) {
			g.UI.handle("clear")
		} else {
			for _, v := range []struct {
				Key    ebiten.Key
				Action string
			}{{ebiten.KeyEnter, "recruit"}, {ebiten.KeyArrowUp, "up"}, {ebiten.KeyArrowDown, "down"}, {ebiten.KeyArrowLeft, "minus"}, {ebiten.KeyArrowRight, "plus"}, {ebiten.KeyPageUp, "prev"}, {ebiten.KeyPageDown, "next"}, {ebiten.KeyBackspace, "backspace"}, {ebiten.KeyEscape, "escape"}} {
				if inpututil.IsKeyJustPressed(v.Key) {
					g.UI.handle(v.Action)
					break
				}
			}
			g.UI.text(string(ebiten.AppendInputChars(nil)))
		}
		capture = inpututil.IsKeyJustPressed(ebiten.KeyF12)
	}
	if g.UI.Dirty || g.Frame == nil {
		g.Frame, g.Texts = paintArmyUI(g.UI, g.Fonts)
		g.FrameSHA = contentSHA(g.Frame.Pix)
		g.Texture.WritePixels(g.Frame.Pix)
		g.UI.Dirty = false
	}
	if capture && g.Capture != "" {
		g.Captures++
		g.LastCapture = fmt.Sprintf("frame-%03d-%s.png", g.Captures, g.UI.Font)
		f, err := os.OpenFile(filepath.Join(g.Capture, g.LastCapture), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
		if err != nil {
			return err
		}
		err = png.Encode(f, g.Frame)
		ce := f.Close()
		if err != nil {
			return err
		}
		if ce != nil {
			return ce
		}
	}
	g.Updates++
	if g.Capture != "" && g.Updates%3 == 0 {
		if err := g.writeStatus("ui-state.json"); err != nil {
			return err
		}
	}
	if g.MaxUpdates != 0 && g.Updates >= g.MaxUpdates {
		return ebiten.Termination
	}
	return nil
}
func (g *armyUIApp) Draw(screen *ebiten.Image) {
	screen.DrawImage(g.Texture, nil)
	g.Draws++
	g.PresentedSHA = g.FrameSHA
	g.PresentedFont = g.UI.Font
}
func (g *armyUIApp) Layout(int, int) (int, int) { return armyUIWidth, armyUIHeight }
func (g *armyUIApp) status() map[string]any {
	q, _ := g.UI.quote()
	var rows []map[string]any
	for i, id := range g.UI.pageOffers() {
		p := g.UI.profile(id)
		rows = append(rows, map[string]any{"id": id, "unit": p.ID, "name": p.Name, "rect": uiBox(uiOfferRect(i)), "gold": p.Gold, "rank": p.Rank})
	}
	return map[string]any{"schema": 1, "prototype": true, "army": g.UI.Army, "selected": g.UI.Selected, "quantity": g.UI.Quantity, "quote": q, "new_only": g.UI.NewOnly, "page": g.UI.Page, "rows": rows, "font_id": g.UI.Font, "font_sources": g.Fonts.Sources, "font_fallbacks": g.Fonts.Fallbacks, "message": g.UI.Message, "transactions": g.UI.Transactions, "session_sha256": g.UI.Store.SavedSHA, "original_sha256": g.UI.Store.OriginalSHA, "canvas_sha256": g.FrameSHA, "presented_sha256": g.PresentedSHA, "presented_font": g.PresentedFont, "updates": g.Updates, "draws": g.Draws, "last_capture": g.LastCapture, "text_fields": g.Texts, "guest_instructions": 0, "canvas_size": []int{armyUIWidth, armyUIHeight}}
}
func (g *armyUIApp) writeStatus(name string) error {
	raw, err := json.MarshalIndent(g.status(), "", "  ")
	if err != nil {
		return err
	}
	target := filepath.Join(g.Capture, name)
	temp := target + ".tmp"
	if err = os.WriteFile(temp, append(raw, '\n'), 0600); err != nil {
		return err
	}
	return os.Rename(temp, target)
}
func runArmyUI() error {
	catalog := flag.String("catalog", "", "固定兵種資料")
	pack := flag.String("ui-assets", "", "軍隊視窗字圖")
	session := flag.String("session", "", "獨立軍隊進度目錄")
	capture := flag.String("capture-dir", "", "抽驗輸出目錄")
	scale := flag.Float64("scale", 2.0/3, "視窗比例")
	maxUpdates := flag.Uint64("max-updates", 0, "抽驗更新上限")
	flag.Parse()
	if os.Getuid() != 1000 || *catalog == "" || *pack == "" || *session == "" || *scale < 0.5 || *scale > 2 {
		return errors.New("請指定資料、字圖、進度與有效視窗比例")
	}
	font, err := loadArmyUIFonts(*pack)
	if err != nil {
		return err
	}
	raw, err := armyUIRead(*catalog, 1<<20)
	if err != nil {
		return err
	}
	if contentSHA(raw) != font.CatalogRawSHA {
		return errors.New("兵種資料與字圖不符")
	}
	var c ArmyCatalog
	if err = strictJSON(raw, &c); err != nil {
		return err
	}
	if _, err = c.index(); err != nil {
		return err
	}
	s, a, err := openArmyUIStore(*session, c, freshArmyUI(c))
	if err != nil {
		return err
	}
	defer s.Close()
	ui, err := newArmyUI(c, s, a)
	if err != nil {
		return err
	}
	preference := filepath.Join(*session, "font-preference.json")
	selected, err := game.LoadFontPreference(preference)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
	}
	ui.Font = selected
	if *capture != "" {
		st, err := os.Stat(*capture)
		if err != nil || !st.IsDir() {
			return errors.New("抽驗目錄不存在")
		}
	}
	g := &armyUIApp{UI: ui, Fonts: font, Texture: ebiten.NewImage(armyUIWidth, armyUIHeight), Capture: *capture, Preference: preference, MaxUpdates: *maxUpdates}
	ebiten.SetWindowSize(int(float64(armyUIWidth)**scale), int(float64(armyUIHeight)**scale))
	ebiten.SetWindowTitle("神州八劍・軍隊試作")
	ebiten.SetTPS(30)
	if err = ebiten.RunGame(g); err != nil {
		return err
	}
	if *capture != "" {
		return g.writeStatus("ui-final.json")
	}
	return nil
}
func main() {
	if err := runArmyUI(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
