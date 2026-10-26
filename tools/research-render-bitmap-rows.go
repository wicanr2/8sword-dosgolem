//go:build ignore

// 047 DRAFT. Native planar row copies at the atomic original REP boundary.
package eightsword

import (
	"crypto/sha256"
	"fmt"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

type sourceBitmapRowLayout struct {
	Entry oracle.Addr
	Planes int
	Table uint16
	CodeSHA string
}

func pamBitmapRows(seg uint16) []sourceBitmapRowLayout {
	return []sourceBitmapRowLayout{
		{oracle.Addr{Seg:seg,Off:0x99c},4,6,"a2f457e4ad98813eb3b8e2d727e71074b612c52b473cc3153ce42f915c1b70c8"},
		{oracle.Addr{Seg:seg,Off:0x76f},5,6,"49285f927aa83c57fce4d990102e6fda59e61581d8b571bb8c8d9ebc5e255419"},
	}
}

func introBitmapRows() []sourceBitmapRowLayout {
	return []sourceBitmapRowLayout{{oracle.Far(0,0x576a),4,4,"88d6cfe05ddb19b00bd42cb4857a95cbcf9bdf764320ea21e503b9f202a947d8"}}
}

func endingBitmapRows() []sourceBitmapRowLayout {
	return []sourceBitmapRowLayout{
		{oracle.Addr{Seg:0x393,Off:0x996},4,0,"603833bfa266acbc8f7a3c8ecf3a30e9f15b5242211367534a7ca1145bb4cfad"},
		{oracle.Addr{Seg:0x393,Off:0x769},5,0,"285723c100da394f2c125b5a1a293c0b24d4f18a8cf2276937ef4a47db4124bc"},
	}
}

func (l sourceBitmapRowLayout) rep() oracle.Addr {return oracle.Addr{Seg:l.Entry.Seg,Off:l.Entry.Off+0x60}}

func sourceBitmapRowInstruction(m *dg.Machine,l sourceBitmapRowLayout)(bool,error) {
	if !m.CycleClock || !m.CPU.DOSBoxCost || m.VideoMode()!=0x0e || m.CPU.Flags&dg.DF!=0 {return false,nil}
	if uint32(m.CPU.Seg[dg.CS])*16+uint32(m.CPU.IP)!=l.rep().Linear() {return false,nil}
	size:=uint32(212);if l.Planes==5 {size=230}
	if l.Entry.Linear()+size>0xa0000 || fmt.Sprintf("%x",sha256.Sum256(m.Mem[l.Entry.Linear():l.Entry.Linear()+size]))!=l.CodeSHA {return false,nil}
	gc,seq,_:=m.VGAState()
	if gc[1]&15!=0 || gc[3]&31!=0 || gc[5]&3!=0 || gc[8]!=255 {return false,nil}
	es,ds:=m.CPU.Seg[dg.ES],m.CPU.Seg[dg.DS]
	if es!=0xa000 && es!=0xa400 {return false,nil}
	count,di,si:=m.CPU.R[dg.CX],m.CPU.R[dg.DI],m.CPU.R[dg.SI]
	if count<1 || count>80 || uint32(si)+uint32(count)>65536 || uint32(di)+uint32(count)>16000 {return false,nil}
	from:=uint32(ds)*16+uint32(si)
	if from+uint32(count)>0xa0000 {return false,nil}
	plane:=-1
	for i:=0;i<4;i++ {if seq[2]&15==1<<uint(i) {plane=i}}
	if plane<0 {return false,nil}
	to:=uint32(es-0xa000)*16+uint32(di)
	copy(m.EGAPlane(plane)[to:to+uint32(count)],m.Mem[from:from+uint32(count)])
	m.CPU.R[dg.SI]+=count;m.CPU.R[dg.DI]+=count;m.CPU.R[dg.CX]=0;m.CPU.IP+=2
	m.CPU.Cycles+=1+uint64(count)
	return true,nil
}
