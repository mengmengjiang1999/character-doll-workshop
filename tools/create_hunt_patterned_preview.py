#!/usr/bin/env python3
"""Map the existing Hunt motifs onto the complete garment pieces for review only."""
from pathlib import Path
from copy import deepcopy
import xml.etree.ElementTree as ET
import json, math, re, hashlib
import create_hunt_garment as base
from create_dimension_previews import label
from create_preservation_patterned_preview import append_material_panel, material_lines, card_materials
ROOT=base.ROOT
GP=base.OUT
OUT=GP/'patterned'
COMP=GP.parent/'fabric-print/components'
NS='http://www.w3.org/2000/svg';XL='http://www.w3.org/1999/xlink'
ET.register_namespace('',NS);ET.register_namespace('xlink',XL)
def serial(n):return ET.tostring(n,encoding='unicode')
def read(name):return ET.parse(COMP/name).getroot()
common=read('h01-chest-scrolls.svg').find('{'+NS+'}defs')
DEFS=''.join(serial(c) for c in common)
def selected(name,predicate):return ''.join(serial(c) for c in read(name) if c.tag.endswith('path') and predicate(c))
large=selected('h03-large-hem-scroll.svg',lambda c:c.get('fill')=='#251724')
small=selected('h04-small-front-hem-scroll.svg',lambda c:c.get('fill')=='#281925')
inner=selected('h02-red-opening-scrolls.svg',lambda c:c.get('stroke')=='#7E1D20')
# Keep complete motifs; source background rectangles and original sample border shapes are not embedded.
SOURCES={'H-C01':'h01-chest-scrolls.svg','H-R01':'h02-red-opening-scrolls.svg','H-R03':'h05-shoulder-gold-cyan.svg','H-R04':'h02-red-opening-scrolls.svg','H-S01':'h03-large-hem-scroll.svg','H-S02':'h04-small-front-hem-scroll.svg','H-B03':'h09-white-sleeve-flower-print.svg','H-W03':'h10-blue-ribbon-tail-print.svg'}
MAPPING=[]
def use(symbol,transform,opacity=1):return f'<use xlink:href="#{symbol}" transform="{transform}" opacity="{opacity}"/>'
def pth(d,fill='none',stroke='none',sw=1):return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>'
def group(t,s):return f'<g transform="{t}">{s}</g>'
def border(p,color='#F0E3BC',offset=3,width=1.8):
    q=base.Polygon(p['net']).buffer(-offset,join_style=1)
    return base.svgpath(list(q.exterior.coords),'none',color,width) if not q.is_empty and q.geom_type=='Polygon' else ''
def fill(p):
    n=p['piece_id']
    if n=='H-C01':return 'url(#chestTone)'
    if n.startswith('H-R'):return '#A13B3B' if n=='H-R04' else 'url(#redTone)'
    if n in ('H-S01','H-S02'):return '#493B48'
    if n in ('H-W01','H-W03'):return 'url(#blueTone)'
    if n in ('H-W02','H-W04','H-S04','H-S05','H-T01'):return 'url(#pinkTone)'
    if n=='H-B04':return '#39343F'
    return '#FFF8F5'
def pattern(p):
    n=p['piece_id'];s=''
    if n=='H-C01':
        s+=border(p,'#BDA57F',3,2.3)+border(p,'#F1E0B7',4.2,.8)
        s+=use('chestCurl','translate(-7 24) scale(-.58 .60)')+use('chestCurl','translate(7 24) scale(.58 .60)')
        s+=pth('M0 20 V103','none','#F1E0B7',2)+pth('M3 23 V101','none','#DAC598',.6)
    elif n=='H-R01':
        s+=pth('M30 39 C42 69 59 91 69 114','none','#F3E9CD',1.5)
        s+=use('openingCurl','translate(34 43) scale(.43 .58)')
    elif n=='H-R03':s+=use('shoulderEmblem','translate(-13 9) scale(.43)')
    elif n=='H-R04':
        s+=group('translate(9 27) scale(.58 1.18) translate(-143 -16)',inner)
        s+=border(p,'#6E2431',3,1.3)
    elif n=='H-S01':
        s+=border(p,'#B29F79',2.7,3.1)+border(p,'#F0E3BC',3.8,1.6)
        s+=group('translate(12 22) scale(.52 .67) translate(-55 -25)',large)
    elif n=='H-S02':
        s+=border(p,'#B29F79',2.7,3.1)+border(p,'#F0E3BC',3.8,1.6)
        s+=group('translate(13 17) scale(.57 .52) translate(-25 -27)',small)
    elif n=='H-B03':
        s+=use('blossom','translate(-24 57) scale(.35)',.42)+use('blossom','translate(-4 62) scale(.36) rotate(-17 30 30)',.42)+use('blossom','translate(19 54) scale(.37) rotate(16 30 30)',.42)
        s+=pth('M-45 89 Q-15 82 8 88 Q30 91 50 81','none','#EAC7D5',1.5)+pth('M-49 94 Q-15 87 8 93 Q30 96 54 86','none','#F1D4DF',1)
    elif n=='H-W03':
        s+=border(p,'#DADDE0',3,1.8)+border(p,'#A5AEC2',5,.65)
        # redraw only the running stem along this narrow, tapering tail; retain source quatrefoil motifs
        s+=pth('M12 5 C10 24 23 22 20 40 S8 55 13 70 S28 87 23 105 S9 121 17 140','none','#C0C5D1',2.5)
        s+=use('quatrefoil','translate(23 25) scale(.66)')+use('quatrefoil','translate(25 75) scale(.48)')+use('quatrefoil','translate(26 120) scale(.34)')
    return s

