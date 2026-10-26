//go:build ignore

// 047 DRAFT. The opening uses the same six-block masked source contract.
package eightsword

import (
	"crypto/sha256"
	"fmt"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

const introMaskedCodeSHA = "c7c0315ee13ef29e26ea2b35098c3cae6453e4f4e5fcd34da6cee81ae57c4dd3"

func (e *Engine) sourceIntroMaskedInstall() func() {
	bound:=false
	return func(){
		if bound || !e.sourceEnabled || !e.HD || e.PAMLoaded || e.renderFault!=nil {return}
		if fmt.Sprintf("%x",sha256.Sum256(e.Oracle.Bytes(oracle.Far(0,0x52c0),0x134)))!=introMaskedCodeSHA {return}
		bound=true
		for _,at:=range []uint16{0x52c0,0x533d} {
			e.Oracle.OnHostCall(oracle.Far(0,at),func(_ *oracle.Oracle,m *dg.Machine,b oracle.HostWorkLimits)(bool,error){
				if !e.sourceEnabled || !e.HD || e.PAMLoaded || e.renderFault!=nil {return false,nil}
				p,_:=runtimePlanarPrepare(m,b);if p==nil {return false,nil}
				if err:=p.commit(m,b);err!=nil {return false,err}
				e.sourceDirectCalls++;e.sourceIntroMaskCalls++
				return true,nil
			})
		}
	}
}
