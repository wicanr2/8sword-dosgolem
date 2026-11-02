// 030 DRAFT: one verified militia shop caller, with Go-owned army calculations
// and commit. This is an isolated experiment, not an Engine loading option.
package ownedworld

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"math"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

type worldArmyMetrics struct {
	Used     uint64 `json:"used"`
	Total    uint64 `json:"total"`
	Occupied int    `json:"occupied"`
}

func measureWorldArmy(c ArmyCatalog, a OwnedArmy) (worldArmyMetrics, error) {
	var v worldArmyMetrics
	if e := a.validate(c); e != nil {
		return v, e
	}
	idx, _ := c.index()
	for _, s := range a.Slots {
		if s.Unit == "" {
			continue
		}
		n := uint64(s.Count)
		cost := n * idx[s.Unit].Command
		if v.Total > math.MaxUint64-n || v.Used > math.MaxUint64-cost {
			return worldArmyMetrics{}, errors.New("army aggregate overflow")
		}
		v.Total += n
		v.Used += cost
		v.Occupied++
	}
	return v, nil
}

func worldArmyCapacity(c ArmyCatalog, a OwnedArmy, id string) (bool, error) {
	if _, e := measureWorldArmy(c, a); e != nil {
		return false, e
	}
	idx, _ := c.index()
	if _, ok := idx[id]; !ok {
		return false, errors.New("unknown requested unit")
	}
	for _, s := range a.Slots {
		if s.Unit == id || s.Unit == "" {
			return true, nil
		}
	}
	return false, nil
}

type worldArmyPortRecord struct {
	IP    uint16 `json:"ip"`
	Route string `json:"route"`
	Kind  uint16 `json:"native_kind"`
	Value uint16 `json:"value"`
	Token string `json:"pair_token"`
}

type worldArmyPortFault struct{ Reason string }

func (f *worldArmyPortFault) Error() string { return "world army port: " + f.Reason }

type worldArmyPort struct {
	OriginalReview           *originalArmyReview
	OriginalDismiss          *originalArmyDismiss
	Store                    *progressPairStore
	Current                  progressPairSnapshot
	Expected                 map[uint16][]byte
	ShopID, ShopUnit         string
	ShopKind, ShopSP, ShopBP uint16
	ShopGroup, ShopRow       int
	ShopCommitted            bool
	ShopStock                uint16
	ShopOpen                 bool
	Records                  []worldArmyPortRecord
	NativeEntries            uint64
	Purchases                uint64
}

// IDA 9.4 operand candidates in the twelve other strategic consumers. A map
// dispatcher may execute harmless branches on every move; reject at the actual
// army operand, not at the entry to that whole dispatcher.
var worldArmyReadGuards = []uint16{
	0x165c, 0x1900, 0x1cd8, 0x2709, 0x2710, 0x271a, 0x2742, 0x2748,
	0x3054, 0x3371, 0x3379, 0x3755, 0x375d, 0x6db1, 0x6dba, 0x6dd2, 0x6de2, 0x6de9,
	0x75fd, 0x76ad, 0x76e8, 0x77cd, 0x781b, 0x7850, 0x78ad, 0x78ff, 0x7930,
	0x798d, 0x79db, 0x7a10, 0x7a6d, 0x7abf, 0x7af0, 0x7b43, 0x7b49, 0x7baf,
	0x7c0a, 0x7c11, 0x7c15, 0x7c19, 0x7c1d, 0x7c21, 0x7c27, 0x8de9,
	0x56f1, // the native recruit loop if a disabled host hook ever escapes.
}

func (p *worldArmyPort) snapshot() (progressPairSnapshot, error) {
	v, e := p.Store.Recover()
	if e != nil {
		return v, e
	}
	if v.Token != p.Current.Token {
		return v, errors.New("paired world changed outside the adapter")
	}
	if v.World.Battle != nil {
		return v, errors.New("army shop during battle")
	}
	return v, nil
}

