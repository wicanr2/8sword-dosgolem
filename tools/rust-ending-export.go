//go:build ignore

// Development exporter, copied into the isolated eightsword test package.
// Runtime input is declarative drawing data, never x86 or a captured RGB movie.
package eightsword

import (
 "bytes"
 "encoding/binary"
 "fmt"
 "hash/fnv"
 "image"
 "os"
 "path/filepath"
 "strconv"
 "testing"
)

type rustEndingTexture struct { w,h int; pix []byte }
type rustEndingBitmap struct { w,h,mode int; repeat bool; pixels,mask []byte; textures [3]uint32 }
type rustEndingGlyph struct { w int; mask []byte; alpha [3][]byte }
type rustEndingOp struct { kind byte; id,x,y uint16; fg,bg byte }
type rustEndingFrame struct { ms uint32; stage,cue byte; ops []uint32 }
type rustEndingExport struct {
 t *testing.T; e *Engine; dir string; begin uint64; begun bool
 textures []rustEndingTexture; bitmaps []rustEndingBitmap; glyphs []rustEndingGlyph; ops []rustEndingOp; frames []rustEndingFrame
 textureIDs,bitmapIDs,glyphIDs,opIDs map[string]uint32
 samples []string; lastPage *endingPage; revision uint64; cue byte
}
func newRustEndingExport(t *testing.T,e *Engine,dir string)*rustEndingExport{return &rustEndingExport{t:t,e:e,dir:dir,textureIDs:map[string]uint32{},bitmapIDs:map[string]uint32{},glyphIDs:map[string]uint32{},opIDs:map[string]uint32{},frames:[]rustEndingFrame{{}},cue:1}}
func endingFNV(raw []byte)uint64{h:=fnv.New64a();h.Write(raw);return h.Sum64()}
func(p *rustEndingExport)texture(im image.Image)uint32{
 b:=im.Bounds();raw:=make([]byte,b.Dx()*b.Dy()*8)
 // Preserve Color.RGBA's full premultiplied 16-bit contract, including
 // material loaders that already hold an 8-bit premultiplied RGBA image.
 for y:=0;y<b.Dy();y++{for x:=0;x<b.Dx();x++{r,g,bb,a:=im.At(b.Min.X+x,b.Min.Y+y).RGBA();for k,v:=range []uint32{r,g,bb,a}{binary.LittleEndian.PutUint16(raw[(y*b.Dx()+x)*8+k*2:],uint16(v))}}}
 key:=fmt.Sprintf("%d/%d/%x",b.Dx(),b.Dy(),endingFNV(raw));if id,ok:=p.textureIDs[key];ok{return id}
 id:=uint32(len(p.textures));p.textureIDs[key]=id;p.textures=append(p.textures,rustEndingTexture{b.Dx(),b.Dy(),raw});return id
}
func(p *rustEndingExport)bitmap(c *endingCommand)uint16{
 if id,ok:=p.bitmapIDs[c.SourceSHA];ok{return uint16(id)}
 b:=rustEndingBitmap{w:c.W,h:c.H,pixels:c.Pixels,mask:c.Mask,textures:[3]uint32{^uint32(0),^uint32(0),^uint32(0)}}
 art:=p.e.ending.assets.art;var im image.Image
 if v:=art.completion[c.SourceSHA];v!=nil{im=v;b.mode=3;b.repeat=true;if c.SourceFile=="END4.AY"&&c.W==176||c.SourceFile=="END9.AY"{b.mode=1}}else if v:=art.pair[c.SourceSHA];v!=nil{im=v;b.mode=3;b.repeat=true}else if v:=art.effects[c.SourceSHA];v!=nil{im=v;b.mode=2;b.repeat=true}else if c.SourceSHA==endingDuelSource{im=art.duel;b.mode=1}else if c.SourceSHA==endingRingSource{im=art.ring;b.mode=2;b.repeat=true}else if c.SourceSHA==endingSwordsSource{im=art.swords;b.mode=2;b.repeat=true}else if v:=art.portraits[c.SourceSHA];v!=nil{im=v;b.mode=1}else if c.SourceFile=="END7.AY"{im=art.end7;b.mode=1}else if c.SourceFile=="END8.AY"{
  b.mode=4;for i,name:=range []string{"noto","lishu","caoshu"}{b.textures[i]=p.texture(art.titles[name])}
 }
 if im!=nil{id:=p.texture(im);b.textures=[3]uint32{id,id,id}}
 if b.mode!=0&&b.textures[0]==^uint32(0){p.t.Fatal("HD ending material absent",c.SourceSHA)}
 id:=uint32(len(p.bitmaps));p.bitmapIDs[c.SourceSHA]=id;p.bitmaps=append(p.bitmaps,b);return uint16(id)
}
func(p *rustEndingExport)glyph(c *endingCommand)uint16{
 key:=fmt.Sprintf("%s/%d/%d",c.Kind,c.Code,c.Char);if id,ok:=p.glyphIDs[key];ok{return uint16(id)}
 g:=rustEndingGlyph{w:c.W,mask:c.Mask}
 for i,name:=range []string{"noto","lishu","caoshu"}{
  alpha:=make([]byte,c.W*3*90);profile:=p.e.ending.assets.profile(name)
  if c.Char!=' ' {ink,ok:=profile.glyphs[c.Char];if !ok{p.t.Fatal("missing ending glyph",c.Char)};iw,ih:=ink.Ink[2],ink.Ink[3];dw,dh:=min(iw,c.W*3),min(ih,90);left,top:=(c.W*3-dw)/2,(90-dh)/2
   for y:=0;y<dh;y++{for x:=0;x<dw;x++{_,_,_,a:=profile.image.At(ink.Ink[0]+x*iw/dw,ink.Ink[1]+y*ih/dh).RGBA();alpha[(top+y)*c.W*3+left+x]=byte(a>>8)}}
  };g.alpha[i]=alpha
 }
 id:=uint32(len(p.glyphs));p.glyphIDs[key]=id;p.glyphs=append(p.glyphs,g);return uint16(id)
}
func(p *rustEndingExport)op(c *endingCommand)uint32{
 o:=rustEndingOp{x:uint16(c.X),y:uint16(c.Y),fg:c.FG,bg:c.BG}
 if c.Kind=="bitmap"{o.id=p.bitmap(c)}else{o.kind=1;o.id=p.glyph(c)}
 key:=fmt.Sprint(o);if id,ok:=p.opIDs[key];ok{return id};id:=uint32(len(p.ops));p.opIDs[key]=id;p.ops=append(p.ops,o);return id
}
func(p *rustEndingExport)capture(){
 e:=p.e;if !e.inEndingPhase(){return};if !p.begun{p.begin=e.Oracle.Cycles();p.begun=true}
 a:=e.ending;if a==nil||!a.bound||!a.scene.mode||a.active!=0{return};page:=a.scene.pages[a.scene.active]
 // Source read selects the cue; HD MFIG presentation uses the approved battle track.
 cue:=byte(1);for _,op:=range e.Oracle.FileOps(){if op.Name=="mend.ay"&&op.Op=="read"{cue=2}}
 if p.lastPage==page&&p.revision==page.revision&&p.cue==cue{return};p.lastPage=page;p.revision=page.revision;p.cue=cue
 f:=rustEndingFrame{ms:uint32((e.Oracle.Cycles()-p.begin)/3000),cue:cue}
 if len(page.stage)==7{n,err:=strconv.Atoi(page.stage[3:4]);if err==nil&&n>=1&&n<=9{f.stage=byte(n)}}
 for _,c:=range page.ops{f.ops=append(f.ops,p.op(c))};p.frames=append(p.frames,f)
}
func(p *rustEndingExport)sample(stage string){
 p.capture();if !p.begun{return};a:=p.e.ending;page:=a.scene.pages[a.scene.active];var hashes []uint64
 for _,name:=range []string{"original","noto","lishu","caoshu"}{var profile *endingFontProfile;if name!="original"{profile=a.assets.profile(name)};im:=renderEndingPage(page,endingPalette,a.assets.art,profile);hashes=append(hashes,endingFNV(im.Pix))}
 p.samples=append(p.samples,fmt.Sprintf("%d\t%d\t%s\t%016x\t%016x\t%016x\t%016x",len(p.frames)-1,p.frames[len(p.frames)-1].ms,stage,hashes[0],hashes[1],hashes[2],hashes[3]))
}
func(p *rustEndingExport)finish(){
 if !p.begun||!p.e.Exited||p.e.ExitCode!=0{p.t.Fatal("ending export incomplete")};duration:=uint32((p.e.Oracle.Cycles()-p.begin)/3000)
 var out bytes.Buffer;out.WriteString("8SEND003");put:=func(v any){if err:=binary.Write(&out,binary.LittleEndian,v);err!=nil{p.t.Fatal(err)}}
 put(duration);put(uint32(len(p.textures)));for _,v:=range p.textures{put(uint16(v.w));put(uint16(v.h));out.Write(v.pix)}
 put(uint16(len(p.bitmaps)));for _,v:=range p.bitmaps{put(uint16(v.w));put(uint16(v.h));put(byte(v.mode));put(v.repeat);put(v.textures);out.Write(v.pixels);out.Write(v.mask)}
 put(uint16(len(p.glyphs)));for _,v:=range p.glyphs{put(byte(v.w));out.Write(v.mask);for _,a:=range v.alpha{out.Write(a)}}
 put(uint32(len(p.ops)));for _,v:=range p.ops{put(v.kind);put(v.id);put(v.x);put(v.y);put(v.fg);put(v.bg)}
 put(uint32(len(p.frames)));for _,v:=range p.frames{put(v.ms);put(v.stage);put(v.cue);put(uint16(len(v.ops)));put(v.ops)}
 put(endingFNV(out.Bytes()));if err:=os.WriteFile(filepath.Join(p.dir,"ending.bin"),out.Bytes(),0644);err!=nil{p.t.Fatal(err)}
 var samples bytes.Buffer;samples.WriteString("# frame ms source original noto lishu caoshu\n");for _,v:=range p.samples{fmt.Fprintln(&samples,v)};if err:=os.WriteFile(filepath.Join(p.dir,"ending-reference.tsv"),samples.Bytes(),0644);err!=nil{p.t.Fatal(err)}
 p.t.Logf("ending export duration=%dms frames=%d ops=%d bitmaps=%d glyphs=%d textures=%d bytes=%d",duration,len(p.frames),len(p.ops),len(p.bitmaps),len(p.glyphs),len(p.textures),out.Len())
}
