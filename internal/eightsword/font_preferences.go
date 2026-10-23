package eightsword

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

type FontPreferences struct {
	Schema int    `json:"schema"`
	Font   string `json:"font"`
}

func LoadFontPreference(path string) (string, error) {
	b, err := os.ReadFile(path)
	if os.IsNotExist(err) {
		return "noto", nil
	}
	if err != nil {
		return "noto", err
	}
	var p FontPreferences
	if len(b) > 4096 || json.Unmarshal(b, &p) != nil || p.Schema != 1 || (p.Font != "noto" && p.Font != "lishu" && p.Font != "caoshu") {
		return "noto", fmt.Errorf("字型設定檔無效，使用 Noto")
	}
	return p.Font, nil
}

func SaveFontPreference(path, id string) error {
	if id != "noto" && id != "lishu" && id != "caoshu" {
		return fmt.Errorf("字型設定值無效")
	}
	if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		return err
	}
	b, err := json.MarshalIndent(FontPreferences{Schema: 1, Font: id}, "", "  ")
	if err != nil {
		return err
	}
	f, err := os.CreateTemp(filepath.Dir(path), ".font-settings-*")
	if err != nil {
		return err
	}
	name := f.Name()
	defer os.Remove(name)
	if _, err = f.Write(append(b, '\n')); err != nil {
		f.Close()
		return err
	}
	if err = f.Close(); err != nil {
		return err
	}
	return os.Rename(name, path)
}
