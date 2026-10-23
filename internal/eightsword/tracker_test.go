package eightsword

import (
	"bytes"
	"image"
	"os"
	"path/filepath"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

func ownerFixture() *Tracker {
	t := &Tracker{loadSegment: 0x110, owners: make([]cell, 65536*8), glyphs: map[uint32]*glyph{1: {ID: 1, Width: 16}}}
	for i := 0; i < 8; i++ {
		t.set(10*8+uint32(i), cell{ID: 1, Local: uint16(24 + i), Ink: i%2 == 0})
	}
	return t
}

func TestSameValueNonTextWriteInvalidatesOwnership(t *testing.T) {
	tracker := ownerFixture()
	// The event's byte value does not decide invalidation. Even writing zero
	// back over zero must discard the prior presentation ownership.
	tracker.write(oracle.VideoWrite{Offset: 10, Value: 0})
	for i := 0; i < 8; i++ {
		if got := tracker.owners[80+i]; got.ID != 0 {
			t.Fatalf("stale ownership: %+v", got)
		}
	}
	if tracker.glyphs[1].Refs != 0 {
		t.Fatal("stale live glyph references")
	}
}

func TestPageCopyPreservesGlyphLocalCoordinates(t *testing.T) {
	tracker := ownerFixture()
	before := append([]cell(nil), tracker.owners[80:88]...)
	tracker.copyByte(0x400a, 10)
	for i, want := range before {
		if got := tracker.owners[0x400a*8+i]; got != want {
			t.Fatalf("pixel %d: %+v != %+v", i, got, want)
		}
	}
	if tracker.glyphs[1].Refs != 16 {
		t.Fatal(tracker.glyphs[1].Refs)
	}
	tracker.copyByte(10, 10)
	if tracker.glyphs[1].Refs != 16 {
		t.Fatal("same-location copy changed references")
	}
	tracker.write(oracle.VideoWrite{Offset: 10})
	if tracker.glyphs[1].Refs != 8 {
		t.Fatal("invalidating source also lost copied page")
	}
}

func realAssets(t *testing.T) (*Assets, []byte, string) {
	t.Helper()
	root := os.Getenv("EIGHTSWORD_TEST_ORIG")
	dir := os.Getenv("EIGHTSWORD_TEST_ASSETS")
	if root == "" || dir == "" {
		t.Skip("requires real original PAM.AY and prepared Noto assets")
	}
	pam, err := os.ReadFile(filepath.Join(root, "PAM.AY"))
	if err != nil {
		t.Fatal(err)
	}
	assets, err := LoadAssets(dir, pam)
	if err != nil {
		t.Fatal(err)
	}
	return assets, pam, dir
}
func TestActualNotoInkStaysInsideSafeRectangle(t *testing.T) {
	assets, _, _ := realAssets(t)
	out := image.NewRGBA(image.Rect(0, 0, 120, 140))
	for i := range out.Pix {
		out.Pix[i] = 31
	}
	prior := append([]byte(nil), out.Pix...)
	safe := image.Rect(40, 20, 88, 110)
	assets.DrawRune(out, '劍', safe, [3]uint8{255, 241, 181})
	changed := 0
	for y := 0; y < 140; y++ {
		for x := 0; x < 120; x++ {
			at := y*out.Stride + x*4
			if !bytes.Equal(prior[at:at+4], out.Pix[at:at+4]) {
				changed++
				if !image.Pt(x, y).In(safe) {
					t.Fatalf("ink escaped safe rectangle at %d,%d", x, y)
				}
			}
		}
	}
	if changed == 0 {
		t.Fatal("real Noto glyph drew no ink")
	}
}
func TestTamperedFontPNGIsRejected(t *testing.T) {
	_, pam, dir := realAssets(t)
	temp := t.TempDir()
	for _, name := range []string{"font.json", "font.png"} {
		data, err := os.ReadFile(filepath.Join(dir, name))
		if err != nil {
			t.Fatal(err)
		}
		if name == "font.png" {
			data = append(data, 0)
		}
		if err = os.WriteFile(filepath.Join(temp, name), data, 0600); err != nil {
			t.Fatal(err)
		}
	}
	if _, err := LoadAssets(temp, pam); err == nil {
		t.Fatal("tampered PNG was accepted")
	}
}
