package eightsword

import (
	"bytes"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"image"
	"image/draw"
	"os"
	"path/filepath"
	"strings"

	"github.com/wicanr2/dosgolem/oracle"
)

const storyRuntimeSHA = "a764a110b9f8b1d32a6ee9cc0dd650350f917959d647fe4b45cd7f1013eaae68"
const storyTableSHA = "bf10ab412d18dc7d4f77ba2918e55aeefd3ab02b53aa40c34cd3fae6119ed7aa"
const storyCodesSHA = "2cf9a571e729cf77de2dd739207b015c2ec14c940182edb087d41784bdcc9fc8"
const storyInkSHA = "a87a063a736aaf847e4014cb3ecb22a3d8782ee6d67fb2bec474c7d9ff84de63"
const storyBackgroundSHA = "2df60e86386ebbea78d307fe620f426c6ff9cb8f34551c689a9343c5af13baa2"

type IntroStoryStats struct {
	Bound, Started, Retired                  bool
	Calls, Glyphs, Pages, Composed, Timeouts uint64
	Errors                                   []string
}

type storyCell struct {
	x, y int
	r    rune
}
type IntroStory struct {
	o                                          *oracle.Oracle
	font                                       *Assets
	codes                                      map[uint16]rune
	table                                      []byte
	Stats                                      IntroStoryStats
	active, failed, inDraw, inText             bool
	start                                      uint64
	cells                                      []storyCell
	background, last, hold                     *image.RGBA
	palette                                    [256][3]uint8
	lastCalls, lastPages, holdCalls, holdPages uint64
	art                                        *image.RGBA
	BackgroundError                            string
	prelude                                    *StoryPrelude
	PreludeError                               string
}

func loadIntroStory(o *oracle.Oracle, dir string) (*IntroStory, error) {
	raw, err := os.ReadFile(filepath.Join(dir, "story.json"))
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	var m struct {
		fontManifest
		RuntimeSHA string `json:"runtime_sha256"`
		CodesSHA   string `json:"codes_sha256"`
		InkSHA     string `json:"native_ink_sha256"`
		TableSHA   string `json:"table_sha256"`
		Codes      string `json:"codes"`
	}
	if err = json.Unmarshal(raw, &m); err != nil {
		return nil, err
	}
	if m.Schema != 1 || m.SourceSHA != "b9c7abdac7849711b68b6b6fd5861052e6f3d025b25af5f96d4605bf673cadaa" ||
		m.RuntimeSHA != storyRuntimeSHA || m.CodesSHA != storyCodesSHA || m.InkSHA != storyInkSHA || m.TableSHA != storyTableSHA ||
		m.FontSHA != NotoSHA || m.Family != "Noto Sans CJK TC" || m.Weight != 900 ||
		m.Atlas != "story-font.png" || m.Width != 1024 || m.Height != 1792 || len(m.Glyphs) != 448 {
		return nil, fmt.Errorf("故事字集來源／形狀不符")
	}
	codes, err := hex.DecodeString(m.Codes)
	if err != nil || len(codes) != 706 || hash(codes) != storyCodesSHA {
		return nil, fmt.Errorf("故事 Big5 字碼不符")
	}
	png, err := os.ReadFile(filepath.Join(dir, m.Atlas))
	if err != nil {
		return nil, err
	}
	if hash(png) != m.AtlasSHA {
		return nil, fmt.Errorf("故事字型圖片 SHA-256 不符")
	}
	cfg, _, err := image.DecodeConfig(bytes.NewReader(png))
	if err != nil || cfg.Width != m.Width || cfg.Height != m.Height {
		return nil, fmt.Errorf("故事字型圖片尺寸不符")
	}
	atlas, _, err := image.Decode(bytes.NewReader(png))
	if err != nil {
		return nil, err
	}
	t := &IntroStory{o: o, font: &Assets{Atlas: atlas, Glyphs: map[rune]FontGlyph{}}, codes: map[uint16]rune{}}
	var unicode strings.Builder
	for i, g := range m.Glyphs {
		runes := []rune(g.Character)
		if len(runes) != 1 {
			return nil, fmt.Errorf("故事字集不是單字")
		}
		r := runes[0]
		if _, exists := t.font.Glyphs[r]; exists {
			return nil, fmt.Errorf("故事字集重複")
		}
		cell := image.Rect(g.Cell[0], g.Cell[1], g.Cell[0]+g.Cell[2], g.Cell[1]+g.Cell[3])
		ink := image.Rect(g.Ink[0], g.Ink[1], g.Ink[0]+g.Ink[2], g.Ink[1]+g.Ink[3])
		if g.Cell != [4]int{i % 16 * 64, i / 16 * 64, 64, 64} || !cell.In(atlas.Bounds()) ||
			g.Ink[2] < 0 || g.Ink[3] < 0 || !ink.In(cell) {
			return nil, fmt.Errorf("故事字框越界")
		}
		if i < 353 {
			if g.SourceIndex != i || g.Big5 != hex.EncodeToString(codes[i*2:i*2+2]) {
				return nil, fmt.Errorf("故事字碼順序不符")
			}
			t.codes[binary.LittleEndian.Uint16(codes[i*2:])] = r
			unicode.WriteRune(r)
		} else if r != rune(32+i-353) {
			return nil, fmt.Errorf("故事 ASCII 字集不符")
		}
		t.font.Glyphs[r] = g
	}
	if hash([]byte(unicode.String())) != "55b9da7db8da920061a3a3f709556e7f90a35b38ab91ed0362687037d2f9ff3e" {
		return nil, fmt.Errorf("故事 Unicode 對應不符")
	}
	t.art, err = loadStoryBackground(dir)
	if err != nil {
		t.BackgroundError = err.Error()
	}
	t.prelude, err = loadStoryPrelude(t, dir)
	if err != nil {
		t.PreludeError = err.Error()
	}
	return t, nil
}

