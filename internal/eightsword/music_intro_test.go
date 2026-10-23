package eightsword

import (
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

func introTone() []byte {
	var code []byte
	for _, rv := range [][2]byte{{0x20, 1}, {0x23, 1}, {0x40, 0x10}, {0x43, 0}, {0x60, 0xf0}, {0x63, 0xf0}, {0x80, 0x77}, {0x83, 0x77}, {0xa0, 0x98}, {0xb0, 0x31}} {
		code = append(code, 0xba, 0x88, 3, 0xb0, rv[0], 0xee, 0x42, 0xb0, rv[1], 0xee)
	}
	return append(code, 0xeb, 0xfe)
}

func TestMusicIntroInitializationAndHandoff(t *testing.T) {
	o := musicFixture(t, introTone())
	sound := o.NewAudio(48000)
	track := &MusicCue{ID: 1, Frames: 2, PCM: []int16{100, 200, 300, 400}}
	m := &Music{o: o, tracks: map[int]*MusicCue{1: track}, seenOPL: map[uint64]uint8{}}
	// PREDELLA has no intervening Stop call before initialization.
	m.queue = []MusicEvent{{Kind: "request", Cue: 1, Valid: true, Reason: introProgram}}
	for i := 0; i < 2; i++ {
		if err := o.RunCycles(75000); err != nil {
			t.Fatal(err)
		}
		for _, v := range m.Render(sound) {
			if v != 0 {
				t.Fatal("intro native FM leaked before validated Start")
			}
		}
	}
	if !m.oplMuted || m.playing != nil {
		t.Fatal(m.Status())
	}
	start := o.Cycles()
	m.queue = []MusicEvent{{Kind: "start", Cue: 1, Cycles: start, Valid: true, Reason: introProgram}, {Kind: "handoff", Cycles: start + 37500, Valid: true, Reason: introProgram}}
	if err := o.RunCycles(75000); err != nil {
		t.Fatal(err)
	}
	pcm := m.Render(sound)
	if pcm[0] != 100 || pcm[1] != 200 || m.playing != nil || m.oplMuted || m.CurrentCue != 0 {
		t.Fatal("handoff did not leave HD cleanly", m.Status())
	}
	nonzero := false
	for _, v := range pcm[4800:] {
		nonzero = nonzero || v != 0
	}
	if !nonzero || m.Stops != 0 || m.Fallbacks != 0 {
		t.Fatal("handoff lost native sound or fabricated a Stop/failure", m.Status())
	}
}

func TestMusicIntroDisabledRequestPreservesNative(t *testing.T) {
	o := musicFixture(t, introTone())
	sound := o.NewAudio(48000)
	track := &MusicCue{ID: 1, Frames: 2, PCM: []int16{100, 200, 300, 400}}
	m := &Music{o: o, tracks: map[int]*MusicCue{1: track}, seenOPL: map[uint64]uint8{}}
	m.queue = []MusicEvent{{Kind: "request", Cue: 1, Valid: false, Reason: introProgram}}
	if err := o.RunCycles(75000); err != nil {
		t.Fatal(err)
	}
	nonzero := false
	for _, v := range m.Render(sound) {
		nonzero = nonzero || v != 0
	}
	if !nonzero || m.oplMuted || m.playing != nil {
		t.Fatal("disabled original intro request suppressed native sound")
	}
}

func TestMusicIntroProducerInterval(t *testing.T) {
	m := &Music{introBound: true, introBoundCycle: 100, introRetired: true, introEndStep: 200, bound: true, boundCycle: 400}
	for _, test := range []struct {
		step, cycles uint64
		observed     bool
	}{{50, 99, false}, {100, 100, true}, {199, 299, true}, {200, 300, false}, {201, 399, false}, {202, 400, true}} {
		if got := m.observedWrite(oracle.OPLWrite{Step: test.step, Cycles: test.cycles}); got != test.observed {
			t.Fatal("producer scope crosses program boundary", test, got)
		}
	}
	o := musicFixture(t, []byte{0xeb, 0xfe})
	m.o = o
	m.introRetired = false
	m.retireIntro(200)
	m.retireIntro(201)
	if len(m.Events) != 1 || m.Events[0].Kind != "handoff" || m.introEndStep != 200 || m.introLive() {
		t.Fatal("retired observer remained active or repeated handoff", m.Status())
	}
}
