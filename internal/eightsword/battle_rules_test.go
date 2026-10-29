package eightsword

import (
	"bytes"
	"errors"
	"os"
	"path/filepath"
	"testing"
)

func TestRulesMarkerBindingAndCorruption(t *testing.T) {
	dir := t.TempDir()
	data := bytes.Repeat([]byte{37}, 2987)
	save := filepath.Join(dir, "gamedata.ay")
	if mode, exists, err := readRulesMarker(dir); err != nil || exists || mode != "native" {
		t.Fatal(mode, exists, err)
	}
	if err := os.WriteFile(save, data, 0600); err != nil {
		t.Fatal(err)
	}
	for _, mode := range []string{"formation", "native", "tactics"} {
		if err := writeRulesMarker(dir, mode); err != nil {
			t.Fatal(err)
		}
		got, exists, err := readRulesMarker(dir)
		if err != nil || !exists || got != mode {
			t.Fatal(got, exists, err)
		}
	}
	data[0]++
	os.WriteFile(save, data, 0600)
	if _, _, err := readRulesMarker(dir); err == nil {
		t.Fatal("mismatched progress accepted")
	}
	data[0]--
	os.WriteFile(save, data, 0600)
	for _, bad := range []string{`{"schema":2}`, `{"schema":1,"rules":"other","save_bytes":2987}`, `{"schema":1,"extra":true}`, `{} {}`} {
		os.WriteFile(filepath.Join(dir, "gamedata.ay.rules.json"), []byte(bad), 0600)
		if _, _, err := readRulesMarker(dir); err == nil {
			t.Fatal("bad marker accepted", bad)
		}
	}
	os.Remove(filepath.Join(dir, "gamedata.ay.rules.json"))
	os.Mkdir(filepath.Join(dir, "gamedata.ay.rules.json"), 0700)
	if writeRulesMarker(dir, "formation") == nil {
		t.Fatal("non-regular marker replaced")
	}
	if _, _, err := readRulesMarker(dir); err == nil {
		t.Fatal("non-regular marker accepted")
	}
}
func TestRuleSelectionLock(t *testing.T) {
	e := &Engine{rules: &battleRulesController{BattleRuleInfo: BattleRuleInfo{Mode: "native", Active: true}}}
	if err := e.SetBattleRules("formation"); !errors.Is(err, ErrBattleRulesLocked) || e.BattleRulesMode() != "native" {
		t.Fatal("mid-battle switch", err)
	}
	if err := e.SetBattleRules("tactics"); !errors.Is(err, ErrBattleRulesLocked) || e.BattleRulesMode() != "native" {
		t.Fatal("mid-battle tactics", err)
	}
	if err := e.SetBattleRules("unknown"); err == nil || e.BattleRulesMode() != "native" {
		t.Fatal("invalid rule accepted")
	}
}