func (t *IntroStory) invalidate() {
	t.active, t.inDraw, t.inText = false, false, false
	t.cells = nil
	t.last, t.hold = nil, nil
}
func (t *IntroStory) fail(message string) {
	if t.prelude != nil {
		t.prelude.stop("story-failure", false)
	}
	if len(t.Stats.Errors) < 8 {
		t.Stats.Errors = append(t.Stats.Errors, message)
	}
	t.failed = true
	t.invalidate()
}
func (t *IntroStory) observeWrite(v oracle.VideoWrite) {
	if t.prelude != nil {
		t.prelude.observeWrite(v)
	}
	if t.active && !t.inDraw && !t.inText {
		t.fail("故事出現未知視訊寫入，恢復原版")
	}
}
func (t *IntroStory) valid() bool {
	return t.Stats.Bound && !t.Stats.Retired && !t.failed && len(t.o.Overlays()) == 0
}
func (t *IntroStory) geometry() bool {
	s, ok := t.o.PlanarDisplay()
	return ok && s.Width == 640 && s.Height == 200 && s.Start == 0 && s.Pitch == 80 && s.LineCompare >= 199
}
func (t *IntroStory) Bind() {
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
	for _, w := range []struct {
		at  uint16
		n   int
		sha string
	}{
		{0x203e, 366, "bba7997a5a28f67a58f0193c1ff2adde6c498b8af8f1cd290a786aad603de553"},
		{0x58b1, 95, "c05428726639bb22cfaa28ed4078610189fbddb2fe093d4d2ba7830b8709aa10"},
		{0x4c74, 352, "1aff4e0dbdf1831e8ba94e960bc6a0730a2edb075ac4c961a31d4a9b169beb6b"},
		{0x5910, 68, "eaee2bb6409de05595174b268acd57cd0e3afe14365db06ad56da5eca14952c9"},
		{0x576a, 212, "88d6cfe05ddb19b00bd42cb4857a95cbcf9bdf764320ea21e503b9f202a947d8"},
	} {
		if hash(t.o.Bytes(oracle.Far(0, w.at), w.n)) != w.sha {
			return
		}
	}
	t.Stats.Bound = true
	t.o.OnCall(oracle.Far(0, 0x203e), func(o *oracle.Oracle) {
		if !t.valid() {
			return
		}
		r := o.Regs()
		table := o.Bytes(oracle.Far(r.DS, 0xe2), 1924)
		if r.DS != 0xb31 || hash(table) != storyTableSHA || hash(o.Bytes(oracle.Far(r.DS, 0x9fc), 706)) != storyCodesSHA ||
			hash(o.Bytes(oracle.Far(0x231, 6), 10590)) != storyInkSHA || !t.geometry() {
			t.fail("故事執行期來源不符")
			return
		}
		t.table = append([]byte(nil), table...)
		t.Stats.Started = true
	})
	t.o.OnCall(oracle.Far(0, 0x576a), func(o *oracle.Oracle) {
		if !t.valid() || !t.Stats.Started {
			return
		}
		if !t.geometry() || o.Arg(0) != 0 || o.Arg(1) != 0x6000 || o.Arg(2) != 0 || o.Arg(3) != 0 ||
			hash(o.Bytes(oracle.Far(0x6000, 0), 64004)) != storyBackgroundSHA || t.Stats.Calls%192 != 0 || t.Stats.Pages >= 5 {
			t.fail("故事背景／頁次不符")
			return
		}
		t.hold = t.last
		t.holdCalls, t.holdPages = t.lastCalls, t.lastPages
		t.cells = nil
		t.active, t.inDraw = true, true
		t.start = o.Cycles()
		t.Stats.Pages++
	})
	t.o.OnCall(oracle.Far(0, 0x583d), func(o *oracle.Oracle) {
		if !t.valid() || !t.inDraw {
			return
		}
		w, h, rgb := o.ScreenRGB()
		if w != 640 || h != 200 {
			t.fail("故事背景幾何不符")
			return
		}
		t.background = image.NewRGBA(image.Rect(0, 0, 1920, 1200))
		for y := 0; y < 1200; y++ {
			for x := 0; x < 1920; x++ {
				at := y*t.background.Stride + x*4
				src := (y/6*640 + x/3) * 3
				copy(t.background.Pix[at:at+3], rgb[src:src+3])
				t.background.Pix[at+3] = 255
			}
		}
		t.palette = o.Palette()
		t.inDraw = false
		t.hold = nil
		if t.prelude != nil {
			t.prelude.stop("story-background", false)
		}
	})
	t.o.OnCall(oracle.Far(0, 0x58b1), func(o *oracle.Oracle) { t.beginText() })
	t.o.OnCall(oracle.Far(0, 0x590f), func(o *oracle.Oracle) {
		if t.valid() {
			t.inText = false
		}
	})
	t.o.OnCall(oracle.Far(0, 0x1322), func(o *oracle.Oracle) {
		if t.valid() && t.active {
			t.hold = t.last
			t.holdCalls, t.holdPages = t.lastCalls, t.lastPages
			t.inDraw = true
			t.start = o.Cycles()
		}
	})
}

