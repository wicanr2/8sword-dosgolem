package eightsword

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"image"
	"os"
	"path/filepath"
)

const PMAPSHA = "9db04157a546a4fe8615becf483520b1a7d3a0a5357fef56f88dcb694dd21e02"
const ApprovedStyleSHA = "2a88912c229f226d99ca3f8f6c643137b731eed943585f991ecc631af3b0dad6"

type nativeBitmap struct {
	Index, WidthBytes, Height int
	NativeSHA                 string
	Pixels                    []uint8
}
type graphicMaterial struct {
	NativeWidth, NativeHeight int
	Tile                      *image.RGBA
}
type GraphicsAssets struct {
	Native    []nativeBitmap
	ByNative  map[string]uint16
	Materials map[uint16]*graphicMaterial
}
type terrainManifest struct {
	Schema    int    `json:"schema"`
	SourceSHA string `json:"source_sha256"`
	Style     string `json:"style"`
	StyleSHA  string `json:"style_reference_sha256"`
	Materials []struct {
		Index      int    `json:"source_index"`
		File       string `json:"file"`
		SHA        string `json:"sha256"`
		Width      int    `json:"width"`
		Height     int    `json:"height"`
		Sampling   string `json:"sampling"`
		SourceRect []int  `json:"source_rect"`
	} `json:"materials"`
	Composites []struct {
		Index int    `json:"source_index"`
		Land  int    `json:"land_source"`
		Water int    `json:"water_source"`
		Rule  string `json:"mask_rule"`
	} `json:"composites"`
}

func decodePMAP(raw []byte) ([]nativeBitmap, error) {
	if hash(raw) != PMAPSHA {
		return nil, fmt.Errorf("PMAP.AY 來源雜湊不符")
	}
	out := []nativeBitmap{}
	for at := 0; at < len(raw); {
		if at+4 > len(raw) {
			return nil, fmt.Errorf("PMAP 圖像表頭遭截斷")
		}
		w, h := int(binary.LittleEndian.Uint16(raw[at:])), int(binary.LittleEndian.Uint16(raw[at+2:]))
		area := w * h
		n := 4 + area*5
		if w < 1 || w > 80 || h < 1 || h > 200 || at+n > len(raw) {
			return nil, fmt.Errorf("PMAP 圖像越界")
		}
		pixels := make([]uint8, area*8)
		for i := range pixels {
			for plane := 0; plane < 4; plane++ {
				pixels[i] |= ((raw[at+4+plane*area+i/8] >> uint(7-i%8)) & 1) << uint(plane)
			}
		}
		out = append(out, nativeBitmap{len(out), w, h, hash(raw[at : at+4+area*4]), pixels})
		at += n
	}
	if len(out) != 68 {
		return nil, fmt.Errorf("PMAP 圖像數量不符")
	}
	for i, b := range out {
		if (i < 65 && (b.WidthBytes != 8 || b.Height != 25)) || (i >= 65 && (b.WidthBytes != 1 || b.Height != 3)) {
			return nil, fmt.Errorf("PMAP 圖像形狀不符")
		}
	}
	return out, nil
}

