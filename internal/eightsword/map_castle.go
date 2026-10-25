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

const mapCastleImageSHA = "744a39bb04c869803c0583604ac3c5c0481e174ad3153c4a8489f1219ad50a97"

type mapCastleRecord struct {
	Index     int    `json:"source_index"`
	NativeSHA string `json:"native_sha256"`
	RecordSHA string `json:"record_sha256"`
	CacheSHA  string `json:"cache_sha256"`
}

var mapCastleRecords = [...]mapCastleRecord{
	{59, "53547549bf81398b065bd810035682bbf0c26c559003b15dfea560dfd4ec71da", "6aa6029bcd6e39aa49a447abeb749a0a21cef3df79ef049339cbdb025aca2549", "f559bcaa54ffb080ed1d049dd16fb652a41901394dddf63a5d53697ef9deabdf"},
	{60, "8c1be3b01483ba84ac18359a3dda8eff33a74ce8b1640409796196d48bd1fb30", "43ac0201ad031f4711dc02b68fc91f254ea90cf3f0d525e63d75cec9a8931545", "3912e71422f4e03357d145c657f614dafaab99064730349624abd258a8751822"},
	{61, "87bfd2840b6c9ac709894d95edbaac1473441fd35351f8ec5c13325fec173361", "c6baf40819edea0fdf3f5e168837ac1293860a877d64d8656524d1eba4887fc4", "930f2493e01185914169e26c1ce12928cc70674f3aacc29e85832852031c9450"},
	{62, "2a8341dc6cdb006bbbbef0c048c6d4ef4343156612cb376fab3e2895b0d9a7b6", "076654c60eeb60069664242588026975139971f405c7757aac6a0536bc6c4ecf", "bd490ec89fbe00c1856a5ddad1ad1ae76b359168d2383e9145ad6cc9a08141b5"},
	{63, "d215587dfc305a4ad08e671380e23497b10d8a13694dc06abab643f4bc8071c7", "7d54e41a1270f5635638344ab53bcc0ea544e55ea3e155ab526d63198c0a1204", "5f6236bce522acb5e0606e3fc1d06116bceb5cf24c2924038207e09dc06142a9"},
	{64, "49541be7818eeb1258246b9f263a21c707113331362faa2704dd23c290dbcffe", "ee488e6ef350b5dfdfb7f51601a93aa500f98b11d086950da840687af518fb5f", "610a7beecd74a656b566a45014a194dc321a93f63270dfb87f51d710d9ad1d10"},
}

type mapCastleManifest struct {
	Schema    int    `json:"schema"`
	Source    string `json:"source_file"`
	SourceSHA string `json:"source_sha256"`
	StyleSHA  string `json:"style_reference_sha256"`
	Layout    []int  `json:"layout"`
	Grass     int    `json:"grass_source"`
	Sampling  string `json:"sampling"`
	Image     struct {
		File   string `json:"file"`
		SHA    string `json:"sha256"`
		Width  int    `json:"width"`
		Height int    `json:"height"`
	} `json:"image"`
	Records []mapCastleRecord `json:"records"`
}

