package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"os"
	"path/filepath"

	"github.com/jfreymuth/oggvorbis"
)

type musicSource struct {
	Title, Score, Bank, ScoreSHA, BankSHA string
	ScoreBytes, BankBytes                 int
}

type MusicCue struct {
	ID        int     `json:"id"`
	Title     string  `json:"title"`
	ScoreSHA  string  `json:"score_sha256"`
	BankSHA   string  `json:"bank_sha256"`
	File      string  `json:"file"`
	SHA       string  `json:"sha256"`
	Rate      int     `json:"sample_rate"`
	Channels  int     `json:"channels"`
	Frames    int64   `json:"frames"`
	LoopStart int64   `json:"loop_start_frame"`
	LoopEnd   int64   `json:"loop_end_frame"`
	Rights    string  `json:"rights"`
	PCM       []int16 `json:"-"`
}
type musicCatalog struct {
	Schema int        `json:"schema"`
	PAMSHA string     `json:"pam_sha256"`
	Cues   []MusicCue `json:"cues"`
}

func loadMusicAssets(dir string) (map[int]*MusicCue, error) {
	path := filepath.Join(dir, "music.json")
	info, err := os.Stat(path)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > 1<<20 {
		return nil, fmt.Errorf("HD 音樂清單大小或類型不符")
	}
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	dec := json.NewDecoder(bytes.NewReader(b))
	dec.DisallowUnknownFields()
	var catalog musicCatalog
	if err = dec.Decode(&catalog); err != nil {
		return nil, fmt.Errorf("HD 音樂清單：%w", err)
	}
	var extra any
	if dec.Decode(&extra) != io.EOF {
		return nil, fmt.Errorf("HD 音樂清單有多餘內容")
	}
	if catalog.Schema != 1 || catalog.PAMSHA != PAMSHA || len(catalog.Cues) == 0 || len(catalog.Cues) > 10 {
		return nil, fmt.Errorf("HD 音樂清單來源或版本不符")
	}
	result := map[int]*MusicCue{}
	var total int64
	for i := range catalog.Cues {
		cue := &catalog.Cues[i]
		source, ok := musicSources[cue.ID]
		if !ok || result[cue.ID] != nil || cue.Title != source.Title || cue.ScoreSHA != source.ScoreSHA || cue.BankSHA != source.BankSHA {
			return nil, fmt.Errorf("HD 音樂來源或曲目重複：%d", cue.ID)
		}
		if cue.Rate != 48000 || cue.Channels != 2 || cue.Frames <= 0 || cue.Frames > 48000*360 || cue.LoopStart != 0 || cue.LoopEnd != cue.Frames || cue.Rights != "original-derived-local" {
			return nil, fmt.Errorf("HD 音樂參數不符：%d", cue.ID)
		}
		total += cue.Frames * 4
		if total > 256<<20 {
			return nil, fmt.Errorf("HD 音樂解碼總量超出上限")
		}
		if cue.File == "" || filepath.Base(cue.File) != cue.File || cue.File == "." || cue.File == ".." || filepath.Ext(cue.File) != ".ogg" {
			return nil, fmt.Errorf("HD 音樂路徑不符")
		}
		file := filepath.Join(dir, cue.File)
		resolved, e := filepath.EvalSymlinks(file)
		if e != nil {
			return nil, e
		}
		base, e := filepath.EvalSymlinks(dir)
		if e != nil {
			return nil, e
		}
		resolved, e = filepath.Abs(resolved)
		if e != nil {
			return nil, e
		}
		base, e = filepath.Abs(base)
		if e != nil {
			return nil, e
		}
		if filepath.Dir(resolved) != base {
			return nil, fmt.Errorf("HD 音樂路徑超出素材目錄")
		}
		stat, e := os.Stat(file)
		if e != nil {
			return nil, e
		}
		if !stat.Mode().IsRegular() || stat.Size() <= 0 || stat.Size() > 32<<20 {
			return nil, fmt.Errorf("HD 音樂檔案大小不符")
		}
		data, e := os.ReadFile(file)
		if e != nil {
			return nil, e
		}
		if hash(data) != cue.SHA {
			return nil, fmt.Errorf("HD 音樂 %s SHA-256 不符", cue.File)
		}
		r, e := oggvorbis.NewReader(bytes.NewReader(data))
		if e != nil {
			return nil, fmt.Errorf("HD 音樂解碼：%w", e)
		}
		if r.SampleRate() != cue.Rate || r.Channels() != 2 || r.Length() != cue.Frames {
			return nil, fmt.Errorf("HD 音樂實際格式或長度不符")
		}
		cue.PCM = make([]int16, int(cue.Frames)*2)
		buffer := make([]float32, 16384)
		pos, zeroReads := 0, 0
		for {
			n, readErr := r.Read(buffer)
			if pos+n > len(cue.PCM) {
				return nil, fmt.Errorf("HD 音樂解碼超過宣告長度")
			}
			for j, v := range buffer[:n] {
				if math.IsNaN(float64(v)) || math.IsInf(float64(v), 0) {
					return nil, fmt.Errorf("HD 音樂含非有限取樣")
				}
				cue.PCM[pos+j] = int16(math.Round(float64(v) * 32767))
			}
			pos += n
			if readErr == io.EOF {
				break
			}
			if readErr != nil {
				return nil, fmt.Errorf("HD 音樂解碼：%w", readErr)
			}
			if n == 0 {
				zeroReads++
			} else {
				zeroReads = 0
			}
			if zeroReads > 3 {
				return nil, io.ErrNoProgress
			}
		}
		if pos != len(cue.PCM) {
			return nil, fmt.Errorf("HD 音樂解碼長度不足")
		}
		result[cue.ID] = cue
	}
	return result, nil
}
