package eightsword

import (
	"bytes"
	"errors"
	"os"
	"path/filepath"
	"testing"
)

func TestOwnedArmySaveStopsBeforeDOSLoad(t *testing.T) {
	for _, hd := range []bool{false, true} {
		for _, mode := range []string{"native", "formation", "tactics"} {
			for _, name := range []string{"gamedata.ay.army.json", "GAMEDATA.AY.ARMY.JSON"} {
				t.Run(mode+"/"+name+map[bool]string{false: "/native-graphics", true: "/HD"}[hd], func(t *testing.T) {
					dir := t.TempDir()
					payload := []byte(`{"schema":"eightsword-owned-army/1","new-unit":"openkb:wolf"}`)
					path := filepath.Join(dir, name)
					if err := os.WriteFile(path, payload, 0600); err != nil {
						t.Fatal(err)
					}
					// An absent original root proves that no DOS binary was loaded.
					e, err := Open(Options{Root: filepath.Join(dir, "absent-original"), Saves: dir, HD: hd, BattleRules: mode})
					if e != nil || !errors.Is(err, ErrOwnedArmyHandoffPending) {
						t.Fatalf("wrong early result: %v %v", e, err)
					}
					after, err := os.ReadFile(path)
					if err != nil || !bytes.Equal(payload, after) {
						t.Fatal("sidecar changed", err)
					}
				})
			}
		}
	}
}

func TestOwnedArmySaveGuardPreservesOrdinarySaves(t *testing.T) {
	dir := t.TempDir()
	for _, name := range []string{"gamedata.ay", "gamedata.ay.rules.json", "readme.txt"} {
		if err := os.WriteFile(filepath.Join(dir, name), []byte("ordinary"), 0600); err != nil {
			t.Fatal(err)
		}
	}
	if err := guardOwnedArmySave(dir); err != nil {
		t.Fatal(err)
	}
	if err := guardOwnedArmySave(filepath.Join(dir, "new-saves")); err != nil {
		t.Fatal(err)
	}
	if err := os.Mkdir(filepath.Join(dir, "gamedata.ay.army.json"), 0700); err != nil {
		t.Fatal(err)
	}
	if err := guardOwnedArmySave(dir); !errors.Is(err, ErrOwnedArmyHandoffPending) {
		t.Fatal("directory sidecar was ignored", err)
	}
}
