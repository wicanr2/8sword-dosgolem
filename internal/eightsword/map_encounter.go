package eightsword

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"image"
	"io"
	"math/bits"
	"os"
	"path/filepath"
)

const encounterSourceSHA = "0d18b068e177b54f7b8a2b30072e9ae3ebc984fbed9fd6a8706f71d3140a5ffd"
const encounterImageSHA = "81f72e1ad3e1363c38c49eed75fcd906302a74818f21845e073310026954e146"
const encounterPromptSHA = "9b5cbabeeab94c5eb542b4a4e775aceb3148ecfef29265b681e022361d16360d"
const encounterFirstID uint16 = 116

func encounterRead(path string, limit int64) ([]byte, error) {
	info, err := os.Lstat(path)
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > limit {
		return nil, fmt.Errorf("地圖遭遇檔案類型／容量不符")
	}
	return os.ReadFile(path)
}

// Each fixed source group commits independently. Spec 037 keeps empty,
// shared heights 1/3/5 native; spec 038 has thirteen unique visible prefixes.
type encounterGroup struct {
	Manifest              string
	Record, FirstHeight   int
	FirstID               uint16
	Image                 graphicPNG
	Rect, Target          [4]int
	SampleRect            image.Rectangle
	PromptFile, PromptSHA string
	MirrorCache           bool
}

func loadMapEncounter(dir, root string, assets *GraphicsAssets) error {
	return loadMapEncounterGroup(dir, root, assets, encounterGroup{
		Manifest: "map-encounter.json", Record: 13, FirstHeight: 7, FirstID: encounterFirstID,
		Image: graphicPNG{Index: 115, File: "map-encounter-13-r1.png", SHA: encounterImageSHA, Width: 1419, Height: 1108, Sampling: "bitmap"},
		Rect:  [4]int{11, 72, 1408, 1078}, Target: [4]int{3, 30, 189, 150}, SampleRect: image.Rect(11, 72, 1408, 1078),
		PromptFile: "map-encounter-13-r1.prompt.txt", PromptSHA: encounterPromptSHA,
	})
}

func loadMapEncounter10(dir, root string, assets *GraphicsAssets) error {
	return loadMapEncounterGroup(dir, root, assets, encounterGroup{
		Manifest: "map-encounter-10.json", Record: 10, FirstHeight: 1, FirstID: 126,
		Image: graphicPNG{Index: 125, File: "battle-man16-0-r1.png", SHA: "53a599a6db8f10cf76d08de389fbf07b72b6f3c8f9fdf6647256c440809300ad", Width: 1176, Height: 1337, Sampling: "bitmap"},
		Rect:  [4]int{123, 311, 1052, 902}, Target: [4]int{0, 0, 192, 150}, SampleRect: image.Rect(123, 311, 1175, 1213),
		PromptFile: "battle-actors-prompts.txt", PromptSHA: "c319d1165e849f1177a537a05fdf32a74418998f83cf2b6f6f9f45340b6ddf62", MirrorCache: true,
	})
}

func loadMapEncounter7(dir, root string, assets *GraphicsAssets) error {
	return loadMapEncounterGroup(dir, root, assets, encounterGroup{
		Manifest: "map-encounter-7.json", Record: 7, FirstHeight: 5, FirstID: 139,
		Image: graphicPNG{Index: 138, File: "map-encounter-7-r1.png", SHA: "b5f71a301064ed1d2a050588d400b0fe9113289e9baa2e5bb39c4e66def4e1b0", Width: 1419, Height: 1108, Sampling: "bitmap"},
		Rect:  [4]int{62, 54, 1360, 1045}, Target: [4]int{21, 18, 162, 150}, SampleRect: image.Rect(62, 54, 1360, 1045),
		PromptFile: "map-encounter-7-r1.prompt.txt", PromptSHA: "cef47c1fcc11ebc15810b596f720df9b8db25b12ef1a01162c25412e7cb2eb4e",
	})
}

