//go:build ignore

package main

import (
	"encoding/json"
	"image"
	"math"
	"os"
	"path/filepath"
	"strings"
	"testing"

	dg "github.com/wicanr2/dosgolem"
)

func reviewFixture(t *testing.T) (ArmyCatalog, OwnedWorld, *armyUIFonts) {
	t.Helper()
	root := os.Getenv("EIGHTSWORD_REVIEW_INPUT")
	assets := os.Getenv("EIGHTSWORD_REVIEW_FONTS")
	if root == "" || assets == "" {
		t.Fatal("real review inputs/fonts required")
	}
	var c ArmyCatalog
	var s WorldSave
	for _, v := range []struct {
		Name string
		Dst  any
	}{{"army-catalog.json", &c}, {"review-save.json", &s}} {
		raw, e := os.ReadFile(filepath.Join(root, v.Name))
		if e != nil {
			t.Fatal(e)
		}
		if e = pairStrictJSON(raw, v.Dst); e != nil {
			t.Fatal(e)
		}
	}
	f, e := loadArmyUIFonts(assets)
	if e != nil {
		t.Fatal(e)
	}
	return c, s.World, f
}
func TestArmyReviewActualSavedRowsAreReadOnly(t *testing.T) {
	c, w, _ := reviewFixture(t)
	before, _ := json.Marshal(w)
	v, e := describeArmyReview(c, w)
	if e != nil {
		t.Fatal(e)
	}
	if v.Metrics.Total != 36 || v.Metrics.Used != 46 || v.Rows[0].ID != "native:01" || v.Rows[0].Count != 31 || v.Rows[1].ID != "openkb:wolf" || v.Rows[1].Count != 5 || v.Rows[1].Native {
		t.Fatal("saved army not fully represented", v)
	}
	for i := 2; i < 6; i++ {
		if v.Rows[i].Count != 0 || v.Rows[i].Slot != i {
			t.Fatal("empty slots shifted")
		}
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("review changed saved world")
	}
	w.Army.Slots[1].Unit = "26"
	if _, e = describeArmyReview(c, w); e == nil {
		t.Fatal("unregistered ID accepted")
	}
}
func TestArmyReviewThreeFontsSixRowsAndWideNumbers(t *testing.T) {
	c, w, f := reviewFixture(t)
	for _, a := range []string{"noto", "lishu", "caoshu"} {
		for _, wide := range []bool{false, true} {
			v := w
			if wide {
				v.Army.Leadership = math.MaxUint64
				v.Army.Gold = math.MaxUint64
				v.Army.Slots = [6]ArmyStack{{"native:01", math.MaxUint32}, {"native:02", math.MaxUint32}, {"native:03", math.MaxUint32}, {"native:04", math.MaxUint32}, {"native:25", math.MaxUint32}, {"openkb:wolf", math.MaxUint32}}
			}
			data, e := describeArmyReview(c, v)
			if e != nil {
				t.Fatal(e)
			}
			out, texts := paintArmyReview(data, f, a)
			if out.Bounds() != image.Rect(0, 0, 1920, 1200) {
				t.Fatal("canvas")
			}
			for _, s := range texts {
				r := image.Rect(s.Rect[0], s.Rect[1], s.Rect[2], s.Rect[3])
				ink := image.Rect(s.Ink[0], s.Ink[1], s.Ink[2], s.Ink[3])
				if !ink.Empty() && !ink.In(r) {
					t.Fatal("ink overflow", a, s)
				}
				if strings.Contains(s.Role, "-count") && s.Ellipsized {
					t.Fatal("count truncated", s)
				}
			}
		}
	}
	data, e := describeArmyReview(c, w)
	if e != nil {
		t.Fatal(e)
	}
	data.Rows[1].Name = strings.Repeat("野狼", 30)
	_, texts := paintArmyReview(data, f, "lishu")
	found := false
	for _, s := range texts {
		if s.Role == "review-1-name" {
			found = s.Ellipsized && strings.HasSuffix(s.Text, "…")
		}
	}
	if !found {
		t.Fatal("long unit name policy")
	}
}
func TestArmyReviewRejectedABILeavesGuestUntouched(t *testing.T) {
	for _, scenario := range []string{"inactive", "segments", "selector", "argument", "mode", "code", "repeated"} {
		t.Run(scenario, func(t *testing.T) {
			m := dg.New()
			m.CPU.Seg[dg.CS] = 0x110
			m.CPU.Seg[dg.DS] = 0x1e88
			m.CPU.Seg[dg.SS] = 0x1e88
			m.CPU.IP = 0x3ebc
			m.CPU.R[dg.SP] = 0xff00
			m.Write16(0x1e880+0xff00, 0x110)
			m.Write16(0x1e880+0xff02, 0x2f)
			m.Write16(0x1e880+0x56bc, 1)
			v := &armyReview{Active: true, EntryMode: 1, Expected: make([]byte, 0x76)}
			switch scenario {
			case "inactive":
				v.Active = false
			case "segments":
				m.CPU.Seg[dg.DS] = 0
			case "selector":
				m.Write16(0x1e880+0x56bc, 2)
			case "argument":
				m.Write16(0x1e880+0xff02, 0x30)
			case "mode":
				v.EntryMode = 3
			case "code":
				m.Mem[0x1100+0x3e92] = 1
			case "repeated":
				v.ThisSkip = 1
			}
			before := append([]byte(nil), m.Mem...)
			regs, segs, ip, cycles := m.CPU.R, m.CPU.Seg, m.CPU.IP, m.CPU.Cycles
			ok, e := v.skipRows(m, 0x3ebc, 0x2f)
			if ok || e == nil {
				t.Fatal("unsafe ABI admitted")
			}
			if string(before) != string(m.Mem) || regs != m.CPU.R || segs != m.CPU.Seg || ip != m.CPU.IP || cycles != m.CPU.Cycles {
				t.Fatal("rejection mutated guest")
			}
		})
	}
}