// Spec 043. This optional group only adds six presentation caches after validation.
func loadMapCastle(dir string, pmap []byte, assets *GraphicsAssets) error {
	raw, err := encounterRead(filepath.Join(dir, "map-castle.json"), 64*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var m mapCastleManifest
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if err = decoder.Decode(&m); err != nil {
		return err
	}
	if decoder.Decode(new(any)) != io.EOF {
		return fmt.Errorf("城堡清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != "PMAP.AY" || m.SourceSHA != PMAPSHA || m.StyleSHA != ApprovedStyleSHA || len(m.Layout) != 2 || m.Layout[0] != 3 || m.Layout[1] != 2 || m.Grass != 0 || m.Sampling != "bilinear-full-then-split" || len(m.Records) != 6 {
		return fmt.Errorf("城堡清單來源或配置不符")
	}
	if m.Image.File != "map-castle-r2.png" || m.Image.SHA != mapCastleImageSHA || m.Image.Width != 1736 || m.Image.Height != 906 {
		return fmt.Errorf("城堡圖片來源不符")
	}
	if hash(pmap) != PMAPSHA || assets == nil || len(assets.Native) < 65 || assets.Materials == nil {
		return fmt.Errorf("城堡缺少完整 PMAP 來源")
	}
	for i, want := range mapCastleRecords {
		if m.Records[i] != want {
			return fmt.Errorf("城堡第 %d 筆清單不符", want.Index)
		}
		start := want.Index * 1004
		raw := pmap[start : start+1004]
		n := assets.Native[want.Index]
		id := uint16(want.Index + 1)
		if hash(raw) != want.RecordSHA || hash(raw[:804]) != want.NativeSHA || n.Index != want.Index || n.WidthBytes != 8 || n.Height != 25 || n.NativeSHA != want.NativeSHA || assets.ByNative[want.NativeSHA] != id {
			return fmt.Errorf("城堡第 %d 筆原始來源不符", want.Index)
		}
		if assets.Materials[id] != nil || assets.Actors[id] != nil || assets.Effects[id] != nil {
			return fmt.Errorf("城堡第 %d 筆識別重複", want.Index)
		}
	}
	grass := assets.Materials[1]
	if grass == nil || grass.NativeWidth != 64 || grass.NativeHeight != 25 || grass.Tile == nil || grass.Tile.Bounds() != image.Rect(0, 0, 192, 150) || grass.Tile.Stride != 192*4 || len(grass.Tile.Pix) != 192*150*4 {
		return fmt.Errorf("城堡缺少完整草地快取")
	}
	raw, err = encounterRead(filepath.Join(dir, m.Image.File), 8*1024*1024)
	if err != nil {
		return err
	}
	if hash(raw) != mapCastleImageSHA {
		return fmt.Errorf("城堡圖片 SHA-256 不符")
	}
	config, err := png.DecodeConfig(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	if config.Width != 1736 || config.Height != 906 {
		return fmt.Errorf("城堡圖片尺寸不符")
	}
	decoded, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	background := image.NewRGBA(image.Rect(0, 0, 576, 300))
	for y := 0; y < 300; y++ {
		for col := 0; col < 3; col++ {
			at := y*background.Stride + col*192*4
			src := (y % 150) * grass.Tile.Stride
			copy(background.Pix[at:at+192*4], grass.Tile.Pix[src:src+192*4])
		}
	}
	whole, err := compositeMapCastle(decoded, background)
	if err != nil {
		return err
	}
	prepared := make(map[uint16]*graphicMaterial, 6)
	for i, want := range mapCastleRecords {
		tile := image.NewRGBA(image.Rect(0, 0, 192, 150))
		ox, oy := (i%3)*192, (i/3)*150
		for y := 0; y < 150; y++ {
			copy(tile.Pix[y*tile.Stride:(y+1)*tile.Stride], whole.Pix[(y+oy)*whole.Stride+ox*4:(y+oy)*whole.Stride+(ox+192)*4])
		}
		if hash(tile.Pix) != want.CacheSHA {
			return fmt.Errorf("城堡第 %d 筆快取不符", want.Index)
		}
		prepared[uint16(want.Index+1)] = &graphicMaterial{64, 25, tile}
	}
	for id, tile := range prepared {
		assets.Materials[id] = tile
	}
	return nil
}

func compositeMapCastle(source image.Image, background *image.RGBA) (*image.RGBA, error) {
	if background.Bounds() != image.Rect(0, 0, 576, 300) {
		return nil, fmt.Errorf("HD 靜物草底尺寸不符")
	}
	bounds := source.Bounds()
	sw, sh := bounds.Dx(), bounds.Dy()
	hasZero, hasOpaque := false, false
alphaCheck:
	for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			_, _, _, a := source.At(x, y).RGBA()
			hasZero = hasZero || a == 0
			hasOpaque = hasOpaque || a == 65535
			if hasZero && hasOpaque {
				break alphaCheck
			}
		}
	}
	if !hasZero || !hasOpaque {
		return nil, fmt.Errorf("HD 靜物須有透明背景及不透明主體")
	}
	out := image.NewRGBA(background.Bounds())
	for y := 0; y < 300; y++ {
		for x := 0; x < 576; x++ {
			sx, sy := max(0, (float64(x)+0.5)*float64(sw)/576-0.5), max(0, (float64(y)+0.5)*float64(sh)/300-0.5)
			x0, y0 := int(sx), int(sy)
			x1, y1 := min(x0+1, sw-1), min(y0+1, sh-1)
			fx, fy := sx-float64(x0), sy-float64(y0)
			points := [4]image.Point{{x0, y0}, {x1, y0}, {x0, y1}, {x1, y1}}
			weights := [4]float64{(1 - fx) * (1 - fy), fx * (1 - fy), (1 - fx) * fy, fx * fy}
			sum := [4]float64{}
			for n, p := range points {
				r, g, b, a := source.At(bounds.Min.X+p.X, bounds.Min.Y+p.Y).RGBA()
				if a <= 3*257 {
					continue
				}
				for c, v := range [4]uint32{r, g, b, a} {
					sum[c] += float64(v) * weights[n]
				}
			}
			alpha := sum[3] / 65535
			at := y*out.Stride + x*4
			bg := y*background.Stride + x*4
			for c := 0; c < 3; c++ {
				out.Pix[at+c] = uint8(max(0, min(255, sum[c]/257+float64(background.Pix[bg+c])*(1-alpha))) + 0.5)
			}
			out.Pix[at+3] = 255
		}
	}
	return out, nil
}
