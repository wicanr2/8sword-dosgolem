//go:build ignore

package eightsword

import (
	"encoding/json"
	"fmt"
	"image"
	"image/color"
	"image/png"
	"os"
	"path/filepath"
	"testing"
)

func TestRecruitmentUnitIcons(t *testing.T) {
	root, assets, out := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS"), os.Getenv("EIGHTSWORD_RECRUIT_ICON_OUT")
	if root == "" || assets == "" || out == "" {
		t.Fatal("real source/assets and new output required")
	}
	if e := os.Mkdir(out, 0700); e != nil {
		t.Fatal(e)
	}
	e, err := Open(Options{Root: root, Assets: assets, Saves: filepath.Join(out, "shadow"), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	rows := []map[string]any{}
	for k := uint16(1); k <= 25; k++ {
		im := e.RecruitmentUnitIcon(k)
		if im == nil || im.Bounds() != image.Rect(0, 0, 264, 300) {
			t.Fatalf("missing validated kind%d", k)
		}
		h := hash(im.Pix)
		visible := 0
		for i := 3; i < len(im.Pix); i += 4 {
			if im.Pix[i] != 0 {
				visible++
			}
		}
		if visible == 0 {
			t.Fatalf("empty kind%d", k)
		}
		im.SetRGBA(0, 0, color.RGBA{255, 0, 255, 255})
		again := e.RecruitmentUnitIcon(k)
		if hash(again.Pix) != h {
			t.Fatalf("caller mutated shared kind%d cache", k)
		}
		n := fmt.Sprintf("kind%02d.png", k)
		if err = os.WriteFile(filepath.Join(out, fmt.Sprintf("kind%02d.rgba", k)), again.Pix, 0600); err != nil {
			t.Fatal(err)
		}
		f, err := os.OpenFile(filepath.Join(out, n), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
		if err != nil {
			t.Fatal(err)
		}
		err = png.Encode(f, again)
		ce := f.Close()
		if err != nil || ce != nil {
			t.Fatal(err, ce)
		}
		rows = append(rows, map[string]any{"kind": k, "file": n, "rgba_sha256": h, "visible_pixels": visible})
	}
	for _, k := range []uint16{0, 26, 65535} {
		if e.RecruitmentUnitIcon(k) != nil {
			t.Fatal("unknown kind accepted")
		}
	}
	e.HD = false
	if e.RecruitmentUnitIcon(1) != nil {
		t.Fatal("native mode got HD icon")
	}
	e.HD = true
	saved := e.Tracker.graphics.assets.Actors[85]
	delete(e.Tracker.graphics.assets.Actors, 85)
	if e.RecruitmentUnitIcon(1) != nil || e.RecruitmentUnitIcon(2) == nil {
		t.Fatal("missing material fallback affected unrelated group")
	}
	e.Tracker.graphics.assets.Actors[85] = saved
	b, err := json.MarshalIndent(map[string]any{"status": "passed-25-real-recruitment-icons", "rows": rows, "cache_immutable": true, "native_mode_nil": true, "unknown_kind_nil": true, "missing_material_nil": true}, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(out, "receipt.json"), append(b, '\n'), 0600); err != nil {
		t.Fatal(err)
	}
}
