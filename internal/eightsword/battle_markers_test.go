package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func TestChoiRealSourcesRotationsAndAtomicFailure(t *testing.T) {
	dir, root, cache := os.Getenv("EIGHTSWORD_TEST_CHOI_ASSETS"), os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_CHOI_CACHE")
	if dir == "" || root == "" || cache == "" {
		t.Skip("需要本機 CHOI 素材、原版與獨立快取")
	}
	good, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer good.Close()
	if good.BattleMarkerError != "" || good.BattleEffectError != "" || len(good.Tracker.graphics.assets.Effects) != 8 {
		t.Fatalf("marker/effect load: %s / %s", good.BattleMarkerError, good.BattleEffectError)
	}
	a := good.Tracker.graphics.assets
	raw, err := os.ReadFile(filepath.Join(root, "CHOI.EGG"))
	if err != nil {
		t.Fatal(err)
	}
	for i, expected := range choiSources {
		id := uint16(108 + i)
		if hash(raw[i*3304:(i+1)*3304]) != expected.Record || hash(raw[i*3304:i*3304+2204]) != expected.Native || a.ByNative[expected.Native] != id || a.EffectSHA[id] != expected.Record || a.Actors[id] != nil {
			t.Fatalf("CHOI source %d differs", i)
		}
		pixels, err := os.ReadFile(filepath.Join(cache, fmt.Sprintf("cache-frame-%d.rgba", i)))
		if err != nil || !bytes.Equal(pixels, a.Effects[id].Tile.Pix) {
			t.Fatalf("CHOI rotation %d differs from independent cache: %v", i, err)
		}
	}
	for _, failure := range []string{"broken-png", "fourth-cache"} {
		t.Run(failure, func(t *testing.T) {
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
				if failure == "broken-png" && entry.Name() == "battle-choi-r1.png" {
					data[len(data)/2] ^= 1
				}
				if failure == "fourth-cache" && entry.Name() == "battle-choi.json" {
					var manifest map[string]any
					if err = json.Unmarshal(data, &manifest); err != nil {
						t.Fatal(err)
					}
					manifest["frames"].([]any)[3].(map[string]any)["cache_sha256"] = "invalid"
					data, err = json.Marshal(manifest)
					if err != nil {
						t.Fatal(err)
					}
				}
				if err = os.WriteFile(filepath.Join(broken, entry.Name()), data, 0644); err != nil {
					t.Fatal(err)
				}
			}
			bad, err := Open(Options{Root: root, Assets: broken, Saves: t.TempDir(), HD: true})
			if err != nil {
				t.Fatal(err)
			}
			defer bad.Close()
			b := bad.Tracker.graphics.assets
			if bad.BattleMarkerError == "" || !bad.HD || bad.AssetError != "" || bad.GraphicsError != "" || bad.BattleBackgroundError != "" || bad.BattleActorError != "" || bad.BattleEffectError != "" || len(b.Effects) != 4 || !reflect.DeepEqual(good.Assets, bad.Assets) {
				t.Fatal("broken CHOI disabled another asset group")
			}
			for _, expected := range choiSources {
				if b.ByNative[expected.Native] != 0 {
					t.Fatal("partial CHOI group published")
				}
			}
			for id, actor := range a.Actors {
				if b.Actors[id] == nil || !bytes.Equal(actor.Tile.Pix, b.Actors[id].Tile.Pix) {
					t.Fatalf("other actor %d changed", id)
				}
			}
			for id := uint16(103); id <= 106; id++ {
				if !bytes.Equal(a.Effects[id].Tile.Pix, b.Effects[id].Tile.Pix) {
					t.Fatalf("PON %d changed", id)
				}
			}
		})
	}
}

func TestChoiMissingGroupAndAbortCounters(t *testing.T) {
	assets := &GraphicsAssets{}
	if err := loadBattleMarkers(t.TempDir(), t.TempDir(), assets); err != nil || assets.Effects != nil || assets.ByNative != nil {
		t.Fatal("missing optional group changed graphics")
	}
	g := effectMetadataFixture()
	g.effectDraft = &battleEffectDraft{First: 0, ID: 1, Frame: &battleEffectFrame{Source: 109, Tile: image.NewRGBA(image.Rect(0, 0, 264, 300))}}
	g.active = &bitmapCall{Effect: 109}
	g.abortBattleEffect()
	if g.Stats.BattleMarkerFallbackCalls != 1 || g.Stats.BattleEffectFallbackCalls != 0 || g.effectDraft != nil {
		t.Fatal("CHOI abort changed PON counters")
	}
	// Keep the source family even when a failed active call lost its effect ID.
	g.effectDraft = &battleEffectDraft{First: 0, ID: 1, Frame: &battleEffectFrame{Source: 110}}
	g.active = &bitmapCall{}
	g.abortBattleEffect()
	if g.Stats.BattleMarkerFallbackCalls != 2 || g.Stats.BattleEffectFallbackCalls != 0 {
		t.Fatal("CHOI draft source lost after active reset")
	}
}
