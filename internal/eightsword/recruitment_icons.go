// Read-only HD recruitment portraits; source mapping follows spec 030.
package eightsword

import (
	"fmt"
	"image"
	"image/draw"
)

// RecruitmentUnitIcon copies a fully validated, immutable HD actor cache.
// Native IDs are presentation input only; no expanded ID enters guest tables.
func (e *Engine) RecruitmentUnitIcon(kind uint16) *image.RGBA {
	if !e.HD || kind < 1 || kind > 25 || e.Tracker == nil || e.Tracker.graphics == nil || e.Tracker.graphics.assets == nil {
		return nil
	}
	assets := e.Tracker.graphics.assets
	id := map[uint16]uint16{1: 85, 6: 91, 11: 95, 16: 87, 21: 99}[kind]
	if id == 0 {
		source := fmt.Sprintf("MAN%02d.EGG", kind)
		for i, g := range troopGroups {
			if g.Source == source {
				id = uint16(160 + i*16)
				break
			}
		}
	}
	actor := assets.Actors[id]
	if id == 0 || assets.ActorSHA[id] == "" || actor == nil || actor.Tile == nil || actor.Tile.Bounds() != image.Rect(0, 0, 264, 300) {
		return nil
	}
	out := image.NewRGBA(actor.Tile.Bounds())
	draw.Draw(out, out.Bounds(), actor.Tile, actor.Tile.Bounds().Min, draw.Src)
	return out
}
