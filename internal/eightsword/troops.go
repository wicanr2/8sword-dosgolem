package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"io"
	"math/bits"
	"os"
	"path/filepath"
	"strings"
)

// Spec 048, fixed source files and reviewed registration bytes. No guest addresses.
var troopGroups = [...]struct{ Source, SourceSHA, ManifestSHA string }{
	{"MAN02.EGG", "b841ad624b4a4d845697947eb88cfde01fb65f163bdb33d20424da7a05648dad", "b15702efee32586786d05bdc7e0716f63a8eaecd981141d039aecbcd9c0626cc"},
	{"MAN03.EGG", "8cf371cfa83169148d22c844d03a0e59815a975e0d04067e89c153502799bb85", "9d184cef9119fecd3a863ab65477d943f683ebca0ecae43b5699713683a58504"},
	{"MAN04.EGG", "9d25c1975be500c7cab5ddff2d53cb42427e865641d84e33bbf6546c42206507", "291393d0e0f86105a97ffbad48d4fbd85435c8583b5f189a9873e179a35f4040"},
	{"MAN05.EGG", "3a07ad1144f283fb75494872ccab3796e75afaa04c1ff1a0ae101541f8d99c71", "5a8c8d2004e05fa9876ce79be1d1eb64c825b435488bbcdc29cea4b17a992e72"},
	{"MAN07.EGG", "559db8b16febe5a48509a91a3823342c68d0f70ac7dca5c62dc909bb340236c3", "2477b5c7611450ef74db1a1c1f7a8fdbfb96546344bd36ae8c49384f06f82582"},
	{"MAN08.EGG", "e1b199444ee808a1f54b716e47740c9b995733e4383b51bb9f0e638387a83fa0", "910e5d46655bb7512d97f892754042fc8c3e0eb60086ca5cbce9c1aa7320f0b4"},
	{"MAN09.EGG", "cbdb54928507ca620725c006044025c51d6a22d59151bf0b27b3c57bd9e87211", "de77e9d201357bb7bb3687778aeae30dfe6d7309fc8d9fcd23d85efa08f3173c"},
	{"MAN10.EGG", "3891eda7763a2d0b82816ab03d021ab7f602047dbebb396b4a22b3abf9ccf250", "885e04d916bf081a506addacffdb16280dd1c89ac0c53dc195cdeb71b937c3d2"},
	{"MAN12.EGG", "bca2b7d5f05ae7ac23972e6ea8f5308ac22a243c78acd5970690d93c8a827632", "c19d823b44e8fcc76a6c3011b21f5b7cfcd24ca1fbfa49aab67ef993d8632c8e"},
	{"MAN13.EGG", "834530fe217c0cb63b57598096ae37e8acbdbe8cb565ffbee5d7622901624bfa", "3cf6b3221188f0abc9709e07b92fa40eeccbac68ff8a520474c99c4b8a881781"},
	{"MAN14.EGG", "fcd414c4a50816fe435b9cf15a39026cbb57b25fab3954f2fddaca0e81882c82", "424e7aaefead34a7cdd80e447b29f081518e6d963eae01151be741ba5eb6fd46"},
	{"MAN15.EGG", "16efb34ad279d3e13aa70b0242c73a4c756d11c55d7a45f6f96d38483c51ede8", "4f49b51e19e9b1a2d09a7d1498ab229bc545c3c5bd6f881edf1339281fbbae94"},
	{"MAN17.EGG", "01d5fcc69a2968ad4cdaa3c95fcae59888f4c2697d6c328364a5083a8bbe13b0", "162f460641e23dab694b1236f7f1cbbb741103f1a49f4fb1dc84e31ad075deff"},
	{"MAN18.EGG", "3621110448141e861f93fc4f6f0a885dd36fabdff393bbae953b5ecedb454215", "7aa5313db66e1a8c544aa499ac42601f7be7cc619357666930b35c7027b3bf94"},
	{"MAN19.EGG", "de0ec47e4f146a249b8e5196c184099dd008b45243150a47c022db76e1549e4c", "be651678fcc63a5b6aa04440f37f415e024721450ca8424ed75d1e983ba37664"},
	{"MAN20.EGG", "8d797ae688960fbc63bdc74372a4b7c775e99be38989dd47ba0e5d3ca0ae508f", "9fe471d9bbb861255320e3b8c1a518931e92fc92517c718897071732f6b3588c"},
	{"MAN22.EGG", "2b29ec53671ced2f114a040ebd27521393ab65e106ed85d17624b0d1272775e0", "99c602f8f2fc4c4424c8b7d1eb396c54bbd52e6fb61d9c65b47bc61e4024134f"},
	{"MAN23.EGG", "381e7bdbda9cf0a68cc1a7587ed98828a5aed594d26dc9771d709258a60bf1cf", "831e1c0f17da2c786940bc0faff8e1d0e45e71d423afd9bd0c2d6ce0ea9c7c57"},
	{"MAN24.EGG", "e9f19e9bda935d96721452bddbd17009d88f61bdc4903ea3abf3735017c31b87", "4a89f0968f5a3f59657374ef3ca5e9a1d625025b45f21d06aebeb45306c4deec"},
	{"MAN25.EGG", "96589d7667217f365259aa23a7056bec63ec3460d978a33bf4837eb9419c1ab7", "6fb03a8bada7cb2bd19dacca291b8a2ad780424d85daef374631e917caa9ed5f"},
}

type troopFrame struct {
	Record  int        `json:"record"`
	Image   graphicPNG `json:"image"`
	Target  []int      `json:"target_rect"`
	Native  [2]string  `json:"native_sha256"`
	Records [2]string  `json:"record_sha256"`
	Caches  [2]string  `json:"cache_sha256"`
}

