// Original-compatible integer RNG and bounded refusal/retreat admission.
package ownedworld

import (
	"bytes"
	"encoding/binary"
	"errors"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

type originalRandPlan struct {
	Before, After uint32
	Value         uint16
}

func planOriginalRand(seed uint32) originalRandPlan {
	next := seed*uint32(214013) + uint32(2531011)
	return originalRandPlan{seed, next, uint16((next >> 16) & 32767)}
}
func originalSeed(o *oracle.Oracle) uint32 {
	return uint32(o.Word(oracle.Far(0x1e88, 0x81bc))) | uint32(o.Word(oracle.Far(0x1e88, 0x81be)))<<16
}
func writeOriginalSeed(o *oracle.Oracle, seed uint32) {
	o.WriteU16(oracle.Far(0x1e88, 0x81bc), uint16(seed))
	o.WriteU16(oracle.Far(0x1e88, 0x81be), uint16(seed>>16))
}
func originalRandAddress(code []byte) (oracle.Addr, error) {
	if len(code) < 0x19566 || code[0x173a] != 0x9a {
		return oracle.Addr{}, errors.New("rand source bounds")
	}
	a := oracle.Far(binary.LittleEndian.Uint16(code[0x173d:]), binary.LittleEndian.Uint16(code[0x173b:]))
	if a.Linear() != 0x1100+0x1953e {
		return a, errors.New("rand relocation")
	}
	return a, nil
}
func checkOriginalRand(o *oracle.Oracle, code []byte) error {
	a, e := originalRandAddress(code)
	if e != nil {
		return e
	}
	r := o.Regs()
	if r.DS != 0x1e88 || r.SS != 0x1e88 || !bytes.Equal(code[0x1953e:0x19566], o.Bytes(a, 40)) {
		return errors.New("rand runtime source/segments")
	}
	return nil
}

var lastRetreatRand *originalRandPlan

func settleRuntimeRetreat(b *controlledBattle, o *oracle.Oracle) error {
	if !b.Pending || b.Settled || b.Returned || b.Current.World.Battle == nil {
		return errors.New("retreat phase")
	}
	if e := checkOriginalRand(o, b.Code); e != nil {
		return e
	}
	r := o.Regs()
	if r.CS != 0x110 || r.IP != 0x32e0 || r.SP != b.SP || r.BP != b.BP || o.Word(oracle.Far(r.SS, r.SP)) != 0x171d || o.Word(oracle.Far(r.SS, r.SP+2)) != 0x110 {
		return errors.New("retreat held frame")
	}
	if !bytes.Equal(b.Code[0x151c:0x1796], o.Bytes(oracle.Far(0x110, 0x151c), 0x27a)) || !bytes.Equal(b.Code[0x32e0:0x3774], o.Bytes(oracle.Far(0x110, 0x32e0), 0x494)) {
		return errors.New("retreat wrapper source")
	}
	s, e := b.Store.Recover()
	if e != nil {
		return e
	}
	if s.Token != b.Current.Token {
		return errors.New("retreat stale pair")
	}
	for i, v := range b.BeforeResources {
		if o.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2))) != v {
			return errors.New("retreat resource binding")
		}
	}
	plan := planOriginalRand(originalSeed(o))
	value := uint32(plan.Value)
	// Commit first. Failure consumes neither the saved army nor the RNG state.
	if e = b.settle(DefeatInput{Reason: "retreat", Random: &value}); e != nil {
		return e
	}
	writeOriginalSeed(o, plan.After)
	lastRetreatRand = &plan
	return nil
}

type refusalGate struct {
	Code     []byte
	BP, SP   uint16
	Guard    func(*dg.Machine) error
	Decision func(originalRandPlan, bool)
	Applied  bool
	Plan     originalRandPlan
	Pursued  bool
}

func (g *refusalGate) execute(m *dg.Machine) (bool, error) {
	c := m.CPU
	ds := uint32(0x1e880)
	if g.Applied || g.Guard == nil || c.Cycles == ^uint64(0) || c.IP != 0x173a || c.Seg[dg.CS] != 0x110 || c.Seg[dg.DS] != 0x1e88 || c.Seg[dg.SS] != 0x1e88 || c.R[dg.BP] != g.BP || c.R[dg.SP] != g.SP || g.BP < 32 || g.BP > 65520 || m.Read16(ds+uint32(g.BP)+2) != 0xbd3 || m.Read16(ds+uint32(g.BP)+4) != 0x110 {
		return false, errors.New("refusal frame/phase")
	}
	if _, e := originalRandAddress(g.Code); e != nil {
		return false, e
	}
	if !bytes.Equal(g.Code[0x151c:0x1796], m.Mem[0x1100+0x151c:0x1100+0x1796]) || !bytes.Equal(g.Code[0x1953e:0x19566], m.Mem[0x1100+0x1953e:0x1100+0x19566]) {
		return false, errors.New("refusal source")
	}
	if e := g.Guard(m); e != nil {
		return false, e
	}
	seed := uint32(m.Read16(ds+0x81bc)) | uint32(m.Read16(ds+0x81be))<<16
	plan := planOriginalRand(seed)
	pursued := plan.Value/8192 == 1
	m.Write16(ds+0x81bc, uint16(plan.After))
	m.Write16(ds+0x81be, uint16(plan.After>>16))
	c.R[dg.AX] = plan.Value / 8192
	c.R[dg.DX] = 0
	c.R[dg.CX] = 13
	c.IP = 0x1782
	if pursued {
		c.IP = 0x1752
	}
	c.Cycles++
	g.Applied = true
	g.Plan = plan
	g.Pursued = pursued
	if g.Decision != nil {
		g.Decision(plan, pursued)
	}
	return true, nil
}
