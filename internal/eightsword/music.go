package eightsword

import (
	"bytes"
	"sort"
	"strings"

	"github.com/wicanr2/dosgolem/oracle"
)

type MusicEvent struct {
	Kind   string `json:"kind"`
	Cue    int    `json:"cue"`
	Step   uint64 `json:"step"`
	Cycles uint64 `json:"cycles"`
	Valid  bool   `json:"valid"`
	Reason string `json:"reason,omitempty"`
}

// Music observes the fixed PAM version. It never replaces guest instructions.
type Music struct {
	endingRetired                                      bool
	oplMuted                                           bool
	nextHD                                             bool
	blocked                                            bool
	o                                                  *oracle.Oracle
	pam                                                []byte
	tracks                                             map[int]*MusicCue
	bound                                              bool
	boundCycle                                         uint64
	introBound, introRetired, introRequestValid        bool
	introBoundCycle, introEndStep                      uint64
	pending                                            int
	queue                                              []MusicEvent
	Events                                             []MusicEvent
	seenOPL                                            map[uint64]uint8
	playing                                            *MusicCue
	position                                           int64
	lastCycle                                          uint64
	LoadError                                          string
	BindingError                                       string
	CurrentCue                                         int
	Starts, Stops, Fallbacks, Loops, HDFrames, Clipped uint64
}

func newMusic(o *oracle.Oracle, pam []byte, dir string, enabled bool) *Music {
	m := &Music{o: o, pam: pam, seenOPL: map[uint64]uint8{}, lastCycle: o.Cycles()}
	if enabled {
		var err error
		m.tracks, err = loadMusicAssets(dir)
		if err != nil {
			m.LoadError = err.Error()
		}
	}
	return m
}

func (m *Music) record(event MusicEvent) {
	m.queue = append(m.queue, event)
	m.Events = append(m.Events, event)
	if len(m.Events) > 256 {
		m.Events = append([]MusicEvent(nil), m.Events[len(m.Events)-256:]...)
	}
}
func (m *Music) event(kind string, cue int, valid bool, reason string) {
	if _, ending := endingOverlay(m.o); ending && kind != "handoff" {
		return
	}
	m.record(MusicEvent{kind, cue, m.o.Steps(), m.o.Cycles(), valid, reason})
}

func (m *Music) Bind() {
	if _, ending := endingOverlay(m.o); ending {
		if !m.endingRetired {
			m.endingRetired = true
			m.bound = false
			m.introBound = false
			m.event("handoff", 0, true, "PAE.AY")
		}
		return
	}
	m.bindIntro()
	if m.bound || m.BindingError != "" {
		return
	}
	for _, overlay := range m.o.Overlays() {
		if !strings.EqualFold(overlay.Name, "PAM.AY") {
			continue
		}
		if overlay.Seg != 0x110 || overlay.Reloc != 0x110 {
			m.BindingError = "未知 PAM 音樂重定位"
			return
		}
		// This prologue contains no relocated operand. Original names/locations
		// and the complete source identity remain in spec 008.
		if !bytes.Equal(m.o.Bytes(oracle.Far(0x110, 0x5cd0), 6), []byte{0x55, 0x8b, 0xec, 0xb8, 4, 0}) {
			m.BindingError = "PAM 音樂入口不符"
			return
		}
		m.bound = true
		m.boundCycle = m.o.Cycles()
		at := func(ida uint32) oracle.Addr {
			linear := ida - 0xef00
			return oracle.Far(uint16(linear>>4), uint16(linear&15))
		}
		m.o.OnCall(at(0x15cd0), func(o *oracle.Oracle) {
			m.pending = int(o.Arg(0))
			_, ok := musicSources[m.pending]
			m.event("request", m.pending, ok, "")
		})
		m.o.OnCall(at(0x26100), func(*oracle.Oracle) { m.event("stop", 0, true, "") })
		m.o.OnCall(at(0x15e6e), func(o *oracle.Oracle) {
			id := m.pending
			m.pending = 0
			s, ok := musicSources[id]
			if !ok {
				m.event("start", id, false, "未知原版曲目")
				return
			}
			if o.Byte(oracle.Far(0x1e82, 0x0e)) != 1 {
				m.event("start", id, false, "原版未進入播放狀態")
				return
			}
			if hash(o.Bytes(oracle.Far(0x9000, 0), s.ScoreBytes)) != s.ScoreSHA || hash(o.Bytes(oracle.Far(0x9400, 0), s.BankBytes)) != s.BankSHA {
				m.event("start", id, false, "原版音樂緩衝區來源不符")
				return
			}
			m.event("start", id, true, "")
		})
		if len(m.tracks) > 0 {
			m.o.OnCall(at(0x28efb), func(o *oracle.Oracle) {
				r := o.Regs()
				if r.DX == 0x389 {
					m.seenOPL[o.Steps()+1] = uint8(r.AX)
				}
			})
		}
		return
	}
}

func stereoMono(pcm []int16) []int16 {
	out := make([]int16, len(pcm)*2)
	for i, v := range pcm {
		out[i*2], out[i*2+1] = v, v
	}
	return out
}

func (m *Music) trackFor(e MusicEvent) *MusicCue {
	if e.Kind != "start" || !e.Valid || m.o.DOSBoxCycles() == 0 || m.BindingError != "" {
		return nil
	}
	return m.tracks[e.Cue]
}

