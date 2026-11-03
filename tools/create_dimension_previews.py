#!/usr/bin/env python3
"""Draw annotated textile artwork previews from manifest millimetres.

The dimensions belong to the existing artwork canvases, not fitted garment
pieces. Production artwork is read but never changed. Chinese labels are
outlined for reliable display; set FABRIC_LABEL_FONT to a local CJK TTF/TTC.
"""
from pathlib import Path
from copy import deepcopy
import argparse
import hashlib
import html
import json
import math
import os
import subprocess
import xml.etree.ElementTree as ET

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

ROOT = Path(__file__).resolve().parents[1]
FONT_PATH = Path(os.environ.get('FABRIC_LABEL_FONT', '/System/Library/Fonts/STHeiti Medium.ttc'))
FONT = TTFont(FONT_PATH, fontNumber=int(os.environ.get('FABRIC_LABEL_FONT_INDEX', '0')))
GLYPHS = FONT.getGlyphSet()
CMAP = FONT.getBestCmap()
UPM = FONT['head'].unitsPerEm
INK, MUTED, ACCENT = '#233747', '#576A76', '#A34E38'
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')

NAMES = {
    'skirt-border-panel': '裙摆边纹', 'collar-left': '披领左片',
    'collar-right': '披领右片', 'jacket-gradient-field': '外搭蓝紫渐变',
    'back-ribbon-left': '背部垂尾左片', 'back-ribbon-right': '背部垂尾右片',
    'waist-panel-left': '深色腰片左片', 'waist-panel-right': '深色腰片右片',
    'colored-four-petal-badge': '彩色四瓣花饰', 'white-four-petal-badge': '白色四瓣标志',
    'cuff-stripe-field': '袖口条纹', 'lilac-belt-field': '淡紫腰带',
    'H01': '胸前双卷纹', 'H02': '红衣前缘与内尾纹', 'H03': '侧面大下摆卷纹',
    'H04': '前方小下摆卷纹', 'H05': '肩部浅金青蓝纹', 'H06': '蓝色腰带',
    'H07': '粉色腰带', 'H08': '粉花布贴', 'H09': '白袖淡粉花边', 'H10': '蓝垂带边纹',
}


def label(x, y, value, size=24, fill=INK, anchor='start', rotate=None):
    widths = [GLYPHS[CMAP[ord(c)]].width for c in value]
    total = sum(widths) * size / UPM
    offset = {'start': 0, 'middle': total / 2, 'end': total}[anchor]
    elements = []
    cursor = x - offset
    for character, width in zip(value, widths):
        pen = SVGPathPen(GLYPHS)
        GLYPHS[CMAP[ord(character)]].draw(pen)
        if pen.getCommands():
            elements.append(f'<path d="{pen.getCommands()}" transform="translate({cursor:.4f} {y}) scale({size/UPM:.6f} {-size/UPM:.6f})"/>')
        cursor += width * size / UPM
    transform = f' transform="rotate({rotate} {x} {y})"' if rotate else ''
    return f'<g fill="{fill}" aria-label="{html.escape(value)}"{transform}><title>{html.escape(value)}</title>'+''.join(elements)+'</g>'


