package eightsword

import (
	"image"
	"strings"
)

// FramePresentation describes the frame submitted to the frontend, including a
// held transaction. It does not describe a later guest state.
type FramePresentation struct {
	Intro, Museum           string
	PreludeInfo, MuseumInfo map[string]any
	HeroinePixels           int
	CaptionSource           uint16
	StoryCalls, StoryPages  uint64
}
type sourceFrameMetadata struct {
	Frame *image.RGBA
	Kind  string
	FramePresentation
}

func sourceIntroStage(kind string) string {
	switch {
	case kind == "publisher":
		return "publisher-noto"
	case kind == "title":
		return "title-noto"
	case kind == "prelude-handoff":
		return "story-prelude-handoff"
	case strings.HasPrefix(kind, "prelude-"):
		return "story-prelude"
	case strings.HasPrefix(kind, "story-"):
		return "story-noto"
	case strings.HasPrefix(kind, "museum-"):
		return kind
	}
	return ""
}
func (e *Engine) initSourceRenderer() {
	pamInstall, pamFrame, pamClose := e.newSourcePAM()
	introInstall, introFrame, introClose := e.newSourceIntro()
	endingInstall, endingFrame, endingClose := e.newSourceEnding()
	directInstall := e.sourceDirectInstall()
	e.sourceInstall = func() {
		if e.inEndingPhase() {
			endingInstall()
			return
		}
		introInstall()
		pamInstall()
		directInstall()
	}
	e.sourceClose = func() { introClose(); pamClose(); endingClose() }
	e.sourceRender = func() *image.RGBA {
		if e.inEndingPhase() {
			return endingFrame()
		}
		if im := pamFrame(); im != nil {
			e.sourceMetadata = sourceFrameMetadata{Frame: im, Kind: "pam"}
			return im
		}
		return introFrame()
	}
}
func (e *Engine) PresentedFrameInfo(frame *image.RGBA) FramePresentation {
	if e.sourceEnabled {
		if frame != nil && frame == e.sourceMetadata.Frame {
			return e.sourceMetadata.FramePresentation
		}
		return FramePresentation{}
	}
	info := FramePresentation{Intro: e.IntroFrameStage(frame)}
	if e.Story != nil {
		info.PreludeInfo = e.Story.PreludeStatus()
		info.StoryCalls, info.StoryPages = e.Story.FrameInfo(frame)
	}
	if e.Museum != nil {
		info.Museum = e.Museum.FrameStage(frame)
		info.MuseumInfo = e.Museum.Status()
	}
	if e.Heroine != nil {
		info.HeroinePixels = e.Heroine.FramePixels(frame)
	}
	if e.Captions != nil {
		info.CaptionSource = e.Captions.FrameSource(frame)
	}
	return info
}