type troopManifest struct {
	Schema    int          `json:"schema"`
	Source    string       `json:"source_file"`
	SourceSHA string       `json:"source_sha256"`
	PAMSHA    string       `json:"pam_sha256"`
	Style     string       `json:"style"`
	StyleSHA  string       `json:"style_reference_sha256"`
	Geometry  string       `json:"geometry"`
	Frames    []troopFrame `json:"frames"`
}

func loadTroops(dir, root string, assets *GraphicsAssets) error {
	var failures []string
	for index := range troopGroups {
		if err := loadTroopGroup(dir, root, assets, index); err != nil {
			failures = append(failures, troopGroups[index].Source+": "+err.Error())
		}
	}
	if len(failures) > 0 {
		return fmt.Errorf("%s", strings.Join(failures, "；"))
	}
	return nil
}

func loadTroopGroup(dir, root string, assets *GraphicsAssets, index int) error {
	group := troopGroups[index]
	stem := "troop-" + strings.ToLower(strings.TrimSuffix(group.Source, ".EGG"))
	raw, err := encounterRead(filepath.Join(dir, stem+".json"), 32*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	if hash(raw) != group.ManifestSHA {
		return fmt.Errorf("部隊清單雜湊不符")
	}
	var m troopManifest
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err := d.Decode(&m); err != nil {
		return err
	}
	if d.Decode(new(any)) != io.EOF {
		return fmt.Errorf("部隊清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != group.Source || m.SourceSHA != group.SourceSHA || m.PAMSHA != PAMSHA || m.Style != "B-bright-painted-r1" || m.StyleSHA != ApprovedStyleSHA || m.Geometry != "native-mask-components-r1" || len(m.Frames) != 4 {
		return fmt.Errorf("部隊來源／樣式／圖格不符")
	}
	if assets == nil || assets.Actors == nil || assets.ByNative == nil || assets.ActorSHA == nil || assets.Materials[battleBackgroundID] == nil || assets.ByNative[battleBackgroundNativeSHA] != battleBackgroundID {
		return fmt.Errorf("部隊缺少已驗圖像及背景")
	}
	source, err := encounterRead(filepath.Join(root, group.Source), 13216)
	if err != nil {
		return err
	}
	if len(source) != 13216 || hash(source) != group.SourceSHA {
		return fmt.Errorf("部隊原始檔案不符")
	}
	var tiles [4][2]*image.RGBA
	for ri, frame := range m.Frames {
		id := uint16(160 + index*16 + ri*4)
		entry := frame.Image
		if frame.Record != ri || entry.Index != int(id)-1 || entry.File != fmt.Sprintf("%s-%d-r1.png", stem, ri) || entry.Sampling != "bitmap" || entry.Width < 256 || entry.Height < 256 || entry.Width > 2048 || entry.Height > 2048 {
			return fmt.Errorf("部隊第%d筆圖像配置不符", ri)
		}
		record := source[ri*3304 : (ri+1)*3304]
		if !bytes.Equal(record[:4], []byte{11, 0, 50, 0}) {
			return fmt.Errorf("部隊來源尺寸不符")
		}
		mirrored := append([]byte(nil), record...)
		for row := 4; row < 3304; row += 11 {
			for x := 0; x < 11; x++ {
				mirrored[row+x] = bits.Reverse8(record[row+10-x])
			}
		}
		for di, original := range [][]byte{record, mirrored} {
			global, battle := id+uint16(di*2), id+uint16(di*2)+1
			if frame.Native[di] != hash(original[:2204]) || frame.Records[di] != hash(original) {
				return fmt.Errorf("部隊六平面指紋不符")
			}
			if assets.ByNative[frame.Native[di]] != 0 {
				return fmt.Errorf("部隊原生來源識別重複")
			}
			for _, target := range []uint16{global, battle} {
				if assets.Actors[target] != nil || assets.Materials[target] != nil || assets.Effects[target] != nil || assets.ActorSHA[target] != "" || assets.EffectSHA[target] != "" || assets.BattleActors[target] || assets.BattleAliases[target] != 0 {
					return fmt.Errorf("部隊目的識別重複")
				}
				for _, mapped := range assets.ByNative {
					if mapped == target {
						return fmt.Errorf("部隊識別已有來源")
					}
				}
			}
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
		tiles[ri][0], err = sampleBattleActor(decoded, src, dst)
		if err != nil {
			return err
		}
		tiles[ri][1] = image.NewRGBA(image.Rect(0, 0, 264, 300))
		for y := 0; y < 300; y++ {
			for x := 0; x < 264; x++ {
				copy(tiles[ri][1].Pix[(y*264+x)*4:(y*264+x+1)*4], tiles[ri][0].Pix[(y*264+263-x)*4:(y*264+264-x)*4])
			}
		}
		for di := 0; di < 2; di++ {
			if hash(tiles[ri][di].Pix) != frame.Caches[di] {
				return fmt.Errorf("部隊快取與獨立取樣不符")
			}
		}
	}
	// Commit only after every source, both directions and all four images pass.
	if assets.BattleAliases == nil {
		assets.BattleAliases = map[uint16]uint16{}
	}
	if assets.BattleActors == nil {
		assets.BattleActors = map[uint16]bool{}
	}
	for ri, frame := range m.Frames {
		for di, tile := range tiles[ri] {
			global := uint16(160 + index*16 + ri*4 + di*2)
			battle := global + 1
			material := &graphicMaterial{88, 50, tile}
			assets.ByNative[frame.Native[di]] = global
			assets.Actors[global], assets.Actors[battle] = material, material
			assets.ActorSHA[global], assets.ActorSHA[battle] = frame.Records[di], frame.Records[di]
			assets.BattleActors[battle] = true
			assets.BattleAliases[global] = battle
		}
	}
	return nil
}
