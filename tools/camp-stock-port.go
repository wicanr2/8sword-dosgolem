//go:build ignore

package main

import (
	"bytes"
	"errors"
	"flag"

	"github.com/wicanr2/dosgolem/oracle"
)

func (p *worldArmyPort) bindCamp(o *oracle.Oracle) error {
	r := o.Regs()
	if r.CS != 0x110 || r.DS != 0x1e88 || r.SS != 0x1e88 || r.SP > 65520 || r.BP < 16 || r.BP > 65520 {
		return errors.New("camp ABI")
	}
	for start, want := range p.Expected {
		if !bytes.Equal(want, o.Bytes(oracle.Far(0x110, start), len(want))) {
			return errors.New("camp source changed")
		}
	}
	word := func(off uint16) uint16 { return o.Word(oracle.Far(r.SS, off)) }
	ret, kind, stock := word(r.SP), word(r.SP+4), word(r.SP+6)
	group := -1
	for i := 0; i < 5; i++ {
		if ret == uint16(0x5a21+i*0x90) {
			group = i
		}
	}
	if group < 0 || word(r.SP+2) != 0x110 || kind < 1 || kind > 25 || stock > 32767 || word(0x26b8) != 0 {
		return errors.New("camp caller/kind/stock/modifier")
	}
	row := int(word(r.BP - 6))
	region := int(word(0x56d6))
	if region > 7 || row < region*3 || row >= region*3+3 {
		return errors.New("camp region/row")
	}
	base := campDS(group, row)
	if word(base+2) != word(0x8e12) || word(base+4) != word(0x8e44) || word(base+6) != kind || word(base+8) != stock {
		return errors.New("camp live identity")
	}
	if p.ShopOpen {
		if p.ShopGroup != group || p.ShopRow != row || p.ShopKind != kind || p.ShopStock != stock || p.ShopSP != r.SP || p.ShopBP != r.BP {
			return errors.New("overlapping camp entry")
		}
		return nil
	}
	v, e := p.snapshot()
	if e != nil {
		return e
	}
	rec, e := decodeCampRecord(v.Bytes.Native, group, row)
	if e != nil {
		return e
	}
	for f, w := range rec.Words {
		if word(base+uint16(f*2)) != w {
			return errors.New("camp checkpoint/live mismatch")
		}
	}
	idx, e := p.Store.Catalog.index()
	if e != nil {
		return e
	}
	profile, ok := idx[rec.unit()]
	if !ok || profile.NativeKind != kind || profile.Gold == 0 || profile.Gold > 32767 || profile.Command == 0 || profile.Command > 32767 {
		return errors.New("camp catalog ABI")
	}
	maps, e := decodeCheckpointMaps(v.Bytes.World)
	if e != nil {
		return e
	}
	if maps == nil {
		f := flag.Lookup("scratch")
		if f == nil {
			return errors.New("camp needs scratch maps")
		}
		maps, e = readNativeCheckpointMaps(f.Value.String())
		if e != nil {
			return e
		}
	}
	next, e := p.Store.BindCamp(v.Token, group, row, maps)
	if e != nil {
		return e
	}
	p.Current = next
	p.ShopID = campKey(group, row)
	p.ShopUnit = rec.unit()
	p.ShopKind = kind
	p.ShopGroup = group
	p.ShopRow = row
	p.ShopStock = stock
	p.ShopSP = r.SP
	p.ShopBP = r.BP
	p.ShopCommitted = false
	p.ShopOpen = true
	return nil
}
func (p *worldArmyPort) finishCamp(o *oracle.Oracle, group int) error {
	if !p.ShopOpen {
		return nil
	}
	r := o.Regs()
	if r.CS != 0x110 || r.DS != 0x1e88 || r.SS != 0x1e88 || group != p.ShopGroup || r.BP != p.ShopBP {
		return errors.New("camp return context")
	}
	rec, e := decodeCampRecord(p.Current.Bytes.Native, p.ShopGroup, p.ShopRow)
	if e != nil {
		return e
	}
	if o.Word(oracle.Far(0x1e88, campDS(group, p.ShopRow)+8)) != rec.Words[4] {
		return errors.New("camp wrapper stock mismatch")
	}
	for i, n := range pairWorldResources(p.Current.World).words() {
		if uint64(o.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
			return errors.New("camp return resources")
		}
	}
	p.ShopOpen = false
	return nil
}