func worldArmyCode(pam []byte) ([]byte, error) {
	if nativeSHA(pam) != nativeProgressSource {
		return nil, errors.New("PAM source")
	}
	u16 := func(at int) uint16 { return binary.LittleEndian.Uint16(pam[at:]) }
	header := int(u16(8)) * 16
	code := append([]byte(nil), pam[header:]...)
	for i := 0; i < int(u16(6)); i++ {
		at := int(u16(24)) + i*4
		pos := int(u16(at+2))*16 + int(u16(at))
		binary.LittleEndian.PutUint16(code[pos:], binary.LittleEndian.Uint16(code[pos:])+0x110)
	}
	return code, nil
}

func installWorldArmyPort(e *game.Engine, store *progressPairStore, snap progressPairSnapshot) (*worldArmyPort, error) {
	if !e.PAMLoaded || !e.HD {
		return nil, errors.New("verified PAM/HD map required")
	}
	idx, x := store.Catalog.index()
	if x != nil {
		return nil, x
	}
	if u := idx["native:01"]; u.NativeKind != 1 || u.Gold != 1 || u.Command != 1 {
		return nil, errors.New("militia catalog/ABI mismatch")
	}
	code, err := worldArmyCode(e.PAM)
	if err != nil {
		return nil, err
	}
	p := &worldArmyPort{Store: store, Current: snap, Expected: map[uint16][]byte{}}
	for _, region := range [][2]uint16{{0x54ea, 0x58f0}, {0x58f0, 0x59c4}, {0x59c4, 0x5c94}} {
		p.Expected[region[0]] = code[region[0]:region[1]]
		if !bytes.Equal(p.Expected[region[0]], e.Oracle.Bytes(oracle.Far(0x110, region[0]), int(region[1]-region[0]))) {
			return nil, errors.New("runtime code differs")
		}
	}
	fail := func(reason string) { panic(&worldArmyPortFault{reason}) }
	swordOnCall(e.Oracle, oracle.Far(0x110, 0x54ea), func(o *oracle.Oracle) {
		if err := p.bindCamp(o); err != nil {
			fail(err.Error())
		}
	})
	for group := 0; group < 5; group++ {
		group := group
		swordOnCall(e.Oracle, oracle.Far(0x110, uint16(0x5a3b+group*0x90)), func(o *oracle.Oracle) {
			if err := p.finishCamp(o, group); err != nil {
				fail(err.Error())
			}
		})
	}

	// These sentinels forbid accidentally falling back to the native helpers,
	// including when tracing/watch configuration disables host instructions.
	for _, ip := range []uint16{0x58f0, 0x593c, 0x5962} {
		swordOnCall(e.Oracle, oracle.Far(0x110, ip), func(*oracle.Oracle) { p.NativeEntries++; fail("native army helper escaped the Go port") })
	}
	for _, ip := range worldArmyReadGuards {
		ip := ip
		swordOnCall(e.Oracle, oracle.Far(0x110, ip), func(*oracle.Oracle) {
			if p.OriginalReview.acceptsRead(ip) || p.OriginalDismiss.acceptsRead(ip) {
				return
			}
			fail(fmt.Sprintf("unsupported world army operand at 0110:%04X", ip))
		})
	}
	for ip, route := range map[uint16]string{0x556a: "capacity", 0x55c2: "command", 0x55cd: "used", 0x56ec: "commit"} {
		ip, route := ip, route
		swordOnHostInstruction(e.Oracle, oracle.Far(0x110, ip), func(m *dg.Machine) (bool, error) {
			if err := p.execute(m, ip, route); err != nil {
				return false, err
			}
			return true, nil
		})
	}
	return p, nil
}

