//go:build ignore

// The same pure-Go XGB/XTEST protocol used by tools/gui-check.go.
package main

import (
	"encoding/binary"
	"fmt"
	"github.com/jezek/xgb"
	"github.com/jezek/xgb/xproto"
	"github.com/jezek/xgb/xtest"
	"os"
	"strconv"
	"strings"
	"time"
)

func xc(err error) {
	if err != nil {
		panic(err)
	}
}
func main() {
	if len(os.Args) < 2 {
		panic("command required")
	}
	c, e := xgb.NewConn()
	xc(e)
	defer c.Close()
	xc(xtest.Init(c))
	setup := xproto.Setup(c)
	if setup.ImageByteOrder != 0 {
		panic("fixed Xvfb byte order")
	}
	root := setup.DefaultScreen(c).Root
	atom, e := xproto.InternAtom(c, false, uint16(len("_NET_WM_NAME")), "_NET_WM_NAME").Reply()
	xc(e)
	tree, e := xproto.QueryTree(c, root).Reply()
	xc(e)
	var window xproto.Window
	for _, w := range tree.Children {
		p, e := xproto.GetProperty(c, false, w, atom.Atom, 0, 0, 1024).Reply()
		if e == nil && strings.Contains(string(p.Value), "軍隊試作") {
			window = w
			break
		}
	}
	if window == 0 {
		if len(os.Args) > 3 && os.Args[1] == "key" && os.Args[3] == "up" {
			// XTEST releases target the server device, including after the
			// application has destroyed its window during Ctrl+Q.
			window = root
		} else {
			panic("army UI window absent")
		}
	}
	xc(xproto.SetInputFocusChecked(c, 1, window, 0).Check())
	geo, e := xproto.GetGeometry(c, xproto.Drawable(window)).Reply()
	xc(e)
	key := func(name string, down bool) {
		symbols := map[string]xproto.Keysym{"Control_L": 0xffe3, "Return": 0xff0d, "Escape": 0xff1b, "F2": 0xffbf, "F10": 0xffc7, "F12": 0xffc9}
		sym, ok := symbols[name]
		if !ok && len(name) == 1 {
			sym = xproto.Keysym(name[0])
			ok = true
		}
		if !ok {
			panic("unsupported keysym")
		}
		mapping, e := xproto.GetKeyboardMapping(c, setup.MinKeycode, byte(int(setup.MaxKeycode)-int(setup.MinKeycode)+1)).Reply()
		xc(e)
		code := byte(0)
		for i := 0; i < len(mapping.Keysyms); i += int(mapping.KeysymsPerKeycode) {
			if mapping.Keysyms[i] == sym {
				code = byte(int(setup.MinKeycode) + i/int(mapping.KeysymsPerKeycode))
				break
			}
		}
		if code == 0 {
			panic("keycode absent")
		}
		kind := byte(3)
		if down {
			kind = 2
		}
		xc(xtest.FakeInputChecked(c, kind, code, 0, root, 0, 0, 0).Check())
	}
	switch os.Args[1] {
	case "info":
		fmt.Printf("{\"width\":%d,\"height\":%d}\n", geo.Width, geo.Height)
	case "click", "hold":
		if len(os.Args) < 4 {
			panic("coordinates required")
		}
		x, e := strconv.Atoi(os.Args[2])
		xc(e)
		y, e := strconv.Atoi(os.Args[3])
		xc(e)
		if x < 0 || y < 0 || x >= int(geo.Width) || y >= int(geo.Height) {
			panic("pointer bounds")
		}
		pos, e := xproto.TranslateCoordinates(c, window, root, 0, 0).Reply()
		xc(e)
		xc(xtest.FakeInputChecked(c, 6, 0, 0, root, pos.DstX+int16(x), pos.DstY+int16(y), 0).Check())
		xc(xtest.FakeInputChecked(c, 4, 1, 0, root, 0, 0, 0).Check())
		ms := 80
		if len(os.Args) > 4 {
			ms, e = strconv.Atoi(os.Args[4])
			xc(e)
		}
		if ms < 40 || ms > 10000 {
			panic("hold duration")
		}
		time.Sleep(time.Duration(ms) * time.Millisecond)
		xc(xtest.FakeInputChecked(c, 5, 1, 0, root, 0, 0, 0).Check())
		time.Sleep(100 * time.Millisecond)
	case "key":
		if len(os.Args) < 3 {
			panic("key required")
		}
		if len(os.Args) > 3 {
			key(os.Args[2], os.Args[3] == "down")
		} else {
			key(os.Args[2], true)
			time.Sleep(80 * time.Millisecond)
			key(os.Args[2], false)
		}
		time.Sleep(100 * time.Millisecond)
	case "screenshot":
		if len(os.Args) != 3 || geo.Width != 1920 || geo.Height != 1200 {
			panic("capture shape")
		}
		c.Sync()
		im, e := xproto.GetImage(c, 2, xproto.Drawable(window), 0, 0, geo.Width, geo.Height, 0xffffffff).Reply()
		xc(e)
		if len(im.Data) != 1920*1200*4 {
			panic("fixed Xvfb 32bpp layout")
		}
		rgb := make([]byte, 1920*1200*3)
		for i := 0; i < 1920*1200; i++ {
			v := binary.LittleEndian.Uint32(im.Data[i*4 : i*4+4])
			rgb[i*3] = byte(v >> 16)
			rgb[i*3+1] = byte(v >> 8)
			rgb[i*3+2] = byte(v)
		}
		f, e := os.OpenFile(os.Args[2], os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
		xc(e)
		_, e = fmt.Fprint(f, "P6\n1920 1200\n255\n")
		xc(e)
		_, e = f.Write(rgb)
		xc(e)
		xc(f.Close())
	default:
		panic("unknown XTEST command")
	}
}
