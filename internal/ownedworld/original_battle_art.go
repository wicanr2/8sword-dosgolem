package ownedworld

import (
	"bytes"
	"errors"
	"image"
	"os"
	"path/filepath"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

type originalBattleArtContext struct {
	Active        bool
	SP, Slot, Raw uint16
	Unit          string
	Clear         bool
	X, Y          int
}
type originalBattleArt struct {
	Guard   *originalBattleGuard
	Context originalBattleArtContext
	Tiles   map[string]*image.RGBA
	Events  []map[string]any
}

func originalBattleArtTile(im *image.RGBA) (*image.RGBA, error) {
	if im == nil || im.Bounds() != image.Rect(0, 0, 512, 512) {
		return nil, errors.New("battle art input bounds")
	}
	box := image.Rectangle{}
	for y := 0; y < 512; y++ {
		for x := 0; x < 512; x++ {
			if im.RGBAAt(x, y).A != 0 {
				box = box.Union(image.Rect(x, y, x+1, y+1))
			}
		}
	}
	if box.Empty() {
		return nil, errors.New("battle art empty silhouette")
	}
	w, h := 252, 288
	if w*box.Dy() > h*box.Dx() {
		w = h * box.Dx() / box.Dy()
	} else {
		h = w * box.Dy() / box.Dx()
	}
	left, top := (264-w)/2, 300-h
	out := image.NewRGBA(image.Rect(0, 0, 264, 300))
	for y := 0; y < h; y++ {
		for x := 0; x < w; x++ {
			sx, sy := box.Min.X+x*box.Dx()/w, box.Min.Y+y*box.Dy()/h
			src, dst := im.PixOffset(sx, sy), out.PixOffset(left+x, top+y)
			copy(out.Pix[dst:dst+4], im.Pix[src:src+4])
		}
	}
	return out, nil
}

func installOriginalBattleArt(g *originalBattleGuard, dir string) (*originalBattleArt, error) {
	if g == nil || g.Engine == nil || g.Rounds == nil || g.Rounds.Actions == nil || !g.Engine.HD || !g.Engine.OwnedBattleArtAvailable() {
		return nil, errors.New("battle art candidate source backend unavailable")
	}
	raw, err := os.ReadFile(filepath.Join(dir, "..", "inputs", "army-catalog.json"))
	if err != nil {
		return nil, err
	}
	pack := loadHDUnitArtwork(g.Engine, dir, contentSHA(raw))
	if len(pack.Failures) != 0 {
		return nil, errors.New("battle art package incomplete")
	}
	v := &originalBattleArt{Guard: g, Tiles: map[string]*image.RGBA{}}
	for _, id := range openKBArtIDs {
		tile, err := originalBattleArtTile(pack.Images[id])
		if err != nil {
			return nil, err
		}
		v.Tiles[id] = tile
	}
	if err = g.Engine.SetOwnedBattleArt(v.Tiles, v.resolve); err != nil {
		return nil, err
	}
	swordOnCall(g.Engine.Oracle, oracle.Far(0xf67, 0x2bf8), func(o *oracle.Oracle) {
		if err := v.enter(o); err != nil {
			panic(&worldArmyPortFault{err.Error()})
		}
	})
	swordOnCall(g.Engine.Oracle, oracle.Far(0xf67, 0x2c90), func(o *oracle.Oracle) {
		if !v.Context.Active {
			return
		}
		if o.Regs().SP != v.Context.SP || o.Regs().CS != 0xf67 {
			panic(&worldArmyPortFault{"battle art return frame"})
		}
		v.Context = originalBattleArtContext{}
	})
	return v, nil
}

func (v *originalBattleArt) enter(o *oracle.Oracle) error {
	g := v.Guard
	r := o.Regs()
	if r.CS != 0xf67 || r.DS != 0x1e88 || r.SS != 0x1e88 || r.SP > 65526 || !bytes.Equal(g.Code[0x21168-0x10000:0x21201-0x10000], o.Bytes(oracle.Far(0xf67, 0x2bf8), 0x99)) {
		return errors.New("battle art wrapper source/segments")
	}
	if v.Context.Active && v.Context.SP == r.SP {
		return nil
	}
	if v.Context.Active {
		return errors.New("battle art nested wrapper")
	}
	slot := o.Arg(0)
	if slot >= 6 {
		return errors.New("battle art slot")
	}
	a := g.Rounds.Actions
	rows, slots := a.rows(), a.slots()
	if g.Rounds.Done {
		rows, slots = g.Rounds.Rows, g.Rounds.Slots
	}
	raw := slots[0][slot]
	if raw >= 6 {
		return errors.New("battle art raw")
	}
	row := rows[0][raw]
	if row.Unit == "" {
		return nil
	}
	p, ok := g.Port.Store.Combat.Profiles[row.Unit]
	if !ok {
		return errors.New("battle art unit identity")
	}
	if p.NativeKind != 0 {
		return nil
	}
	if v.Tiles[row.Unit] == nil || g.Projection.Phase != "projected" && g.Projection.Phase != "captured" {
		return errors.New("battle art unit/lifecycle")
	}
	coords := o.Bytes(oracle.Far(0x1e88, 0x703c+slot*2), 2)
	v.Context = originalBattleArtContext{Active: true, SP: r.SP, Slot: slot, Raw: raw, Unit: row.Unit, Clear: row.Count == 0, X: int(coords[0]), Y: int(coords[1])}
	return nil
}

func (v *originalBattleArt) resolve(req game.OwnedBattleArtRequest) (game.OwnedBattleArtSelection, error) {
	selection := game.OwnedBattleArtSelection{}
	if v.Guard != nil {
		r := v.Guard.Rounds
		if r.Active || r.Done {
			rows := r.Actions.rows()
			if r.Done {
				rows = r.Rows
			}
			for _, row := range rows[0] {
				if row.Unit != "" && row.Count == 0 && v.Tiles[row.Unit] != nil {
					selection.Retire = append(selection.Retire, row.Unit)
				}
			}
		}
	}
	c := v.Context
	if !c.Active {
		return selection, nil
	}
	paired := req.Entry == 0x423 && req.CallerIP == 0x2c8a || req.Entry == 0x626 && req.CallerIP == 0x2c50
	geometry := req.WidthBytes == 11 && req.Height == 50 || req.Entry == 0x423 && req.WidthBytes == 8 && req.Height == 25
	if !paired || req.CallerCS != 0xf67 || req.XByte != c.X || req.Y != c.Y || !geometry || req.Destination != 0xa000 || req.Mode != 1 || c.Clear && req.Entry != 0x423 {
		return game.OwnedBattleArtSelection{}, errors.New("battle art command does not match bound wrapper")
	}
	v.Events = append(v.Events, map[string]any{"unit": c.Unit, "clear": c.Clear, "slot": c.Slot, "raw": c.Raw, "x": c.X, "y": c.Y, "source_width_bytes": req.WidthBytes, "source_height": req.Height})
	if c.Clear {
		selection.Clear = true
		return selection, nil
	}
	selection.Unit = c.Unit
	return selection, nil
}
