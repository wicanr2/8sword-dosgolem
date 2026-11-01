// Spec 030: isolated random-encounter total loss, roam branch only.
package ownedworld

import (
	"bytes"
	"errors"

	"github.com/wicanr2/dosgolem/oracle"
)

func roamAvailable(x *encounterExtra) bool {
	return x != nil && x.Bridge != nil && !x.Bridge.Settled && x.UI != nil && x.UI.World.Battle != nil && x.UI.World.Battle.State.Result == "loss"
}

func settleRuntimeRoam(b *controlledBattle, o *oracle.Oracle) error {
	if !b.Pending || b.Settled || b.Returned || b.Current.World.Battle == nil || b.Current.World.Battle.State.Result != "loss" {
		return errors.New("roam requires an unsettled total loss")
	}
	r := o.Regs()
	if r.CS != 0x110 || r.DS != 0x1e88 || r.SS != 0x1e88 || r.IP != 0x32e0 || r.SP != b.SP || r.BP != b.BP || o.Word(oracle.Far(r.SS, r.SP)) != 0x171d || o.Word(oracle.Far(r.SS, r.SP+2)) != 0x110 {
		return errors.New("roam held frame")
	}
	if !bytes.Equal(b.Code[0x151c:0x1796], o.Bytes(oracle.Far(0x110, 0x151c), 0x27a)) || !bytes.Equal(b.Code[0x32e0:0x3774], o.Bytes(oracle.Far(0x110, 0x32e0), 0x494)) {
		return errors.New("roam wrapper source")
	}
	s, e := b.Store.Recover()
	if e != nil {
		return e
	}
	if s.Token != b.Current.Token {
		return errors.New("roam stale pair")
	}
	for i, v := range b.BeforeResources {
		if o.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2))) != v {
			return errors.New("roam resource binding")
		}
	}
	// The durable return reference records result 2. No random call or native
	// army write is needed. Cold return uses the same verified redraw bridge.
	return b.settle(DefeatInput{Reason: "annihilation", Choice: "roam"})
}
