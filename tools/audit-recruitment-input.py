"""原版募兵數字編輯、字型墨點及修正前後視窗輸入驗證。Docker only。"""
import argparse
import importlib.util
import json
from pathlib import Path
from PIL import Image

spec=importlib.util.spec_from_file_location('building_audit',Path(__file__).with_name('audit-recruitment.py'))
building=importlib.util.module_from_spec(spec);spec.loader.exec_module(building)
FIELD=(864,1002,1056,1092)

def input_template(profiles,font,text,cursor):
    glyphs,atlas=profiles[font];im=Image.new('RGB',(192,90),(85,85,85));pixels=im.load()
    items=[(ch,i*48) for i,ch in enumerate(text)]
    if cursor:items.append(('_',len(text)*48))
    for ch,x in items:
        ix,iy,iw,ih=glyphs[ch]['ink'];dw,dh=min(iw,24),min(ih,90);left=x+(24-dw)//2;top=(90-dh)//2
        for yy in range(dh):
            for xx in range(dw):
                a=atlas.getpixel((ix+xx*iw//dw,iy+yy*ih//dh))
                old=pixels[left+xx,top+yy]
                pixels[left+xx,top+yy]=tuple((color*a+v*(255-a)+127)//255 for color,v in zip((223,195,121),old))
    return im.tobytes()

def check_input(im,profiles,font,text):
    actual=im.convert('RGB').crop(FIELD).tobytes()
    assert actual in [input_template(profiles,font,text,False),input_template(profiles,font,text,True)],('numeric field',font,text)

def digits(im,profiles,font,text,x,y,color=(255,241,181),advance=8):
    glyphs,atlas=profiles[font];pixels=im.load();count=0
    for ch in text:
        ix,iy,iw,ih=glyphs[ch]['ink'];dw,dh=min(iw,24),min(ih,90);left=x*3+(24-dw)//2;top=y*6+(90-dh)//2
        for yy in range(dh):
            for xx in range(dw):
                if atlas.getpixel((ix+xx*iw//dw,iy+yy*ih//dh))==255:
                    assert pixels[left+xx,top+yy][:3]==color,('digit',font,text,x,y,ch)
                    count+=1
        x+=advance
    assert count>0
    return count

def normal(a,profiles):
    checks=[]
    for name,font,text in [('13-enter-one','noto','1'),('13b-enter-ten','noto','10'),('13b-ten-lishu','lishu','10'),('13b-ten-caoshu','caoshu','10'),('13c-backspace-one','noto','1')]:
        im=Image.open(a.receipt/(name+'-hd.png'));check_input(im,profiles,font,text)
        checks.append(dict(file=name,font=font,text=text,field_rgb_bytes=192*90*3))
    im=Image.open(a.receipt/'15-army-after-hire-hd.png').convert('RGBA')
    points=digits(im,profiles,'noto','31',152,29)+digits(im,profiles,'noto','31',152,45)
    im=Image.open(a.receipt/'16-character-after-hire-hd.png').convert('RGBA');points+=digits(im,profiles,'noto','499',112,117,advance=16)
    return dict(status='passed-original-numeric-edit-and-HD-font',checks=checks,result_digit_points=points,limit='observed one-hire outcome only; no general cost or limit formula')

def gui(a,profiles,inputs=True):
    root=a.receipt;meta=list(map(json.loads,(root/'intro-draw.jsonl').read_text().splitlines()));targets={}
    names={'recruitment-input-ten':'10','recruitment-edited-one':'1'}
    for n in range(4,10):names['recruitment-input-digit-'+str(n)]=str(n);names['recruitment-cleared-digit-'+str(n)]=''
    if inputs:
        for name,text in names.items():
            s=building.read(root/(name+'.json'));targets[int(s['presented_frames'])]=(name,text,s['font_id'])
        assert len(targets)==14
    party={}
    for p in root.glob('*-army-*.json'):
        s=building.read(p);party[int(s['presented_frames'])]='army'
    accepted=root/'recruitment-accepted.json';after=building.read(accepted)['steps'] if accepted.exists() else 0
    for e in building.read(root/'gui-input-receipt.json')['events']:
        s=e['status']
        if e['x11_keycode']==9 and e['down'] and s.get('presented_scene')=='character' and s['steps']>after:
            party[int(s['presented_frames'])]='character'
    checked=[];party_checks=[];examples=set()
    for n,step,im in building.helper.stream(root):
        if n in targets:
            name,text,font=targets[n];assert meta[n-1]['font_id']==font
            check_input(im,profiles,font,text);checked.append(dict(draw=n,name=name,text=text))
        if n in party:
            font=meta[n-1]['font_id'];kind=party[n]
            points=(digits(im,profiles,font,'31',152,29)+digits(im,profiles,font,'31',152,45)) if kind=='army' else digits(im,profiles,font,'499',112,117,advance=16)
            party_checks.append(dict(draw=n,kind=kind,opaque_points=points))
            if kind not in examples:im.save(root/('hire-'+kind+'-actual-draw.png'));examples.add(kind)
    assert len(checked)==(14 if inputs else 0)
    if inputs:
        events=building.read(root/'gui-final.json')['input_events']
        for scan in list(range(5,12))+[14]:
            for down in [True,False]: assert any(e['Scan']==scan and e['Down']==down for e in events),('DOS key missing',scan,down)
    assert sum(p['kind']=='army' for p in party_checks)==2 and sum(p['kind']=='character' for p in party_checks)>=2
    return dict(status='passed-actual-GUI-numeric-edit-and-party',checkpoints=checked,party_checks=party_checks,dos_make_break_scans=list(range(5,12))+[14] if inputs else [])

def main():
    p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('mode',choices=['normal','gui','party']);a=p.parse_args()
    assert not a.out.exists();profiles=building.helper.fonts(a.assets)
    result=normal(a,profiles) if a.mode=='normal' else gui(a,profiles,a.mode=='gui')
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
