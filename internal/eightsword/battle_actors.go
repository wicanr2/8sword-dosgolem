package eightsword

import (
	"encoding/json"
	"fmt"
	"image"
	"os"
	"path/filepath"
	"strings"
)

const man16SourceSHA = "d4acf7c58c199c1776ffde6c86afa3c9b0ae3b132e4cc59973e1e0d5c2011d6a"

// Spec 023: original file offsets record*3304, no runtime pointer aliases.
type battleActorSource struct{ Native, Record string }

var man16Sources = [...]battleActorSource{
	{"fc39ee5d322f75dcfd282c49577428e17b618aa6e7b3c66cd3cec6c2c91d1ebc", "6f63681e789a462164c7213774c2cac6367cb820ad661665aad541d0cfc6250d"},
	{"49333ee62fcb5752cd36a5c96de680d3203dc0a89d5820ace9dfc02248955b13", "821286f200de68b303d4ecaa11791b6d54b1dfe922f098b17fd35707d1673b3a"},
	{"e7e80754f15a5523cf48648081e8def41df88e67d4d2b38eb60e2aaf8af73c93", "e00d323c14f7ecb4d4b871ce06cd8d35efc278ad8bb9810908007bed4781307b"},
	{"22a1a2f66c408d00728611bb8eeaeb2fe426e86cac3f47aaf35b825d83a7e55b", "e36b6be555cca76fe43a6c38d830d1277bce3e0d6a6ba3802cbf56cf6fd5c2d3"},
}

var man16Targets = [...][4]int{{30, 84, 231, 192}, {30, 96, 231, 180}, {27, 36, 234, 174}, {33, 60, 228, 174}}

const man06SourceSHA = "97be211dd9289538aaa46f01b2340bcac9ce0a7c8e44ed9d3c4e9abdac873579"

// Spec 024: MAN06.EGG file offsets record*3304, all six blocks verified.
var man06Sources = [...]battleActorSource{
	{"aa5f02e465c9de0a3e5712b113bf55485f9a77b0f0ee4e899d09740ddc6ead44", "26912dfd61615c79153fdce658ef87e8c7a91033b8b696b1944671ebf12a9191"},
	{"5684432d40e7bf4dfdb4c530a28b0cd08f4d7445acec8935dece70001f337b6b", "665bac29b8c8d54912a52da5eda20ae44ed9c81c3d6fcd8b039a9317a066c022"},
	{"86c1ad22335e8d4031ec519c04ca136a2e3b5fca05def14ec0fce56b0faf008c", "feb0565d9333a288d5e8f89d37cdfbfa1804cc4d33183810120ba3f74e77c9a7"},
	{"b414a5e640206ffe720c71737dce7a2d70e31fb478e58f9bd84e06e43a271674", "8ce14e5fa82252dd91b698803e3738ab2b6ce3f3e3f3f22ec1b7b4c1f03f1b00"},
}

var man06Targets = [...][4]int{{75, 54, 177, 210}, {78, 42, 177, 222}, {78, 0, 183, 210}, {18, 0, 243, 210}}

type battleActorGroup struct {
	Manifest, Source, SourceSHA, Stem string
	FirstID                           uint16
	Sources                           [4]battleActorSource
	Targets                           [4][4]int
}

func battleActorRect(values []int, width, height int) (image.Rectangle, error) {
	if len(values) != 4 {
		return image.Rectangle{}, fmt.Errorf("部隊矩形須有四個整數")
	}
	x, y, w, h := values[0], values[1], values[2], values[3]
	if x < 0 || y < 0 || w <= 0 || h <= 0 || w > width || h > height || x > width-w || y > height-h {
		return image.Rectangle{}, fmt.Errorf("部隊矩形越界")
	}
	return image.Rect(x, y, x+w, y+h), nil
}

// Groups commit independently; a broken optional group cannot disable another.
func loadBattleActors(dir, root string, assets *GraphicsAssets) error {
	groups := []battleActorGroup{
		{"battle-actors.json", "MAN16.EGG", man16SourceSHA, "battle-man16", 87, man16Sources, man16Targets},
		{"battle-man06.json", "MAN06.EGG", man06SourceSHA, "battle-man06", 91, man06Sources, man06Targets},
	}
	var failures []string
	for _, group := range groups {
		if err := loadBattleActorGroup(dir, root, assets, group); err != nil {
			failures = append(failures, group.Source+": "+err.Error())
		}
	}
	if len(failures) > 0 {
		return fmt.Errorf("%s", strings.Join(failures, "；"))
	}
	return nil
}

