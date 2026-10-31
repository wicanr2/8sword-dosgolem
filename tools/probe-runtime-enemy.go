//go:build ignore

// Fixed-state paired controls. No rerolling of original enemy generation.
package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func emust(e error) {
	if e != nil {
		panic(e)
	}
}
func ewrite(p string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	emust(e)
	f, e := os.OpenFile(p, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	emust(e)
	_, e = f.Write(append(b, '\n'))
	emust(e)
	emust(f.Close())
}
func main() {
	root := flag.String("root", "", "read-only original")
	input := flag.String("input", "", "fixed inputs")
	out := flag.String("out", "", "new output")
	flag.Parse()
	if os.Getuid() != 1000 {
		panic("UID1000")
	}
	emust(os.Mkdir(*out, 0755))
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	var seed OwnedWorld
	for _, v := range []struct {
		Name string
		Dst  any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}, {"world-runtime.json", &seed}} {
		b, e := os.ReadFile(filepath.Join(*input, v.Name))
		emust(e)
		emust(pairStrictJSON(b, v.Dst))
	}
	pam, e := os.ReadFile(filepath.Join(*input, "PAM.AY"))
	emust(e)
	code, e := worldArmyCode(pam)
	emust(e)
	base, e := os.ReadFile(filepath.Join(*input, "original-save.ay"))
	emust(e)
	parserCases := []map[string]any{}
	for _, name := range []string{"first", "last-slot-kind25", "signed-max", "empty", "kind26", "kind-ffff", "orphan-count", "zero-count", "negative-count", "duplicate", "short", "long"} {
		b := make([]byte, 24)
		binary.LittleEndian.PutUint16(b, 1)
		binary.LittleEndian.PutUint16(b[2:], 1)
		valid := false
		switch name {
		case "first":
			valid = true
		case "last-slot-kind25":
			clear(b)
			binary.LittleEndian.PutUint16(b[20:], 25)
			binary.LittleEndian.PutUint16(b[22:], 1)
			valid = true
		case "signed-max":
			binary.LittleEndian.PutUint16(b[2:], 32767)
			valid = true
		case "empty":
			clear(b)
		case "kind26":
			binary.LittleEndian.PutUint16(b, 26)
		case "kind-ffff":
			binary.LittleEndian.PutUint16(b, 65535)
		case "orphan-count":
			binary.LittleEndian.PutUint16(b, 0)
		case "zero-count":
			binary.LittleEndian.PutUint16(b[2:], 0)
		case "negative-count":
			binary.LittleEndian.PutUint16(b[2:], 32768)
		case "duplicate":
			copy(b[4:8], b[:4])
		case "short":
			b = b[:23]
		case "long":
			b = append(b, 0)
		}
		before := append([]byte(nil), b...)
		rows, e := decodeRuntimeEnemy(b, c, cc)
		if (e == nil) != valid || !bytes.Equal(b, before) {
			panic("parser case " + name)
		}
		parserCases = append(parserCases, map[string]any{"name": name, "raw_hex": fmt.Sprintf("%x", b), "accepted": valid, "rows": rows, "error": fmt.Sprint(e)})
	}
	results := []map[string]any{}
	for _, caseSpec := range []struct {
		Name         string
		Rank, Region uint16
	}{{"rank1-region0", 1, 0}, {"rank5-region7", 5, 7}} {
		var controlEnemy []byte
		var controlRand []map[string]uint16
		for _, mode := range []string{"original", "go"} {
			dir := filepath.Join(*out, caseSpec.Name+"-"+mode)
			emust(os.Mkdir(dir, 0755))
			w := seed
			w.Progress.Rank = uint32(caseSpec.Rank)
			w.Army.RecruitRank = uint32(caseSpec.Rank)
			var store *progressPairStore
			var snap progressPairSnapshot
			var bridge *runtimeEnemyBattle
			if mode == "go" {
				paired := filepath.Join(dir, "paired-save")
				emust(initializeProgressPair(paired, base, c, cc, w))
				store, snap, e = openProgressPair(paired, c, cc)
				emust(e)
			}
			o, e := oracle.LoadWith(filepath.Join(*root, "PAM.AY"), *root, oracle.Options{Adlib: true})
			emust(e)
			emust(o.LoadStateFile(filepath.Join(*input, "battle-before.state")))
			o.OnHostInstruction(oracle.Far(0x110, 0x3733), func(m *dg.Machine) (bool, error) {
				cpu := m.CPU
				ds := uint32(0x1e880)
				bp := cpu.R[dg.BP]
				if bp < 32 || m.Read16(ds+uint32(bp)+2) != 0x171d || m.Read16(ds+uint32(bp)+4) != 0x110 {
					return false, errors.New("fixed source frame")
				}
				emust(o.SaveStateFile(filepath.Join(dir, "before-commit.state")))
				cpu.R[dg.SI] = m.Read16(ds + uint32(bp) - 0x12)
				cpu.R[dg.DI] = m.Read16(ds + uint32(bp) - 0x10)
				cpu.R[dg.SP] = bp + 2
				cpu.R[dg.BP] = m.Read16(ds + uint32(bp))
				cpu.IP = 0x32e0
				for i, n := range pairWorldResources(w).words() {
					m.Write16(ds+0x4f2+uint32(i*2), uint16(n))
				}
				m.Write16(ds+0x56d6, caseSpec.Region)
				if mode == "go" {
					for _, off := range []uint32{ds + 0x54a, ds + 0x56e8} {
						for i := uint32(0); i < 24; i++ {
							m.Write8(off+i, 255)
						}
					}
				}
				cpu.Cycles++
				emust(o.SaveStateFile(filepath.Join(dir, "after-commit.state")))
				return true, nil
			})
			emust(o.RunUntil(oracle.At(oracle.Far(0x110, 0x32e0)), oracle.Budget(100000)))
			if mode == "go" {
				bridge = installRuntimeEnemyBattle(o, store, snap, code)
			}
			rng := []map[string]uint16{}
			for _, ip := range []uint16{0x354c, 0x356a, 0x3596, 0x35cd, 0x35eb, 0x3617, 0x3640} {
				ip := ip
				o.OnCall(oracle.Far(0x110, ip), func(o *oracle.Oracle) { rng = append(rng, map[string]uint16{"ip": ip, "ax": o.Regs().AX}) })
			}
			emust(o.RunUntil(oracle.At(oracle.Far(0x110, 0x36b4)), oracle.Budget(4000000)))
			raw := o.Bytes(oracle.Far(0x1e88, 0x5700), 24)
			rows, e := decodeRuntimeEnemy(raw, c, cc)
			emust(e)
			emust(o.SaveStateFile(filepath.Join(dir, "generated.state")))
			if mode == "original" {
				controlEnemy = raw
				controlRand = rng
			} else {
				if !bytes.Equal(controlEnemy, raw) || worldDigest(controlRand) != worldDigest(rng) {
					panic("paired original enemy/RNG mismatch")
				}
				runErr := o.Run(100000)
				if !errors.Is(runErr, errControlledBattleYield) {
					panic(fmt.Sprintf("import yield: %v", runErr))
				}
				emust(o.SaveStateFile(filepath.Join(dir, "held.state")))
				if bridge.Rows != rows || bridge.CopySkipped != 1 || bridge.Current.World.Battle == nil {
					panic("Go import differs")
				}
				s := bridge.Current.World.Battle.State
				plan, e := s.Choose(cc, 0, 0, "normal", 0, -1)
				emust(e)
				event, e := bridge.apply(plan.Action)
				emust(e)
				r := uint32(2730)
				emust(bridge.settle(DefeatInput{Reason: "retreat", Random: &r}))
				emust(o.RunUntil(oracle.At(oracle.Far(0x110, 0xbd3)), oracle.Budget(20000000)))
				if !bridge.Returned || bridge.NativeCalls != 0 {
					panic("native battle escaped")
				}
				emust(o.SaveStateFile(filepath.Join(dir, "final-map.state")))
				ewrite(filepath.Join(dir, "result.json"), map[string]any{"rows": rows, "rng": rng, "world": bridge.Current.World, "event": event, "return_ip": o.Regs().IP, "native_calls": bridge.NativeCalls, "copy_skipped": bridge.CopySkipped, "events": bridge.Events})
				store.Close()
			}
			ewrite(filepath.Join(dir, "generation.json"), map[string]any{"case": caseSpec.Name, "mode": mode, "rank": caseSpec.Rank, "region": caseSpec.Region, "enemy_hex": fmt.Sprintf("%x", raw), "rows": rows, "rng": rng, "paired_equal": mode == "go"})
			o.Close()
		}
		results = append(results, map[string]any{"case": caseSpec.Name, "enemy_hex": fmt.Sprintf("%x", controlEnemy), "rng_returns": len(controlRand), "paired_equal": true})
	}
	ewrite(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-runtime-enemy-import-pairs", "parser_cases": parserCases, "pairs": results, "rng_method": "identical saved original RNG state plus declared rank/region inputs, no rerolls", "normal_player_path": false})
}
