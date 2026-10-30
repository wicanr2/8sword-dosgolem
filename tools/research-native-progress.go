//go:build ignore

// 030 DRAFT: exact narrow resource transport; all other progress bytes opaque.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"errors"
)

const nativeProgressSource = "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"

type NativeResources struct {
	Rank       uint64 `json:"rank"`
	Merit      uint64 `json:"merit"`
	MonthlyPay uint64 `json:"monthly_pay"`
	Gold       uint64 `json:"gold"`
	Leadership uint64 `json:"leadership"`
	SpellPower uint64 `json:"spell_power"`
}

func (v NativeResources) words() [6]uint64 {
	return [6]uint64{v.Rank, v.Merit, v.MonthlyPay, v.Gold, v.Leadership, v.SpellPower}
}
func (v NativeResources) validate() error {
	if v.Rank < 1 || v.Rank > 5 {
		return errors.New("native rank outside verified range")
	}
	for _, n := range v.words() {
		if n > 30000 {
			return errors.New("native resource outside strategic cap")
		}
	}
	return nil
}
func nativeSHA(b []byte) string { h := sha256.Sum256(b); return hex.EncodeToString(h[:]) }
func decodeNativeResources(source string, raw []byte) (NativeResources, error) {
	var v NativeResources
	if source != nativeProgressSource || len(raw) != 2987 {
		return v, errors.New("unverified native progress source or length")
	}
	var n [6]uint64
	for i := range n {
		off := i * 2
		n[i] = uint64(binary.LittleEndian.Uint16(raw[off:]) - uint16(off+3))
	}
	v = NativeResources{n[0], n[1], n[2], n[3], n[4], n[5]}
	return v, v.validate()
}

type NativeResourcePlan struct {
	SourceSHA string          `json:"source_sha256"`
	BeforeSHA string          `json:"before_sha256"`
	AfterSHA  string          `json:"after_sha256"`
	Before    NativeResources `json:"before"`
	After     NativeResources `json:"after"`
}

func planNativeResources(source string, raw []byte, expected, next NativeResources) (NativeResourcePlan, error) {
	var p NativeResourcePlan
	before, e := decodeNativeResources(source, raw)
	if e != nil {
		return p, e
	}
	if before != expected {
		return p, errors.New("stale native resources")
	}
	if e = next.validate(); e != nil {
		return p, e
	}
	result := bytes.Clone(raw)
	for i, n := range next.words() {
		off := i * 2
		binary.LittleEndian.PutUint16(result[off:], uint16(n)+uint16(off+3))
	}
	return NativeResourcePlan{source, nativeSHA(raw), nativeSHA(result), before, next}, nil
}
func applyNativeResources(raw []byte, p NativeResourcePlan) ([]byte, error) {
	if nativeSHA(raw) != p.BeforeSHA {
		return nil, errors.New("stale native progress bytes")
	}
	checked, e := planNativeResources(p.SourceSHA, raw, p.Before, p.After)
	if e != nil {
		return nil, e
	}
	if checked != p {
		return nil, errors.New("changed native resource plan")
	}
	out := bytes.Clone(raw)
	for i, n := range p.After.words() {
		off := i * 2
		binary.LittleEndian.PutUint16(out[off:], uint16(n)+uint16(off+3))
	}
	return out, nil
}
