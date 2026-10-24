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

// Spec 037. Empty, shared heights 1/3/5 stay native; only the ten fixed
// visible prefixes of mirrored ENEMY.AY record 13 are registered together.
func loadMapEncounter(dir, root string, assets *GraphicsAssets) error {
	raw, err := encounterRead(filepath.Join(dir, "map-encounter.json"), 64*1024)
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
	if m.Schema != 1 || m.Source != "ENEMY.AY" || m.SourceSHA != encounterSourceSHA || m.Record != 13 || m.Transform != "mirror-six-planes" || m.Style != "B-bright-painted-r1" || m.StyleSHA != ApprovedStyleSHA || m.Image.Index != 115 || m.Image.File != "map-encounter-13-r1.png" || m.Image.SHA != encounterImageSHA || m.Image.Width != 1419 || m.Image.Height != 1108 || m.Image.Sampling != "bitmap" || m.PromptFile != "map-encounter-13-r1.prompt.txt" || m.PromptSHA != encounterPromptSHA {
		return fmt.Errorf("地圖遭遇來源／圖像不符")
	}
	if !equalEncounterRect(m.Image.SourceRect, [4]int{11, 72, 1408, 1078}) || !equalEncounterRect(m.Target, [4]int{3, 30, 189, 150}) {
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
	if hash(prompt) != encounterPromptSHA {
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
	sampled, err := sampleBattleActor(im, image.Rect(11, 72, 1408, 1078), image.Rect(3, 30, 189, 150))
	if err != nil {
		return err
	}
	full := image.NewRGBA(image.Rect(0, 0, 192, 150))
	for y := 0; y < 150; y++ {
		copy(full.Pix[y*full.Stride:(y+1)*full.Stride], sampled.Pix[y*sampled.Stride:y*sampled.Stride+192*4])
	}
	record := source[13*1204 : 14*1204]
	mirrored := make([]byte, 1204)
	copy(mirrored, record[:4])
	for row := 4; row < 1204; row += 8 {
		for x := 0; x < 8; x++ {
			mirrored[row+x] = bits.Reverse8(record[row+7-x])
		}
	}
	var native, complete [10]string
	for i := range native {
		height := 7 + i*2
		prefix := make([]byte, 4+48*height)
		binary.LittleEndian.PutUint16(prefix, 8)
		binary.LittleEndian.PutUint16(prefix[2:], uint16(height))
		for plane := 0; plane < 6; plane++ {
			copy(prefix[4+plane*8*height:], mirrored[4+plane*200:4+plane*200+8*height])
		}
		native[i], complete[i] = hash(prefix[:4+32*height]), hash(prefix)
		id := encounterFirstID + uint16(i)
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
		height, id := 7+i*2, encounterFirstID+uint16(i)
		assets.ByNative[native[i]] = id
		assets.ActorSHA[id] = complete[i]
		assets.Actors[id] = &graphicMaterial{64, height, full.SubImage(image.Rect(0, 0, 192, height*6)).(*image.RGBA)}
	}
	return nil
}

func equalEncounterRect(got []int, want [4]int) bool {
	return len(got) == 4 && got[0] == want[0] && got[1] == want[1] && got[2] == want[2] && got[3] == want[3]
}