def art(p,prefix,include_base=True):
    cid=prefix+'-'+p['piece_id']
    cut=base.pathstr(p['cut']);net=base.pathstr(p['net'])
    result=f'<defs><clipPath id="{cid}"><path d="{net}"/></clipPath></defs>'
    if include_base:result+=pth(cut,fill(p))
    result+=f'<g clip-path="url(#{cid})">'+pattern(p)+'</g>'
    return result

def writepieces():
    for p in base.pieces:
        src=GP/p['file'];r=ET.parse(src).getroot();r.insert(1,ET.fromstring('<defs xmlns="'+NS+'" xmlns:xlink="'+XL+'">'+DEFS+'</defs>'))
        target=next(c for c in r if c.tag.endswith('g') and c.get('transform','').startswith('translate('))
        target.insert(0,ET.fromstring('<g xmlns="'+NS+'" xmlns:xlink="'+XL+'">'+art(p,'single')+'</g>'))
        # Original cut fill would hide the fabric; retain every original outline, measurement and label.
        for c in target:
            if c.tag.endswith('path') and c.get('fill')=='#f1f1ef':c.set('fill','none')
        # Insert a small explicit preview legend, not a production approval.
        legend='花纹定位看稿；不是印厂生产文件'
        if p['piece_id']=='H-R04':legend='本图显示暗纹里侧；红色表面净色'
        r.append(ET.fromstring('<g xmlns="'+NS+'">'+label(10,40,legend,3.6,'#954532')+'</g>'))
        append_material_panel(r,GP,p['piece_id'])
        file=OUT/p['file'];file.parent.mkdir(parents=True,exist_ok=True);file.write_text(serial(r))
        MAPPING.append({'piece_id':p['piece_id'],'name':p['name'],'source_motif':SOURCES.get(p['piece_id']),'preview_face':'lining' if p['piece_id']=='H-R04' else 'outer face','base_color_covers_allowance':True,'motif_clipped_to_net_shape':True,'geometry_source':'../'+p['file'],'notes':'里布/贴边不另加无关纹样；未知后背为净色；R04单片显示里侧暗纹，外面用净红色。'})

def overview():
    cols=4;cw=440;maxlines=max(len(material_lines(GP,p['piece_id'],compact=True,width=386,font_size=17))for p in base.pieces);ch=405+maxlines*23;rows=math.ceil(len(base.pieces)/cols);W=cols*cw+60;H=rows*ch+180
    body='<defs>'+DEFS+'</defs>'+label(35,55,'巡猎坐娃 · 完整衣片花纹定位看稿',40)+label(35,95,'保留原衣片尺寸、缝份与净线；底色覆盖裁边，纹样按成品区域定位。',23,'#a54d39')
    body+=label(35,130,'R04 显示暗纹里侧，外面净红；后背及隐藏贴边保持净色。未做实布验证。',22)
    for i,p in enumerate(base.pieces):
        x=30+i%cols*cw;y=165+i//cols*ch
        body+=f'<rect x="{x}" y="{y}" width="420" height="{ch-18}" rx="12" fill="#f7f7f3" stroke="#c6d0d5"/>'
        body+=label(x+14,y+28,p['piece_id']+' '+p['name'],21)
        a,b,c,d=base.basicpiece(p);s=min(360/(c-a),170/(d-b),2)
        tx=x+210-(a+c)/2*s;ty=y+132-(b+d)/2*s
        body+=f'<g transform="translate({tx} {ty}) scale({s})">'+art(p,'overview')+base.svgpath(p['cut'],'none','#283b47',.5)+base.svgpath(p['net'],'none','#b8615e',.5,'2 1')+'</g>'
        body+=label(x+14,y+239,'净 '+str(p['net_bbox_mm'][0])+' × '+str(p['net_bbox_mm'][1])+' mm',20)+label(x+14,y+269,'裁 '+str(p['cut_bbox_mm'][0])+' × '+str(p['cut_bbox_mm'][1])+' mm',19)
        body+=label(x+14,y+298,p['cut_count']+' / 缝份 '+str(p['allowance_mm'])+' mm',18)
        note='里侧暗纹；外面净红' if p['piece_id']=='H-R04' else p['layer']
        body+=label(x+14,y+323,note,17,'#61727e')
        body+=card_materials(GP,p['piece_id'],x+14,y+360)
    f=OUT/'pieces-overview.svg';f.write_text(base.svgdoc(W,H,body).replace('xmlns="'+NS+'"','xmlns="'+NS+'" xmlns:xlink="'+XL+'"',1));base.render(f,f.with_suffix('.png'),1800)

