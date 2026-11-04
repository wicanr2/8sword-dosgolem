package eightsword

import (
	"fmt"
	"image"
	"image/draw"
	"sort"
	"sync"

	"github.com/wicanr2/dosgolem/oracle"
)

// Spec030: optional candidate-only source-command input. No framebuffer or
// guest write access is passed to the resolver or the RGB backend.
type OwnedBattleArtRequest struct {
	Entry, Destination, Mode, CallerCS, CallerIP uint16
	XByte, Y, WidthBytes, Height                 int
}

type OwnedBattleArtSelection struct {
	Unit   string
	Clear  bool
	Retire []string
}

type ownedBattleArtState struct {
	adapter                    *sourceAdapter
	resolve                    func(OwnedBattleArtRequest) (OwnedBattleArtSelection, error)
	ids                        map[string]uint16
	commands, cells            uint64
	retired                    map[uint16]bool
	retirements, retiredPixels uint64
}

var ownedBattleArtEngines sync.Map

// These two methods are called only by the checked source_scene.go candidate
// patch. The formal renderer never advertises the optional capability.
func (p *sourceAdapter) bindOwnedBattleArt() {
	ownedBattleArtEngines.LoadOrStore(p.e, &ownedBattleArtState{adapter: p, ids: map[string]uint16{}, retired: map[uint16]bool{}})
}
func (p *sourceAdapter) closeOwnedBattleArt() { ownedBattleArtEngines.Delete(p.e) }

func (e *Engine) OwnedBattleArtAvailable() bool {
	v, ok := ownedBattleArtEngines.Load(e)
	return ok && e.HD && e.sourceEnabled && v.(*ownedBattleArtState).adapter.bound
}

func (e *Engine) SetOwnedBattleArt(tiles map[string]*image.RGBA, resolve func(OwnedBattleArtRequest) (OwnedBattleArtSelection, error)) error {
	if !e.OwnedBattleArtAvailable() || resolve == nil || len(tiles) != 8 {
		return fmt.Errorf("owned battle art unavailable or incomplete")
	}
	s, _ := ownedBattleArtEngines.Load(e)
	state := s.(*ownedBattleArtState)
	if state.resolve != nil {
		return fmt.Errorf("owned battle art already installed")
	}
	art := state.adapter.graphicsAssets()
	if art.Actors == nil || art.Materials == nil {
		return fmt.Errorf("owned battle art missing graphics")
	}
	ids := map[string]uint16{}
	prepared := map[uint16]*graphicMaterial{}
	// Keys are sorted so diagnostics and the immutable material IDs reproduce.
	keys := sortedBattleArtKeys(tiles)
	for i, key := range keys {
		if key == "" {
			return fmt.Errorf("owned battle art empty identity")
		}
		im := tiles[key]
		if im == nil || im.Bounds() != image.Rect(0, 0, 264, 300) || im.Stride != 264*4 || len(im.Pix) != 264*300*4 {
			return fmt.Errorf("owned battle art tile bounds/storage")
		}
		zero, opaque := false, false
		for at := 0; at < len(im.Pix); at += 4 {
			a := im.Pix[at+3]
			zero = zero || a == 0
			opaque = opaque || a == 255
			if im.Pix[at] > a || im.Pix[at+1] > a || im.Pix[at+2] > a {
				return fmt.Errorf("owned battle art non-premultiplied")
			}
		}
		if !zero || !opaque {
			return fmt.Errorf("owned battle art requires transparent silhouette")
		}
		id := uint16(60000 + i)
		if art.Actors[id] != nil || art.Materials[id] != nil {
			return fmt.Errorf("owned battle art material collision")
		}
		copyTile := image.NewRGBA(im.Bounds())
		draw.Draw(copyTile, copyTile.Bounds(), im, image.Point{}, draw.Src)
		prepared[id] = &graphicMaterial{88, 50, copyTile}
		ids[key] = id
	}
	for id, tile := range prepared {
		art.Actors[id] = tile
	}
	state.ids, state.resolve = ids, resolve
	return nil
}

