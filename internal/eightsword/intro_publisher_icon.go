package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/png"
	"io"
	"os"
	"path/filepath"
)

const publisherIconSHA = "21b9bb5de42c011434160cb208ff9a28354959a2d751e286c078a6b68699f2a0"
const publisherIconMaskSHA = "124dd022ac27ef2070195bf53baeb59915600317531766f5ae197ce6970c417d"

type publisherIcon struct {
	art   image.Image
	erase *image.Alpha
}

func publisherIconFile(dir, name string, limit int64) ([]byte, error) {
	file := filepath.Join(dir, name)
	s, err := os.Lstat(file)
	if err != nil {
		return nil, err
	}
	if !s.Mode().IsRegular() || s.Size() > limit {
		return nil, fmt.Errorf("發行商圖案檔案類型／容量不符")
	}
	return os.ReadFile(file)
}

func loadPublisherIcon(dir string, words *publisherWords) (*publisherIcon, error) {
	raw, err := publisherIconFile(dir, "publisher-icon.json", 65536)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	var m struct {
		Schema      int    `json:"schema"`
		SourceSHA   string `json:"source_sha256"`
		DecodedSHA  string `json:"decoded_sha256"`
		ApprovedSHA string `json:"approved_sha256"`
		Image       string `json:"image"`
		ImageSHA    string `json:"image_sha256"`
		Width       int    `json:"width"`
		Height      int    `json:"height"`
		Mask        string `json:"mask"`
		MaskSHA     string `json:"mask_sha256"`
		Rights      string `json:"rights"`
	}
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err = d.Decode(&m); err != nil {
		return nil, err
	}
	if d.Decode(new(any)) != io.EOF {
		return nil, fmt.Errorf("發行商圖案清單包含尾隨資料")
	}
	if m.Schema != 1 || m.SourceSHA != publisherSourceSHA || m.DecodedSHA != publisherDecodedSHA || m.ApprovedSHA != publisherIconSHA || m.Image != "publisher-icon.png" || m.ImageSHA != publisherIconSHA || m.Width != 1920 || m.Height != 1200 || m.Mask != "publisher-icon-erase.png" || m.MaskSHA == "" || m.Rights == "" {
		return nil, fmt.Errorf("發行商圖案來源／形狀不符")
	}
	decode := func(name, sha string, limit int64, w, h int) (image.Image, error) {
		data, err := publisherIconFile(dir, name, limit)
		if err != nil {
			return nil, err
		}
		if hash(data) != sha {
			return nil, fmt.Errorf("發行商圖案 %s SHA-256 不符", name)
		}
		cfg, err := png.DecodeConfig(bytes.NewReader(data))
		if err != nil || cfg.Width != w || cfg.Height != h {
			return nil, fmt.Errorf("發行商圖案尺寸不符")
		}
		return png.Decode(bytes.NewReader(data))
	}
	mask, err := decode(m.Mask, m.MaskSHA, 1024*1024, 640, 200)
	if err != nil {
		return nil, err
	}
	gray := make([]byte, 640*200)
	erase := image.NewAlpha(image.Rect(0, 0, 1920, 1200))
	for y := 0; y < 200; y++ {
		for x := 0; x < 640; x++ {
			r, g, b, a := mask.At(x, y).RGBA()
			if r != g || r != b || a != 65535 || (r != 0 && r != 65535) {
				return nil, fmt.Errorf("發行商圖案遮罩不是二值")
			}
			gray[y*640+x] = byte(r >> 8)
			if r != 0 {
				for yy := y * 6; yy < (y+1)*6; yy++ {
					for xx := x * 3; xx < (x+1)*3; xx++ {
						erase.Pix[yy*erase.Stride+xx] = 255
					}
				}
			}
		}
	}
	if hash(gray) != publisherIconMaskSHA {
		return nil, fmt.Errorf("發行商圖案遮罩來源不符")
	}
	art, err := decode(m.Image, m.ImageSHA, 8*1024*1024, 1920, 1200)
	if err != nil {
		return nil, err
	}
	safe := image.Rect(654, 114, 1281, 828)
	for y := 0; y < 1200; y++ {
		for x := 0; x < 1920; x++ {
			_, _, _, a := art.At(x, y).RGBA()
			if a == 0 {
				continue
			}
			if !image.Pt(x, y).In(safe) {
				return nil, fmt.Errorf("發行商圖案越界")
			}
			for _, word := range words.words {
				_, _, _, ink := word.At(x, y).RGBA()
				if ink != 0 {
					return nil, fmt.Errorf("發行商圖案與字墨重疊")
				}
			}
		}
	}
	return &publisherIcon{art: art, erase: erase}, nil
}
