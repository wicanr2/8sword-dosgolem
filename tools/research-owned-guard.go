//go:build ignore

package eightsword

import (
	"encoding/json"
	"fmt"
	"image"
	"os"
	"path/filepath"

	"github.com/wicanr2/dosgolem/oracle"
)

// OwnedRenderFault is a diagnostic, not a guest exception or a recovery rule.
type OwnedRenderFault struct {
	Phase  string `json:"phase"`
	Reason string `json:"reason"`
	Step   uint64 `json:"step"`
	CS     uint16 `json:"cs"`
	IP     uint16 `json:"ip"`
	Mode   uint8  `json:"mode"`
}

func (f *OwnedRenderFault) Error() string {
	return fmt.Sprintf("HD 來源呈現停止：%s/%s，執行期 %04X:%04X，step %d，mode %02X", f.Phase, f.Reason, f.CS, f.IP, f.Step, f.Mode)
}

func (e *Engine) researchGuardEnabled() bool {
	return os.Getenv("EIGHTSWORD_RESEARCH_GUARD_CONTROL") != "1"
}

// Only our explicitly typed contract failures are caught. Runtime panics and
// I/O failures remain defects; silently swallowing them would hide evidence.
func (e *Engine) researchGuardCall(fn func()) {
	if e.researchRenderFault != nil {
		return
	}
	defer func() {
		if v := recover(); v != nil {
			if f, ok := v.(*OwnedRenderFault); ok {
				e.researchRenderFault = f
				return
			}
			panic(v)
		}
	}()
	fn()
}

func (e *Engine) researchReject(phase, reason string) {
	r := e.Oracle.Regs()
	e.researchRejectAt(phase, reason, e.Oracle.Steps(), r.CS, r.IP, e.Oracle.VideoMode())
}

func (e *Engine) researchRejectAt(phase, reason string, step uint64, cs, ip uint16, mode uint8) {
	if !e.researchGuardEnabled() {
		return
	}
	panic(&OwnedRenderFault{phase, reason, step, cs, ip, mode})
}

func (p *ownedProbe) reject(reason string)      { p.e.researchReject("pam", reason) }
func (p *ownedIntroProbe) reject(reason string) { p.e.researchReject("intro", reason) }

func (p *ownedProbe) onCall(at oracle.Addr, fn func(*oracle.Oracle)) {
	p.e.Oracle.OnCall(at, func(o *oracle.Oracle) { p.e.researchGuardCall(func() { fn(o) }) })
}
func (p *ownedIntroProbe) onCall(at oracle.Addr, fn func(*oracle.Oracle)) {
	p.e.Oracle.OnCall(at, func(o *oracle.Oracle) { p.e.researchGuardCall(func() { fn(o) }) })
}

func (e *Engine) researchGuardObserver(ob PresentationObserver) func() {
	return e.ObservePresentation(PresentationObserver{
		Write: func(v PresentationWrite) {
			e.researchGuardCall(func() {
				if ob.Write != nil {
					ob.Write(v)
				}
			})
		},
		ModeChange: func(v PresentationModeChange) {
			e.researchGuardCall(func() {
				phase, admitted := "intro", v.Mode == 3 || v.Mode == 0x0e || v.Mode == 0x13
				if e.PAMLoaded {
					phase, admitted = "pam", v.Mode == 3 || v.Mode == 0x0e
				}
				if !admitted {
					r := e.Oracle.Regs()
					e.researchRejectAt(phase, "unhandled-display-mode", v.Step, r.CS, r.IP, v.Mode)
				}
				if ob.ModeChange != nil {
					ob.ModeChange(v)
				}
			})
		},
	})
}

func (p *ownedProbe) observe(ob PresentationObserver) func() { return p.e.researchGuardObserver(ob) }
func (p *ownedIntroProbe) observe(ob PresentationObserver) func() {
	return p.e.researchGuardObserver(ob)
}

func (e *Engine) researchGuardFrame(render func() *image.RGBA) *image.RGBA {
	var out *image.RGBA
	e.researchGuardCall(func() { out = render() })
	if e.researchRenderFault != nil {
		e.researchGuardHeldFrames++
		if e.researchGuardHeld == nil {
			e.researchGuardHeld = image.NewRGBA(image.Rect(0, 0, 1920, 1200))
			for i := 3; i < len(e.researchGuardHeld.Pix); i += 4 {
				e.researchGuardHeld.Pix[i] = 255
			}
		}
		return e.researchGuardHeld
	}
	if out != nil {
		e.researchGuardHeld = out
	}
	return out
}

func (e *Engine) researchGuardFinish(out string) error {
	data, err := json.MarshalIndent(map[string]any{
		"production": false, "enabled": e.researchGuardEnabled(), "fault": e.researchRenderFault,
		"held_frames": e.researchGuardHeldFrames, "renderer_reads_vga": false,
		"address_space": "dosgolem runtime CS:IP and guest Step; mode-change timestamp is pre-palette",
		"scope":         "typed source rejection, unclassified writes and unsupported modes; no guessed resynchronization",
	}, "", "  ")
	if err != nil {
		return err
	}
	f, err := os.OpenFile(filepath.Join(out, "owned-guard-receipt.json"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
	if err != nil {
		return err
	}
	_, writeErr := f.Write(append(data, 10))
	closeErr := f.Close()
	if writeErr != nil {
		return writeErr
	}
	return closeErr
}