func (m *Music) apply(e MusicEvent) {
	switch e.Kind {
	case "request":
		m.blocked = false
		m.nextHD = m.trackFor(MusicEvent{Kind: "start", Cue: e.Cue, Valid: e.Valid}) != nil
		if e.Reason == introProgram {
			m.playing = nil
			m.position = 0
			m.oplMuted = m.nextHD
		}
	case "start":
		m.Starts++
		m.CurrentCue = e.Cue
		m.playing = m.trackFor(e)
		if m.blocked {
			m.playing = nil
		}
		m.oplMuted = m.playing != nil
		m.nextHD = false
		m.position = 0
	case "stop":
		m.Stops++
		m.CurrentCue = 0
		m.playing = nil
		m.oplMuted = m.nextHD
		m.position = 0
	case "fallback":
		m.blocked = true
		m.Fallbacks++
		m.playing = nil
		m.oplMuted = false
		m.nextHD = false
		m.position = 0
	case "handoff":
		m.playing = nil
		m.position = 0
		m.CurrentCue = 0
		m.oplMuted = false
		m.nextHD = false
		m.blocked = false
	}
}

// Render returns interleaved stereo. It uses the same sample boundaries as the
// original synthesizer; output is not driven by host frame rate or wall time.
func (m *Music) Render(sound *oracle.Audio) []int16 {
	now := m.o.Cycles()
	if m.o.DOSBoxCycles() == 0 || now < m.lastCycle {
		m.playing = nil
		m.position = 0
		for _, e := range m.queue {
			m.apply(e)
		}
		m.playing = nil
		m.queue = nil
		m.oplMuted = false
		m.nextHD = false
		clear(m.seenOPL)
		m.lastCycle = now
		return stereoMono(sound.Render())
	}
	// An unexpected producer overrides HD at its actual write cycle. The
	// native synthesizer still receives it and all speaker writes.
	if (m.bound || m.introBound) && len(m.tracks) > 0 {
		for _, w := range m.o.OPLWrites() {
			if w.Cycles < m.lastCycle || !m.observedWrite(w) {
				continue
			}
			v, ok := m.seenOPL[w.Step]
			if w.Bank != 0 || !ok || v != w.Val {
				m.record(MusicEvent{"fallback", m.CurrentCue, w.Step, w.Cycles, false, "未知 OPL 寫入來源"})
			}
		}
	}
	clear(m.seenOPL)
	events := m.queue
	m.queue = nil
	sort.SliceStable(events, func(i, j int) bool {
		if events[i].Cycles != events[j].Cycles {
			return events[i].Cycles < events[j].Cycles
		}
		return events[i].Kind != "fallback" && events[j].Kind == "fallback"
	})
	points := make([]oracle.OPLMutePoint, 0, len(events))
	nextHD := m.nextHD
	blocked := m.blocked
	for _, e := range events {
		switch e.Kind {
		case "request":
			blocked = false
			nextHD = m.trackFor(MusicEvent{Kind: "start", Cue: e.Cue, Valid: e.Valid}) != nil
			if e.Reason == introProgram {
				points = append(points, oracle.OPLMutePoint{At: e.Cycles, Muted: nextHD})
			}
		case "stop":
			points = append(points, oracle.OPLMutePoint{At: e.Cycles, Muted: nextHD})
		case "fallback":
			blocked = true
			nextHD = false
			points = append(points, oracle.OPLMutePoint{At: e.Cycles, Muted: false})
		case "start":
			nextHD = false
			points = append(points, oracle.OPLMutePoint{At: e.Cycles, Muted: !blocked && m.trackFor(e) != nil})
		case "handoff":
			blocked = false
			nextHD = false
			points = append(points, oracle.OPLMutePoint{At: e.Cycles, Muted: false})
		}
	}
	native := sound.RenderWithOPLMute(m.oplMuted, points)
	out := make([]int16, len(native)*2)
	span, ei := now-m.lastCycle, 0
	for i, v := range native {
		at := m.lastCycle + uint64(float64(span)*float64(i)/float64(len(native)))
		for ei < len(events) && events[ei].Cycles <= at {
			m.apply(events[ei])
			ei++
		}
		for c := 0; c < 2; c++ {
			x := int32(v)
			if m.playing != nil {
				x += int32(m.playing.PCM[m.position*2+int64(c)])
			}
			if x > 32767 {
				x = 32767
				m.Clipped++
			}
			if x < -32768 {
				x = -32768
				m.Clipped++
			}
			out[i*2+c] = int16(x)
		}
		if m.playing != nil {
			m.HDFrames++
			m.position++
			if m.position == m.playing.Frames {
				m.position = 0
				m.Loops++
			}
		}
	}
	for ; ei < len(events); ei++ {
		m.apply(events[ei])
	}
	m.lastCycle = now
	return out
}

func (m *Music) Status() map[string]any {
	mode := "native"
	if m.playing != nil {
		mode = "hd"
	} else if m.oplMuted {
		mode = "loading-hd"
	}
	return map[string]any{"bound": m.bound, "intro_bound": m.introBound, "intro_retired": m.introRetired, "intro_bound_cycle": m.introBoundCycle, "intro_end_step": m.introEndStep, "mode": mode, "cue": m.CurrentCue, "frame": m.position, "loaded_cues": len(m.tracks), "load_error": m.LoadError, "binding_error": m.BindingError, "starts": m.Starts, "stops": m.Stops, "fallbacks": m.Fallbacks, "loops": m.Loops, "hd_frames": m.HDFrames, "clipped_samples": m.Clipped, "events": m.Events}
}

func (m *Music) Close() { m.playing = nil; m.tracks = nil; m.queue = nil; clear(m.seenOPL) }
