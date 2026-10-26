//go:build ignore

// 047 DRAFT. Forty source pixels per reveal tile, drawn by native Go.
package eightsword

import (
	"crypto/sha256"
	"fmt"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

const sourceRevealCodeSHA = "88798f6778b00b0e11a9d49a6035f03f85a0eb5c499593dc4ef1b2f77c6bc537"

type sourceRevealPixel struct { At int; Color byte }
type sourceRevealTile struct {
	Pixels []sourceRevealPixel
	Steps uint64
	registers [8]uint16
	segments [4]uint16
	flags uint16
	stack []uint16
}

func prepareSourceRevealTile(m *dg.Machine,b oracle.HostWorkLimits)(*sourceRevealTile,string) {
	if !m.CycleClock || !m.CPU.DOSBoxCost || m.VideoMode()!=0x13 {return nil,"clock-or-mode"}
	r,s:=m.CPU.R,m.CPU.Seg
	if uint32(s[dg.CS])*16+uint32(m.CPU.IP)!=0xa400 || s[dg.CS]!=0xa3d {return nil,"entry"}
	if fmt.Sprintf("%x",sha256.Sum256(m.Mem[0xa3d0:0xa49f]))!=sourceRevealCodeSHA {return nil,"code"}
	if fmt.Sprintf("%x",sha256.Sum256(m.Mem[0xa633:0xa633+3200]))!=preludeTableSHA {return nil,"order-table"}
	count:=int(r[dg.CX]);sp,ss:=uint32(r[dg.SP]),uint32(s[dg.SS])*16
	if count<1 || count>1600 || sp<32 || sp+16>65535 || ss+sp+16>0xa0000 || uint32(r[dg.BP])!=sp+16 {return nil,"stack-or-count"}
	if m.Read16(0xa49f)!=0x6000 || m.Read16(0xa4a1)!=768 || fmt.Sprintf("%x",sha256.Sum256(m.Mem[0x60000:0x60000+64768]))!=preludeSourceSHA {return nil,"source"}
	lo,hi:=ss+sp-32,ss+sp+18
	overlap:=func(a,z uint32)bool{return a<hi && lo<z}
	if overlap(0xa3d0,0xa633+3200) || overlap(0x60000,0x60000+64768) {return nil,"stack-alias"}
	steps:=uint64(467+40*41)
	available:=m.HostWorkBudget(b.Steps,b.Cycles)
	if steps>available.Steps || steps>available.Cycles {return nil,"quota-or-event"}
	v:=int(m.Read16(0xa633+uint32((count-1)*2)))
	if v>=1600 {return nil,"order-index"}
	x,y:=v%40,v/40
	pixels:=make([]sourceRevealPixel,0,40)
	for col:=0;col<8;col++ {for row:=0;row<5;row++ {
		xx,yy:=x+col*40,y+row*40
		if m.Read16(0xa4a3+uint32(yy*2))!=uint16(yy*320) {return nil,"row-table"}
		at:=yy*320+xx
		pixels=append(pixels,sourceRevealPixel{at,m.Mem[0x60300+at]})
	}}
	xlast,ylast:=uint16(x+280),uint16(y+160)
	stack:=[]uint16{uint16(y-40),ylast+1,xlast+1,ylast,xlast,s[dg.CS],0x5f,r[dg.BP],ylast,40,r[dg.CX],xlast,280,160,s[dg.DS],s[dg.ES]}
	return &sourceRevealTile{pixels,steps,r,s,m.CPU.Flags,stack},""
}

func (p *sourceRevealTile) commit(m *dg.Machine,b oracle.HostWorkLimits)error {
	ss,sp:=uint32(p.segments[dg.SS])*16,uint32(p.registers[dg.SP])
	for i,v:=range p.stack {m.Write16(ss+sp-uint32((i+1)*2),v)}
	for _,pixel:=range p.Pixels {m.Mem[0xa0000+pixel.At]=pixel.Color}
	m.CPU.R,m.CPU.Seg=p.registers,p.segments
	first:=p.Pixels[0].At
	m.CPU.R[dg.AX]=uint16(first/320-40)
	m.CPU.R[dg.BX]=40;m.CPU.R[dg.CX]--;m.CPU.R[dg.DX]=uint16(first%320+280)
	m.CPU.R[dg.SI]=320;m.CPU.R[dg.DI]=200
	m.CPU.Flags=p.flags &^ uint16(dg.CF|dg.PF|dg.AF|dg.ZF|dg.SF|dg.OF) | dg.PF | dg.ZF
	m.CPU.IP=0x30;if m.CPU.R[dg.CX]==0 {m.CPU.IP=0x77}
	return m.CommitHostWork(p.Steps,p.Steps,b.Steps,b.Cycles)
}

type sourceRevealPoint struct {
	Pixel sourceRevealPixel
	registers [8]uint16
	segments [4]uint16
	flags uint16
}

func prepareSourceRevealPoint(m *dg.Machine,b oracle.HostWorkLimits)(*sourceRevealPoint,string) {
	if !m.CycleClock || !m.CPU.DOSBoxCost || m.VideoMode()!=0x13 {return nil,"clock-or-mode"}
	r,s:=m.CPU.R,m.CPU.Seg
	if s[dg.CS]!=0xa3d || m.CPU.IP!=0x81 || fmt.Sprintf("%x",sha256.Sum256(m.Mem[0xa3d0:0xa49f]))!=sourceRevealCodeSHA {return nil,"entry-code"}
	ss,sp:=uint32(s[dg.SS])*16,uint32(r[dg.SP])
	if sp<18 || sp+12>65536 || ss+sp+12>0xa0000 {return nil,"stack-bounds"}
	arg:=func(i uint32)uint16{return m.Read16(ss+sp+4+i*2)}
	x,y:=int(arg(0)),int(arg(1))
	if x>=320 || y>=200 || arg(2)!=uint16(x) || arg(3)!=uint16(y) || m.Read16(0xa4a3+uint32(y*2))!=uint16(y*320) {return nil,"geometry"}
	if m.Read16(0xa49f)!=0x6000 || m.Read16(0xa4a1)!=768 || fmt.Sprintf("%x",sha256.Sum256(m.Mem[0x60000:0x60000+64768]))!=preludeSourceSHA {return nil,"source"}
	lo,hi:=ss+sp-18,ss+sp+12;overlap:=func(a,z uint32)bool{return a<hi && lo<z}
	if overlap(0xa3d0,0xa633+3200) || overlap(0x60000,0x60000+64768) {return nil,"stack-alias"}
	available:=m.HostWorkBudget(b.Steps,b.Cycles)
	if available.Steps<40 || available.Cycles<40 {return nil,"quota-or-event"}
	at:=y*320+x
	return &sourceRevealPoint{sourceRevealPixel{at,m.Mem[0x60300+at]},r,s,m.CPU.Flags},""
}

func (p *sourceRevealPoint) commit(m *dg.Machine,b oracle.HostWorkLimits)error {
	ss,sp:=uint32(p.segments[dg.SS])*16,uint32(p.registers[dg.SP])
	stack:=[]uint16{p.registers[dg.BP],p.registers[dg.AX],p.registers[dg.BX],p.registers[dg.CX],p.registers[dg.DX],p.registers[dg.SI],p.registers[dg.DI],p.segments[dg.DS],p.segments[dg.ES]}
	for i,v:=range stack {m.Write16(ss+sp-uint32((i+1)*2),v)}
	m.Write16(ss+sp+8,uint16(p.Pixel.At%320+1));m.Write16(ss+sp+10,uint16(p.Pixel.At/320+1))
	m.Mem[0xa0000+p.Pixel.At]=p.Pixel.Color
	m.CPU.R,m.CPU.Seg=p.registers,p.segments
	m.CPU.Flags=p.flags &^ uint16(dg.CF|dg.PF|dg.AF|dg.ZF|dg.SF|dg.OF) | dg.PF | dg.ZF
	m.CPU.IP=0xce
	return m.CommitHostWork(40,40,b.Steps,b.Cycles)
}

// Event-adjacent compatibility store. The native source renderer receives the
// same typed pixel; the x86 video-store instruction is never executed.
func sourceRevealPixelInstruction(m *dg.Machine)(sourceRevealPixel,bool) {
	r,s:=m.CPU.R,m.CPU.Seg
	if m.CPU.Halted || !m.CycleClock || !m.CPU.DOSBoxCost || m.VideoMode()!=0x13 || s[dg.CS]!=0xa3d || m.CPU.IP!=0xb6 || s[dg.ES]!=0xa000 || s[dg.DS]!=0x6000 || r[dg.BX]!=768 || r[dg.SI]>=64000 {return sourceRevealPixel{},false}
	if fmt.Sprintf("%x",sha256.Sum256(m.Mem[0xa3d0:0xa49f]))!=sourceRevealCodeSHA || byte(r[dg.AX])!=m.Mem[0x60300+uint32(r[dg.SI])] {return sourceRevealPixel{},false}
	pixel:=sourceRevealPixel{int(r[dg.SI]),byte(r[dg.AX])}
	m.Mem[0xa0000+pixel.At]=pixel.Color;m.CPU.IP+=3;m.CPU.Cycles++
	return pixel,true
}

// Typed scene submission: source pixels/order, never a rendered VGA frame.
func (p *sourceIntroAdapter) submitRevealSpan(pixels []sourceRevealPixel) {
	if p.retired || p.scene.Mode!=0x13 || p.written+len(pixels)>len(p.order) {p.reject("native reveal span lifecycle")}
	if pending:=p.pixelPending;pending!=nil {
		if len(pixels)!=1 || pending.At!=pixels[0].At || byte(pending.AX)!=pixels[0].Color {p.reject("native reveal pending pixel differs")}
	}
	for i,pixel:=range pixels {
		if pixel.At!=int(p.order[p.written+i]) || pixel.Color!=p.source[pixel.At] {p.reject("native reveal span source/order")}
	}
	for _,pixel:=range pixels {p.write(pixel.At,pixel.Color);p.scene.Reveal[pixel.At]=true;p.scene.Revision++;p.written++}
	p.pixelPending=nil
	p.counts["reveal-pixels"]+=uint64(len(pixels));p.counts["reveal-go-spans"]++
}

func (e *Engine) sourceRevealInstall() func() {
	bound:=false
	return func(){
		if bound || !e.sourceEnabled || !e.HD || e.PAMLoaded || e.renderFault!=nil {return}
		if fmt.Sprintf("%x",sha256.Sum256(e.Oracle.Bytes(oracle.Far(0,0xa3d0),0xcf)))!=sourceRevealCodeSHA {return}
		bound=true
		e.Oracle.OnHostCall(oracle.Far(0,0xa400),func(_ *oracle.Oracle,m *dg.Machine,b oracle.HostWorkLimits)(bool,error){
			if e.PAMLoaded || !e.sourceEnabled || !e.HD || e.renderFault!=nil || e.sourceRevealSubmit==nil {return false,nil}
			p,_:=prepareSourceRevealTile(m,b);if p==nil {return false,nil}
			if err:=p.commit(m,b);err!=nil {return false,err}
			e.sourceGuardCall(func(){e.sourceRevealSubmit(p.Pixels)})
			e.sourceRevealTiles++;e.sourceRevealPixels+=uint64(len(p.Pixels))
			return true,nil
		})
		e.Oracle.OnHostCall(oracle.Far(0,0xa451),func(_ *oracle.Oracle,m *dg.Machine,b oracle.HostWorkLimits)(bool,error){
			if e.PAMLoaded || !e.sourceEnabled || !e.HD || e.renderFault!=nil || e.sourceRevealSubmit==nil {return false,nil}
			p,_:=prepareSourceRevealPoint(m,b);if p==nil {return false,nil}
			if err:=p.commit(m,b);err!=nil {return false,err}
			e.sourceGuardCall(func(){e.sourceRevealSubmit([]sourceRevealPixel{p.Pixel})})
			e.sourceRevealPoints++;e.sourceRevealPixels++
			return true,nil
		})
		e.Oracle.OnHostInstruction(oracle.Far(0,0xa486),func(m *dg.Machine)(bool,error){
			if e.PAMLoaded || !e.sourceEnabled || !e.HD || e.renderFault!=nil || e.sourceRevealSubmit==nil {return false,nil}
			pixel,done:=sourceRevealPixelInstruction(m);if !done {return false,nil}
			e.sourceGuardCall(func(){e.sourceRevealSubmit([]sourceRevealPixel{pixel})})
			e.sourceRevealAtomic++;e.sourceRevealPixels++
			return true,nil
		})
	}
}
