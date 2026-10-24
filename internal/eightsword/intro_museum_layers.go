package eightsword

import (
	"bytes"
	"image"
	"image/color"
	"image/draw"
)

type museumPlacedActor struct {
	sprite *image.NRGBA
	rows   []uint32
	page   uint32
	offset int
}

func (m *IntroMuseum) assignHDActor(p *museumPage, t museumTX) {
	p.maskedCount++
	p.actor = nil
	if p.maskedCount != 1 {
		return
	}
	sprite := m.actorSprites[museumSHA(t.record.raw)]
	if sprite == nil {
		return
	}
	if len(t.rows) != 46 {
		m.ActorRejected++
		return
	}
	for _, row := range t.rows {
		if row < t.page || row-t.page >= 16000 || (row-t.page+9)/80 >= 150 || (row-t.page)/80 < 50 {
			m.ActorRejected++
			return
		}
	}
	p.actor = &museumPlacedActor{sprite: sprite, rows: append([]uint32(nil), t.rows...), page: t.page, offset: t.record.offset}
	m.ActorAssignments++
}

// Sprite columns follow physical VGA byte rows, including wrapping to the next row.
func (m *IntroMuseum) paintHDActor(band *image.RGBA, a *museumPlacedActor) {
	for y := 0; y < 276; y++ {
		row := a.rows[y/6] - a.page
		for x := 0; x < 240; x++ {
			source := a.sprite.NRGBAAt(x, y)
			if source.A == 0 {
				continue
			}
			address := row + uint32(x/24)
			dx, dy := int(address%80)*24+x%24, (int(address/80)-20)*6+y%6
			if dx < 0 || dx >= 1920 || dy < 0 || dy >= 780 {
				m.fail("museum actor escaped artwork band")
				return
			}
			dest := band.RGBAAt(dx, dy)
			alpha := uint32(source.A)
			inverse := 255 - alpha
			mix := func(s, d uint8) uint8 { return uint8((uint32(s)*alpha + uint32(d)*inverse + 127) / 255) }
			band.SetRGBA(dx, dy, color.RGBA{mix(source.R, dest.R), mix(source.G, dest.G), mix(source.B, dest.B), 255})
		}
	}
}

type museumScene struct {
	portrait, beam *museumPlacedRecord
}
type museumPlacedRecord struct {
	record *museumRecord
	rows   []uint32
	page   uint32
}

