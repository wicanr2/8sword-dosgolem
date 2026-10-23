package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"os"
	"path/filepath"

	"github.com/wicanr2/dosgolem/oracle"
)

const publisherSourceSHA = "8e971808ea94931ceb3ba78f3d1918984290584bd592d13ce7d081dfb08a34ac"
const publisherDecodedSHA = "d0bcfa366f8d8c13745c253fbeef1a04691aad24d4a5718cebd9645c17fc1308"
const publisherEraseSHA = "7c6f7c1719915f4ddee9ac2d03938e42654c45777a3236c58b1ee3ea89a90985"

var publisherRects = []image.Rectangle{
	image.Rect(273, 642, 729, 840), image.Rect(1212, 648, 1626, 840), image.Rect(195, 942, 450, 1044), image.Rect(471, 840, 1425, 1068), image.Rect(1425, 942, 1665, 1044),
}

type publisherWords struct {
	erase *image.Alpha
	words map[string]image.Image
}

func loadIntroPublisher(o *oracle.Oracle, dir, root string) (*IntroTitle, error) {
	raw, err := os.ReadFile(filepath.Join(dir, "publisher.json"))
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	var m struct {
		Schema     int
		SourceSHA  string `json:"source_sha256"`
		DecodedSHA string `json:"decoded_sha256"`
		Mask       string
		MaskSHA    string `json:"mask_sha256"`
		Words      []struct {
			ID, File, SHA string
			Width, Height int
		}
	}
	if json.Unmarshal(raw, &m) != nil || m.Schema != 1 || m.SourceSHA != publisherSourceSHA || m.DecodedSHA != publisherDecodedSHA || m.Mask != "publisher-erase.png" || len(m.Words) != 3 {
		return nil, fmt.Errorf("發行商字圖清單來源／形狀不符")
	}
	original, err := os.ReadFile(filepath.Join(root, "TIT1.AY"))
	if err != nil {
		return nil, err
	}
	if hash(original) != publisherSourceSHA {
		return nil, fmt.Errorf("TIT1.AY 來源不符")
	}
	decode := func(file, sha string, w, h int) (image.Image, error) {
		b, err := os.ReadFile(filepath.Join(dir, file))
		if err != nil {
			return nil, err
		}
		if hash(b) != sha {
			return nil, fmt.Errorf("發行商字圖 %s SHA-256 不符", file)
		}
		cfg, _, err := image.DecodeConfig(bytes.NewReader(b))
		if err != nil || cfg.Width != w || cfg.Height != h {
			return nil, fmt.Errorf("發行商字圖尺寸不符")
		}
		im, _, err := image.Decode(bytes.NewReader(b))
		return im, err
	}
	mask, err := decode(m.Mask, m.MaskSHA, 640, 200)
	if err != nil {
		return nil, err
	}
	gray := make([]byte, 640*200)
	alpha := image.NewAlpha(image.Rect(0, 0, 1920, 1200))
	for y := 0; y < 200; y++ {
		for x := 0; x < 640; x++ {
			r, g, b, a := mask.At(x, y).RGBA()
			if r != g || r != b || a != 65535 || (r != 0 && r != 65535) {
				return nil, fmt.Errorf("發行商清墨遮罩不是二值")
			}
			gray[y*640+x] = byte(r >> 8)
			if r != 0 {
				for yy := y * 6; yy < (y+1)*6; yy++ {
					for xx := x * 3; xx < (x+1)*3; xx++ {
						alpha.Pix[yy*alpha.Stride+xx] = 255
					}
				}
			}
		}
	}
	if hash(gray) != publisherEraseSHA {
		return nil, fmt.Errorf("發行商清墨來源不符")
	}
	p := &publisherWords{erase: alpha, words: map[string]image.Image{}}
	for _, v := range m.Words {
		if (v.ID != "noto" && v.ID != "lishu" && v.ID != "caoshu") || p.words[v.ID] != nil || v.File != "publisher-"+v.ID+".png" || v.Width != 1920 || v.Height != 1200 {
			return nil, fmt.Errorf("發行商字圖選項不符")
		}
		im, err := decode(v.File, v.SHA, 1920, 1200)
		if err != nil {
			return nil, err
		}
		counts := make([]int, len(publisherRects))
		for y := 0; y < 1200; y++ {
			for x := 0; x < 1920; x++ {
				_, _, _, a := im.At(x, y).RGBA()
				if a == 0 {
					continue
				}
				found := false
				for i, r := range publisherRects {
					if image.Pt(x, y).In(r) {
						counts[i]++
						found = true
						break
					}
				}
				if !found {
					return nil, fmt.Errorf("發行商字墨越界")
				}
			}
		}
		for _, n := range counts {
			if n == 0 {
				return nil, fmt.Errorf("發行商字墨缺欄位")
			}
		}
		p.words[v.ID] = im
	}
	return &IntroTitle{o: o, ink: p.words["noto"], publisher: p}, nil
}

func introNativeFrame(o *oracle.Oracle) *image.RGBA {
	w, h, rgb := o.ScreenRGB()
	if w != 640 || h != 200 {
		return nil
	}
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	for y := 0; y < 1200; y++ {
		for x := 0; x < 1920; x++ {
			src := (y/6*640 + x/3) * 3
			at := y*out.Stride + x*4
			copy(out.Pix[at:at+3], rgb[src:src+3])
			out.Pix[at+3] = 255
		}
	}
	return out
}
