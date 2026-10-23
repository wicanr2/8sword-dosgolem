package eightsword

import (
	"encoding/binary"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

func musicFixture(t *testing.T, code []byte) *oracle.Oracle {
	t.Helper()
	header := make([]byte, 32)
	copy(header, "MZ")
	put := func(off int, v uint16) { binary.LittleEndian.PutUint16(header[off:], v) }
	put(2, uint16((32+len(code))%512))
	put(4, uint16((32+len(code)+511)/512))
	put(8, 2)
	put(10, 0x100)
	put(12, 0xffff)
	put(16, 0x400)
	put(24, 0x1c)
	root := t.TempDir()
	exe := filepath.Join(root, "AUDIO.EXE")
	if err := os.WriteFile(exe, append(header, code...), 0644); err != nil {
		t.Fatal(err)
	}
	o, err := oracle.LoadWith(exe, root, oracle.Options{Adlib: true})
	if err != nil {
		t.Fatal(err)
	}
	o.SetDOSBoxCycles(750)
	t.Cleanup(o.Close)
	return o
}

func TestMusicStereoClockRestartAndStop(t *testing.T) {
	o := musicFixture(t, []byte{0xeb, 0xfe})
	sound := o.NewAudio(48000)
	track := &MusicCue{ID: 1, Frames: 2, PCM: []int16{100, 200, 300, 400}}
	m := &Music{o: o, tracks: map[int]*MusicCue{1: track}, seenOPL: map[uint64]uint8{}}
	m.queue = []MusicEvent{{Kind: "start", Cue: 1, Cycles: 0, Valid: true}, {Kind: "start", Cue: 1, Cycles: 37515, Valid: true}, {Kind: "stop", Cycles: 56250, Valid: true}}
	if err := o.RunCycles(75000); err != nil {
		t.Fatal(err)
	}
	pcm := m.Render(sound)
	if len(pcm) != 9600 {
		t.Fatal("stereo duration", len(pcm))
	}
	for _, frame := range []int{0, 2, 2401, 2403} {
		if pcm[frame*2] != 100 || pcm[frame*2+1] != 200 {
			t.Fatal("start/restart or channels", frame, pcm[frame*2:frame*2+2])
		}
	}
	for _, v := range pcm[3600*2:] {
		if v != 0 {
			t.Fatal("stop did not silence HD")
		}
	}
	if m.Starts != 2 || m.Stops != 1 || m.playing != nil {
		t.Fatal(m.Status())
	}
}

func TestMusicUnknownOPLProducerReturnsNative(t *testing.T) {
	// The fixture emits an OPL write outside the verified PAM producer.
	o := musicFixture(t, []byte{0xba, 0x88, 3, 0xb0, 0x20, 0xee, 0x42, 0xb0, 1, 0xee, 0xeb, 0xfe})
	sound := o.NewAudio(48000)
	track := &MusicCue{ID: 1, Frames: 2, PCM: []int16{100, 200, 300, 400}}
	m := &Music{o: o, bound: true, tracks: map[int]*MusicCue{1: track}, playing: track, seenOPL: map[uint64]uint8{}}
	if err := o.RunCycles(75000); err != nil {
		t.Fatal(err)
	}
	regs := o.Regs()
	pcm := m.Render(sound)
	if len(pcm) != 9600 || m.Fallbacks == 0 || m.playing != nil {
		t.Fatal(m.Status())
	}
	for _, v := range pcm[10:] {
		if v != 0 {
			t.Fatal("unknown source remained HD")
		}
	}
	if regs != o.Regs() {
		t.Fatal("presentation fallback changed CPU")
	}
}

func TestMusicLoadingKeepsFMMutedAcrossUpdates(t *testing.T) {
	var code []byte
	for _, rv := range [][2]byte{{0x20, 1}, {0x23, 1}, {0x40, 0x10}, {0x43, 0}, {0x60, 0xf0}, {0x63, 0xf0}, {0x80, 0x77}, {0x83, 0x77}, {0xa0, 0x98}, {0xb0, 0x31}} {
		code = append(code, 0xba, 0x88, 3, 0xb0, rv[0], 0xee, 0x42, 0xb0, rv[1], 0xee)
	}
	code = append(code, 0xeb, 0xfe)
	o := musicFixture(t, code)
	sound := o.NewAudio(48000)
	track := &MusicCue{ID: 1, Frames: 2, PCM: []int16{100, 200, 300, 400}}
	m := &Music{o: o, tracks: map[int]*MusicCue{1: track}, seenOPL: map[uint64]uint8{}}
	m.queue = []MusicEvent{{Kind: "request", Cue: 1, Valid: true}, {Kind: "stop", Valid: true}}
	for frame := 0; frame < 2; frame++ {
		if err := o.RunCycles(75000); err != nil {
			t.Fatal(err)
		}
		for _, v := range m.Render(sound) {
			if v != 0 {
				t.Fatal("FM leaked during HD initialization")
			}
		}
		if !m.oplMuted || m.playing != nil {
			t.Fatal(m.Status())
		}
	}
	m.queue = []MusicEvent{{Kind: "start", Cue: 1, Cycles: o.Cycles(), Valid: false}}
	if err := o.RunCycles(75000); err != nil {
		t.Fatal(err)
	}
	nonzero := false
	for _, v := range m.Render(sound) {
		nonzero = nonzero || v != 0
	}
	if !nonzero || m.oplMuted || m.playing != nil {
		t.Fatal("failed start did not recover native FM", m.Status())
	}
}

func TestMusicFallbackDuringInitializationWaitsForNewRequest(t *testing.T) {
	o := musicFixture(t, []byte{0xeb, 0xfe})
	sound := o.NewAudio(48000)
	track := &MusicCue{ID: 1, Frames: 2, PCM: []int16{100, 200, 300, 400}}
	m := &Music{o: o, tracks: map[int]*MusicCue{1: track}, seenOPL: map[uint64]uint8{}}
	m.queue = []MusicEvent{{Kind: "request", Cue: 1, Valid: true}, {Kind: "stop", Valid: true}, {Kind: "fallback", Cycles: 100}, {Kind: "start", Cue: 1, Cycles: 200, Valid: true}}
	if err := o.RunCycles(75000); err != nil {
		t.Fatal(err)
	}
	for _, v := range m.Render(sound) {
		if v != 0 {
			t.Fatal("later initializer bypassed unknown-source fallback")
		}
	}
	if m.playing != nil || !m.blocked || m.oplMuted {
		t.Fatal(m.Status())
	}
	m.queue = []MusicEvent{{Kind: "request", Cue: 1, Cycles: o.Cycles(), Valid: true}, {Kind: "stop", Cycles: o.Cycles(), Valid: true}, {Kind: "start", Cue: 1, Cycles: o.Cycles(), Valid: true}}
	if err := o.RunCycles(75000); err != nil {
		t.Fatal(err)
	}
	pcm := m.Render(sound)
	if m.playing == nil || m.blocked || pcm[0] != 100 || pcm[1] != 200 {
		t.Fatal("fresh original request could not recover HD", m.Status())
	}
}

func realMusicDir(t *testing.T) string {
	t.Helper()
	dir := os.Getenv("EIGHTSWORD_TEST_MUSIC_ASSETS")
	if dir == "" {
		t.Skip("未指定本機 HD 音樂素材")
	}
	return dir
}

func TestMusicRealOGGDecode(t *testing.T) {
	dir := realMusicDir(t)
	tracks, err := loadMusicAssets(dir)
	if err != nil {
		t.Fatal(err)
	}
	if len(tracks) != 1 || tracks[1] == nil {
		t.Fatal("missing real MINT track")
	}
	c := tracks[1]
	if c.Frames != 4108980 || len(c.PCM) != 8217960 {
		t.Fatal("actual decoded frame count", c.Frames, len(c.PCM))
	}
	peak := 0
	for _, v := range c.PCM {
		x := int(v)
		if x < 0 {
			x = -x
		}
		if x > peak {
			peak = x
		}
	}
	if peak < 100 || peak >= 32767 {
		t.Fatal("silent or clipped candidate", peak)
	}
}

func TestMusicRealCatalogRejectsFaults(t *testing.T) {
	dir := realMusicDir(t)
	raw, err := os.ReadFile(filepath.Join(dir, "music.json"))
	if err != nil {
		t.Fatal(err)
	}
	var original musicCatalog
	if err = json.Unmarshal(raw, &original); err != nil {
		t.Fatal(err)
	}
	ogg, err := os.ReadFile(filepath.Join(dir, original.Cues[0].File))
	if err != nil {
		t.Fatal(err)
	}
	cases := []struct {
		name   string
		change func(*musicCatalog)
	}{
		{"schema", func(c *musicCatalog) { c.Schema = 2 }},
		{"source", func(c *musicCatalog) { c.Cues[0].ScoreSHA = strings.Repeat("0", 64) }},
		{"path", func(c *musicCatalog) { c.Cues[0].File = "../outside.ogg" }},
		{"channels", func(c *musicCatalog) { c.Cues[0].Channels = 1 }},
		{"frames", func(c *musicCatalog) { c.Cues[0].Frames--; c.Cues[0].LoopEnd-- }},
		{"sha", func(c *musicCatalog) { c.Cues[0].SHA = strings.Repeat("0", 64) }},
		{"duplicate", func(c *musicCatalog) { c.Cues = append(c.Cues, c.Cues[0]) }},
	}
	for _, test := range cases {
		t.Run(test.name, func(t *testing.T) {
			var catalog musicCatalog
			json.Unmarshal(raw, &catalog)
			test.change(&catalog)
			out := t.TempDir()
			data, _ := json.Marshal(catalog)
			if err := os.WriteFile(filepath.Join(out, "music.json"), data, 0644); err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(filepath.Join(out, original.Cues[0].File), ogg, 0644); err != nil {
				t.Fatal(err)
			}
			tracks, err := loadMusicAssets(out)
			if err == nil || tracks != nil {
				t.Fatal("accepted malformed music", err)
			}
		})
	}
}
