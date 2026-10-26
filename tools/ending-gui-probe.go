//go:build ignore

// 053: copied only into an isolated GUI diagnostic module by prepare-ending-gui.
package eightsword

import (
	"encoding/json"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"

	"github.com/wicanr2/dosgolem/oracle"
)

var endingGUIProbe struct {
	armed, changed bool
	mutations      []map[string]any
	pending        *image.RGBA
	meta           map[string]any
	seen           map[string]bool
	samples        []map[string]any
}

func (e *Engine) ResearchEndingTick(out string) error {
	if os.Getenv("EIGHTSWORD_RESEARCH_ENDING_BRANCH") != "1" || endingGUIProbe.armed || !e.PAMLoaded {
		return nil
	}
	endingGUIProbe.armed = true
	e.Oracle.OnCall(oracle.Addr{Seg: 0x110, Off: 0x20e}, func(o *oracle.Oracle) {
		if endingGUIProbe.changed || e.inEndingPhase() {
			return
		}
		at := oracle.Addr{Seg: o.Regs().DS, Off: 0x56e2}
		old := o.Word(at)
		o.WriteU16(at, 1)
		endingGUIProbe.changed = true
		endingGUIProbe.mutations = append(endingGUIProbe.mutations, map[string]any{"step": o.Steps(), "address": at, "old": old, "new": 1})
	})
	return nil
}

func (e *Engine) ResearchEndingFrame(frame *image.RGBA) error {
	endingGUIProbe.pending, endingGUIProbe.meta = nil, nil
	p := e.ending
	if !e.inEndingPhase() || p == nil || !p.bound || !p.scene.mode || p.active != 0 || frame != p.cached {
		return nil
	}
	page := p.cachedPage
	stage := page.stage
	if stage != "END5.AY" && stage != "END7.AY" && stage != "END8.AY" && stage != "END9.AY" {
		return nil
	}
	if (stage == "END5.AY" || stage == "END9.AY") && page.glyphs == 0 {
		return nil
	}
	key := stage + "-" + e.FontID()
	if endingGUIProbe.seen[key] {
		return nil
	}
	display, ok := e.Oracle.PlanarDisplay()
	if !ok {
		return fmt.Errorf("diagnostic ending display absent")
	}
	// Capture the immutable command list now, before another Update can change it.
	raw, err := json.Marshal(map[string]any{"stage": stage, "font": e.FontID(), "palette": display.Palette, "ops": page.ops, "glyphs": page.glyphs, "step": e.Oracle.Steps(), "key": key})
	if err != nil {
		return err
	}
	var meta map[string]any
	if err = json.Unmarshal(raw, &meta); err != nil {
		return err
	}
	endingGUIProbe.meta, endingGUIProbe.pending = meta, frame
	return nil
}

func (e *Engine) ResearchEndingDraw(out string, presented *image.RGBA, draw uint64) error {
	if endingGUIProbe.pending == nil {
		return nil
	}
	key := endingGUIProbe.meta["key"].(string)
	if endingGUIProbe.seen[key] {
		return nil
	}
	dir := filepath.Join(out, "ending-draw")
	if err := os.MkdirAll(dir, 0755); err != nil {
		return err
	}
	for name, im := range map[string]*image.RGBA{"central": endingGUIProbe.pending, "presented": presented} {
		f, err := os.Create(filepath.Join(dir, key+"-"+name+".png"))
		if err != nil {
			return err
		}
		err = png.Encode(f, im)
		closeErr := f.Close()
		if err != nil {
			return err
		}
		if closeErr != nil {
			return closeErr
		}
	}
	meta := endingGUIProbe.meta
	meta["draw"] = draw
	meta["method"] = "after actual Ebiten Draw; central CPU frame matches uploaded texture"
	raw, err := json.MarshalIndent(meta, "", "  ")
	if err != nil {
		return err
	}
	if err = os.WriteFile(filepath.Join(dir, key+".json"), append(raw, '\n'), 0644); err != nil {
		return err
	}
	if endingGUIProbe.seen == nil {
		endingGUIProbe.seen = map[string]bool{}
	}
	endingGUIProbe.seen[key] = true
	endingGUIProbe.samples = append(endingGUIProbe.samples, map[string]any{"key": key, "draw": draw, "step": meta["step"]})
	return nil
}

func (e *Engine) ResearchEndingStatus() map[string]any {
	return map[string]any{"armed": endingGUIProbe.armed, "changed": endingGUIProbe.changed, "mutations": endingGUIProbe.mutations, "samples": endingGUIProbe.samples, "seen": endingGUIProbe.seen}
}