def rect(x, y, w, h, fill='none', stroke='none', radius=0, extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" {extra}/>'


def line(x1, y1, x2, y2, color=MUTED, width=1.4):
    return f'<path d="M{x1} {y1} L{x2} {y2}" fill="none" stroke="{color}" stroke-width="{width}"/>'


def horizontal_dimension(x, y, width, text, top_of_art):
    out = line(x, top_of_art, x, y-8) + line(x+width, top_of_art, x+width, y-8)
    out += line(x, y, x+width, y)
    out += f'<path d="M{x} {y} l9 -4 v8Z M{x+width} {y} l-9 -4 v8Z" fill="{MUTED}"/>'
    out += label(x+width/2, y-9, text, 23, anchor='middle')
    return out


def vertical_dimension(x, y, height, text, edge_of_art, text_left=False):
    out = line(edge_of_art, y, x+(8 if not text_left else -8), y)
    out += line(edge_of_art, y+height, x+(8 if not text_left else -8), y+height)
    out += line(x, y, x, y+height)
    out += f'<path d="M{x} {y} l-4 9 h8Z M{x} {y+height} l-4 -9 h8Z" fill="{MUTED}"/>'
    out += label(x+(-12 if text_left else 28), y+height/2, text, 23, anchor='middle', rotate=-90)
    return out


def embed(file, x, y, width, height, prefix):
    document = ET.fromstring(file.read_text())
    id_map = {n.get('id'): prefix+n.get('id') for n in document.iter() if n.get('id')}
    for n in document.iter():
        for attr, value in list(n.attrib.items()):
            if attr == 'id':
                n.set(attr, id_map[value])
            elif value.startswith('#') and value[1:] in id_map:
                n.set(attr, '#'+id_map[value[1:]])
            else:
                for old, new in id_map.items():
                    value = value.replace(f'url(#{old})', f'url(#{new})')
                n.set(attr, value)
    for key, value in {'x': x, 'y': y, 'width': width, 'height': height}.items():
        document.set(key, str(value))
    return ET.tostring(document, encoding='unicode')


def wrap(width, height, body, title):
    return f'<svg xmlns="{NS}" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}px" height="{height}px" viewBox="0 0 {width} {height}"><title>{title}</title><desc>Annotated preview only. All numbers come from manifest artwork_size_mm and canvas_mm. Not a production print file or a fitted garment pattern.</desc>{rect(0,0,width,height,"#F3F5F5")}{body}</svg>\n'


def overview(directory, manifest, title, records, master):
    width, height = 1800, 1510
    mw, mh = manifest['canvas_mm']
    scale = min(920/mw, 1110/mh)
    aw, ah = mw*scale, mh*scale
    ax, ay = 112, 230
    body = label(55, 67, f'三月七·{title}  整版尺寸总览', 39)
    body += label(57, 112, '现有纹样画布尺寸 · 单位 mm · 用于打样沟通', 25, MUTED)
    body += label(57, 150, '以下数值不是娃体、成衣或裁片尺寸；标注图不用于印布。', 23, ACCENT)
    body += rect(ax,ay,aw,ah,'#FFFFFF','#B6C1C9')
    body += embed(master, ax,ay,aw,ah,'overview-')
    body += horizontal_dimension(ax,ay-38,aw,f'{mw} mm',ay)
    body += vertical_dimension(ax-38,ay,ah,f'{mh} mm',ax,True)
    for record in records:
        x,y=record['sheet_origin_mm']; cw,ch=record['artwork_size_mm']
        bx,by,bw,bh=ax+x*scale,ay+y*scale,cw*scale,ch*scale
        body += rect(bx,by,bw,bh,'none',ACCENT,extra='stroke-width="1.2" stroke-dasharray="5 4"')
        body += rect(bx,by,52,27,'#FFFFFF',ACCENT,radius=3)
        body += label(bx+26,by+20,record['dimension_id'],19,ACCENT,'middle')
    body += label(1080, 233, '编号 / 纹样名称', 27)
    body += label(1080, 274, '尺寸均为「宽 × 高」，含组件画布留白。', 22, MUTED)
    body += line(1080,292,1735,292,'#CFD7DC')
    row_height = 80 if len(records)>10 else 95
    for i,record in enumerate(records):
        row=322+i*row_height
        body+=rect(1080,row-2,61,30,'#DFE7EB',radius=5)
        body+=label(1110.5,row+20,record['dimension_id'],21,INK,'middle')
        body+=label(1160,row+21,NAMES[record['id']],25)
        cw,ch=record['artwork_size_mm']
        body+=label(1160,row+53,f'{cw} × {ch} mm',25,MUTED)
        body+=line(1080,row+row_height-12,1735,row+row_height-12,'#DFE5E8',1)
    body += label(57, 1415, '橙色虚线表示纹样组件画布范围，供核对尺寸，不是裁剪线。', 24, MUTED)
    body += label(57, 1455, '图片为缩放预览；无标注 SVG / PNG / TIFF 才是印花文件。正式排版另按实际衣片定尺寸。', 23, MUTED)
    return wrap(width,height,body,f'三月七{title}整版尺寸总览 v0.1')


def components(directory, manifest, title, records):
    width=1800; cols=3; card_w=550; card_h=465; gap=25
    rows=math.ceil(len(records)/cols); height=228+rows*(card_h+gap)+108
    body=label(55,66,f'三月七·{title}  分件尺寸图',39)
    body+=label(57,111,'横向为宽，纵向为高；单位 mm。标注尺寸直接读取现有纹样文件。',25,MUTED)
    body+=label(57,151,'尺寸是打样设计值，非成衣或裁片尺码。各卡片按版面分别缩放，不可从屏幕量取。',23,ACCENT)
    for i, record in enumerate(records):
        cx=50+(i%cols)*(card_w+gap); cy=210+(i//cols)*(card_h+gap)
        body+=rect(cx,cy,card_w,card_h,'#FFFFFF','#D3DBDF',12)
        body+=rect(cx+23,cy+22,62,32,'#DFE7EB',radius=5)
        body+=label(cx+54,cy+45,record['dimension_id'],22,INK,'middle')
        body+=label(cx+101,cy+47,NAMES[record['id']],26)
        cw,ch=record['artwork_size_mm']
        body+=label(cx+25,cy+87,f'纹样画布：{cw} × {ch} mm',23,MUTED)
        scale=min(385/cw,245/ch)
        aw,ah=cw*scale,ch*scale
        ax=cx+44+(385-aw)/2; ay=cy+161+(245-ah)/2
        body+=rect(ax,ay,aw,ah,'#F3F4F3','#BEC9CF',extra='stroke-width="1" stroke-dasharray="5 4"')
        body+=embed(directory/record['file'],ax,ay,aw,ah,f'card{i}-')
        body+=horizontal_dimension(ax,ay-25,aw,f'{cw} mm',ay)
        body+=vertical_dimension(ax+aw+24,ay,ah,f'{ch} mm',ax+aw)
        body+=label(cx+25,cy+440,'尺寸包含该组件文件内的留白。',19,MUTED)
    footer=height-65
    body+=label(57,footer,'尺寸依据：manifest.json / artwork_size_mm。原彩色印花母版保持无尺寸线、无说明文字。',23,MUTED)
    body+=label(57,footer+37,'如更改图案大小，需同步更新源文件与尺寸清单，再生成这些预览。',23,MUTED)
    return wrap(width,height,body,f'三月七{title}分件尺寸图 v0.1')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render', action='store_true', help='Also render PNGs with Node and the installed sharp package.')
    args = parser.parse_args()
    rendered_sources = []
    for directory in sorted((ROOT/'projects/honkai-star-rail').glob('*/fabric-print')):
        manifest=json.loads((directory/'manifest.json').read_text())
        master=next(directory.glob('*-print-master-v0.1.svg'))
        is_hunt='hunt' in directory.parent.name
        title='巡猎' if is_hunt else '存护'
        records=deepcopy(manifest['components'])
        for i,record in enumerate(records):
            record['dimension_id']=record['id'] if is_hunt else f'S{i+1:02d}'
            source=ET.fromstring((directory/record['file']).read_text())
            actual=[float(source.attrib[axis].replace('mm','')) for axis in ('width','height')]
            assert actual==record['artwork_size_mm'], (record['id'],actual)
        for stem,document in [
            ('dimensions-overview-v0.1',overview(directory,manifest,title,records,master)),
            ('dimensions-components-v0.1',components(directory,manifest,title,records))]:
            root=ET.fromstring(document)
            ids=[n.get('id') for n in root.iter() if n.get('id')]
            assert len(ids)==len(set(ids)),f'Duplicate ids in {stem}'
            (directory/f'{stem}.svg').write_text(document)
            rendered_sources.append(str(directory/f'{stem}.svg'))
        checks={'status':'Dimension values checked against manifest and source SVG canvases; visual preview review required after rendering.',
                'units':'mm','canvas_mm':manifest['canvas_mm'],'dimension_kind':'artwork canvas, not garment or cutting-piece measurements',
                'source_manifest_sha256':hashlib.sha256((directory/'manifest.json').read_bytes()).hexdigest(),
                'components':[{'dimension_id':r['dimension_id'],'source_id':r['id'],'file':r['file'],'name':NAMES[r['id']],
                               'width_mm':r['artwork_size_mm'][0],'height_mm':r['artwork_size_mm'][1]} for r in records]}
        (directory/'dimension-checks-v0.1.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
        print(f'{title}: {manifest["canvas_mm"]} mm; {len(records)} components; overview and component SVGs created')
    if args.render:
        js = '''const sharp=require('sharp');
        (async()=>{for(const source of process.argv.slice(2)) {
          await sharp(source,{density:72}).flatten({background:'#FFFFFF'}).removeAlpha()
            .withIccProfile('srgb').png().toFile(source.replace(/\\.svg$/,'.png'));
          console.log('PNG: '+source.replace(/\\.svg$/,'.png'));
        }})().catch(error=>{console.error(error);process.exit(1)});'''
        subprocess.run([os.environ.get('FABRIC_NODE_BIN', 'node'), '-', *rendered_sources],
                       input=js, text=True, check=True)


if __name__=='__main__':
    main()
