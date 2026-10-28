// 054 READY. Additive assets only; original mode never opens this group.
package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/draw"
	"image/png"
	"io"
	"os"
	"path/filepath"
)

const completionManifestSHA = "f19fd53de76b27e7b6ba36aa0f517957871b73a7bec4372579285404908d3f94"

type completionRecord struct {
	SourceFile   string `json:"source_file"`
	Record       int    `json:"record"`
	OriginalSHA  string `json:"original_sha256"`
	SourceSHA    string `json:"source_sha256"`
	NativeSHA    string `json:"native_sha256"`
	NativeWidth  int    `json:"native_width"`
	NativeHeight int    `json:"native_height"`
	Planes       int    `json:"planes"`
	Route        string `json:"route"`
	ID           uint16 `json:"id"`
	Alias        uint16 `json:"alias"`
	Image        string `json:"image"`
	ImageSHA     string `json:"image_sha256"`
	Width        int    `json:"width"`
	Height       int    `json:"height"`
	texture      *image.RGBA
}
type completionAssets struct {
	Records []completionRecord
	ending  map[string]image.Image
}

func completionRead(dir, name string, limit int64) ([]byte, error) {
	if name == "" || name != filepath.Base(name) || name == "." || name == ".." {
		return nil, fmt.Errorf("補齊素材檔名不符")
	}
	p := filepath.Join(dir, name)
	s, err := os.Lstat(p)
	if err != nil {
		return nil, err
	}
	if !s.Mode().IsRegular() || s.Size() <= 0 || s.Size() > limit {
		return nil, fmt.Errorf("補齊素材檔案種類／大小不符：%s", name)
	}
	return os.ReadFile(p)
}
func loadCompletionAssets(dir, root string) (*completionAssets, error) {
	data, err := completionRead(dir, "completion.json", 128<<10)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if hash(data) != completionManifestSHA {
		return nil, fmt.Errorf("補齊素材清單SHA不符")
	}
	var manifest struct {
		Schema  int                `json:"schema"`
		Spec    string             `json:"spec"`
		Records []completionRecord `json:"records"`
	}
	d := json.NewDecoder(bytes.NewReader(data))
	d.DisallowUnknownFields()
	if err = d.Decode(&manifest); err != nil {
		return nil, err
	}
	if d.Decode(new(any)) != io.EOF || manifest.Schema != 1 || manifest.Spec != "054" || len(manifest.Records) != 62 {
		return nil, fmt.Errorf("補齊素材清單範圍不符")
	}
	a := &completionAssets{Records: manifest.Records, ending: map[string]image.Image{}}
	checked := map[string]string{}
	active := 0
	for i := range a.Records {
		r := &a.Records[i]
		if checked[r.SourceFile] != r.OriginalSHA {
			b, er := completionRead(root, r.SourceFile, 2<<20)
			if er != nil {
				return nil, er
			}
			if hash(b) != r.OriginalSHA {
				return nil, fmt.Errorf("補齊素材原始來源不符：%s", r.SourceFile)
			}
			checked[r.SourceFile] = r.OriginalSHA
		}
		b, er := completionRead(dir, r.Image, 8<<20)
		if er != nil {
			return nil, er
		}
		if hash(b) != r.ImageSHA {
			return nil, fmt.Errorf("補齊素材PNG SHA不符：%s", r.Image)
		}
		cfg, er := png.DecodeConfig(bytes.NewReader(b))
		if er != nil || cfg.Width != r.Width || cfg.Height != r.Height {
			return nil, fmt.Errorf("補齊素材PNG尺寸不符：%s", r.Image)
		}
		if r.Route == "archive" {
			continue
		}
		if r.Route != "ending" && r.Route != "material" && r.Route != "actor" {
			return nil, fmt.Errorf("補齊素材路徑不符")
		}
		if r.Width != r.NativeWidth*3 || r.Height != r.NativeHeight*6 {
			return nil, fmt.Errorf("補齊素材執行期比例不符")
		}
		im, er := png.Decode(bytes.NewReader(b))
		if er != nil {
			return nil, er
		}
		r.texture = image.NewRGBA(image.Rect(0, 0, r.Width, r.Height))
		draw.Draw(r.texture, r.texture.Bounds(), im, im.Bounds().Min, draw.Src)
		active++
		if r.Route == "ending" {
			if a.ending[r.SourceSHA] != nil {
				return nil, fmt.Errorf("補齊結局來源重複")
			}
			a.ending[r.SourceSHA] = r.texture
		}
	}
	if active != 17 || len(a.ending) != 8 {
		return nil, fmt.Errorf("補齊素材組不完整")
	}
	return a, nil
}
func (a *completionAssets) bindGraphics(g *GraphicsAssets) error {
	if a == nil {
		return nil
	}
	if g == nil || g.ByNative == nil || g.Materials == nil || g.Actors == nil || g.ActorSHA == nil {
		return fmt.Errorf("補齊素材缺少圖像目錄")
	}
	// Validate every slot before making any source identity visible.
	for _, r := range a.Records {
		if r.Route != "material" && r.Route != "actor" {
			continue
		}
		existing := g.ByNative[r.NativeSHA]
		if (r.ID >= 66 && r.ID <= 68 && existing != r.ID) || (r.ID > 68 && existing != 0) {
			return fmt.Errorf("補齊素材來源識別衝突")
		}
		for _, id := range []uint16{r.ID, r.Alias} {
			if id == 0 {
				continue
			}
			if g.Materials[id] != nil || g.Actors[id] != nil || g.Effects[id] != nil || g.ActorSHA[id] != "" || g.EffectSHA[id] != "" || g.BattleActors[id] || g.BattleAliases[id] != 0 {
				return fmt.Errorf("補齊素材材質識別衝突")
			}
			for _, mapped := range g.ByNative {
				if mapped == id && !(id >= 66 && id <= 68 && existing == id) {
					return fmt.Errorf("補齊素材來源別名衝突")
				}
			}
		}
	}
	if g.BattleActors == nil {
		g.BattleActors = map[uint16]bool{}
	}
	if g.BattleAliases == nil {
		g.BattleAliases = map[uint16]uint16{}
	}
	for _, r := range a.Records {
		if r.Route != "material" && r.Route != "actor" {
			continue
		}
		m := &graphicMaterial{r.NativeWidth, r.NativeHeight, r.texture}
		g.ByNative[r.NativeSHA] = r.ID
		if r.Route == "material" {
			g.Materials[r.ID] = m
			continue
		}
		g.Actors[r.ID] = m
		g.ActorSHA[r.ID] = r.SourceSHA
		g.Actors[r.Alias] = m
		g.ActorSHA[r.Alias] = r.SourceSHA
		g.BattleActors[r.Alias] = true
		g.BattleAliases[r.ID] = r.Alias
	}
	return nil
}
func (a *completionAssets) status() map[string]any {
	if a == nil {
		return map[string]any{"registered": false}
	}
	return map[string]any{"registered": true, "records": len(a.Records), "new_player_records": 17, "existing_intro_records": 2, "archive_records": 43}
}
