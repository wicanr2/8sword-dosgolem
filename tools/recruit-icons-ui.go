//go:build ignore

// Read-only source admission plus pure Go composition of an existing Go frame.
package main

import (
	"bytes"
	"fmt"
	"image"
	"image/color"
	"image/draw"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

type recruitIcons struct {
	Engine                  *game.Engine
	Code                    []byte
	Active, Ready, Captured bool
	Kind, Stock, SP, BP     uint16
	Group, Row              int
	Icons                   map[uint16]*image.RGBA
	Events                  []map[string]any
	Frames                  uint64
}

var recruitIconsCurrent *recruitIcons
var recruitIconCard = image.Rect(1060, 96, 1324, 618)

func installRecruitIcons(e *game.Engine) error {
	if !e.HD {
		return nil
	}
	code, err := worldArmyCode(e.PAM)
	if err != nil {
		return err
	}
	x := &recruitIcons{Engine: e, Code: code, Icons: map[uint16]*image.RGBA{}}
	recruitIconsCurrent = x
	for k := uint16(1); k <= 25; k++ {
		if im := e.RecruitmentUnitIcon(k); im != nil {
			x.Icons[k] = im
		}
	}
	o := e.Oracle
	source := func() bool {
		r := o.Regs()
		return r.CS == 0x110 && r.DS == 0x1e88 && r.SS == 0x1e88 && bytes.Equal(code[0x54ea:0x5c94], o.Bytes(oracle.Far(0x110, 0x54ea), 0x5c94-0x54ea))
	}
	o.OnCall(oracle.Far(0x110, 0x54ea), func(o *oracle.Oracle) {
		x.Active = false
		x.Ready = false
		x.Captured = false
		if !source() {
			return
		}
		r := o.Regs()
		if r.SP > 65520 || r.BP < 16 || r.BP > 65520 {
			return
		}
		word := func(off uint16) uint16 { return o.Word(oracle.Far(r.SS, off)) }
		ret, seg, kind, stock := word(r.SP), word(r.SP+2), word(r.SP+4), word(r.SP+6)
		group := -1
		for i := 0; i < 5; i++ {
			if ret == uint16(0x5a21+i*0x90) {
				group = i
			}
		}
		if group < 0 || seg != 0x110 || kind < 1 || kind > 25 || stock > 32767 {
			return
		}
		row := int(word(r.BP - 6))
		region := o.Word(oracle.Far(0x1e88, 0x56d6))
		if region > 7 || row < int(region)*3 || row >= int(region)*3+3 {
			return
		}
		base := uint16(0x3f00 + group*0xf0 + row*10)
		if o.Word(oracle.Far(0x1e88, base+4)) != kind || o.Word(oracle.Far(0x1e88, base+6)) != stock {
			return
		}
		x.Active = true
		x.Captured = true
		x.Kind = kind
		x.Stock = stock
		x.SP = r.SP
		x.BP = r.BP
		x.Group = group
		x.Row = row
		x.Events = append(x.Events, map[string]any{"event": "entry", "kind": kind, "stock": stock, "group": group, "row": row, "source_ds": fmt.Sprintf("%04x", base), "return_ip": ret, "steps": o.Steps()})
	})
	o.OnCall(oracle.Far(0x110, 0x4ea6), func(*oracle.Oracle) {
		if x.Active && source() {
			x.Ready = true
		}
	})
	for _, ip := range []uint16{0x5565, 0x5772} {
		o.OnCall(oracle.Far(0x110, ip), func(o *oracle.Oracle) {
			if x.Active && source() && o.Regs().SP == x.SP {
				x.Active = false
				x.Ready = false
				x.Events = append(x.Events, map[string]any{"event": "leave", "count": o.Regs().AX, "steps": o.Steps()})
			}
		})
	}
	for i := 0; i < 5; i++ {
		i := i
		o.OnCall(oracle.Far(0x110, uint16(0x5a3b+i*0x90)), func(o *oracle.Oracle) {
			if !x.Captured || !source() || i != x.Group || o.Regs().BP != x.BP {
				return
			}
			base := uint16(0x3f00 + i*0xf0 + x.Row*10)
			x.Events = append(x.Events, map[string]any{"event": "native-stock-after", "group": i, "row": x.Row, "stock": o.Word(oracle.Far(0x1e88, base+6)), "count": o.Regs().AX, "steps": o.Steps()})
			x.Captured = false
		})
	}
	return nil
}
func (x *recruitIcons) state() map[string]any {
	return map[string]any{"active": x.Active, "ready": x.Ready, "kind": x.Kind, "stock": x.Stock, "frames": x.Frames, "cached_kinds": len(x.Icons), "events": x.Events, "native_gold": x.Engine.Oracle.Word(oracle.Far(0x1e88, 0x4f8))}
}
func composeRecruitIcons(e *game.Engine, base *image.RGBA) *image.RGBA {
	x := recruitIconsCurrent
	if x == nil || x.Engine != e || !e.HD || !x.Active || !x.Ready || base == nil || base.Bounds() != image.Rect(0, 0, 1920, 1200) {
		return base
	}
	icon := x.Icons[x.Kind]
	if icon == nil {
		return base
	}
	out := image.NewRGBA(base.Bounds())
	draw.Draw(out, out.Bounds(), base, base.Bounds().Min, draw.Src)
	draw.Draw(out, recruitIconCard, image.NewUniform(color.RGBA{176, 150, 85, 255}), image.Point{}, draw.Src)
	inside := recruitIconCard.Inset(3)
	draw.Draw(out, inside, image.NewUniform(color.RGBA{7, 36, 26, 255}), image.Point{}, draw.Src)
	// Fit the complete alpha silhouette, preserving aspect ratio and a fixed
	// inset. No portrait pixels enter the text or numeric input area below.
	bounds := image.Rectangle{}
	for y := 0; y < icon.Bounds().Dy(); y++ {
		for xx := 0; xx < icon.Bounds().Dx(); xx++ {
			if icon.RGBAAt(xx, y).A != 0 {
				p := image.Rect(xx, y, xx+1, y+1)
				if bounds.Empty() {
					bounds = p
				} else {
					bounds = bounds.Union(p)
				}
			}
		}
	}
	if bounds.Empty() {
		return base
	}
	area := inside.Inset(18)
	w, h := area.Dx(), area.Dy()
	if w*bounds.Dy() > h*bounds.Dx() {
		w = h * bounds.Dx() / bounds.Dy()
	} else {
		h = w * bounds.Dy() / bounds.Dx()
	}
	dst := image.Rect(area.Min.X+(area.Dx()-w)/2, area.Min.Y+(area.Dy()-h)/2, area.Min.X+(area.Dx()-w)/2+w, area.Min.Y+(area.Dy()-h)/2+h)
	for y := dst.Min.Y; y < dst.Max.Y; y++ {
		sy := bounds.Min.Y + (y-dst.Min.Y)*bounds.Dy()/h
		for xx := dst.Min.X; xx < dst.Max.X; xx++ {
			sx := bounds.Min.X + (xx-dst.Min.X)*bounds.Dx()/w
			c := icon.RGBAAt(sx, sy)
			if c.A != 0 {
				bg := out.RGBAAt(xx, y)
				a := uint32(c.A)
				out.SetRGBA(xx, y, color.RGBA{uint8(uint32(c.R) + (uint32(bg.R)*(255-a)+127)/255), uint8(uint32(c.G) + (uint32(bg.G)*(255-a)+127)/255), uint8(uint32(c.B) + (uint32(bg.B)*(255-a)+127)/255), 255})
			}
		}
	}
	x.Frames++
	return out
}
