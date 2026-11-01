package ownedworld

import (
	"flag"
	"image"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

type checkpointExtra struct {
	Previous   armyScreenExtra
	Checkpoint *nativeCheckpointPort
}

func (x *checkpointExtra) IsActive() bool               { return x.Previous.IsActive() }
func (x *checkpointExtra) NoteKey(k byte, d bool)       { x.Previous.NoteKey(k, d) }
func (x *checkpointExtra) Click(a, b int) (byte, error) { return x.Previous.Click(a, b) }
func (x *checkpointExtra) Paint(f *armyUIFonts, id string) (*image.RGBA, []armyUIText) {
	return x.Previous.Paint(f, id)
}
func (x *checkpointExtra) State() map[string]any {
	v := x.Previous.State()
	v["native_checkpoint_saves"] = x.Checkpoint.Saves
	v["native_checkpoint_events"] = x.Checkpoint.Events
	v["native_checkpoint_active"] = x.Checkpoint.Active
	v["native_location"] = checkpointLocation(x.Checkpoint.Engine.Oracle)
	return v
}
func initializeLayer24() {
	previous := armyReviewExtraFactory
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) {
		old, err := previous(e, p)
		if err != nil {
			return nil, err
		}
		v, err := installNativeCheckpoint(e, p, flag.Lookup("scratch").Value.String())
		if err != nil {
			return nil, err
		}
		return &checkpointExtra{old, v}, nil
	}
	armyReviewTitle = "神州八劍・軍隊試作・完整進度存檔"
}
