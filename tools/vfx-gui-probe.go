//go:build ignore

// Private GUI observer and explicitly enabled memory fixture; never production.
package eightsword

import (
	"bytes"
	"compress/gzip"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"github.com/wicanr2/dosgolem/oracle"
	"image"
	"image/png"
	"os"
	"path/filepath"
)

var researchVFXScene *ownedScene
var researchVFX struct {
	armed, changed bool
	forced         int
	mutations      []map[string]any
	seen           map[string]bool
	pending        *image.RGBA
	base, layer    *image.RGBA
	mask           []byte
	meta           map[string]any
}

func (e *Engine) ResearchVFXTick() error {
	if os.Getenv("EIGHTSWORD_VFX_FIXTURE") != "1" || researchVFX.armed || e.battleVFX == nil {
		return nil
	}
	researchVFX.armed = true
	v := e.battleVFX
	e.Oracle.OnCall(oracle.Addr{Seg: v.code, Off: 0x216a}, func(o *oracle.Oracle) {
		if researchVFX.changed {
			return
		}
		change := func(off, value uint16) {
			at := oracle.Addr{Seg: v.data, Off: off}
			old := o.Word(at)
			if old != value {
				o.WriteU16(at, value)
				researchVFX.mutations = append(researchVFX.mutations, map[string]any{"step": o.Steps(), "offset": off, "old": old, "new": value})
			}
		}
		for i := uint16(0); i < 6; i++ {
			n := uint16(0)
			if i == 0 {
				n = 50
			}
			change(0x5702+i*4, n)
		}
		change(0x5700, 12)
		for i, id := range []uint16{5, 5, 5, 0, 5, 5} {
			change(0x6fc2+uint16(i*2), id)
		}
		researchVFX.changed = true
	})
	e.Oracle.OnCall(oracle.Addr{Seg: v.code, Off: 0xd88}, func(o *oracle.Oracle) {
		if !researchVFX.changed || researchVFX.forced >= 8 {
			return
		}
		at := oracle.Addr{Seg: o.Regs().SS, Off: o.Regs().BP - 4}
		old := o.Word(at)
		o.WriteU16(at, 0)
		researchVFX.forced++
		researchVFX.mutations = append(researchVFX.mutations, map[string]any{"step": o.Steps(), "selector_old": old, "selector_new": 0})
	})
	return nil
}
func (e *Engine) ResearchVFXFrame(out string, frame *image.RGBA) error {
	researchVFX.pending = nil
	v := e.battleVFX
	if v == nil || !v.Active || frame != v.cached || researchVFXScene == nil {
		return nil
	}
	key := v.cachedPhase
	if researchVFX.seen[key] || key == "" {
		return nil
	}
	if err := os.MkdirAll(filepath.Join(out, "vfx-draw"), 0755); err != nil {
		return err
	}
	before := filepath.Join(out, "vfx-draw", key+"-before.state")
	after := filepath.Join(out, "vfx-draw", key+"-after.state")
	if err := e.Oracle.SaveStateFile(before); err != nil {
		return err
	}
	e.battleVFX = nil
	base := e.sourceRender()
	e.battleVFX = v
	if err := e.Oracle.SaveStateFile(after); err != nil {
		return err
	}
	a, err := os.ReadFile(before)
	if err != nil {
		return err
	}
	b, err := os.ReadFile(after)
	if err != nil {
		return err
	}
	if !bytes.Equal(a, b) {
		return fmt.Errorf("diagnostic base frame changed guest")
	}
	layer := drawBattleVFX(key, float64(v.cachedSample)/120, v.Source, v.Target)
	if layer == nil {
		return nil
	}
	mask := make([]byte, 128000)
	for i, pixel := range researchVFXScene.Pixels[researchVFXScene.Start : researchVFXScene.Start+128000] {
		if pixel.Text.ID != 0 {
			mask[i] = 1
		}
	}
	researchVFX.pending, researchVFX.base, researchVFX.layer, researchVFX.mask = frame, base, layer, mask
	researchVFX.meta = map[string]any{"phase": key, "step": e.Oracle.Steps(), "cycles": e.Oracle.Cycles(), "sample": v.cachedSample, "vfx": v.BattleVFXInfo, "layer_rect": []int{layer.Rect.Min.X, layer.Rect.Min.Y, layer.Rect.Dx(), layer.Rect.Dy()}, "layer_stride": layer.Stride, "guest_state_sha256": fmt.Sprintf("%x", sha256.Sum256(a)), "frame_guest_pure": true, "fixture": researchVFX.changed}
	return nil
}
func (e *Engine) ResearchVFXDraw(out string, presented *image.RGBA, draw uint64) error {
	if researchVFX.pending == nil {
		return nil
	}
	key := researchVFX.meta["phase"].(string)
	if researchVFX.seen[key] {
		return nil
	}
	dir := filepath.Join(out, "vfx-draw")
	for name, im := range map[string]*image.RGBA{"central": researchVFX.pending, "base": researchVFX.base, "presented": presented} {
		f, err := os.Create(filepath.Join(dir, key+"-"+name+".png"))
		if err != nil {
			return err
		}
		err = png.Encode(f, im)
		closed := f.Close()
		if err != nil {
			return err
		}
		if closed != nil {
			return closed
		}
	}
	for name, raw := range map[string][]byte{"layer-rgba": researchVFX.layer.Pix, "native-text-mask": researchVFX.mask} {
		f, err := os.Create(filepath.Join(dir, key+"-"+name+".bin.gz"))
		if err != nil {
			return err
		}
		gz := gzip.NewWriter(f)
		if _, err = gz.Write(raw); err != nil {
			return err
		}
		if err = gz.Close(); err != nil {
			return err
		}
		if err = f.Close(); err != nil {
			return err
		}
	}
	researchVFX.meta["draw"] = draw
	researchVFX.meta["method"] = "After actual Ebiten Draw; immutable CPU image was uploaded, X11 screenshot is a separate nearby-frame sample."
	raw, err := json.MarshalIndent(researchVFX.meta, "", "  ")
	if err != nil {
		return err
	}
	if err = os.WriteFile(filepath.Join(dir, key+".json"), append(raw, '\n'), 0644); err != nil {
		return err
	}
	if researchVFX.seen == nil {
		researchVFX.seen = map[string]bool{}
	}
	researchVFX.seen[key] = true
	return nil
}
func (e *Engine) ResearchVFXStatus() map[string]any {
	return map[string]any{"armed": researchVFX.armed, "fixture": researchVFX.changed, "forced_selectors": researchVFX.forced, "mutations": researchVFX.mutations, "seen": researchVFX.seen}
}
