package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/draw"
	"os"
	"path/filepath"

	"github.com/wicanr2/dosgolem/oracle"
)

const titleSourceSHA = "ff31a0a4916ee1b27a56f2f7da32ec06df3716b42f831b547ed5518586f64060"
const titleDecodedSHA = "5f62f595ac003c069acace22770cd71b99e14d48bdd43db671598f5320c74f65"
const titleTransactionLimit = 2000000

type IntroTitleStats struct {
	Bound, Retired                          bool
	Starts, Composed, Transitions, Timeouts uint64
	Errors                                  []string
}

type IntroTitle struct {
	o          *oracle.Oracle
	ink        image.Image
	Stats      IntroTitleStats
	active     bool
	inDraw     bool
	end        uint16
	start      uint64
	last, hold *image.RGBA
	publisher  *publisherWords
}

func loadIntroTitle(o *oracle.Oracle, dir, root string) (*IntroTitle, error) {
	raw, err := os.ReadFile(filepath.Join(dir, "intro.json"))
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	var m struct {
		Schema        int    `json:"schema"`
		SourceSHA     string `json:"source_sha256"`
		DecodedSHA    string `json:"decoded_sha256"`
		FontSHA       string `json:"font_sha256"`
		Family, Text  string
		Weight        int
		File          string
		SHA           string `json:"sha256"`
		Width, Height int
		InkRect       []int `json:"ink_rect"`
	}
	if err = json.Unmarshal(raw, &m); err != nil {
		return nil, err
	}
	if m.Schema != 1 || m.SourceSHA != titleSourceSHA || m.DecodedSHA != titleDecodedSHA ||
		m.FontSHA != NotoSHA || m.Family != "Noto Sans CJK TC" || m.Weight != 900 || m.Text != "神州八劍" ||
		m.File != "intro-title-noto-r1.png" || m.Width != 1776 || m.Height != 570 || len(m.InkRect) != 4 {
		return nil, fmt.Errorf("HD 片頭清單來源／字型／形狀不符")
	}
	original, err := os.ReadFile(filepath.Join(root, "TIT2.AY"))
	if err != nil {
		return nil, err
	}
	if hash(original) != titleSourceSHA {
		return nil, fmt.Errorf("TIT2.AY 來源不符")
	}
	png, err := os.ReadFile(filepath.Join(dir, m.File))
	if err != nil {
		return nil, err
	}
	if hash(png) != m.SHA {
		return nil, fmt.Errorf("HD 片頭圖片 SHA-256 不符")
	}
	cfg, _, err := image.DecodeConfig(bytes.NewReader(png))
	if err != nil || cfg.Width != 1776 || cfg.Height != 570 {
		return nil, fmt.Errorf("HD 片頭圖片尺寸不符")
	}
	ink, _, err := image.Decode(bytes.NewReader(png))
	if err != nil {
		return nil, err
	}
	bounds := image.Rectangle{}
	for y := 0; y < 570; y++ {
		for x := 0; x < 1776; x++ {
			_, _, _, alpha := ink.At(x, y).RGBA()
			if alpha != 0 {
				bounds = bounds.Union(image.Rect(x, y, x+1, y+1))
			}
		}
	}
	if bounds.Empty() || !bounds.In(image.Rect(24, 24, 1752, 546)) ||
		bounds != image.Rect(m.InkRect[0], m.InkRect[1], m.InkRect[2], m.InkRect[3]) {
		return nil, fmt.Errorf("HD 片頭字墨安全範圍不符")
	}
	t := &IntroTitle{o: o, ink: ink}
	return t, nil
}

func (t *IntroTitle) observeWrite(oracle.VideoWrite) {
	if !t.inDraw && t.active {
		t.invalidate()
	}
}

func (t *IntroTitle) invalidate() {
	t.active, t.inDraw = false, false
	t.last, t.hold = nil, nil
}

