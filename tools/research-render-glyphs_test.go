//go:build ignore

package eightsword

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"testing"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

type sourceGlyphEvent struct { Read *dg.VideoRead; Write *dg.VideoWrite }

func sourceGlyphFixture(t *testing.T, raw []byte, intro bool, l sourceGlyphLayout, code,dest uint16,fg,bg byte) *dg.Machine {
	t.Helper()
	m:=dg.New(); m.SetVideoMode(0x0e); m.SetDOSBoxCycles(3000); m.VGAFrameEvery=0
	hdr:=int(binary.LittleEndian.Uint16(raw[8:]))*16
	copy(m.Mem[0x1100:],raw[hdr:])
	count,table:=int(binary.LittleEndian.Uint16(raw[6:])),int(binary.LittleEndian.Uint16(raw[24:]))
	for i:=0;i<count;i++ {
		p:=table+4*i
		at:=uint32(0x1100)+uint32(binary.LittleEndian.Uint16(raw[p:]))+uint32(binary.LittleEndian.Uint16(raw[p+2:]))*16
		m.Write16(at,m.Read16(at)+0x110)
	}
	cs,ds:=uint16(0x14d2),uint16(0x1e88)
	if l.CJK { cs=0xaa8 }
	if intro { cs=0x4dd; ds=0xb31; if l.CJK { cs=0x231 } }
	// PAM builds its shared row table during startup. The controlled call
	// supplies that documented input; the primitive never initializes it.
	if !intro { for row:=0;row<200;row++ { m.Write16(0x14d20+6+uint32(row*2),uint16(row*80)) } }
	m.Write16(uint32(ds)*16+uint32(l.Mode),1)
	m.Write16(uint32(ds)*16+uint32(l.Destination),dest)
	m.Mem[uint32(ds)*16+uint32(l.Foreground)]=fg
	m.Mem[uint32(ds)*16+uint32(l.Foreground)+1]=bg
	m.CPU.R=[8]uint16{0x1234,0x2345,0x3456,0x4567,0xff00,0x6789,0x789a,0x89ab}
	m.CPU.Seg=[4]uint16{0x7000,cs,0x9000,ds}
	m.CPU.IP=uint16(l.Entry.Linear()-uint32(cs)*16); m.CPU.Flags=0x202
	x,y:=uint16(0),uint16(0)
	if dest==0xa400 { x=79; if l.CJK {x--};y=185 }
	for i:=0;i<32;i++ {m.Mem[0x9fee0+i]=0xc7+byte(i)}
	for i,v:=range []uint16{0xfff0,0x110,code,x,y} {m.Write16(0x9ff00+uint32(i*2),v)}
	for p:=0;p<4;p++ {for off:=range m.EGAPlane(p) {m.EGAPlane(p)[off]=byte(off*7+p*31)}}
	m.Out8(0x3ce,4);m.Out8(0x3cf,2);m.Read8(0xa0000+77)
	return m
}

func sourceGlyphWatch(m *dg.Machine,out *[]sourceGlyphEvent) {
	m.ObserveVideoReads(func(v dg.VideoRead){*out=append(*out,sourceGlyphEvent{Read:&v})})
	m.ObserveVideoWrites(func(v dg.VideoWrite){*out=append(*out,sourceGlyphEvent{Write:&v})})
}

func sourceGlyphState(t *testing.T,a,b *dg.Machine,ae,be []sourceGlyphEvent) {
	t.Helper();var x,y bytes.Buffer
	if err:=a.SaveState(&x);err!=nil {t.Fatal(err)}
	if err:=b.SaveState(&y);err!=nil {t.Fatal(err)}
	if !bytes.Equal(x.Bytes(),y.Bytes()) {t.Fatalf("full state differs steps%d/%d cycles%d/%d IP%x/%x flags%x/%x regs%v/%v",a.Steps,b.Steps,a.CPU.Cycles,b.CPU.Cycles,a.CPU.IP,b.CPU.IP,a.CPU.Flags,b.CPU.Flags,a.CPU.R,b.CPU.R)}
	if !reflect.DeepEqual(ae,be) {t.Fatalf("ordered events differ lengths%d/%d",len(ae),len(be))}
}

