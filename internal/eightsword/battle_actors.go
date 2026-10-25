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

const man11SourceSHA = "860ab98a7165f25fe2007dd597ddf6fc698c9d2f048701eec955a1a0cd65f832"

// Spec 025: MAN11.EGG file offsets record*3304, all six blocks verified.
var man11Sources = [...]battleActorSource{
	{"d9e5a89286a0a638fab3e58fa97971b43e4ca91bb2511242a3389999f69e6e01", "6da1d9280af54d9f30da94fd6da26c6c61149dc2e8a615affbd497a0a0b43d5d"},
	{"25b04512737dbb914f852a421d805279afb5134c2153964550b1833f05536a37", "87c1811812b52903da1e84d28097f2aa36bf2dbffdda733499ee09140bfacadf"},
	{"f2a8d585bdc3c07d263d3add30817e6b79cf5316c0b5ab2fc449e54aa8ee0fc8", "8b62cd1556331c561f8e83d1b1afc8b5cb08d059a4c1c085b339679a8babcf96"},
	{"8de82b2648b9624e11fe619f9884dd6663ac749dc858613b2a7fce73d9f39fff", "5ce96cf4662823aada52459ae9d1a2a933f9b45d844a128defbf10dd6b300693"},
}

var man11Targets = [...][4]int{{96, 30, 165, 246}, {96, 18, 165, 258}, {96, 6, 165, 234}, {24, 6, 237, 234}}

const man21SourceSHA = "47cc484319abeba53551c20b7cf4b9b2c6061f2da3b6cda14155b3598f10982c"

// Spec 026: exact source records; action-trigger semantics remain unverified.
var man21Sources = [...]battleActorSource{
	{"acf951cb60d240be24a1359db34bb16e16268961ad064ce66e81b43e0d8e4235", "60692a5484c93406ec70ae7316e0a905d09ce9a9d1f8cce5b051692dbcc64164"},
	{"220a6ab3f6303d844a43657e98a64d58c29a43547b41c1c5ba0197018f9a085f", "0426c60e7ab8b5ea3dbcf184b7372beb3a520406e730c4527b666ab2bc56777f"},
	{"72657edc7d53a4729afc8d6bdc11ec838bd3beaf5f9bd5399f441b5d68ef4576", "547205ea9d571c29e718c0a94f2633902270c2139aa2a8939c6dbd006746b146"},
	{"4777b384a41809bee4e3b77e611ce2300f83145e5be91ee73b4d29c6c7c3d455", "549d51ea698bcd20116cdc3e552d5a47826a077ce13bf7debd5086e6f38d6051"},
}

var man21Targets = [...][4]int{{48, 78, 213, 186}, {60, 78, 201, 186}, {84, 78, 177, 186}, {0, 78, 261, 186}}

// Spec 036: records 1–3 after all six planes have been mirrored by the guest.
// Record 0 keeps the shared F2 cache and the separate spec 028 battle alias.
var man01PoseSources = [4]battleActorSource{
	{"99b7d57ea025fe32f02f245c457c6fc779794fdd6ed50baf62654de031335d7c", "ea9735a587549708dcfb17d8c163065b5265e0ccfcd66fd9cb505f68f386f175"},
	{"8bc1fa0a96f90ab9b8636d765bbd6eb949223e781c2d73aff8e76cb755dc4e42", "f741358c8c7ffe767479f5be83236afca0fcc7087b6d1dd02506c76bfd0f2611"},
	{"9679f25b082babf9376fc4093e2cba00b8bafea538724d82b28cf4b2be122a6c", "343d7379493dffbfaf7f23e074bc5799aa74bc705d1a3cf4fa556ed3d91b2c21"},
}

var man01PoseTargets = [4][4]int{{0, 0, 264, 300}, {0, 0, 264, 300}, {0, 0, 264, 300}}

type battleActorGroup struct {
	Manifest, Source, SourceSHA, Stem string
	FirstID                           uint16
	Sources                           [4]battleActorSource
	Targets                           [4][4]int
	FirstRecord, Count                int
	Transform                         string
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
		{"battle-actors.json", "MAN16.EGG", man16SourceSHA, "battle-man16", 87, man16Sources, man16Targets, 0, 4, ""},
		{"battle-man06.json", "MAN06.EGG", man06SourceSHA, "battle-man06", 91, man06Sources, man06Targets, 0, 4, ""},
		{"battle-man11.json", "MAN11.EGG", man11SourceSHA, "battle-man11", 95, man11Sources, man11Targets, 0, 4, ""},
		{"battle-man21.json", "MAN21.EGG", man21SourceSHA, "battle-man21", 99, man21Sources, man21Targets, 0, 4, ""},
		{"battle-man01.json", "MAN01.EGG", militiaSourceSHA, "battle-man01", 113, man01PoseSources, man01PoseTargets, 1, 3, "mirror-six-planes"},
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

// Each fixed group commits only after all of its images pass validation.
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
		Transform string `json:"transform"`
		Frames    []struct {
			Record int        `json:"record"`
			Image  graphicPNG `json:"image"`
			Target []int      `json:"target_rect"`
		} `json:"frames"`
	}
	if err = json.Unmarshal(raw, &m); err != nil {
		return err
	}
	if m.Schema != 1 || m.Source != group.Source || m.SourceSHA != group.SourceSHA || m.Style != "B-bright-painted-r1" || m.StyleSHA != ApprovedStyleSHA || m.Transform != group.Transform || len(m.Frames) != group.Count {
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
		if frame.Record != group.FirstRecord+i || entry.Index != int(group.FirstID)-1+i || entry.File != fmt.Sprintf("%s-%d-r1.png", group.Stem, group.FirstRecord+i) || entry.Sampling != "bitmap" || len(frame.Target) != 4 {
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
	for i, tile := range tiles[:group.Count] {
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
	return g.battleBackgroundKnown(first, width, height)
}
