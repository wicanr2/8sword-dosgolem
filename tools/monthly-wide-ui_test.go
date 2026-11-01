//go:build ignore

package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"testing"
)

func TestWideMonthly(t *testing.T) {
	dir := os.Getenv("EIGHTSWORD_WIDE_ASSETS")
	if dir == "" {
		t.Fatal("EIGHTSWORD_WIDE_ASSETS required")
	}
	f, e := loadArmyUIFonts(dir)
	if e != nil {
		t.Fatal(e)
	}
	result := []map[string]any{}
	for _, id := range []string{"noto", "lishu", "caoshu"} {
		b := monthlyBudget{Before: 30000, Income: 30000, Due: math.MaxUint64, Charged: 0, After: 30000, Disbanded: true}
		im, texts := paintWideMonthly(b, f, id)
		seen := false
		for _, v := range texts {
			if v.Ellipsized {
				t.Fatal("monthly text truncated", v)
			}
			if v.Role == "monthly-due" {
				seen = true
				if v.Text != fmt.Sprint(uint64(math.MaxUint64)) {
					t.Fatal(v)
				}
			}
		}
		if !seen {
			t.Fatal("missing full due")
		}
		result = append(result, map[string]any{"font": id, "texts": texts, "canvas_sha256": contentSHA(im.Pix)})
	}
	if out := os.Getenv("EIGHTSWORD_WIDE_TEST_OUT"); out != "" {
		b, e := json.MarshalIndent(result, "", "  ")
		if e != nil {
			t.Fatal(e)
		}
		if e = os.WriteFile(filepath.Join(out, "wide-ui-test.json"), append(b, '\n'), 0600); e != nil {
			t.Fatal(e)
		}
	}
}
