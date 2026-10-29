package eightsword

import (
	"bytes"
	"encoding/json"
	"image"
	"image/color"
	"image/png"
	"os"
	"path/filepath"
	"testing"
)

func TestBattleVFXApprovedKernel(t *testing.T) {
	project := os.Getenv("EIGHTSWORD_VFX_PROJECT")
	if project == "" {
		t.Skip("需要永久B樣式與來源")
	}
	var observation struct {
		Cases []struct {
			Start  uint64
			Events []struct {
				File       string `json:"file"`
				Entry      uint64 `json:"entry_step"`
				ReturnStep uint64 `json:"return_step"`
			}
		}
	}
	raw, err := os.ReadFile(filepath.Join(project, "preserved/battle-vfx-observation-r1.json"))
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(raw, &observation); err != nil {
		t.Fatal(err)
	}
	var frames struct {
		Frames []struct {
			Step uint64
			BBox [4]int
		}
	}
	root := filepath.Join(project, "artwork/approved/provenance/battle-vfx-b-r1")
	raw, err = os.ReadFile(filepath.Join(root, "frames.json"))
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(raw, &frames); err != nil {
		t.Fatal(err)
	}
	ponStart, ponFirst, ponLast := uint64(0), uint64(0), uint64(0)
	for _, v := range observation.Cases[0].Events {
		if v.File == "PON.EGG" {
			if ponStart == 0 {
				ponStart = v.Entry
				ponFirst = v.ReturnStep
			}
			ponLast = v.ReturnStep
		}
	}
	for _, sample := range []struct {
		Index       int
		Name, Phase string
	}{{12, "b-12.png", "flight"}, {24, "b-24.png", "impact"}} {
		t.Run(sample.Phase, func(t *testing.T) {
			f := frames.Frames[sample.Index]
			progress := float64(f.Step-observation.Cases[0].Start) / float64(ponStart-observation.Cases[0].Start)
			if sample.Phase == "impact" {
				progress = float64(f.Step-ponFirst) / float64(ponLast+100000-ponFirst)
			}
			layer := drawBattleVFX(sample.Phase, progress, [2]int{456, 75}, [2]int{184, 100})
			var buffer bytes.Buffer
			if err := png.Encode(&buffer, layer); err != nil {
				t.Fatal(err)
			}
			actual, err := png.Decode(&buffer)
			if err != nil {
				t.Fatal(err)
			}
			file, err := os.Open(filepath.Join(project, "artwork/approved/masters/battle-vfx-b-r1", sample.Name))
			if err != nil {
				t.Fatal(err)
			}
			expected, err := png.Decode(file)
			file.Close()
			if err != nil {
				t.Fatal(err)
			}
			for y := 0; y < 600; y++ {
				for x := 0; x < 960; x++ {
					want := color.NRGBA{}
					if image.Pt(x-f.BBox[0], y-f.BBox[1]).In(expected.Bounds()) {
						want = color.NRGBAModel.Convert(expected.At(x-f.BBox[0], y-f.BBox[1])).(color.NRGBA)
					}
					got := color.NRGBA{}
					pt := image.Pt(x*2-layer.Rect.Min.X, y*2-layer.Rect.Min.Y)
					if pt.In(actual.Bounds()) {
						got = color.NRGBAModel.Convert(actual.At(pt.X, pt.Y)).(color.NRGBA)
					}
					if got != want {
						t.Fatalf("approved %s pixel %d,%d got%v want%v", sample.Phase, x, y, got, want)
					}
				}
			}
		})
	}
}
func TestBattleVFXTextAndImmutableBase(t *testing.T) {
	base := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	for i := 0; i < len(base.Pix); i += 4 {
		copy(base.Pix[i:i+4], []byte{31, 66, 38, 255})
	}
	before := append([]byte(nil), base.Pix...)
	scene := &ownedScene{Pixels: make([]ownedPixel, 128000)}
	for y := 90; y < 115; y++ {
		for x := 180; x < 280; x++ {
			scene.Pixels[y*640+x].Text = cell{ID: 1}
		}
	}
	v := &battleVFX{BattleVFXInfo: BattleVFXInfo{Active: true, Phase: "impact", Target: [2]int{184, 100}}, pon: 6}
	p := &sourceAdapter{e: &Engine{battleVFX: v}, cachedScene: scene}
	out := p.composeBattleVFX(base)
	if out == base || bytes.Equal(out.Pix, base.Pix) || !bytes.Equal(before, base.Pix) {
		t.Fatal("base mutation or missing effect")
	}
	for y := 90 * 6; y < 115*6; y++ {
		for x := 180 * 3; x < 280*3; x++ {
			if out.RGBAAt(x, y) != base.RGBAAt(x, y) {
				t.Fatal("covered text", x, y)
			}
		}
	}
	if v.ProtectedTextPixels == 0 || p.composeBattleVFX(base) != out {
		t.Fatal("text/caching contract")
	}
	v.cancel("test")
	if p.composeBattleVFX(base) != base || v.cached != nil {
		t.Fatal("effect not cleared")
	}
}
func TestBattleVFXDrawingBounds(t *testing.T) {
	for _, target := range [][2]int{{184, 50}, {184, 150}, {96, 125}, {8, 100}} {
		for _, phase := range []string{"flight", "impact"} {
			m := drawBattleVFX(phase, .6, [2]int{456, 75}, target)
			if m == nil || !m.Rect.In(image.Rect(0, 0, 1920, 1200)) {
				t.Fatal("invalid layer bounds", phase, target)
			}
		}
	}
	if drawBattleVFX("flight", 0, [2]int{}, [2]int{}) != nil || drawBattleVFX("impact", -1, [2]int{}, [2]int{}) != nil {
		t.Fatal("out of range progress")
	}
}

func TestBattleVFXUnknownEffectAndLateCommit(t *testing.T) {
	v := &battleVFX{BattleVFXInfo: BattleVFXInfo{Active: true, Phase: "impact", Target: [2]int{184, 100}}, running: true, pon: 1}
	p := &sourceAdapter{e: &Engine{battleVFX: v}}
	p.battleVFXBitmap(0x4f2, []byte("unknown full source"), 23, 100, 11, 50, 0xa000)
	if v.Active || v.running || v.Cancelled != 1 || v.LastSkip != "effect-source-order" {
		t.Fatal(v.BattleVFXInfo)
	}
	p.battleVFXBitmap(0x626, nil, 57, 75, 11, 50, 0xa000)
	if v.SourceCommits != 0 || v.Active {
		t.Fatal("late source revived effect")
	}
}