func loadGraphicsAssets(dir string, pmap []byte) (*GraphicsAssets, error) {
	raw, err := os.ReadFile(filepath.Join(dir, "terrain.json"))
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	var m terrainManifest
	if err = json.Unmarshal(raw, &m); err != nil {
		return nil, err
	}
	if m.Schema != 1 || m.SourceSHA != PMAPSHA || m.Style != "B-bright-painted-r1" || m.StyleSHA != ApprovedStyleSHA {
		return nil, fmt.Errorf("HD 圖像清單來源／樣式不符")
	}
	native, err := decodePMAP(pmap)
	if err != nil {
		return nil, err
	}
	out := &GraphicsAssets{Native: native, ByNative: map[string]uint16{}, Materials: map[uint16]*graphicMaterial{}}
	for _, b := range native {
		if _, ok := out.ByNative[b.NativeSHA]; ok {
			return nil, fmt.Errorf("PMAP 圖像指紋不唯一")
		}
		out.ByNative[b.NativeSHA] = uint16(b.Index + 1)
	}
	if len(m.Materials) < 1 || len(m.Materials) > len(native) {
		return nil, fmt.Errorf("HD 圖像清單數量不符")
	}
	for _, entry := range m.Materials {
		if entry.Index < 0 || entry.Index >= len(native) || entry.File == "" || entry.File != filepath.Base(entry.File) {
			return nil, fmt.Errorf("HD 圖像來源索引／檔名不符")
		}
		id := uint16(entry.Index + 1)
		if out.Materials[id] != nil {
			return nil, fmt.Errorf("HD 圖像來源索引重複")
		}
		data, err := os.ReadFile(filepath.Join(dir, entry.File))
		if err != nil {
			return nil, err
		}
		if len(data) > 32*1024*1024 || hash(data) != entry.SHA {
			return nil, fmt.Errorf("HD 圖像 %s SHA-256 不符", entry.File)
		}
		config, format, err := image.DecodeConfig(bytes.NewReader(data))
		if err != nil {
			return nil, err
		}
		if format != "png" || config.Width != entry.Width || config.Height != entry.Height || config.Width < 1 || config.Height < 1 || config.Width > 4096 || config.Height > 4096 || config.Width*config.Height > 8388608 {
			return nil, fmt.Errorf("HD 圖像尺寸／格式不符")
		}
		decoded, _, err := image.Decode(bytes.NewReader(data))
		if err != nil {
			return nil, err
		}
		b := native[entry.Index]
		bounds := decoded.Bounds()
		if len(entry.SourceRect) != 0 {
			if len(entry.SourceRect) != 4 {
				return nil, fmt.Errorf("HD 圖像取樣矩形須有四個整數")
			}
			r := entry.SourceRect
			if r[0] < 0 || r[1] < 0 || r[2] <= 0 || r[3] <= 0 || r[2] > bounds.Dx() || r[3] > bounds.Dy() || r[0] > bounds.Dx()-r[2] || r[1] > bounds.Dy()-r[3] {
				return nil, fmt.Errorf("HD 圖像取樣矩形越界")
			}
			bounds = image.Rect(r[0], r[1], r[0]+r[2], r[1]+r[3])
		}
		periodic := entry.Sampling == "" || entry.Sampling == "periodic"
		if !periodic && entry.Sampling != "bitmap" {
			return nil, fmt.Errorf("HD 圖像取樣模式未知")
		}
		tile, err := sampleMaterial(decoded, bounds, b.WidthBytes*8*3, b.Height*6, periodic)
		if err != nil {
			return nil, err
		}
		out.Materials[id] = &graphicMaterial{b.WidthBytes * 8, b.Height, tile}
	}
	// Composite dependencies are frozen before processing to disallow chains.
	materials := make(map[uint16]*graphicMaterial, len(out.Materials))
	for id, material := range out.Materials {
		materials[id] = material
	}
	if len(m.Composites) > 12 {
		return nil, fmt.Errorf("HD 岸線數量不符")
	}
	for _, entry := range m.Composites {
		if entry.Index < 2 || entry.Index > 13 || entry.Land != 0 || entry.Water != 1 || entry.Rule != "pmap-green-blue-v1" {
			return nil, fmt.Errorf("HD 岸線來源／合成規則不符")
		}
		id := uint16(entry.Index + 1)
		if out.Materials[id] != nil {
			return nil, fmt.Errorf("HD 圖像來源索引重複")
		}
		land, water := materials[1], materials[2]
		if land == nil || water == nil {
			return nil, fmt.Errorf("HD 岸線缺少草地或水面")
		}
		b := native[entry.Index]
		tile, err := shoreMaterial(b, land.Tile, water.Tile)
		if err != nil {
			return nil, err
		}
		out.Materials[id] = &graphicMaterial{b.WidthBytes * 8, b.Height, tile}
	}
	return out, nil
}

// Original PNG bytes remain untouched. This is the renderer's sampling cache.
func periodicMaterial(source image.Image, width, height int) (*image.RGBA, error) {
	return sampleMaterial(source, source.Bounds(), width, height, true)
}

