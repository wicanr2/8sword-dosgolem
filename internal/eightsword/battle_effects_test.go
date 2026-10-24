package eightsword

import (
	"bytes"
	"fmt"
	"image"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func TestPonRealSourcesAndAtomicFailure(t *testing.T) {
	dir, root, caches := os.Getenv("EIGHTSWORD_TEST_PON_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_PON_CACHE")
	if dir == "" || root == "" || caches == "" {
		t.Skip("需要本機 PON 素材、原版與獨立取樣")
	}
	good, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer good.Close()
	if good.BattleEffectError != "" || len(good.Tracker.graphics.assets.Effects) != 4 || len(good.Tracker.graphics.assets.BattleActors) != 16 {
		t.Fatal(good.Status())
	}
	a := good.Tracker.graphics.assets
	raw, err := os.ReadFile(filepath.Join(root, "PON.EGG"))
	if err != nil {
		t.Fatal(err)
	}
	for i, want := range ponSources {
		id := uint16(103 + i)
		if hash(raw[i*3304:(i+1)*3304]) != want.Record || hash(raw[i*3304:i*3304+2204]) != want.Native || a.ByNative[want.Native] != id || a.EffectSHA[id] != want.Record || a.Actors[id] != nil {
			t.Fatalf("effect source %d mismatch or registered as actor", i)
		}
		cache, err := os.ReadFile(filepath.Join(caches, fmt.Sprintf("cache-frame-%d.rgba", i)))
		if err != nil || !bytes.Equal(cache, a.Effects[id].Tile.Pix) {
			t.Fatalf("independent effect cache %d: %v", i, err)
		}
	}
	broken := t.TempDir()
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		data, err := os.ReadFile(filepath.Join(dir, entry.Name()))
		if err != nil {
			t.Fatal(err)
		}
		if entry.Name() == "battle-pon-3-r1.png" {
			data[len(data)/2] ^= 1
		}
		if err := os.WriteFile(filepath.Join(broken, entry.Name()), data, 0644); err != nil {
			t.Fatal(err)
		}
	}
	bad, err := Open(Options{Root: root, Assets: broken, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer bad.Close()
	b := bad.Tracker.graphics.assets
	if bad.BattleEffectError == "" || !bad.HD || bad.BattleActorError != "" || bad.GraphicsError != "" || bad.BattleBackgroundError != "" || len(b.Effects) != 0 || len(b.BattleActors) != 16 || !reflect.DeepEqual(good.Assets, bad.Assets) {
		t.Fatal(bad.Status())
	}
	for id, material := range a.Actors {
		if !bytes.Equal(material.Tile.Pix, b.Actors[id].Tile.Pix) {
			t.Fatalf("unrelated actor %d changed", id)
		}
	}
}

func effectMetadataFixture() *Graphics {
	return &Graphics{parent: &Tracker{}, owners: make([]graphicCell, 65536*8), actors: make([]graphicCell, 65536*8), effects: make([]graphicCell, 65536*8), effectBase: make([]uint8, 65536*8), effectFrames: map[uint16]*battleEffectFrame{}}
}

func TestEffectPageCopyReclamationAndAbort(t *testing.T) {
	g := effectMetadataFixture()
	first := &battleEffectFrame{Tile: image.NewRGBA(image.Rect(0, 0, 264, 300)), Source: 103}
	first.Tile.Pix[0] = 91
	g.effectFrames[1] = first
	for bit := uint32(0); bit < 8; bit++ {
		g.setEffect(bit, graphicCell{1, bit}, uint8(bit+1))
	}
	g.copyEffectByte(0x4000, 0)
	if first.Refs != 16 {
		t.Fatal("page copy did not retain immutable frame")
	}
	g.clearEffectByte(0, 255)
	if first.Refs != 8 || g.effectFrames[1] != first {
		t.Fatal("source clear discarded destination page")
	}
	g.effectFrames[2] = &battleEffectFrame{Tile: image.NewRGBA(image.Rect(0, 0, 264, 300)), Source: 104}
	g.setEffect(0, graphicCell{2, 0}, 14)
	if g.effects[0x4000*8].ID != 1 || g.effectBase[0x4000*8] != 1 || g.effectFrames[1].Tile.Pix[0] != 91 {
		t.Fatal("later source page changed destination appearance or base")
	}
	g.clearByte(0x4000, 0x80)
	if g.effects[0x4000*8].ID != 0 || g.effects[0x4000*8+1].ID != 1 || first.Refs != 7 {
		t.Fatal("masked unknown write invalidated wrong cells")
	}
	g.clearEffectByte(0x4000, 255)
	if g.effectFrames[1] != nil {
		t.Fatal("unreferenced frame not reclaimed")
	}
	// A failed in-progress effect must not leave a retained HD troop covering
	// the real, partially written native effect.
	g.owners[0], g.actors[0] = graphicCell{86, 0}, graphicCell{95, 0}
	g.effectDraft = &battleEffectDraft{First: 0, ID: 3}
	g.active = &bitmapCall{Effect: 103}
	g.pending = &battleBitmapTransaction{Entry: 0x4f2}
	g.abortBattleTransaction()
	if g.effectDraft != nil || g.pending != nil || g.active.Effect != 0 || g.owners[0].ID != 0 || g.actors[0].ID != 0 || g.effects[0].ID != 0 || g.Stats.BattleEffectFallbackCalls != 1 {
		t.Fatal("abort left stale graphics ownership")
	}
	g.clear()
	if len(g.effectFrames) != 0 {
		t.Fatal("mode reset retained effect frames")
	}
}

func TestEffectSlotsStayBoundedAndReusable(t *testing.T) {
	g := effectMetadataFixture()
	for id := uint16(1); id <= battleEffectSlots; id++ {
		g.effectFrames[id] = &battleEffectFrame{}
		g.setEffect(uint32(id), graphicCell{id, 0}, 1)
	}
	if g.freeBattleEffectSlot() != 0 {
		t.Fatal("accepted more than 64 referenced caches")
	}
	g.setEffect(33, graphicCell{}, 0)
	if g.freeBattleEffectSlot() != 33 || len(g.effectFrames) != 63 {
		t.Fatal("released cache slot cannot be reused")
	}
}