func (t *IntroStory) beginText() {
	if !t.valid() || !t.Stats.Started {
		return
	}
	if !t.active || t.inDraw || t.inText || t.Stats.Calls >= 888 {
		t.fail("故事文字交易不符")
		return
	}
	i := int(t.Stats.Calls)
	col, row := i/12, i%12
	x, y := 75-5*(col%16), 4+16*row
	r := t.o.Regs()
	pair := t.o.Word(oracle.Far(r.DS, 0x866))
	want := binary.LittleEndian.Uint16(t.table[col*26+row*2:])
	if r.DS != 0xb31 || t.o.Arg(0) != 0x866 || int(t.o.Arg(1)) != x || int(t.o.Arg(2)) != y || pair != want ||
		t.o.Word(oracle.Far(r.SS, r.SP)) != 0x1035 || t.o.Word(oracle.Far(r.SS, r.SP+2)) != 0x110 {
		t.fail("故事字碼／欄列／呼叫順序不符")
		return
	}
	if pair != 0 && pair != 0x2020 {
		c, ok := t.codes[pair]
		if !ok {
			t.fail("故事缺字，恢復原版")
			return
		}
		t.cells = append(t.cells, storyCell{x * 8, y, c})
		t.Stats.Glyphs++
	}
	t.Stats.Calls++
	t.inText = true
	t.start = t.o.Cycles()
}
func (t *IntroStory) Stage() string {
	if !t.active {
		if t.prelude != nil && t.prelude.phase != "" {
			if t.prelude.phase == "handoff" {
				return "story-prelude-handoff"
			}
			return "story-prelude"
		}
		return ""
	}
	if t.hold != nil {
		return "story-transition"
	}
	return "story-noto"
}
func (t *IntroStory) Compose(native *image.RGBA) *image.RGBA {
	if t.prelude != nil {
		if out, used := t.prelude.compose(native); used {
			return out
		}
	}
	if !t.valid() || !t.active {
		return native
	}
	if !t.geometry() {
		t.fail("故事顯示幾何改變")
		return native
	}
	if (t.inDraw || t.inText) && t.o.Cycles()-t.start > titleTransactionLimit {
		t.Stats.Timeouts++
		t.fail("故事呈現交易逾時，恢復原版")
		return native
	}
	if t.hold != nil {
		return t.hold
	}
	if t.background == nil {
		return native
	}
	if t.o.Palette() != t.palette {
		t.fail("故事色盤改變，恢復原版")
		return native
	}
	if t.art != nil {
		draw.Draw(native, native.Bounds(), t.art, t.art.Bounds().Min, draw.Src)
	}
	for _, c := range t.cells {
		r := image.Rect(c.x*3, c.y*6, (c.x+16)*3, (c.y+15)*6)
		if t.art == nil {
			draw.Draw(native, r, t.background, r.Min, draw.Src)
		}
		t.font.DrawRune(native, c.r, r, [3]uint8{245, 207, 113})
	}
	t.last = native
	t.lastCalls, t.lastPages = t.Stats.Calls, t.Stats.Pages
	t.Stats.Composed++
	return native
}

func (t *IntroStory) FrameInfo(frame *image.RGBA) (uint64, uint64) {
	if frame != nil && frame == t.hold {
		return t.holdCalls, t.holdPages
	}
	if frame != nil && frame == t.last {
		return t.lastCalls, t.lastPages
	}
	return 0, 0
}

func (t *IntroStory) Tick() {
	if t.prelude != nil {
		t.prelude.tick()
	}
}

func (t *IntroStory) PreludeStatus() map[string]any {
	return t.prelude.Status()
}