func sampleMaterial(source image.Image, bounds image.Rectangle, width, height int, periodic bool) (*image.RGBA, error) {
	out := image.NewRGBA(image.Rect(0, 0, width, height))
	sw, sh := bounds.Dx(), bounds.Dy()
	for y := 0; y < height; y++ {
		for x := 0; x < width; x++ {
			sx, sy := (float64(x)+0.5)*float64(sw)/float64(width)-0.5, (float64(y)+0.5)*float64(sh)/float64(height)-0.5
			if sx < 0 {
				sx = 0
			}
			if sy < 0 {
				sy = 0
			}
			x0, y0 := int(sx), int(sy)
			x1, y1 := min(x0+1, sw-1), min(y0+1, sh-1)
			fx, fy := sx-float64(x0), sy-float64(y0)
			points := [4]image.Point{{x0, y0}, {x1, y0}, {x0, y1}, {x1, y1}}
			weights := [4]float64{(1 - fx) * (1 - fy), fx * (1 - fy), (1 - fx) * fy, fx * fy}
			sum := [3]float64{}
			for i, p := range points {
				r, g, b, a := source.At(bounds.Min.X+p.X, bounds.Min.Y+p.Y).RGBA()
				if a != 65535 {
					return nil, fmt.Errorf("地表素材須為不透明圖像")
				}
				for c, v := range [3]uint32{r >> 8, g >> 8, b >> 8} {
					sum[c] += float64(v) * weights[i]
				}
			}
			at := y*out.Stride + x*4
			for c := 0; c < 3; c++ {
				out.Pix[at+c] = uint8(sum[c] + 0.5)
			}
			out.Pix[at+3] = 255
		}
	}
	if !periodic {
		return out, nil
	}
	prior := append([]byte(nil), out.Pix...)
	for y := 0; y < height; y++ {
		for x := 0; x < width; x++ {
			ax := 0.5 * max(0, 1-float64(min(x, width-1-x))/16)
			ay := 0.5 * max(0, 1-float64(min(y, height-1-y))/16)
			weights := [4]float64{(1 - ax) * (1 - ay), ax * (1 - ay), (1 - ax) * ay, ax * ay}
			points := [4]image.Point{{x, y}, {width - 1 - x, y}, {x, height - 1 - y}, {width - 1 - x, height - 1 - y}}
			for c := 0; c < 3; c++ {
				v := 0.0
				for i, p := range points {
					v += float64(prior[p.Y*out.Stride+p.X*4+c]) * weights[i]
				}
				out.Pix[y*out.Stride+x*4+c] = uint8(v + 0.5)
			}
		}
	}
	return out, nil
}

// Presentation approximation of the visible shoreline, not a native alpha mask.
func shoreMaterial(b nativeBitmap, land, water *image.RGBA) (*image.RGBA, error) {
	w, h := b.WidthBytes*8, b.Height
	if w != 64 || h != 25 || len(b.Pixels) != w*h || land.Bounds() != water.Bounds() || land.Bounds() != image.Rect(0, 0, w*3, h*6) {
		return nil, fmt.Errorf("HD 岸線幾何不符")
	}
	labels := make([]int, len(b.Pixels))
	for i, code := range b.Pixels {
		switch code {
		case 2, 10, 14:
			labels[i] = 1
		case 1, 9, 11:
			labels[i] = -1
		case 0, 8:
		default:
			return nil, fmt.Errorf("HD 岸線出現未知色碼 %d", code)
		}
	}
	alpha := make([]float64, len(labels))
	wx, wy := [7]int{1, 2, 3, 4, 3, 2, 1}, [3]int{1, 2, 1}
	for y := 0; y < h; y++ {
		for x := 0; x < w; x++ {
			votes, total := 0, 0
			for iy, vy := range wy {
				for ix, vx := range wx {
					label := labels[max(0, min(h-1, y+iy-1))*w+max(0, min(w-1, x+ix-3))]
					if label != 0 {
						total += vx * vy
						if label == 1 {
							votes += vx * vy
						}
					}
				}
			}
			ratio := 0.5
			if total != 0 {
				ratio = float64(votes) / float64(total)
			}
			alpha[y*w+x] = max(0, min(1, (ratio-0.4)/0.2))
		}
	}
	out := image.NewRGBA(land.Bounds())
	for y := 0; y < h*6; y++ {
		for x := 0; x < w*3; x++ {
			sx, sy := max(0, (float64(x)+0.5)/3-0.5), max(0, (float64(y)+0.5)/6-0.5)
			x0, y0 := int(sx), int(sy)
			x1, y1 := min(x0+1, w-1), min(y0+1, h-1)
			fx, fy := sx-float64(x0), sy-float64(y0)
			a := (alpha[y0*w+x0]*(1-fx)+alpha[y0*w+x1]*fx)*(1-fy) + (alpha[y1*w+x0]*(1-fx)+alpha[y1*w+x1]*fx)*fy
			at := y*out.Stride + x*4
			for c := 0; c < 3; c++ {
				out.Pix[at+c] = uint8(float64(land.Pix[y*land.Stride+x*4+c])*a + float64(water.Pix[y*water.Stride+x*4+c])*(1-a) + 0.5)
			}
			out.Pix[at+3] = 255
		}
	}
	return out, nil
}