// Each group commits only after all four images have passed validation.
func loadBattleActorGroup(dir, root string, assets *GraphicsAssets, group battleActorGroup) error {
	raw, err := os.ReadFile(filepath.Join(dir, group.Manifest))
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var m struct {
		Schema    int    `json:"schema"`
		Source    string `json:"source_file"`
		SourceSHA string `json:"source_sha256"`
		Style     string `json:"style"`
		StyleSHA  string `json:"style_reference_sha256"`
		Frames    []struct {
			Record int        `json:"record"`
			Image  graphicPNG `json:"image"`
			Target []int      `json:"target_rect"`
		} `json:"frames"`
	}
	if err = json.Unmarshal(raw, &m); err != nil {
		return err
	}
	if m.Schema != 1 || m.Source != group.Source || m.SourceSHA != group.SourceSHA || m.Style != "B-bright-painted-r1" || m.StyleSHA != ApprovedStyleSHA || len(m.Frames) != 4 {
		return fmt.Errorf("戰場部隊清單來源／樣式不符")
	}
	if assets.Materials[battleBackgroundID] == nil || assets.ByNative[battleBackgroundNativeSHA] != battleBackgroundID {
		return fmt.Errorf("戰場部隊缺少已驗 GRO02 背景")
	}
	source, err := os.ReadFile(filepath.Join(root, m.Source))
	if err != nil {
		return err
	}
	if hash(source) != group.SourceSHA {
		return fmt.Errorf("%s 來源雜湊不符", group.Source)
	}
	var tiles [4]*image.RGBA
	for i, frame := range m.Frames {
		entry, id := frame.Image, group.FirstID+uint16(i)
		if frame.Record != i || entry.Index != int(group.FirstID)-1+i || entry.File != fmt.Sprintf("%s-%d-r1.png", group.Stem, i) || entry.Sampling != "bitmap" || len(frame.Target) != 4 {
			return fmt.Errorf("戰場部隊記錄／檔名不符")
		}
		for n, want := range group.Targets[i] {
			if frame.Target[n] != want {
				return fmt.Errorf("戰場部隊目的位置不符")
			}
		}
		if assets.ByNative[group.Sources[i].Native] != 0 || assets.Materials[id] != nil || assets.Actors[id] != nil {
			return fmt.Errorf("戰場部隊識別重複")
		}
		decoded, err := loadGraphicPNG(dir, entry)
		if err != nil {
			return err
		}
		src, err := battleActorRect(entry.SourceRect, entry.Width, entry.Height)
		if err != nil {
			return err
		}
		dst, err := battleActorRect(frame.Target, 264, 300)
		if err != nil {
			return err
		}
		tiles[i], err = sampleBattleActor(decoded, src, dst)
		if err != nil {
			return err
		}
	}
	if assets.BattleActors == nil {
		assets.BattleActors = map[uint16]bool{}
	}
	for i, tile := range tiles {
		id := group.FirstID + uint16(i)
		assets.ByNative[group.Sources[i].Native] = id
		assets.Actors[id] = &graphicMaterial{88, 50, tile}
		assets.ActorSHA[id] = group.Sources[i].Record
		assets.BattleActors[id] = true
	}
	return nil
}

// Original PNG bytes are preserved. Only this premultiplied cache is registered.
func sampleBattleActor(source image.Image, src, dst image.Rectangle) (*image.RGBA, error) {
	if src.Empty() || !src.In(source.Bounds()) || dst.Empty() || !dst.In(image.Rect(0, 0, 264, 300)) {
		return nil, fmt.Errorf("戰場部隊取樣範圍不符")
	}
	hasZero, hasOpaque := false, false
	for y := source.Bounds().Min.Y; y < source.Bounds().Max.Y; y++ {
		for x := source.Bounds().Min.X; x < source.Bounds().Max.X; x++ {
			_, _, _, a := source.At(x, y).RGBA()
			hasZero = hasZero || a == 0
			hasOpaque = hasOpaque || a == 65535
			if !image.Pt(x, y).In(src) && a > 3*257 {
				return nil, fmt.Errorf("部隊來源矩形裁到可見圖像")
			}
		}
	}
	if !hasZero || !hasOpaque {
		return nil, fmt.Errorf("戰場部隊須有透明背景與不透明主體")
	}
	out := image.NewRGBA(image.Rect(0, 0, 264, 300))
	for y := 0; y < dst.Dy(); y++ {
		for x := 0; x < dst.Dx(); x++ {
			sx := max(0, (float64(x)+0.5)*float64(src.Dx())/float64(dst.Dx())-0.5)
			sy := max(0, (float64(y)+0.5)*float64(src.Dy())/float64(dst.Dy())-0.5)
			x0, y0 := int(sx), int(sy)
			x1, y1 := min(x0+1, src.Dx()-1), min(y0+1, src.Dy()-1)
			fx, fy := sx-float64(x0), sy-float64(y0)
			points := [4]image.Point{{x0, y0}, {x1, y0}, {x0, y1}, {x1, y1}}
			weights := [4]float64{(1 - fx) * (1 - fy), fx * (1 - fy), (1 - fx) * fy, fx * fy}
			sums := [4]float64{}
			for i, p := range points {
				r, g, b, a := source.At(src.Min.X+p.X, src.Min.Y+p.Y).RGBA()
				if a <= 3*257 {
					continue
				}
				for c, v := range [4]uint32{r, g, b, a} {
					sums[c] += weights[i] * float64(v)
				}
			}
			at := (dst.Min.Y+y)*out.Stride + (dst.Min.X+x)*4
			for c, v := range sums {
				out.Pix[at+c] = uint8(min(255, v/257) + 0.5)
			}
		}
	}
	return out, nil
}

func (g *Graphics) battleActorBackgroundKnown(first uint32, width, height int) bool {
	if width != 88 || height != 50 || len(g.actors) == 0 {
		return false
	}
	for y := 0; y < height; y++ {
		for x := 0; x < width; x++ {
			c := g.owners[(first+uint32(y*80+x/8))*8+uint32(x%8)]
			if c.ID != battleBackgroundID || c.Local >= 640*200 {
				return false
			}
		}
	}
	return true
}
