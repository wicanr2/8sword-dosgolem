package eightsword

// Spec 017: validate the selected A group before installing any callbacks.
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

type museumGroupRecord struct {
	File   string `json:"file"`
	Offset int    `json:"decoded_offset"`
	Bytes  int    `json:"bytes"`
	Width  int    `json:"row_bytes"`
	Height int    `json:"rows"`
	Blocks int    `json:"blocks"`
	Role   string `json:"role"`
	SHA    string `json:"sha256"`
}
type museumGroupAsset struct {
	ID       string   `json:"id"`
	File     string   `json:"file"`
	SHA      string   `json:"png_sha256"`
	Width    int      `json:"width"`
	Height   int      `json:"height"`
	Policy   string   `json:"cache_policy"`
	CacheSHA string   `json:"cache_sha256"`
	Sources  []string `json:"source_records"`
}
type museumGroupManifest struct {
	Schema  int                 `json:"schema"`
	Status  string              `json:"status"`
	Palette string              `json:"palette"`
	Rights  string              `json:"rights"`
	Packed  map[string]string   `json:"packed_sources"`
	Decoded map[string]string   `json:"decoded_sources"`
	Records []museumGroupRecord `json:"records"`
	Assets  []museumGroupAsset  `json:"assets"`
}

func museumGroupFile(root, name string, limit int64) ([]byte, error) {
	if name == "" || name == "." || name == ".." || filepath.Base(name) != name || bytes.ContainsAny([]byte(name), "/\\") {
		return nil, fmt.Errorf("group basename differs")
	}
	p := filepath.Join(root, name)
	info, err := os.Lstat(p)
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > limit {
		return nil, fmt.Errorf("group file type/size differs")
	}
	return os.ReadFile(p)
}

func museumCleanCache(p *image.NRGBA, policy string) error {
	if policy == "opaque" {
		for at := 3; at < len(p.Pix); at += 4 {
			if p.Pix[at] != 255 {
				return fmt.Errorf("opaque group image has alpha")
			}
		}
		return nil
	}
	if policy != "floor8-largest8" {
		return fmt.Errorf("group cache policy differs")
	}
	w, h := p.Bounds().Dx(), p.Bounds().Dy()
	seen := make([]bool, w*h)
	var largest []int
	ambiguous := false
	var total, removed uint64
	minA, maxA := byte(255), byte(0)
	for at := 3; at < len(p.Pix); at += 4 {
		a := p.Pix[at]
		total += uint64(a)
		if a < minA {
			minA = a
		}
		if a > maxA {
			maxA = a
		}
	}
	if minA != 0 || maxA != 255 {
		return fmt.Errorf("cutout lacks transparent/opaque pixels")
	}
	for start := 0; start < w*h; start++ {
		if seen[start] || p.Pix[start*4+3] < 8 {
			continue
		}
		seen[start] = true
		queue := []int{start}
		for at := 0; at < len(queue); at++ {
			n := queue[at]
			x, y := n%w, n/w
			for yy := max(0, y-1); yy < min(h, y+2); yy++ {
				for xx := max(0, x-1); xx < min(w, x+2); xx++ {
					q := yy*w + xx
					if !seen[q] && p.Pix[q*4+3] >= 8 {
						seen[q] = true
						queue = append(queue, q)
					}
				}
			}
		}
		if len(queue) == len(largest) {
			ambiguous = true
		}
		if len(queue) > len(largest) {
			largest = queue
			ambiguous = false
		}
	}
	if len(largest) == 0 || ambiguous {
		return fmt.Errorf("empty or ambiguous group cutout")
	}
	clear(seen)
	for _, at := range largest {
		seen[at] = true
	}
	for at, keep := range seen {
		if !keep {
			removed += uint64(p.Pix[4*at+3])
			clear(p.Pix[4*at : 4*at+4])
		}
	}
	if removed*500 > total {
		return fmt.Errorf("alpha removal exceeds 0.2 percent")
	}
	return nil
}

