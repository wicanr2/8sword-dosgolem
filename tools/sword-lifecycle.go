//go:build ignore

package main

import (
	"fmt"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
	"image"
	"image/draw"
)

// PAE reuses PAM linear addresses. Only this candidate's gameplay callbacks
// stop at the proven ending entry; the Engine's rendering hooks remain active.
var swordGameplayEnded bool

func swordOnCall(o *oracle.Oracle, a oracle.Addr, fn func(*oracle.Oracle)) {
	o.OnCall(a, func(q *oracle.Oracle) {
		if !swordGameplayEnded {
			fn(q)
		}
	})
}
func swordOnHostInstruction(o *oracle.Oracle, a oracle.Addr, fn func(*dg.Machine) (bool, error)) {
	o.OnHostInstruction(a, func(m *dg.Machine) (bool, error) {
		if swordGameplayEnded {
			return false, nil
		}
		return fn(m)
	})
}
func swordDecorate(g *armyReviewApp, frame *image.RGBA, texts []armyUIText) (*image.RGBA, []armyUIText) {
	if frame == nil || !g.Owned || !g.Bound || g.Port == nil || g.view() != "character" || swordGameplayEnded {
		return frame, texts
	}
	flags, e := savedSwords(g.Port.Current.Bytes.Native)
	if e != nil {
		return frame, texts
	}
	n := 0
	for _, v := range flags {
		if v {
			n++
		}
	}
	out := image.NewRGBA(frame.Bounds())
	draw.Draw(out, out.Bounds(), frame, image.Point{}, draw.Src)
	p := armyUIPaint{Fonts: g.Fonts, Canvas: out, Font: g.Engine.FontID()}
	p.text("swords", fmt.Sprintf("八劍: %d / 8", n), image.Rect(850, 250, 1310, 310), 40, uiGold, true)
	return out, append(texts, p.Texts...)
}
