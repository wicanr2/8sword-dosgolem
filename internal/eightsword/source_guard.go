package eightsword

import (
	"fmt"
	"image"

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

// Only our explicitly typed contract failures are caught. Runtime panics and
// I/O failures remain defects; silently swallowing them would hide evidence.
func (e *Engine) sourceGuardCall(fn func()) {
	if e.renderFault != nil {
		return
	}
	defer func() {
		if v := recover(); v != nil {
			if f, ok := v.(*OwnedRenderFault); ok {
				e.renderFault = f
				return
			}
			panic(v)
		}
	}()
	fn()
}

func (e *Engine) sourceReject(phase, reason string) {
	r := e.Oracle.Regs()
	e.sourceRejectAt(phase, reason, e.Oracle.Steps(), r.CS, r.IP, e.Oracle.VideoMode())
}

func (e *Engine) sourceRejectAt(phase, reason string, step uint64, cs, ip uint16, mode uint8) {
	panic(&OwnedRenderFault{phase, reason, step, cs, ip, mode})
}

func (p *sourceAdapter) reject(reason string)      { p.e.sourceReject("pam", reason) }
func (p *sourceIntroAdapter) reject(reason string) { p.e.sourceReject("intro", reason) }

func (p *sourceAdapter) onCall(at oracle.Addr, fn func(*oracle.Oracle)) {
	p.e.Oracle.OnCall(at, func(o *oracle.Oracle) {
		if !p.e.inEndingPhase() {
			p.e.sourceGuardCall(func() { fn(o) })
		}
	})
}
func (p *sourceIntroAdapter) onCall(at oracle.Addr, fn func(*oracle.Oracle)) {
	p.e.Oracle.OnCall(at, func(o *oracle.Oracle) { p.e.sourceGuardCall(func() { fn(o) }) })
}

func (e *Engine) sourceGuardObserver(ob PresentationObserver) func() {
	return e.ObservePresentation(PresentationObserver{
		Write: func(v PresentationWrite) {
			e.sourceGuardCall(func() {
				if ob.Write != nil {
					ob.Write(v)
				}
			})
		},
		ModeChange: func(v PresentationModeChange) {
			e.sourceGuardCall(func() {
				phase, admitted := "intro", v.Mode == 3 || v.Mode == 0x0e || v.Mode == 0x13
				if e.PAMLoaded {
					phase, admitted = "pam", v.Mode == 3 || v.Mode == 0x0e
				}
				if e.inEndingPhase() {
					phase, admitted = "ending", v.Mode == 3 || v.Mode == 0x0e
				}
				if !admitted {
					r := e.Oracle.Regs()
					e.sourceRejectAt(phase, "unhandled-display-mode", v.Step, r.CS, r.IP, v.Mode)
				}
				if ob.ModeChange != nil {
					ob.ModeChange(v)
				}
			})
		},
	})
}

func (p *sourceAdapter) observe(ob PresentationObserver) func() {
	return p.e.sourceGuardObserver(PresentationObserver{
		Write: func(v PresentationWrite) {
			if !p.e.inEndingPhase() && ob.Write != nil {
				ob.Write(v)
			}
		},
		ModeChange: func(v PresentationModeChange) {
			if !p.e.inEndingPhase() && ob.ModeChange != nil {
				ob.ModeChange(v)
			}
		},
	})
}
func (p *sourceIntroAdapter) observe(ob PresentationObserver) func() {
	return p.e.sourceGuardObserver(ob)
}

func (e *Engine) sourceGuardFrame(render func() *image.RGBA) *image.RGBA {
	var out *image.RGBA
	e.sourceGuardCall(func() { out = render() })
	if e.renderFault != nil {
		e.sourceHeldFrames++
		if e.sourceHeldFrame == nil {
			e.sourceHeldFrame = image.NewRGBA(image.Rect(0, 0, 1920, 1200))
			for i := 3; i < len(e.sourceHeldFrame.Pix); i += 4 {
				e.sourceHeldFrame.Pix[i] = 255
			}
		}
		return e.sourceHeldFrame
	}
	if out != nil {
		e.sourceHeldFrame = out
	}
	return out
}
