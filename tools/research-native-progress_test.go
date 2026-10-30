//go:build ignore

package main

import (
	"bytes"
	"math"
	"os"
	"path/filepath"
	"testing"
)

func TestNativeProgressRealBytesAndBounds(t *testing.T) {
	p := os.Getenv("EIGHTSWORD_NATIVE_PROGRESS_INPUT")
	if p == "" {
		t.Fatal("real data required")
	}
	raw, e := os.ReadFile(filepath.Join(p, "original-save.ay"))
	if e != nil {
		t.Fatal(e)
	}
	before, e := decodeNativeResources(nativeProgressSource, raw)
	if e != nil {
		t.Fatal(e)
	}
	next := NativeResources{2, 2012, 200, 4400, 1100, 16}
	plan, e := planNativeResources(nativeProgressSource, raw, before, next)
	if e != nil {
		t.Fatal(e)
	}
	out, e := applyNativeResources(raw, plan)
	if e != nil {
		t.Fatal(e)
	}
	if !bytes.Equal(out[12:], raw[12:]) || len(out) != 2987 {
		t.Fatal("army or opaque bytes changed")
	}
	v, e := decodeNativeResources(nativeProgressSource, out)
	if e != nil || v != next {
		t.Fatal(v, e)
	}
	same, e := planNativeResources(nativeProgressSource, raw, before, before)
	if e != nil {
		t.Fatal(e)
	}
	roundtrip, e := applyNativeResources(raw, same)
	if e != nil || !bytes.Equal(raw, roundtrip) {
		t.Fatal("unchanged bytes lost")
	}
	if _, e = applyNativeResources(out, plan); e == nil {
		t.Fatal("reapplied")
	}
	bad := plan
	bad.AfterSHA = "bad"
	if _, e = applyNativeResources(raw, bad); e == nil {
		t.Fatal("edited plan")
	}
	for _, value := range []uint64{30001, 65535, 65536, math.MaxUint64} {
		n := next
		n.Gold = value
		if _, e = planNativeResources(nativeProgressSource, raw, before, n); e == nil {
			t.Fatal("wide overflow accepted", value)
		}
	}
	for _, rank := range []uint64{0, 6, 65536} {
		n := next
		n.Rank = rank
		if _, e = planNativeResources(nativeProgressSource, raw, before, n); e == nil {
			t.Fatal("rank", rank)
		}
	}
	for _, n := range []int{0, 12, 2986, 2988} {
		b := make([]byte, n)
		if _, e = decodeNativeResources(nativeProgressSource, b); e == nil {
			t.Fatal("length", n)
		}
	}
	if _, e = decodeNativeResources("other", raw); e == nil {
		t.Fatal("unverified executable")
	}
	wrong := before
	wrong.Gold++
	if _, e = planNativeResources(nativeProgressSource, raw, wrong, next); e == nil {
		t.Fatal("stale values")
	}
	n := NativeResources{5, 30000, 30000, 30000, 30000, 30000}
	p2, e := planNativeResources(nativeProgressSource, raw, before, n)
	if e != nil {
		t.Fatal(e)
	}
	b, e := applyNativeResources(raw, p2)
	if e != nil {
		t.Fatal(e)
	}
	if v, e = decodeNativeResources(nativeProgressSource, b); e != nil || v != n {
		t.Fatal("boundary", v, e)
	}
}
