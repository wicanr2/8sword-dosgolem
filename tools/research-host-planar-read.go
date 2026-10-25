//go:build ignore

package machine

// ReadHostPlanar performs the native latch-loading read at an explicit legacy
// site. It shares Read8's preparation and observation order, without an opcode
// or an invented CPU OpAddr. The caller validates and budgets the whole prefix.
func (m *Machine) ReadHostPlanar(r VideoRead) uint8 {
	if !m.planarOn || r.Offset >= vgaHi-vgaLo {
		panic("research host planar read outside admitted VGA window")
	}
	if m.preparePlanarRead != nil {
		m.preparePlanarRead(r.Offset)
	}
	if m.onVideoRead != nil {
		m.onVideoRead(r)
	}
	return m.VGA.Read(r.Offset)
}