func loadMapEncounterGroup(dir, root string, assets *GraphicsAssets, cfg encounterGroup) error {
	raw, err := encounterRead(filepath.Join(dir, cfg.Manifest), 64*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var m struct {
		Schema     int        `json:"schema"`
		Source     string     `json:"source"`
		SourceSHA  string     `json:"source_sha256"`
		Record     int        `json:"record"`
		Transform  string     `json:"transform"`
		Style      string     `json:"style"`
		StyleSHA   string     `json:"style_reference_sha256"`
		Image      graphicPNG `json:"image"`
		Target     []int      `json:"target_rect"`
		PromptFile string     `json:"prompt_file"`
		PromptSHA  string     `json:"prompt_sha256"`
		Rights     string     `json:"rights"`
	}
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err = d.Decode(&m); err != nil {
		return err
	}
	if err = d.Decode(new(any)); err != io.EOF {
		return fmt.Errorf("地圖遭遇清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != "ENEMY.AY" || m.SourceSHA != encounterSourceSHA || m.Record != cfg.Record || m.Transform != "mirror-six-planes" || m.Style != "B-bright-painted-r1" || m.StyleSHA != ApprovedStyleSHA || m.Image.Index != cfg.Image.Index || m.Image.File != cfg.Image.File || m.Image.SHA != cfg.Image.SHA || m.Image.Width != cfg.Image.Width || m.Image.Height != cfg.Image.Height || m.Image.Sampling != "bitmap" || m.PromptFile != cfg.PromptFile || m.PromptSHA != cfg.PromptSHA {
		return fmt.Errorf("地圖遭遇來源／圖像不符")
	}
	if !equalEncounterRect(m.Image.SourceRect, cfg.Rect) || !equalEncounterRect(m.Target, cfg.Target) {
		return fmt.Errorf("地圖遭遇取樣位置不符")
	}
	source, err := encounterRead(filepath.Join(root, m.Source), 16856)
	if err != nil {
		return err
	}
	if len(source) != 16856 || hash(source) != encounterSourceSHA {
		return fmt.Errorf("ENEMY.AY 來源 SHA-256 不符")
	}
	prompt, err := encounterRead(filepath.Join(dir, m.PromptFile), 64*1024)
	if err != nil {
		return err
	}
	if hash(prompt) != cfg.PromptSHA {
		return fmt.Errorf("地圖遭遇提示 SHA-256 不符")
	}
	if _, err = encounterRead(filepath.Join(dir, m.Image.File), 8*1024*1024); err != nil {
		return err
	}
	im, err := loadGraphicPNG(dir, m.Image)
	if err != nil {
		return err
	}
	// Reuse the verified premultiplied sampler; keep the map-sized rectangle.
	sampled, err := sampleBattleActor(im, cfg.SampleRect, image.Rect(cfg.Target[0], cfg.Target[1], cfg.Target[2], cfg.Target[3]))
	if err != nil {
		return err
	}
	full := image.NewRGBA(image.Rect(0, 0, 192, 150))
	for y := 0; y < 150; y++ {
		copy(full.Pix[y*full.Stride:(y+1)*full.Stride], sampled.Pix[y*sampled.Stride:y*sampled.Stride+192*4])
	}
	if cfg.MirrorCache {
		for y := 0; y < 150; y++ {
			for x := 0; x < 96; x++ {
				a, b := y*full.Stride+x*4, y*full.Stride+(191-x)*4
				for c := 0; c < 4; c++ {
					full.Pix[a+c], full.Pix[b+c] = full.Pix[b+c], full.Pix[a+c]
				}
			}
		}
	}
	record := source[cfg.Record*1204 : (cfg.Record+1)*1204]
	mirrored := make([]byte, 1204)
	copy(mirrored, record[:4])
	for row := 4; row < 1204; row += 8 {
		for x := 0; x < 8; x++ {
			mirrored[row+x] = bits.Reverse8(record[row+7-x])
		}
	}
	native, complete := make([]string, (27-cfg.FirstHeight)/2), make([]string, (27-cfg.FirstHeight)/2)
	for i := range native {
		height := cfg.FirstHeight + i*2
		prefix := make([]byte, 4+48*height)
		binary.LittleEndian.PutUint16(prefix, 8)
		binary.LittleEndian.PutUint16(prefix[2:], uint16(height))
		for plane := 0; plane < 6; plane++ {
			copy(prefix[4+plane*8*height:], mirrored[4+plane*200:4+plane*200+8*height])
		}
		native[i], complete[i] = hash(prefix[:4+32*height]), hash(prefix)
		id := cfg.FirstID + uint16(i)
		if assets.ByNative[native[i]] != 0 || assets.Materials[id] != nil || assets.Actors[id] != nil || assets.Effects[id] != nil || assets.BattleActors[id] {
			return fmt.Errorf("地圖遭遇來源識別重複")
		}
	}
	// No failure after this point. Prefixes share one immutable cache.
	if assets.ByNative == nil {
		assets.ByNative = map[string]uint16{}
	}
	if assets.Actors == nil {
		assets.Actors = map[uint16]*graphicMaterial{}
	}
	if assets.ActorSHA == nil {
		assets.ActorSHA = map[uint16]string{}
	}
	for i := range native {
		height, id := cfg.FirstHeight+i*2, cfg.FirstID+uint16(i)
		assets.ByNative[native[i]] = id
		assets.ActorSHA[id] = complete[i]
		assets.Actors[id] = &graphicMaterial{64, height, full.SubImage(image.Rect(0, 0, 192, height*6)).(*image.RGBA)}
	}
	return nil
}

func equalEncounterRect(got []int, want [4]int) bool {
	return len(got) == 4 && got[0] == want[0] && got[1] == want[1] && got[2] == want[2] && got[3] == want[3]
}
