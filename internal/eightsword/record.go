package eightsword

import (
	"bytes"
	"compress/gzip"
	"encoding/binary"
	"fmt"
	"image"
	"os"
)

// FrameRecorder saves every submitted frame as lossless changed RGBA rows.
// Repeated frames still have a frame/guest-step record; no frame is dropped.
type FrameRecorder struct {
	file                         *os.File
	zip                          *gzip.Writer
	previous                     []byte
	Width, Height                int
	Frames                       uint64
	RepeatedFrames, ComparedRows uint64
}

func NewFrameRecorder(path string, width, height int) (*FrameRecorder, error) {
	f, err := os.Create(path)
	if err != nil {
		return nil, err
	}
	z, err := gzip.NewWriterLevel(f, gzip.BestSpeed)
	if err != nil {
		f.Close()
		return nil, err
	}
	r := &FrameRecorder{file: f, zip: z, Width: width, Height: height, previous: make([]byte, width*height*4)}
	if _, err = z.Write([]byte("8SFRM001")); err != nil {
		r.Close()
		return nil, err
	}
	if err = binary.Write(z, binary.LittleEndian, [2]uint32{uint32(width), uint32(height)}); err != nil {
		r.Close()
		return nil, err
	}
	return r, nil
}
func (r *FrameRecorder) Write(im *image.RGBA, step uint64) error {
	if im == nil || im.Bounds() != image.Rect(0, 0, r.Width, r.Height) || im.Stride != r.Width*4 {
		return fmt.Errorf("recording frame shape changed")
	}
	changed := []uint16{}
	rowBytes := r.Width * 4
	r.ComparedRows += uint64(r.Height)
	for y := 0; y < r.Height; y++ {
		at := y * rowBytes
		if r.Frames == 0 || !bytes.Equal(im.Pix[at:at+rowBytes], r.previous[at:at+rowBytes]) {
			changed = append(changed, uint16(y))
		}
	}
	if err := r.header(step, uint64(len(changed))); err != nil {
		return err
	}
	for _, y := range changed {
		if err := binary.Write(r.zip, binary.LittleEndian, y); err != nil {
			return err
		}
		at := int(y) * rowBytes
		if _, err := r.zip.Write(im.Pix[at : at+rowBytes]); err != nil {
			return err
		}
		copy(r.previous[at:at+rowBytes], im.Pix[at:at+rowBytes])
	}
	return nil
}

// Repeat records the previous immutable frame at a new guest step. The caller
// must know the pixels have not changed. Write still detects in-place changes.
func (r *FrameRecorder) Repeat(step uint64) error {
	if r.Frames == 0 {
		return fmt.Errorf("recording has no previous frame")
	}
	if err := r.header(step, 0); err != nil {
		return err
	}
	r.RepeatedFrames++
	return nil
}

func (r *FrameRecorder) header(step, rows uint64) error {
	r.Frames++
	return binary.Write(r.zip, binary.LittleEndian, [3]uint64{r.Frames, step, rows})
}
func (r *FrameRecorder) Close() error {
	if r == nil {
		return nil
	}
	first := r.zip.Close()
	if err := r.file.Close(); first == nil {
		first = err
	}
	return first
}
