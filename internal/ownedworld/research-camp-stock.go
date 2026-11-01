// Fixed-PAM five-camp table codec, separate from guest unit-array ownership.
package ownedworld

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"strings"
)

type campRecord struct {
	Group, Row int
	Words      [5]uint16
}

func campKey(group, row int) string { return fmt.Sprintf("native-camp:%02d:%02d", group, row) }
func parseCampKey(key string) (int, int, error) {
	var g, r int
	n, e := fmt.Sscanf(key, "native-camp:%02d:%02d", &g, &r)
	if e != nil || n != 2 || g < 0 || g >= 5 || r < 0 || r >= 24 || key != campKey(g, r) {
		return 0, 0, errors.New("camp source key")
	}
	return g, r, nil
}
func campOffset(group, row, field int) int { return 2 * (18 + row*25 + field*5 + group) }
func campDS(group, row int) uint16         { return uint16(0x3efe + group*0xf0 + row*10) }
func decodeCampRecord(native []byte, group, row int) (campRecord, error) {
	v := campRecord{Group: group, Row: row}
	if len(native) != 2987 || group < 0 || group >= 5 || row < 0 || row >= 24 {
		return v, errors.New("camp table shape")
	}
	for f := 0; f < 5; f++ {
		at := campOffset(group, row, f)
		v.Words[f] = binary.LittleEndian.Uint16(native[at:]) - uint16(at+3)
	}
	if v.Words[3] > 25 || v.Words[4] > 32767 || v.Words[3] == 0 && v.Words[4] != 0 {
		return v, errors.New("camp kind/stock")
	}
	return v, nil
}
func (v campRecord) unit() string { return fmt.Sprintf("native:%02d", v.Words[3]) }
func campOffers(a OwnedArmy) (map[string]ArmyOffer, error) {
	out := map[string]ArmyOffer{}
	for k, v := range a.Offers {
		if strings.HasPrefix(k, "native-camp:") {
			if _, _, e := parseCampKey(k); e != nil {
				return nil, e
			}
			out[k] = v
		}
	}
	return out, nil
}
func validateCampBindings(native []byte, a OwnedArmy) error {
	offers, e := campOffers(a)
	if e != nil {
		return e
	}
	for k, v := range offers {
		g, r, _ := parseCampKey(k)
		rec, e := decodeCampRecord(native, g, r)
		if e != nil {
			return e
		}
		if rec.Words[3] == 0 || rec.unit() != v.Unit || uint32(rec.Words[4]) != v.Stock {
			return errors.New("camp native/Go binding")
		}
	}
	return nil
}
func projectCampStocks(native []byte, a OwnedArmy) ([]byte, error) {
	out := bytes.Clone(native)
	offers, e := campOffers(a)
	if e != nil {
		return nil, e
	}
	for k, v := range offers {
		g, r, _ := parseCampKey(k)
		rec, e := decodeCampRecord(native, g, r)
		if e != nil {
			return nil, e
		}
		if rec.Words[3] == 0 || rec.unit() != v.Unit || v.Stock > 32767 {
			return nil, errors.New("camp stock projection binding")
		}
		at := campOffset(g, r, 4)
		binary.LittleEndian.PutUint16(out[at:], uint16(v.Stock)+uint16(at+3))
	}
	return out, validateCampBindings(out, a)
}