# Apply motifs to corresponding silhouettes in the existing layered engineering flat.
def decorated_flat(x,y,scale,layer,back=False):
    raw=base.flat(x,y,scale,layer,back)
    root=ET.fromstring('<svg xmlns="'+NS+'" xmlns:xlink="'+XL+'">'+raw+'</svg>');g=root[0]
    additions=[]
    for j,child in enumerate(list(g)):
        d=child.get('d','');col=child.get('fill');motif='';note=''
        if col=='#4c3940' and not back:
            motif=use('chestCurl','translate(146 83) scale(-.43 .61)')+use('chestCurl','translate(154 83) scale(.43 .61)')
        elif col=='#ad3835' and d.startswith('M108 25 L75') and not back:
            motif=use('openingCurl','translate(88 58) scale(.32 .52)')
        elif col=='#ad3835' and d.startswith('M192 25 L225') and not back:
            motif=use('openingCurl','translate(212 58) scale(-.32 .52)')
        elif col=='#6f3f51':
            if d.startswith('M74'):motif=group('translate(57 134) scale(.29 .63) translate(-143 -16)',inner)
            else:motif=group('translate(243 134) scale(-.29 .63) translate(-143 -16)',inner)
        elif col=='#49363e':
            if d.startswith('M84'):motif=group('translate(73 173) scale(.27 .33) translate(-55 -25)',large)
            elif d.startswith('M216'):motif=group('translate(227 173) scale(-.27 .33) translate(-55 -25)',large)
            elif d.startswith('M120') and not back:motif=group('translate(131 178) scale(.42 .35) translate(-25 -27)',small)
        elif col=='#f6f1e9':
            motif=use('blossom','translate(44 117) scale(.27) rotate(20 30 30)',.45)+use('blossom','translate(237 117) scale(.27) rotate(-20 30 30)',.45)
        elif col=='#70b0cf':
            # A narrow tail needs its small ornaments rotated with the tail direction.
            if d.startswith('M90'):
                motif=use('quatrefoil','translate(60 203) scale(.47) rotate(25 14 16)')+use('quatrefoil','translate(43 233) scale(.27)')+pth('M73 194 L50 235','none','#CED3DE',1.6)
            else:
                motif=use('quatrefoil','translate(224 203) scale(.47) rotate(-25 14 16)')+use('quatrefoil','translate(246 233) scale(.27)')+pth('M227 194 L250 235','none','#CED3DE',1.6)
        if motif:
            ident=f'flat-{layer}-{int(back)}-{j}'
            s=f'<g xmlns="{NS}" xmlns:xlink="{XL}"><defs><clipPath id="{ident}"><path d="{d}"/></clipPath></defs><g clip-path="url(#{ident})">{motif}</g></g>'
            additions.append((j+1,ET.fromstring(s)))
    for index,node in reversed(additions):g.insert(index,node)
    return serial(g)

def flat_tags(x,y,scale,back=False):
    def tag(px,py,tx,ty,text):
        width=sum(12.5 if ord(c)>127 else 7.1 for c in text)+10
        return pth(f'M{px+width/2} {py+8} L{tx} {ty}','none','#627780',.8)+f'<rect x="{px}" y="{py-4}" width="{width}" height="18" rx="3" fill="#fffdfa" stroke="#a4b0b6" stroke-width=".5" opacity=".95"/>'+label(px+5,py+9,text,12.5,'#30434f')
    if back:
        s=tag(112,20,150,80,'H-R02 净背')+tag(182,112,235,171,'R04 翻露里侧')+tag(14,143,53,138,'H-B03')+tag(174,246,244,228,'H-W03')
    else:
        s=tag(158,20,153,110,'H-C01')+tag(6,51,104,84,'H-R01')+tag(5,142,54,135,'H-B03')+tag(184,110,232,174,'R04 翻露里侧')+tag(0,213,86,201,'H-S01')+tag(112,242,150,208,'H-S02')+tag(220,244,247,227,'H-W03')
    return group(f'translate({x} {y}) scale({scale})',s)

