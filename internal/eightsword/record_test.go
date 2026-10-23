package eightsword

import (
	"bytes"
	"compress/gzip"
	"image"
	"io"
	"os"
	"path/filepath"
	"testing"
)

func TestRecorderRepeatPreservesEveryFrameAndStep(t *testing.T) {
	root := t.TempDir()
	write := func(name string, fast bool) []byte {
		r, err := NewFrameRecorder(filepath.Join(root, name), 16, 8)
		if err != nil {
			t.Fatal(err)
		}
		if r.Repeat(1) == nil {
			t.Fatal("repeat without first frame accepted")
		}
		im := image.NewRGBA(image.Rect(0, 0, 16, 8))
		for i := range im.Pix {
			im.Pix[i] = byte(i)
		}
		for frame, step := range []uint64{10, 10, 30, 75, 80, 120} {
			if frame == 3 {
				im.Pix[4] ^= 255
			} // Explicit Write must notice in-place edits.
			if fast && frame != 0 && frame != 3 {
				err = r.Repeat(step)
			} else {
				err = r.Write(im, step)
			}
			if err != nil {
				t.Fatal(err)
			}
		}
		if r.Frames != 6 || fast && (r.RepeatedFrames != 4 || r.ComparedRows != 16) {
			t.Fatal("frames dropped or unnecessary row comparisons")
		}
		if err = r.Close(); err != nil {
			t.Fatal(err)
		}
		raw, err := os.ReadFile(filepath.Join(root, name))
		if err != nil {
			t.Fatal(err)
		}
		return raw
	}
	a, b := write("scan.frames.gz", false), write("repeat.frames.gz", true)
	if !bytes.Equal(a, b) {
		t.Fatal("same frame/step sequence changed compressed recording bytes")
	}
	z, err := gzip.NewReader(bytes.NewReader(b))
	if err != nil {
		t.Fatal(err)
	}
	decoded, err := io.ReadAll(z)
	if err != nil {
		t.Fatal(err)
	}
	if err = z.Close(); err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(decoded[:8], []byte("8SFRM001")) {
		t.Fatal("recording format changed")
	}
}
