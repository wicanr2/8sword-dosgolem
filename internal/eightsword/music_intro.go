package eightsword

import "github.com/wicanr2/dosgolem/oracle"

const introProgram = "PREDELLA.EXE"

// Runtime linear addresses from the normal unpacked PREDELLA capture.
// These are not offsets in the packed source or PAM IDA database.
var introCodeWindows = []struct {
	address uint16
	length  int
	sha     string
}{
	{0x1ac2, 170, "f57c76eabc6f27f52b5d9287a8cb27264e83c5f9f45c57ef433a0e97185a83cd"},
	{0x7074, 95, "7b2772af1e9eaed51cdf9d4cf9c9fb908f9ba10d731ac52c6fe1e7b633483542"},
	{0x93c6, 14, "465e8a09c4d7c8791ae5f90835c7c3ec4310bb780366483508222fe654031bc7"},
}

func (m *Music) introLive() bool {
	if m.introRetired {
		return false
	}
	for _, overlay := range m.o.Overlays() {
		if overlay.Name == "pam.ay" || overlay.Name == "PAM.AY" {
			m.retireIntro(overlay.Steps)
			return false
		}
	}
	return true
}

func (m *Music) retireIntro(step uint64) {
	if m.introRetired {
		return
	}
	m.introRetired = true
	m.introEndStep = step
	if m.introBound {
		m.record(MusicEvent{"handoff", 0, m.o.Steps(), m.o.Cycles(), true, introProgram})
	}
}

func (m *Music) bindIntro() {
	if !m.introLive() || m.introBound {
		return
	}
	// Decompression may span multiple Advance calls. Wait for all immutable
	// windows, rather than treating partially unpacked bytes as a version error.
	for _, window := range introCodeWindows {
		if hash(m.o.Bytes(oracle.Far(0, window.address), window.length)) != window.sha {
			return
		}
	}
	m.introBound = true
	m.introBoundCycle = m.o.Cycles()
	m.o.OnCall(oracle.Far(0, 0x1ac2), func(o *oracle.Oracle) {
		if !m.introLive() {
			return
		}
		ds := o.Regs().DS
		m.introRequestValid = ds == 0x0b31 && o.Word(oracle.Far(ds, 0x08e4)) == 1 && o.Word(oracle.Far(ds, 0x08e2)) == 1
		m.record(MusicEvent{"request", 1, o.Steps(), o.Cycles(), m.introRequestValid, introProgram})
	})
	m.o.OnCall(oracle.Far(0, 0x1b64), func(o *oracle.Oracle) {
		if !m.introLive() {
			return
		}
		source := musicSources[1]
		valid := m.introRequestValid && o.Byte(oracle.Far(0x0b2c, 5)) == 1 &&
			hash(o.Bytes(oracle.Far(0x9000, 0), source.ScoreBytes)) == source.ScoreSHA &&
			hash(o.Bytes(oracle.Far(0x9600, 0), source.BankBytes)) == source.BankSHA
		m.introRequestValid = false
		reason := introProgram
		if !valid {
			reason += "：片頭播放條件或音樂來源不符"
		}
		m.record(MusicEvent{"start", 1, o.Steps(), o.Cycles(), valid, reason})
	})
	m.o.OnCall(oracle.Far(0, 0x7074), func(o *oracle.Oracle) {
		if m.introLive() {
			m.record(MusicEvent{"stop", 0, o.Steps(), o.Cycles(), true, introProgram})
		}
	})
	if len(m.tracks) > 0 {
		m.o.OnCall(oracle.Far(0, 0x93cf), func(o *oracle.Oracle) {
			if !m.introLive() {
				return
			}
			r := o.Regs()
			if r.DX == 0x389 {
				m.seenOPL[o.Steps()+1] = uint8(r.AX)
			}
		})
	}
}

func (m *Music) observedWrite(w oracle.OPLWrite) bool {
	intro := m.introBound && w.Cycles >= m.introBoundCycle &&
		(!m.introRetired || w.Step < m.introEndStep)
	pam := m.bound && w.Cycles >= m.boundCycle
	return intro || pam
}