func (m *IntroMuseum) loadMuseumGroup(root, originalRoot string) error {
	raw, err := museumGroupFile(root, "museum.json", 65536)
	if err != nil {
		return err
	}
	var list museumGroupManifest
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	if err = dec.Decode(&list); err != nil {
		return err
	}
	if dec.Decode(new(any)) != io.EOF {
		return fmt.Errorf("museum manifest has trailing data")
	}
	if list.Schema != 1 || list.Palette != "a-purple" || len(list.Assets) != 14 || len(list.Records) != 15 {
		return fmt.Errorf("group schema, palette or count differs")
	}
	packed := map[string]string{
		"PREDELLA.EXE": "b9c7abdac7849711b68b6b6fd5861052e6f3d025b25af5f96d4605bf673cadaa",
		"TIT3.AY":      "31b943254292a75df2ad9d0c54eaeff7eacae83fb0f411bae4cfa4e66dd1bdec",
		"TIT4.AY":      "d12b77ead60f2a85033c89a99b8e444473f143413647735196f75685e24de14d",
		"TIT5.AY":      "b4114a8c64d949cba71321adc9979270ce001250845eb685badea9ad77c06d9e",
	}
	decoded := map[string]string{
		"TIT3.AY": "c91efb90db3c5fa8ef9a109c0bf362fee14f9b486693e92088a5c504d3b0f590",
		"TIT4.AY": "59ce4bbb648666351545e0e9c0d6da7015689075b2f29375cf11e15839551d92",
		"TIT5.AY": "1ad430667a6d06969e1e71e1fa0b1f57453e65865488bbaa3416f86027e8924b",
	}
	if len(list.Packed) != 4 || len(list.Decoded) != 3 {
		return fmt.Errorf("group source counts differ")
	}
	for name, sha := range packed {
		data, err := museumGroupFile(originalRoot, name, 128*1024)
		if err != nil || museumSHA(data) != sha || list.Packed[name] != sha {
			return fmt.Errorf("packed source differs: %s", name)
		}
	}
	for name, sha := range decoded {
		if list.Decoded[name] != sha {
			return fmt.Errorf("decoded source differs")
		}
	}
	seenRecords := map[string]bool{}
	for _, r := range list.Records {
		actual := m.records[r.SHA]
		if actual == nil || seenRecords[r.SHA] || actual.offset != r.Offset || actual.w != r.Width || actual.h != r.Height || actual.blocks != r.Blocks || 4+actual.w*actual.h*actual.blocks != r.Bytes {
			return fmt.Errorf("group record differs")
		}
		role, file := actual.role, "TIT4.AY"
		if role == "left" || role == "right" {
			file = "TIT3.AY"
		}
		if role == "portrait" {
			file = "TIT5.AY"
		}
		if actual.w == 24 {
			role = "beam"
		}
		if r.File != file || r.Role != role {
			return fmt.Errorf("record address space differs")
		}
		seenRecords[r.SHA] = true
	}
	staged := map[string]*image.NRGBA{}
	actors := map[string]*image.NRGBA{}
	scenes := map[string]*image.NRGBA{}
	files := map[string]bool{}
	leftSHA, rightSHA := "b6eff2d96d1a6b95ed633fe0bfc409537cae06463ad6228c9261e6215f309a55", "beb39b3c6c2655e9c2e2b68e33360c00548161a993cc39657f9e4ddc4dcdc65f"

	totalPixels := 0
	for _, v := range list.Assets {
		w, h, policy := 240, 276, "floor8-largest8"
		switch v.ID {
		case "left", "right":
			w, h, policy = 1920, 600, "opaque"
		case "portrait":
			w, h, policy = 1272, 600, "opaque"
		case "beam":
			w, h = 576, 300
		default:
			valid := false
			for i := 1; i <= 10; i++ {
				if v.ID == fmt.Sprintf("actor-%02d", i) {
					valid = true
				}
			}
			if !valid {
				return fmt.Errorf("unknown group ID")
			}
		}
		if staged[v.ID] != nil || files[v.File] || v.Width != w || v.Height != h || v.Policy != policy {
			return fmt.Errorf("group asset shape/identity differs")
		}
		if v.ID == "portrait" && (v.File != "intro-heroine.png" || v.SHA != heroinePNGSHA || v.CacheSHA != "3ca4c743c3d9f7487d9963ed4d50fa4b9edab1a3b8578894025c5b360df5078f") {
			return fmt.Errorf("museum portrait differs from spec 033")
		}
		if (v.ID == "left" && v.SHA != leftSHA) || (v.ID == "right" && v.SHA != rightSHA) {
			return fmt.Errorf("mixed museum palettes")
		}
		want := []string{}
		for _, r := range list.Records {
			if r.Role == v.ID || (r.Role == "actor" && v.ID == fmt.Sprintf("actor-%02d", r.Offset/2764+1)) {
				want = append(want, r.SHA)
			}
		}
		if len(want) == 0 || len(want) != len(v.Sources) {
			return fmt.Errorf("asset mapping count differs")
		}
		for i, sha := range want {
			if v.Sources[i] != sha {
				return fmt.Errorf("asset mapping differs")
			}
		}
		data, err := museumGroupFile(root, v.File, 8*1024*1024)
		if err != nil {
			return err
		}
		if museumSHA(data) != v.SHA {
			return fmt.Errorf("group PNG SHA differs")
		}
		cfg, err := png.DecodeConfig(bytes.NewReader(data))
		if err != nil || cfg.Width != w || cfg.Height != h {
			return fmt.Errorf("PNG geometry differs")
		}
		im, err := png.Decode(bytes.NewReader(data))
		if err != nil {
			return err
		}
		p := image.NewNRGBA(image.Rect(0, 0, w, h))
		draw.Draw(p, p.Bounds(), im, image.Point{}, draw.Src)
		if err = museumCleanCache(p, policy); err != nil {
			return err
		}
		if museumSHA(p.Pix) != v.CacheSHA {
			return fmt.Errorf("group cache SHA differs: %s", v.ID)
		}
		staged[v.ID] = p
		files[v.File] = true
		totalPixels += w * h
		for _, sha := range v.Sources {
			if v.ID != "beam" && policy == "floor8-largest8" {
				actors[sha] = p
			}
		}
	}
	if len(staged) != 14 || len(actors) != 10 || totalPixels != 3902400 {
		return fmt.Errorf("incomplete group")
	}
	art := image.NewRGBA(staged["left"].Bounds())
	draw.Draw(art, art.Bounds(), staged["left"], image.Point{}, draw.Src)
	scenes["right:"+m.variant] = staged["right"]
	scenes["portrait:all"] = staged["portrait"]
	scenes["beam:all"] = staged["beam"]
	m.art, m.actorSprites, m.sceneArts = art, actors, scenes
	m.actorRequested = true
	m.ActorValidated = 10
	m.SceneValidated = 3
	return nil
}
