#!/usr/bin/env python3
"""Reconstruct March 7th Preservation textile motifs as editable vector art.

Original source: official character illustrations and the locally inspected
official PMX textures. No raster source images or mesh data are embedded.
All millimetre dimensions are artwork trial choices, not doll measurements.
"""
from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'projects/honkai-star-rail/march-7th-preservation-bjd-1-4/fabric-print'
PALETTE = {
    'skirt_navy': '#334D83', 'collar_blue': '#3C578D',
    'jacket_blue': '#87ADE0', 'jacket_lilac': '#C98DD4',
    'ribbon_cyan': '#72CEE3', 'ribbon_blue': '#91B6EB', 'ribbon_pink': '#F0B8F2',
    'white': '#FAF9F6', 'pink': '#E996D1', 'cyan': '#82DFEF',
    'waist_charcoal': '#454143', 'gold': '#D8C9A5'
}
DEFS = '''
<linearGradient id="jacketGradient" x1="0" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="#C98DD4"/><stop offset="0.12" stop-color="#BF95DC"/>
 <stop offset="0.57" stop-color="#87ADE0"/><stop offset="1" stop-color="#87ADE0"/>
</linearGradient>
<linearGradient id="ribbonGradient" x1="0" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="#72CEE3"/><stop offset="0.28" stop-color="#84C9E8"/>
 <stop offset="0.62" stop-color="#AABCEC"/><stop offset="0.9" stop-color="#EDB7F1"/>
 <stop offset="1" stop-color="#F0B8F2"/>
</linearGradient>
<linearGradient id="beltGradient" x1="0" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="#B8A2DA"/><stop offset="0.5" stop-color="#C3B6E7"/>
 <stop offset="1" stop-color="#ACA3D8"/>
</linearGradient>
<g id="diamondMotif">
 <path d="M0,-6 L4.1,0 L0,6 L-4.1,0 Z" fill="#E7E8F7"/>
 <path d="M0,-6 L0,0 L-4.1,0 Z" fill="#F5C9F1"/>
 <path d="M0,-6 L4.1,0 L0,0 Z" fill="#F7F8FC"/>
 <path d="M-4.1,0 L0,0 L0,6 Z" fill="#84D7E8"/>
 <path d="M0,0 L4.1,0 L0,6 Z" fill="#B6B8E7"/>
</g>
<path id="fourPetalOutline" d="M0,-20 C9,-20 12,-13 8,-8 C13,-12 20,-9 20,0 C20,9 13,12 8,8 C12,13 9,20 0,20 C-9,20 -12,13 -8,8 C-13,12 -20,9 -20,0 C-20,-9 -13,-12 -8,-8 C-12,-13 -9,-20 0,-20 Z"/>
<g id="coloredFlower">
 <g id="coloredWhitePetal" fill="#FAF9F6">
  <path d="M0,1 C-7,-2 -9,-10 -5,-16 C-3,-19 0,-21 0,-21 C3,-19 7,-15 7,-11 C7,-6 4,-2 0,1 Z"/>
 </g>
 <use href="#coloredWhitePetal" transform="rotate(90)"/>
 <use href="#coloredWhitePetal" transform="rotate(180)"/>
 <use href="#coloredWhitePetal" transform="rotate(270)"/>
 <g fill="#E996D1">
  <ellipse cx="0" cy="-10.2" rx="2.8" ry="7.8"/><ellipse cx="10.2" cy="0" rx="7.8" ry="2.8"/>
  <ellipse cx="0" cy="10.2" rx="2.8" ry="7.8"/><ellipse cx="-10.2" cy="0" rx="7.8" ry="2.8"/>
 </g>
 <g fill="#82DFEF">
  <ellipse cx="0" cy="-9.5" rx="1.65" ry="6.4"/><ellipse cx="9.5" cy="0" rx="6.4" ry="1.65"/>
  <ellipse cx="0" cy="9.5" rx="1.65" ry="6.4"/><ellipse cx="-9.5" cy="0" rx="6.4" ry="1.65"/>
 </g>
 <circle r="2.1" fill="#FAF9F6"/>
</g>
<g id="outlineFlower">
 <use href="#fourPetalOutline" fill="none" stroke="#FAF9F6" stroke-width="3.1"/>
 <use href="#fourPetalOutline" transform="scale(.63)" fill="none" stroke="#FAF9F6" stroke-width="2.2"/>
 <circle r="2.4" fill="#FAF9F6"/>
</g>
'''


def svg(width, height, content, title):
    # SVG 1.1 xlink works in both desktop vector editors and PDF renderers.
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}">\n'
            f'<title>{title}</title>\n<desc>Editable textile artwork, millimetres; draft color and placement proof, no cut or seam lines.</desc>\n'
            f'<defs>{DEFS}</defs>\n{content}\n</svg>\n').replace('href=', 'xlink:href=')


def skirt():
    s = '<rect width="360" height="100" fill="#334D83"/>'
    # A broad light hem separated from the thin light stripe by a navy gap.
    s += '<rect y="77" width="360" height="1.7" fill="#FAF9F6"/>'
    s += '<rect y="83" width="360" height="17" fill="#FAF9F6"/>'
    for x in (26, 89, 152, 215, 278):
        s += f'<use href="#diamondMotif" transform="translate({x},67)"/>'
    s += '<use href="#outlineFlower" transform="translate(334,65) scale(.48)"/>'
    return s


