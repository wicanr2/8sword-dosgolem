// Run only the existing native serializer in a detached VM and scratch folder.
// The player's clock, RAM, files and Go world are never advanced by this copy.
package ownedworld

import (
	"bytes"
	"errors"
	"os"
	"path/filepath"
	"strings"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func serializeMonthlyNative(root, pamPath, state, dir string, maps map[string][]byte) ([]byte, map[string][]byte, error) {
	if e := checkNativeMaps(maps); e != nil {
		return nil, nil, e
	}
	if e := os.Mkdir(dir, 0700); e != nil {
		return nil, nil, e
	}
	for n, b := range maps {
		if e := os.WriteFile(filepath.Join(dir, n), b, 0600); e != nil {
			return nil, nil, e
		}
	}
	pam, e := os.ReadFile(pamPath)
	if e != nil {
		return nil, nil, e
	}
	code, e := worldArmyCode(pam)
	if e != nil {
		return nil, nil, e
	}
	o, e := oracle.LoadWith(pamPath, root, oracle.Options{Adlib: true})
	if e != nil {
		return nil, nil, e
	}
	if e = o.LoadStateFile(state); e != nil {
		return nil, nil, e
	}
	o.SetScratch(dir)
	r := o.Regs()
	if r.CS != 0x110 || r.IP != 0x284d || r.DS != 0x1e88 || r.SS != 0x1e88 || r.SP < 64 || r.BP < 32 || r.SP != r.BP-18 || o.Word(oracle.Far(r.SS, r.BP+2)) != 0xbc7 || o.Word(oracle.Far(r.SS, r.BP+4)) != 0x110 {
		return nil, nil, errors.New("monthly serializer source frame")
	}
	if !bytes.Equal(code[0x84c0:0x8d38], o.Bytes(oracle.Far(0x110, 0x84c0), 0x878)) {
		return nil, nil, errors.New("monthly serializer bytes")
	}
	originalRows := append([]byte{}, o.Bytes(oracle.Far(0x1e88, 0x54a), 24)...)
	swordOnHostInstruction(o, oracle.Far(0x110, 0x284d), func(m *dg.Machine) (bool, error) {
		c := m.CPU
		sp := c.R[dg.SP] - 4
		m.Write16(0x1e880+uint32(sp), 0x284d)
		m.Write16(0x1e880+uint32(sp)+2, 0x110)
		c.R[dg.SP] = sp
		c.IP = 0x84c0
		c.Cycles++
		return true, nil
	})
	if e = o.RunUntil(oracle.At(oracle.Far(0x110, 0x8d31)), oracle.Budget(3000000)); e != nil {
		return nil, nil, e
	}
	native, e := pairRead(filepath.Join(dir, "gamedata.ay"), 2987)
	if e != nil {
		return nil, nil, e
	}
	if !bytes.Equal(native, o.Bytes(oracle.Far(0x9e00, 0), 2987)) || !bytes.Equal(originalRows, o.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
		return nil, nil, errors.New("monthly serializer buffer/army")
	}
	files, e := readNativeCheckpointMaps(dir)
	if e != nil {
		return nil, nil, e
	}
	name := o.Bytes(oracle.Far(0x1e88, 0x8e52), 16)
	if i := bytes.IndexByte(name, 0); i >= 0 {
		name = name[:i]
	}
	n := strings.ToLower(string(name))
	if !bytes.Equal(files[n], o.Bytes(oracle.Far(0x9c00, 0), 5761)) {
		return nil, nil, errors.New("monthly serializer current map")
	}
	writes := map[string]int{}
	closed := map[string]bool{}
	for _, w := range o.Wrote() {
		writes[strings.ToLower(filepath.Base(w.Name))] += w.N
	}
	for _, op := range o.FileOps() {
		if op.Failed {
			return nil, nil, errors.New("monthly serializer DOS failure")
		}
		if op.Op == "close" {
			closed[strings.ToLower(filepath.Base(op.Name))] = true
		}
	}
	if writes["gamedata.ay"] != 2987 || writes[n] != 5761 || !closed["gamedata.ay"] || !closed[n] {
		return nil, nil, errors.New("monthly serializer incomplete writes")
	}
	return native, files, nil
}
