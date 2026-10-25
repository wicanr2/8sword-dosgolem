//go:build ignore

package eightsword

import (
	"bytes"
	"encoding/binary"
	"os"

	"github.com/wicanr2/dosgolem/oracle"
)

// Spec047: fixed-PAM IDA functions sub_159C4/sub_154EA/sub_14E7E.
// All offsets are runtime IP with load=0110, not IDA linear addresses.
func (p *ownedProbe) bindRecruitmentPanels() {
	o, t := p.e.Oracle, p.e.Tracker
	control := os.Getenv("EIGHTSWORD_RESEARCH_RECRUIT_CONTROL") == "1"
	p.record("recruitment-policy", map[string]any{"control": control})
	if control {
		return
	}
	header := int(binary.LittleEndian.Uint16(t.pam[8:10])) * 16
	relocated := append([]byte(nil), t.pam[header:]...)
	table, count := int(binary.LittleEndian.Uint16(t.pam[24:26])), int(binary.LittleEndian.Uint16(t.pam[6:8]))
	for i := 0; i < count; i++ {
		entry := table + i*4
		at := int(binary.LittleEndian.Uint16(t.pam[entry:])) + int(binary.LittleEndian.Uint16(t.pam[entry+2:]))*16
		if at+2 > len(relocated) {
			p.reject("recruitment-relocation-bounds")
			return
		}
		binary.LittleEndian.PutUint16(relocated[at:], binary.LittleEndian.Uint16(relocated[at:])+t.loadSegment)
	}
	for _, site := range []struct {
		off uint16
		ret bool
	}{
		{0x59c4, false}, {0x54ea, false}, {0x4e7e, false}, {0x4ea6, false}, {0x4ece, false},
		{0x50c9, true}, {0x50e1, true}, {0x5683, false}, {0x844c, false},
		{0x5565, true}, {0x5772, true}, {0x5a53, true},
	} {
		at := int(site.off)
		if !bytes.Equal(o.Bytes(oracle.Addr{Seg: t.loadSegment, Off: site.off}, 16), relocated[at:at+16]) || site.ret && relocated[at] != 0xcb {
			p.reject("recruitment-boundary-ABI")
			return
		}
	}
	recruiting, input := false, false
	finish := func() {
		if p.panel != nil && (p.panel.Kind == "recruitment" || p.panel.Kind == "recruitment-edit" || p.panel.Kind == "recruitment-result") {
			p.finishPanel()
		}
	}
	call := func(off uint16, fn func(*oracle.Oracle)) { p.onCall(oracle.Addr{Seg: t.loadSegment, Off: off}, fn) }
	call(0x59c4, func(*oracle.Oracle) { recruiting = true; p.beginPanel("recruitment") })
	call(0x54ea, func(*oracle.Oracle) {
		if recruiting {
			p.beginPanel("recruitment")
		}
	})
	call(0x4e7e, func(*oracle.Oracle) {
		if recruiting {
			input = true
		}
	})
	call(0x4ea6, func(*oracle.Oracle) {
		if input {
			finish()
		}
	})
	call(0x4ece, func(*oracle.Oracle) {
		if !input || p.panel != nil {
			return
		}
		p.beginPanel("recruitment-edit")
		p.record("recruitment-key", map[string]any{"key_ax": o.Regs().AX})
	})
	for _, off := range []uint16{0x50c9, 0x50e1} {
		call(off, func(*oracle.Oracle) {
			if input {
				finish()
				input = false
				p.beginPanel("recruitment-result")
			}
		})
	}
	call(0x5683, func(*oracle.Oracle) {
		if recruiting && p.panel == nil {
			p.beginPanel("recruitment-result")
		}
	})
	for _, off := range []uint16{0x844c, 0x5565, 0x5772} {
		call(off, func(*oracle.Oracle) {
			if recruiting {
				finish()
			}
		})
	}
	call(0x5a53, func(*oracle.Oracle) {
		if recruiting {
			finish()
		}
		recruiting, input = false, false
	})
}