def collar(mirror=False):
    # Filled artwork silhouette; not a cutting or stitching contour.
    s = '<path d="M5,0 H85 L70,110 L7,87 Z" fill="#3C578D"/>'
    s += '<path d="M73,0 L60.5,96 L7,77" fill="none" stroke="#FAF9F6" stroke-width="2.7"/>'
    s += '<path d="M66,0 L54.5,87 L7,69" fill="none" stroke="#FAF9F6" stroke-width="2.7"/>'
    return '<g transform="translate(90,0) scale(-1,1)">'+s+'</g>' if mirror else s


def waist(mirror=False):
    s = '<path d="M2,0 H83 V63 C83,90 54,103 6,120 L2,77 Z" fill="#454143"/>'
    s += '<path d="M78,0 V62 C78,86 51,99 6,114" fill="none" stroke="#D8C9A5" stroke-width="1.8"/>'
    s += '<path d="M74,0 V62 C74,83 50,96 6,110" fill="none" stroke="#26262B" stroke-width=".7"/>'
    return '<g transform="translate(85,0) scale(-1,1)">'+s+'</g>' if mirror else s


def ribbon(mirror=False):
    # The taper is a placement cue: the fabric piece is to be fitted separately.
    s = '<path d="M7,0 H68 C72,42 55,103 31,140 C8,99 0,45 7,0 Z" fill="url(#ribbonGradient)"/>'
    return '<g transform="translate(75,0) scale(-1,1)">'+s+'</g>' if mirror else s


def main():
    components = [
      ('skirt-border-panel',360,100,20,18,skirt(), 'P04 裙摆边纹；五枚菱形＋单枚白色四瓣标志'),
      ('collar-left',90,110,20,138,collar(), 'P03 披领双白线，左片展开示意'),
      ('collar-right',90,110,120,138,collar(True), 'P03 披领双白线，右片镜像展开示意'),
      ('jacket-gradient-field',160,110,220,138,'<rect width="160" height="110" fill="url(#jacketGradient)"/>', 'P03 外搭蓝紫过渡色场，可按最终衣片取位'),
      ('back-ribbon-left',75,140,20,267,ribbon(), 'P03 背部蝴蝶结垂尾的蓝粉渐变色场'),
      ('back-ribbon-right',75,140,110,267,ribbon(True), 'P03 背部蝴蝶结垂尾，镜像色场'),
      ('waist-panel-left',85,120,210,267,waist(), 'P05 深色腰片金色细边，平面展开示意'),
      ('waist-panel-right',85,120,305,267,waist(True), 'P05 深色腰片金色细边，镜像展开示意'),
      ('colored-four-petal-badge',44,44,20,430,'<use href="#coloredFlower" transform="translate(22,22)"/>', 'P06 白色长瓣、粉色内瓣、蓝色内心四瓣花饰的可选印刷版本'),
      ('white-four-petal-badge',44,44,80,430,'<rect width="44" height="44" fill="#334D83"/><use href="#outlineFlower" transform="translate(22,22) scale(.9)"/>', 'P04 裙侧四瓣线描标志的单独样块'),
      ('cuff-stripe-field',160,28,220,407,'<rect width="160" height="28" fill="#FAF9F6"/><rect y="18" width="160" height="2.1" fill="#334D83"/>', 'P02 白袖口蓝色细线色场'),
      ('lilac-belt-field',180,16,170,458,'<rect width="180" height="16" fill="url(#beltGradient)"/><path d="M0,2 H180 M0,14 H180" fill="none" stroke="#5F558B" stroke-width=".6"/>', 'P05 淡紫腰带的浅色平面色场与细边'),
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'components').mkdir(exist_ok=True)
    assembled = '<rect width="400" height="500" fill="#FFFFFF"/>\n'
    manifest = {'version':'v0.1-color-placement-proof','units':'mm',
        'canvas_mm':[400,500],'color_space_intent':'sRGB; no printer ICC profile applied',
        'status':'ARTWORK SAMPLE ONLY; placement, final cut shape and colors not approved for production',
        'source_basis':['official Preservation illustrations','official local PMX 衣服.png and 衣服1.png','local front/back/left/right reference renders'],
        'palette':PALETTE,'components':[],
        'no_cut_lines':True,'no_seam_lines':True,'no_printed_labels':True,
        'removed_from_reference':['3D shading','fold shadows','UV seams','mesh topology','metal buttons','camera and skin textures']}
    for name,w,h,x,y,content,mapping in components:
        assert x>=0 and y>=0 and x+w<=400 and y+h<=500
        doc=svg(w,h,content,name)
        ET.fromstring(doc)
        (OUT/'components'/f'{name}.svg').write_text(doc)
        assembled += f'<g id="{name}" transform="translate({x},{y})">{content}</g>\n'
        manifest['components'].append({'id':name,'file':f'components/{name}.svg',
            'artwork_size_mm':[w,h],'sheet_origin_mm':[x,y],'mapping':mapping,
            'scale_status':'design sample size, not measured doll or final pattern'})
    main_doc=svg(400,500,assembled,'March 7th Preservation textile color-placement proof v0.1')
    ET.fromstring(main_doc)
    (OUT/'preservation-print-master-v0.1.svg').write_text(main_doc)
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(f'Created 400 x 500 mm vector master and {len(components)} component SVGs in {OUT}')


if __name__ == '__main__':
    main()