func sortedBattleArtKeys(tiles map[string]*image.RGBA) []string {
	keys := make([]string, 0, len(tiles))
	for key := range tiles {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	return keys
}

func (p *sourceAdapter) ownedBattleArt(entry uint16, first, w, h, x, y int, dest, mode uint16) (uint16, bool) {
	v, ok := ownedBattleArtEngines.Load(p.e)
	if !ok {
		return 0, false
	}
	s := v.(*ownedBattleArtState)
	if s.resolve == nil {
		return 0, false
	}
	o := p.e.Oracle
	r := o.Regs()
	req := OwnedBattleArtRequest{entry, dest, mode, o.Word(oracle.Far(r.SS, r.SP+2)), o.Word(oracle.Far(r.SS, r.SP)), x, y, w, h}
	selection, err := s.resolve(req)
	if err != nil {
		p.reject("owned-battle-art: " + err.Error())
		return 0, false
	}
	if selection.Unit == "" && !selection.Clear {
		if err := p.retireOwnedBattleArt(s, selection); err != nil {
			p.reject("owned-battle-art retirement: " + err.Error())
		}
		return 0, false
	}
	id := s.ids[selection.Unit]
	paired := entry == 0x423 && req.CallerIP == 0x2c8a || entry == 0x626 && req.CallerIP == 0x2c50
	geometry := w == 11 && h == 50 || entry == 0x423 && w == 8 && h == 25
	choice := selection.Clear && selection.Unit == "" && entry == 0x423 || !selection.Clear && id != 0
	if !choice || !paired || dest != 0xa000 || mode != 1 || !geometry || req.CallerCS != 0xf67 || x*8+88 > 640 || y+50 > 200 {
		p.reject("owned-battle-art command context")
		return 0, false
	}
	art := p.graphicsAssets()
	for row := 0; row < 50; row++ {
		for col := 0; col < 88; col++ {
			v := p.scene.Pixels[first+0x4000*8+row*640+col].Material
			m := art.Materials[v.ID]
			if m == nil || v.Local >= uint32(m.NativeWidth*m.NativeHeight) {
				p.reject("owned-battle-art background")
				return 0, false
			}
		}
	}
	if err := p.retireOwnedBattleArt(s, selection); err != nil {
		p.reject("owned-battle-art retirement: " + err.Error())
		return 0, false
	}
	s.commands++
	s.cells += 88 * 50
	if id != 0 {
		s.retired[id] = false
	}
	return id, true
}

// Unit liveness belongs to typed Go battle state. Retiring its Actor layer is
// a source-scene command; effects, glyphs and background material stay intact.
func (p *sourceAdapter) retireOwnedBattleArt(s *ownedBattleArtState, selection OwnedBattleArtSelection) error {
	ids := map[uint16]bool{}
	for _, key := range selection.Retire {
		id := s.ids[key]
		if id == 0 || key == selection.Unit || ids[id] {
			return fmt.Errorf("invalid retired unit")
		}
		ids[id] = true
	}
	for id := range ids {
		if s.retired[id] {
			continue
		}
		changed := uint64(0)
		for i := range p.scene.Pixels {
			if p.scene.Pixels[i].Actor.ID == id {
				p.scene.Pixels[i].Actor = graphicCell{}
				changed++
			}
		}
		if changed > 0 {
			p.scene.Revision++
			s.retirements++
			s.retiredPixels += changed
		}
		s.retired[id] = true
	}
	return nil
}

func (e *Engine) OwnedBattleArtStatus() map[string]any {
	v, ok := ownedBattleArtEngines.Load(e)
	if !ok {
		return map[string]any{"available": false}
	}
	s := v.(*ownedBattleArtState)
	return map[string]any{"available": true, "installed": s.resolve != nil, "materials": len(s.ids), "commands": s.commands, "cells": s.cells, "retired_units": s.retirements, "retired_pixels": s.retiredPixels}
}