func cloneMuseumScene(s *museumScene) *museumScene {
	if s == nil {
		return nil
	}
	c := *s
	return &c // Placements and row slices are immutable after publication.
}
func (m *IntroMuseum) sceneSupported(p *museumPage) bool {
	return p != nil && (p.role == "left" || (p.role == "right" && len(m.sceneArts) == 3))
}
func (m *IntroMuseum) commitMuseumOpaque(t museumTX) {
	r := t.record
	if r.role == "portrait" {
		p := m.pages[t.page]
		if p == nil || p.role != "right" || p.maskedCount != 0 || p.scene == nil || len(t.rows) != 100 || t.rows[0] != t.page+1614 {
			m.fail("portrait source geometry or backing differs")
			return
		}
		p.scene.portrait = &museumPlacedRecord{r, append([]uint32(nil), t.rows...), t.page}
		return
	}
	if r.w != 80 || r.h != 100 || len(t.rows) != 100 || t.rows[0] != t.page+4000 {
		m.fail("background placement differs")
		return
	}
	if previous := m.pages[t.page]; previous != nil && previous.scene != nil && previous.scene.portrait != nil {
		m.fail("portrait backing not retired before normal background")
		return
	}
	m.pages[t.page] = &museumPage{role: r.role, ink: image.NewRGBA(image.Rect(0, 0, 640, 200)), scene: &museumScene{}}
}
func (m *IntroMuseum) assignMuseumBeam(p *museumPage, t museumTX) {
	if p.role != "right" || p.scene == nil || t.record.h != 50 || len(t.rows) != 50 {
		m.fail("beam backing differs")
		return
	}
	if old := p.scene.beam; old != nil {
		if len(old.rows) != len(t.rows) {
			m.fail("beam row count differs")
			return
		}
		for i, row := range old.rows {
			if row != t.rows[i] {
				m.fail("beam location changed without known redraw")
				return
			}
		}
		if !bytes.Equal(old.record.raw[4+5*1200:], t.record.raw[4+5*1200:]) {
			m.fail("beam coverage changed")
			return
		}
	}
	p.scene.beam = &museumPlacedRecord{t.record, append([]uint32(nil), t.rows...), t.page}
}
func (m *IntroMuseum) noteMuseumScene(p *museumPage) {
	m.Stage = p.role
	if p.role == "right" {
		m.RightComposed++
	}
	if p.scene != nil && p.scene.portrait != nil {
		m.Stage = "portrait"
		m.PortraitComposed++
	}
	if p.scene != nil && p.scene.beam != nil {
		m.Stage = "beam"
		m.BeamComposed++
	}
}
func (m *IntroMuseum) renderBand(p *museumPage) *image.RGBA {
	band := image.NewRGBA(image.Rect(0, 0, 1920, 780))
	var art image.Image = m.art
	if p.role == "right" {
		art = m.sceneArts["right:a-purple"]
	}

	draw.Draw(band, image.Rect(0, 180, 1920, 780), art, image.Point{}, draw.Src)
	if p.scene != nil && p.scene.portrait != nil {
		var portrait image.Image = m.sceneArts["portrait:all"]

		draw.Draw(band, image.Rect(336, 0, 1608, 600), portrait, image.Point{}, draw.Src)
	}
	if p.actor != nil {
		m.paintHDActor(band, p.actor)
		if p.scene != nil && p.scene.beam != nil {
			m.paintMuseumBeam(band, p.scene.beam)
		}
		return band
	}
	for y := 50; y < 150; y++ {
		for x := 0; x < 640; x++ {
			c := p.ink.RGBAAt(x, y)
			if c.A == 0 {
				continue
			}
			for yy := (y - 20) * 6; yy < (y-19)*6; yy++ {
				for xx := x * 3; xx < (x+1)*3; xx++ {
					band.SetRGBA(xx, yy, c)
				}
			}
		}
	}
	return band
}
func (m *IntroMuseum) paintMuseumBeam(band *image.RGBA, a *museumPlacedRecord) {
	sprite := m.sceneArts["beam:all"]
	if sprite == nil {
		return
	}
	var tint [3]uint8
	r, n := a.record, a.record.w*a.record.h
	for i := 0; i < n; i++ {
		for bit := 0; bit < 8; bit++ {
			if r.raw[4+5*n+i]&(128>>bit) == 0 {
				continue
			}
			index := byte(0)
			for plane := 0; plane < 4; plane++ {
				index |= ((r.raw[4+plane*n+i] >> uint(7-bit)) & 1) << uint(plane)
			}
			c := m.palette[index]
			if int(c[0])+int(c[1])+int(c[2]) > int(tint[0])+int(tint[1])+int(tint[2]) {
				tint = c
			}
		}
	}
	for y := 0; y < 300; y++ {
		for x := 0; x < 576; x++ {
			c := sprite.NRGBAAt(x, y)
			if c.A == 0 {
				continue
			}
			address := a.rows[y/6] - a.page + uint32(x/24)
			dx, dy := int(address%80)*24+x%24, (int(address/80)-20)*6+y%6
			if dx < 0 || dx >= 1920 || dy < 0 || dy >= 780 {
				m.fail("beam escaped view")
				return
			}
			intensity := max(c.R, c.G, c.B)
			dest := band.RGBAAt(dx, dy)
			alpha := uint32(c.A)
			mix := func(t, d uint8) uint8 {
				s := (uint32(intensity)*uint32(t) + 127) / 255
				return uint8((s*alpha + uint32(d)*(255-alpha) + 127) / 255)
			}
			band.SetRGBA(dx, dy, color.RGBA{mix(tint[0], dest.R), mix(tint[1], dest.G), mix(tint[2], dest.B), 255})
		}
	}
}