func (p *worldArmyPort) execute(m *dg.Machine, ip uint16, route string) error {
	fault := func(s string) error { return &worldArmyPortFault{s} }
	c := m.CPU
	ds := uint32(0x1e88) * 16
	if c.Cycles == math.MaxUint64 || map[uint16]string{0x556a: "capacity", 0x55c2: "command", 0x55cd: "used", 0x56ec: "commit"}[ip] != route {
		return fault("route/accounting")
	}
	if c.Seg[dg.CS] != 0x110 || c.IP != ip || c.Seg[dg.DS] != 0x1e88 || c.Seg[dg.SS] != 0x1e88 || !p.ShopOpen {
		return fault("call site/segments")
	}
	for start, want := range p.Expected {
		at := 0x1100 + int(start)
		if !bytes.Equal(m.Mem[at:at+len(want)], want) {
			return fault("runtime code changed")
		}
	}
	v, err := p.snapshot()
	if err != nil {
		return fault(err.Error())
	}
	for i, n := range pairWorldResources(v.World).words() {
		if uint64(m.Read16(ds+0x4f2+uint32(i*2))) != n {
			return fault("guest/Go resource mismatch")
		}
	}
	bp, sp := c.R[dg.BP], c.R[dg.SP]
	if bp < 16 || bp > 65520 || sp > bp || m.Read16(ds+uint32(bp)+6) != p.ShopKind || m.Read16(ds+uint32(bp)+8) != p.ShopStock {
		return fault("shop frame")
	}
	var value uint16
	if route == "commit" {
		if p.ShopCommitted {
			return fault("purchase already committed")
		}
		count := m.Read16(ds + uint32(bp) - 2)
		if count == 0 || count > 32767 {
			return fault("purchase count")
		}
		next := v.World
		next.Army, _, err = next.Army.recruit(p.Store.Catalog, p.ShopID, uint32(count))
		if err != nil {
			return fault(err.Error())
		}
		if next.Revision == math.MaxUint64 {
			return fault("revision overflow")
		}
		next.Revision++
		updated, x := p.Store.Commit(v.Token, next)
		if x != nil {
			return fault(x.Error())
		}
		// Disk transaction commits before the guest resource projection. Never
		// write any Go unit ID or count into the original six-row table.
		for i, n := range pairWorldResources(updated.World).words() {
			m.Write16(ds+0x4f2+uint32(i*2), uint16(n))
		}
		p.Current = updated
		p.Purchases++
		p.ShopCommitted = true
		value = count
		c.IP = 0x576b
	} else {
		if sp > 65530 || m.Read16(ds+uint32(sp)) != 0x110 {
			return fault("near-call push-CS ABI")
		}
		if route != "used" && m.Read16(ds+uint32(sp)+2) != p.ShopKind {
			return fault("native argument outside supported kind")
		}
		switch route {
		case "capacity":
			ok, x := worldArmyCapacity(p.Store.Catalog, v.World.Army, p.ShopUnit)
			if x != nil {
				return fault(x.Error())
			}
			if ok {
				value = 1
			}
		case "command":
			idx, x := p.Store.Catalog.index()
			if x != nil {
				return fault(x.Error())
			}
			n := idx[p.ShopUnit].Command
			if n == 0 || n > 32767 {
				return fault("command ABI range")
			}
			value = uint16(n)
		case "used":
			n, x := measureWorldArmy(p.Store.Catalog, v.World.Army)
			if x != nil {
				return fault(x.Error())
			}
			if n.Used > 32767 {
				return fault("used leadership ABI range")
			}
			value = uint16(n.Used)
		default:
			return fault("unknown route")
		}
		c.R[dg.AX] = value
		c.R[dg.SP] += 2
		c.IP += 3
	}
	// One verified CALL instruction or commit gate becomes one Go host
	// operation. This is not an original helper step/cycle parity claim.
	c.Cycles++
	p.Records = append(p.Records, worldArmyPortRecord{ip, route, p.ShopKind, value, p.Current.Token})
	return nil
}

func catchWorldArmyFault(run func() error) (err error) {
	defer func() {
		if p := recover(); p != nil {
			if f, ok := p.(*worldArmyPortFault); ok {
				err = f
			} else {
				panic(p)
			}
		}
	}()
	return run()
}

func (p *worldArmyPort) String() string {
	return fmt.Sprintf("Go army port: %d operations, %d purchases", len(p.Records), p.Purchases)
}
