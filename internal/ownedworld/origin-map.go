// Typed origin map transition. No guest instruction execution or register model.
package ownedworld

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"errors"
	"fmt"
)

const originTerrainSHA = "7835299e69ca627034132cb6dffa6f40df640f46dfce430642ad9780093a346a"

type originWord struct{ Offset, Value uint16 }
type originMapPlan struct {
	CurrentName string       `json:"current_name"`
	SavedMap    []byte       `json:"saved_map"`
	LoadedMap   []byte       `json:"loaded_map"`
	Terrain     []byte       `json:"terrain"`
	Words       []originWord `json:"words"`
	X, Y        uint16
}

// sub_252E4/sub_251DE: size, root label, little-endian binary-tree nodes,
// followed by least-significant-bit-first decisions. Leaves are byte values.
func decodeOriginTerrain(raw []byte) ([]byte, error) {
	if len(raw) < 8 {
		return nil, errors.New("short terrain tree")
	}
	n, root := int(binary.LittleEndian.Uint16(raw)), int(binary.LittleEndian.Uint16(raw[2:]))
	if n != 5761 || root < 256 {
		return nil, errors.New("terrain size/root")
	}
	start := 4 + (root-255)*4
	if start >= len(raw) {
		return nil, errors.New("terrain tree bound")
	}
	out := make([]byte, 0, n)
	node := root
	for bit := 0; start+bit/8 < len(raw); bit++ {
		at := 4 + (node-256)*4
		if raw[start+bit/8]&(1<<uint(bit%8)) == 0 {
			at += 2
		}
		if at < 4 || at+2 > start {
			return nil, errors.New("terrain node bound")
		}
		child := int(binary.LittleEndian.Uint16(raw[at:]))
		if child < 256 {
			out = append(out, byte(child))
			if len(out) == n {
				return out, nil
			}
			node = root
		} else if child <= root {
			node = child
		} else {
			return nil, errors.New("terrain child bound")
		}
	}
	return nil, errors.New("truncated terrain decisions")
}

func planOriginMap(mem []byte, maps map[string][]byte, packed []byte) (originMapPlan, error) {
	var p originMapPlan
	if len(mem) != 1<<20 || len(maps) != 9 || fmt.Sprintf("%x", sha256.Sum256(packed)) != originTerrainSHA {
		return p, errors.New("origin map inputs")
	}
	for i := 0; i < 9; i++ {
		if len(maps[fmt.Sprintf("map%02d.ay", i)]) != 5761 {
			return p, errors.New("origin nine maps")
		}
	}
	const ds = 0x1e880
	word := func(off int) uint16 { return binary.LittleEndian.Uint16(mem[ds+off:]) }
	name := mem[ds+0x8e52 : ds+0x8e62]
	at := bytes.IndexByte(name, 0)
	if at < 0 {
		return p, errors.New("origin map name terminator")
	}
	p.CurrentName = string(bytes.ToLower(name[:at]))
	region := word(0x56d6)
	if region > 7 || p.CurrentName != fmt.Sprintf("map%02d.ay", region+1) {
		return p, errors.New("origin map identity")
	}
	p.X, p.Y = word(0x3be), word(0x3c0)
	if p.X != 40 || p.Y != 40 {
		return p, errors.New("fixed PAM origin changed")
	}
	p.SavedMap = bytes.ReplaceAll(mem[0x9c000:0x9c000+5761], []byte{100}, []byte{50})
	p.LoadedMap = bytes.Clone(maps["map01.ay"])
	if p.CurrentName == "map01.ay" {
		p.LoadedMap = bytes.Clone(p.SavedMap)
	}
	terrain, e := decodeOriginTerrain(packed)
	if e != nil {
		return p, e
	}
	p.Terrain = terrain
	bases := map[byte]uint16{99: 0x8cbc, 101: 0x8d6c, 102: 0x8dc8, 103: 0x8de0, 104: 0x8df8, 105: 0x8e14, 106: 0x8e2c, 107: 0x8c60, 113: 0x8c30}
	counts := map[byte]uint16{}
	for y := 0; y < 80; y++ {
		for x := 0; x < 72; x++ {
			kind := terrain[y*72+x]
			base, ok := bases[kind]
			if !ok {
				continue
			}
			off := base + counts[kind]*4
			if off < base || off+2 >= 0x8e44 || off == 0x8e12 || off+2 == 0x8e12 {
				return p, errors.New("origin landmark bound")
			}
			p.Words = append(p.Words, originWord{off, uint16(x)}, originWord{off + 2, uint16(y)})
			counts[kind]++
		}
	}
	p.Words = append(p.Words, originWord{0x56d6, 0}, originWord{0x8e12, p.X}, originWord{0x8e44, p.Y}, originWord{0x56ce, 0}, originWord{0x56c4, 3})
	return p, nil
}