func TestResearchSourceGlyphOracle(t *testing.T) {
	project:=os.Getenv("EIGHTSWORD_GLYPH_PROJECT")
	if project=="" {t.Skip("需唯讀專案與原版來源")}
	for _,phase:=range []string{"pam","intro"} {
		path:="workplace/intake-20261023/sources/game/8sword/PAM.AY"
		want:="83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
		layouts:=pamGlyphLayouts(&Tracker{fontSeg:0xaa8,stringSeg:0x14d2})
		if phase=="intro" {path="workplace/probe-20261023/music-first/intro-events-r1/PREDELLA-runtime-analysis.exe";want="28dbc38d4ef65326ee281b684bf3a7a304ea41c00bfc00410076bce31b1b247a";layouts=introGlyphLayouts()}
		raw,err:=os.ReadFile(filepath.Join(project,path));if err!=nil {t.Fatal(err)}
		if fmt.Sprintf("%x",sha256.Sum256(raw))!=want {t.Fatal("source identity")}
		for _,l:=range layouts {
			codes:=[]uint16{0,90,uint16((l.MaxIndex-1)*30)}
			if !l.CJK { codes=[]uint16{32,65,255} }
			for _,code:=range codes {for _,dest:=range []uint16{0xa000,0xa400} {for variant,colors:=range [][2]byte{{14,255},{0,0},{15,4}} {
				t.Run(fmt.Sprintf("%s/cjk%t/code%d/page%x/colors%d",phase,l.CJK,code,dest,variant),func(t *testing.T){
					a,h:=sourceGlyphFixture(t,raw,phase=="intro",l,code,dest,colors[0],colors[1]),sourceGlyphFixture(t,raw,phase=="intro",l,code,dest,colors[0],colors[1])
					var ae,he []sourceGlyphEvent;sourceGlyphWatch(a,&ae);sourceGlyphWatch(h,&he)
					rows,skipped:=0,uint64(0)
					ret:=l.Entry.Linear()+0xff; if l.CJK {ret=l.Entry.Linear()+0x15f}
					for uint32(a.CPU.Seg[dg.CS])*16+uint32(a.CPU.IP)!=ret && a.Steps<10000 {
						if uint32(a.CPU.Seg[dg.CS])*16+uint32(a.CPU.IP)==l.row().Linear() {
							var before,after bytes.Buffer;h.SaveState(&before)
							if p,_:=prepareSourceGlyph(h,oracle.HostWorkLimits{Steps:1,Cycles:1},l);p!=nil {t.Fatal("short quota accepted")}
							h.SaveState(&after); if !bytes.Equal(before.Bytes(),after.Bytes()){t.Fatal("rejection mutated state")}
							limit:=oracle.HostWorkLimits{Steps:100000,Cycles:100000}
							if variant!=0 {limit.Steps=uint64(variant*39);if l.CJK {limit.Steps=uint64(variant*85)}}
							p,why:=prepareSourceGlyph(h,limit,l);if p==nil {t.Fatal(why)}
							stop:=a.Steps+p.Steps
							for a.Steps<stop {if err:=a.Step();err!=nil {t.Fatal(err)}}
							if err:=p.commit(h,limit);err!=nil {t.Fatal(err)}
							sourceGlyphState(t,a,h,ae,he);rows+=p.Rows;skipped+=p.Steps;continue
						}
						if err:=a.Step();err!=nil {t.Fatal(err)};if err:=h.Step();err!=nil {t.Fatal(err)}
					}
					if rows!=15 || skipped==0 {t.Fatal("glyph rows absent",rows,skipped)}
					if err:=a.Step();err!=nil {t.Fatal(err)};if err:=h.Step();err!=nil {t.Fatal(err)}
					sourceGlyphState(t,a,h,ae,he)
				})
			}}}
		}
	}
}
