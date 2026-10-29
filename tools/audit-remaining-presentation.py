"""Rebuild full HD frames independently with Pillow integer channel arithmetic."""
import argparse,gzip,hashlib,json,pathlib
from PIL import Image,ImageMath,ImageChops
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def rebuild(base,layer,raw):
 base=Image.open(base).convert('RGBA');layer=Image.open(layer).convert('RGBA')if isinstance(layer,pathlib.Path)else layer
 assert base.size==(1920,1200)and len(raw)==128000 and set(raw)<={0,1}
 mask=Image.frombytes('L',(640,200),bytes(255 if v else 0 for v in raw)).resize(base.size,Image.Resampling.NEAREST);clip=Image.new('L',base.size);clip.paste(255,(12,12,1344,1140));allowed=ImageChops.subtract(clip,mask)
 # Bounded strips keep integer temporary images below the audit memory quota.
 for top in range(0,1200,100):
  box=(0,top,1920,top+100);bstrip=base.crop(box);lstrip=layer.crop(box);alpha=lstrip.getchannel('A');channels=[]
  for b,l in zip(bstrip.split()[:3],lstrip.split()[:3]):channels.append(ImageMath.unsafe_eval("convert(min(l+(b*(255-a)+127)/255,255),'L')",b=b.convert('I'),l=l.convert('I'),a=alpha.convert('I')))
  expected=Image.merge('RGBA',(*channels,bstrip.getchannel('A')));base.paste(expected,(0,top),allowed.crop(box))
 return base
def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();assert not a.out.exists();q=a.project/'workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1/remaining-r1';rows=[]
 for kind in range(8):
  d=q/'normal-r2'/str(kind);m=read(d/'receipt.json');assert m['kind']==kind and m['frame_guest_pure']and m['original_f4_menu'];assert sha(d/'before.state')==sha(d/'after.state');s=m['source_status'];assert s['source_renderer']and s['direct_calls']>0 and s['go_compat_writes']>0 and not s['owned_render_fault'];assert m['cue']['Map'][kind]==1
  x,y,w,h=m["layer_rect"];layer=Image.frombytes("RGBA",(w,h),gzip.decompress((d/"layer-rgba.gz").read_bytes()));full=Image.new("RGBA",(1920,1200));full.paste(layer,(x,y))
  expected=rebuild(d/'base.png',full,gzip.decompress((d/'mask.gz').read_bytes()));actual=Image.open(d/'frame.png').convert('RGBA');assert expected.tobytes()==actual.tobytes(),('normal',kind);assert actual.tobytes()!=Image.open(d/'base.png').convert('RGBA').tobytes();rows.append(dict(kind=kind,method='normal F4 Engine Frame, resources fixture',frame_sha256=sha(d/'frame.png'),step=m['step'],sample=m['sample']))
 for folder,kind,expected in [('gui-r1',9,[0,21]),('gui-freeze-r1',8,[1,0])]:
  final=read(q/folder/'gui-final.json');assert final['closed']and final['research_vfx']['player_spell_complete']and final['spell_cues']['Battle']==expected and final['spell_cues']['Started']==final['spell_cues']['Completed']==sum(expected) and final['spell_cues']['Skipped']==0
  for phase in ['cue-early','cue-late']:
   d=q/folder/'vfx-draw';m=read(d/(phase+'.json'));assert m['frame_guest_pure']and m['fixture']and m['vfx']['Kind']==kind;assert sha(d/(phase+'-before.state'))==sha(d/(phase+'-after.state'))==m['guest_state_sha256'];x,y,w,h=m['layer_rect'];raw=gzip.decompress((d/(phase+'-layer-rgba.bin.gz')).read_bytes());layer=Image.frombytes('RGBA',(w,h),raw);full=Image.new('RGBA',(1920,1200));full.paste(layer,(x,y));expected=rebuild(d/(phase+'-base.png'),full,gzip.decompress((d/(phase+'-native-text-mask.bin.gz')).read_bytes()));actual=Image.open(d/(phase+'-central.png')).convert('RGBA');presented=Image.open(d/(phase+'-presented.png')).convert('RGBA');assert expected.tobytes()==actual.tobytes()==presented.crop((512,64,2432,1264)).tobytes();rows.append(dict(kind=kind,phase=phase,method='actual Ebiten Draw, resources fixture',draw=m['draw'],frame_sha256=sha(d/(phase+'-central.png'))))
 result=dict(status='passed-independent-remaining-presentation',normal_map_frames=8,actual_window_draws=4,clone_original_updates=21,frames=rows,limits=['Freeze and clone GUI are representative controlled original-menu casts.','Resource/learning fixtures; not natural acquisition. No new save/load claim.']);a.out.write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
if __name__=='__main__':main()