func (t *IntroTitle) Bind() {
	if t.Stats.Retired {
		return
	}
	if len(t.o.Overlays()) != 0 {
		t.Stats.Retired = true
		t.invalidate()
		return
	}
	if t.Stats.Bound {
		return
	}
	for _, window := range []struct {
		at, n uint16
		sha   string
	}{
		{0x576a, 212, "88d6cfe05ddb19b00bd42cb4857a95cbcf9bdf764320ea21e503b9f202a947d8"},
		{0x6258, 131, "7ebac933d7abf4990004996998fdace5ce11644b38d96cdf08ef33e76a9d747a"},
		{0x5b0c, 55, "9b2e2e5b7c9b878690e526de6705910ee57066806e3a44c3b51fdf853176c76f"},
	} {
		if hash(t.o.Bytes(oracle.Far(0, window.at), int(window.n))) != window.sha {
			return
		}
	}
	t.Stats.Bound = true
	if t.publisher != nil {
		t.o.OnCall(oracle.Far(0, 0x1322), func(*oracle.Oracle) { t.Stats.Retired = true; t.invalidate() })
	}
	t.o.OnCall(oracle.Far(0, 0x576a), func(*oracle.Oracle) { t.begin() })
	t.o.OnCall(oracle.Far(0, 0x5b0c), func(*oracle.Oracle) {
		if t.valid() && t.active {
			t.startTransition(0x5b42)
		}
	})
	for _, end := range []uint16{0x583d, 0x5b42} {
		end := end
		t.o.OnCall(oracle.Far(0, end), func(*oracle.Oracle) {
			if t.valid() && t.inDraw && t.end == end {
				t.inDraw = false
				t.hold = nil
				if !t.active {
					t.last = nil
				}
			}
		})
	}
}

func (t *IntroTitle) valid() bool {
	if t.Stats.Retired || !t.Stats.Bound || len(t.o.Overlays()) != 0 {
		t.invalidate()
		return false
	}
	return true
}

func (t *IntroTitle) startTransition(end uint16) {
	t.hold = t.last
	t.active = false
	t.inDraw = true
	t.end = end
	t.start = t.o.Cycles()
	t.Stats.Transitions++
}

func (t *IntroTitle) begin() {
	if !t.valid() {
		return
	}
	wasTitle := t.active
	off, seg := t.o.Arg(0), t.o.Arg(1)
	x, y := t.o.Arg(2), t.o.Arg(3)
	state, planar := t.o.PlanarDisplay()
	match := planar && state.Width == 640 && state.Height == 200 && state.Start == 0 && state.Pitch == 80 && state.LineCompare >= 199 &&
		off == 0 && seg == 0x8000 && x == 2 && y == 50 &&
		t.o.Word(oracle.Far(seg, off)) == 74 && t.o.Word(oracle.Far(seg, off+2)) == 95 &&
		hash(t.o.Bytes(oracle.Far(seg, off), 28124)) == titleDecodedSHA
	if t.publisher != nil {
		match = planar && state.Width == 640 && state.Height == 200 && state.Start == 0 && state.Pitch == 80 && state.LineCompare >= 199 &&
			off == 0 && seg == 0x8000 && x == 8 && y == 20 && t.o.Word(oracle.Far(seg, off)) == 63 && t.o.Word(oracle.Far(seg, off+2)) == 160 && hash(t.o.Bytes(oracle.Far(seg, off), 40324)) == publisherDecodedSHA
	}
	if match {
		t.active, t.inDraw = true, true
		t.hold = nil
		if t.publisher != nil {
			t.hold = introNativeFrame(t.o)
		}
		t.end, t.start = 0x583d, t.o.Cycles()
		t.Stats.Starts++
	} else if wasTitle {
		t.startTransition(0x583d)
	} else {
		t.invalidate()
	}
}

func (t *IntroTitle) Stage() string {
	if t.publisher != nil {
		if t.Stats.Retired {
			return ""
		}
		if t.hold != nil {
			return "publisher-transition"
		}
		if t.active {
			return "publisher-noto"
		}
		return ""
	}
	if t.active && !t.Stats.Retired {
		return "title-noto"
	}
	if t.hold != nil {
		return "title-transition"
	}
	return ""
}

func (t *IntroTitle) Compose(native *image.RGBA) *image.RGBA {
	if !t.valid() {
		return native
	}
	display, ok := t.o.PlanarDisplay()
	if !ok || display.Width != 640 || display.Height != 200 || display.Start != 0 || display.Pitch != 80 || display.LineCompare < 199 {
		t.invalidate()
		return native
	}
	if t.inDraw && t.o.Cycles()-t.start > titleTransactionLimit {
		t.Stats.Timeouts++
		if len(t.Stats.Errors) < 8 {
			t.Stats.Errors = append(t.Stats.Errors, "片頭呈現交易逾時，恢復原版")
		}
		t.invalidate()
		return native
	}
	if t.hold != nil {
		return t.hold
	}
	if !t.active {
		return native
	}
	if t.publisher != nil {
		draw.DrawMask(native, native.Bounds(), image.Black, image.Point{}, t.publisher.erase, image.Point{}, draw.Over)
		draw.Draw(native, native.Bounds(), t.ink, image.Point{}, draw.Over)
	} else {
		r := image.Rect(48, 300, 1824, 870)
		draw.Draw(native, r, image.Black, image.Point{}, draw.Src)
		draw.Draw(native, r, t.ink, image.Point{}, draw.Over)
	}
	t.last = native
	t.Stats.Composed++
	return native
}
