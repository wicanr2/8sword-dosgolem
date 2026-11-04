package eightsword

import (
	"encoding/binary"
	"fmt"
	"os"
	"path/filepath"
	"testing"
)

// Development projection of approved HD caches, without executing the guest.
func TestRustWorldMedia(t *testing.T) {
	out, root, assets := os.Getenv("EIGHTSWORD_RUST_WORLD_MEDIA"), os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if out == "" || root == "" || assets == "" {
		t.Skip("explicit world media projection")
	}
	pmap, err := os.ReadFile(filepath.Join(root, "PMAP.AY"))
	if err != nil {
		t.Fatal(err)
	}
	a, err := loadGraphicsAssets(assets, pmap)
	if err != nil {
		t.Fatal(err)
	}
	for _, load := range []func(string, []byte, *GraphicsAssets) error{loadMapCastle, loadMapChest, loadMapLandmark55, loadMapLandmark49, loadMapLandmark54, loadMapLandmark52, loadMapLandmark56, loadMapLandmark48, loadMapLandmark51} {
		if err = load(assets, pmap, a); err != nil {
			t.Fatal(err)
		}
	}
	completion, err := loadCompletionAssets(assets, root)
	if err != nil {
		t.Fatal(err)
	}
	if err = completion.bindGraphics(a); err != nil {
		t.Fatal(err)
	}
	write := func(name string, m *graphicMaterial) {
		t.Helper()
		if m == nil {
			t.Fatal("missing world HD", name)
		}
		b := []byte("8SRGBA01")
		b = binary.LittleEndian.AppendUint32(b, uint32(m.Tile.Bounds().Dx()))
		b = binary.LittleEndian.AppendUint32(b, uint32(m.Tile.Bounds().Dy()))
		b = append(b, m.Tile.Pix...)
		h := uint64(14695981039346656037)
		for _, n := range b {
			h = (h ^ uint64(n)) * 1099511628211
		}
		b = binary.LittleEndian.AppendUint64(b, h)
		if err = os.WriteFile(filepath.Join(out, name), b, 0600); err != nil {
			t.Fatal(err)
		}
	}
	for i := 0; i < 65; i++ {
		write(fmt.Sprintf("map-tile-%02d.rgba", i), a.Materials[uint16(i+1)])
	}
	for i := 0; i < 12; i++ {
		write(fmt.Sprintf("map-hero-%02d.rgba", i), a.Actors[uint16(i+73)])
	}
	write("world-frame.rgba", a.Materials[72])
}