def layers():
    W,H=1800,1980
    body='<defs>'+DEFS+'</defs>'+label(40,60,'巡猎三月七 · 完整服装与衣片花纹对照',43)+label(40,104,'看稿版：尺寸仍为假设试版；已知纹样定位，未知后背净色。非印厂生产图。',24,'#a84c39')
    specs=[('01 浅色底衣＋蓬白袖',1,'B01–B08＋T01；粉花仅在B03白袖'),('02 弧形深胸片',2,'C01双卷纹；背面仅见净色底衣'),('03 红肩外搭＋尖长衣尾',3,'R01金卷前缘；R04暗纹在里侧'),('04 分瓣裙＋粉白衬摆',4,'S01大卷／S02小卷；粉白层为真布'),('05 蓝斜带＋粉横带＋垂尾',5,'W03蓝尾浅纹；W01斜带保持素蓝'),('06 合穿花纹位置',6,'前片位置核对；后背不复制胸前花纹')]
    for i,(title,layer,subtitle) in enumerate(specs):
        x=35+i%2*885;y=145+i//2*590
        body+=f'<rect x="{x}" y="{y}" width="850" height="560" rx="18" fill="#f4f5f4" stroke="#c5d1d5"/>'
        body+=label(x+24,y+42,title,29)+label(x+24,y+78,subtitle,20,'#5f707c')+label(x+207,y+116,'前面',22,anchor='middle')+label(x+633,y+116,'背面',22,anchor='middle')
        body+=decorated_flat(x+16,y+135,1.28,layer)+decorated_flat(x+442,y+135,1.28,layer,True)
        if layer==6:body+=flat_tags(x+16,y+135,1.28)+flat_tags(x+442,y+135,1.28,True)
        elif layer==3:body+=label(x+200,y+493,'R04：翻露里侧',18,'#78545c',anchor='middle')+label(x+630,y+493,'R04：翻露里侧',18,'#78545c',anchor='middle')
        body+=label(x+24,y+535,'图中省略的肩饰／花结可另做缠花或立体件；拼接按原净线',19,'#7e625d')
    body+=label(40,1960,'衣片ID完整前缀为H-；单片SVG保留原尺寸与工艺线。立体示意不用于量尺寸。',22)
    f=OUT/'layers-overview.svg';f.write_text(base.svgdoc(W,H,body).replace('xmlns="'+NS+'"','xmlns="'+NS+'" xmlns:xlink="'+XL+'"',1));base.render(f,f.with_suffix('.png'),1800)

def main():
    before={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in GP.glob('*')if f.is_file()}
    OUT.mkdir(exist_ok=True);writepieces();overview();layers()
    (OUT/'mapping.json').write_text(json.dumps({'status':'pattern placement preview; not production print or fit validated','geometry_unchanged':True,'material_source':'../piece-materials.json','single_svg_page_height_extended_for_material_notes':True,'piece_count':len(MAPPING),'pieces':MAPPING},ensure_ascii=False,indent=2)+'\n')
    assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==digest for f,digest in before.items())
    for f in (OUT/'pieces').glob('*.svg'):
        r=ET.parse(f).getroot();src=ET.parse(GP/'pieces'/f.name).getroot();assert r.get('viewBox').split()[:3]==src.get('viewBox').split()[:3] and r.get('width')==src.get('width') and float(r.get('viewBox').split()[3])>float(src.get('viewBox').split()[3])
        oldpaths={e.get('d')for e in src.iter()if e.tag.endswith('path')};newpaths={e.get('d')for e in r.iter()if e.tag.endswith('path')};assert oldpaths<=newpaths
    readme=OUT/'README.md'
    note='## 每片材质标注\n\n单片SVG下方增加材料建议区，总览卡片直接列出中文材质、组号及目标克重。单片还记录面布、里布、贴边／支承布、局部衬的颜色／工艺与位置，均为尚未打样的建议。说明区只增加页高，原衣片坐标、毫米比例和50 mm校准线保留。数据来自[逐片材料记录](../piece-materials.json)。\n'
    if readme.exists():
        text=readme.read_text();text=text.split('## 每片材质标注')[0].rstrip()+'\n\n'+note
    else:text='# 巡猎完整衣片花纹与材质预览\n\n'+note
    readme.write_text(text)
    print('Created 27 patterned piece previews, 2 overview PNGs; original geometry and mm scale unchanged; page heights extended for per-piece material notes.')
if __name__=='__main__':main()
