#!/usr/bin/env python3
"""Build March 7th Hunt placement-print artwork. Units are proof-design mm."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'projects/honkai-star-rail/march-7th-hunt-bandai-sitting-plush/fabric-print'
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'components').mkdir(exist_ok=True)

PALETTE = {
    'chest_brown': '#66505E', 'chest_scroll': '#A57E89',
    'hem_ground': '#493B48', 'hem_ink': '#251724',
    'vermilion': '#BE2F1D', 'red_shadow': '#891C20',
    'light_gold': '#EADDB9', 'gold_shadow': '#A99575',
    'ivory': '#FCF1DC', 'cyan': '#72CFE6',
    'sash_blue': '#54769C', 'ribbon_blue': '#7185AB',
    'pink': '#F3AFBE', 'pink_ink': '#D97996', 'sleeve_white': '#FFF8F5',
}

DEFS = '''<defs>
<linearGradient id="chestTone" x1="0" y1="0" x2="0" y2="1" gradientUnits="objectBoundingBox"><stop offset="0" stop-color="#725A65"/><stop offset="1" stop-color="#534451"/></linearGradient>
<linearGradient id="redTone" x1="0" y1="0" x2="0" y2="1" gradientUnits="objectBoundingBox"><stop offset="0" stop-color="#CC3C22"/><stop offset="1" stop-color="#AF251E"/></linearGradient>
<linearGradient id="blueTone" x1="0" y1="0" x2="0" y2="1" gradientUnits="objectBoundingBox"><stop offset="0" stop-color="#6B92BA"/><stop offset="0.52" stop-color="#5A80AB"/><stop offset="1" stop-color="#42658C"/></linearGradient>
<linearGradient id="pinkTone" x1="0" y1="0" x2="0" y2="1" gradientUnits="objectBoundingBox"><stop offset="0" stop-color="#F9CAD1"/><stop offset="0.5" stop-color="#F4B6C4"/><stop offset="1" stop-color="#E99BAF"/></linearGradient>
<g id="chestCurl">
 <path d="M3 3 C23 11 42 16 65 20 C84 24 94 43 94 61 C94 86 71 102 46 99 C22 96 7 77 8 56 C9 39 19 28 33 29 C49 30 58 43 54 55 C51 65 39 68 32 61 C27 56 28 49 32 47 C30 55 39 58 43 53 C49 43 38 35 30 38 C15 42 18 65 29 76 C42 90 66 92 79 76 C90 63 84 42 69 35 C53 28 32 29 18 22 C11 18 6 10 3 3Z" fill="#A57E89"/>
 <path d="M3 3 C7 10 11 18 18 22 C32 29 53 28 69 35 C84 42 90 63 79 76 C71 85 63 88 52 87 C69 84 76 75 75 62 C74 43 51 38 34 33 C17 28 9 20 3 3Z" fill="#8D6979"/>
</g>
<g id="openingCurl">
 <path d="M18 3 C7 2 0 9 1 18 C2 27 12 30 19 26 C25 23 26 17 21 14 C17 12 14 14 14 18 C16 17 19 18 18 21 C14 26 6 22 6 17 C5 10 12 7 20 9 C34 12 45 23 56 38 C68 55 76 74 87 87 C76 64 70 42 55 26 C44 13 31 4 18 3Z" fill="#F3E9CD"/>
 <path d="M24 11 C41 16 49 28 59 44 C69 60 76 76 87 87 C82 75 73 55 63 38 C50 17 37 11 24 11Z" fill="#C8B78D"/>
 <path d="M16 29 C31 29 42 37 53 49 C68 64 75 80 87 87 C72 81 61 68 48 55 C36 43 26 35 16 29Z" fill="#EADDB9"/>
</g>
<g id="shoulderEmblem">
 <path d="M34 5 C26 4 22 9 23 15 C16 10 9 14 7 20 C2 31 12 38 22 35 C18 47 26 52 33 47 C37 45 39 41 39 35 C48 40 57 35 58 27 C60 17 49 12 42 16 C43 9 40 5 34 5Z" fill="#EADDB9"/>
 <path d="M34 8 C28 8 25 13 28 20 C22 15 15 16 12 21 C6 30 16 35 26 30 C22 39 25 46 31 43 C36 40 36 32 35 27 C40 34 49 35 53 30 C59 23 49 17 40 21 C41 14 39 9 34 8Z" fill="#FAF3DB"/>
 <path d="M33 10 C30 13 31 19 34 21 C37 17 37 13 33 10Z M29 21 C23 17 18 19 15 23 C20 27 26 25 29 21Z M39 21 C42 16 49 18 51 23 C46 26 42 25 39 21Z" fill="#6ACEE5"/>
 <path d="M24 40 C24 52 15 58 14 65 C22 63 26 55 28 50 C28 60 35 64 37 73 C38 61 31 56 33 48 C37 45 39 40 39 36 L36 38 C33 47 29 48 24 40Z" fill="#EADDB9"/>
 <path d="M18 55 C9 53 8 59 12 62 C15 61 15 58 18 55Z M27 58 C24 65 25 73 20 79 C28 76 30 67 27 58Z M36 67 C38 73 42 76 41 83 C46 76 41 71 36 67Z" fill="#D6C69C"/>
</g>
<g id="blossom">
 <path d="M30 26 C15 12 9 3 18 1 C25 -1 29 9 30 17 C31 8 37 -1 44 2 C53 7 44 19 35 26 C45 19 57 18 59 27 C61 38 47 41 35 32 C46 41 45 54 36 56 C28 58 25 46 29 35 C22 45 11 48 6 40 C0 30 13 24 26 29 C16 27 17 21 22 23Z" fill="#FBC8CF" stroke="#D97996" stroke-width="1.3" stroke-linejoin="round"/>
 <path d="M30 28 C26 18 24 11 20 7 C18 15 24 24 30 28Z M32 28 C35 19 41 12 43 9 C45 18 38 25 32 28Z M33 30 C42 27 49 26 53 29 C49 35 41 33 33 30Z M31 32 C31 40 32 46 35 49 C39 44 36 37 31 32Z M29 31 C21 32 14 36 12 39 C19 40 25 35 29 31Z" fill="#E68AA4"/>
 <circle cx="31" cy="30" r="2.4" fill="#FDE7DF"/>
</g>
<g id="quatrefoil">
 <path d="M14 10 C5 1 -3 8 5 15 C-4 22 4 29 13 21 C20 31 28 24 21 16 C31 9 23 1 15 10Z" fill="#EEE9E1" stroke="#B7B7CA" stroke-width="1.5"/>
 <path d="M13.6 12 C7 6 4 10 10 15 C3 20 7 24 13.8 18 C19 25 24 21 18.2 16 C26 11 21 7 16 12Z" fill="#CED3DE"/>
 <path d="M14 13 C12 10 10 12 12 15 C9 17 11 19 14 17 C16 20 18 18 16 16 C19 14 17 12 15 14Z" fill="#F9F4E9"/>
</g>
</defs>'''

def rect(w,h,color):
    return f'<rect width="{w}" height="{h}" fill="{color}"/>'

parts = []
def part(code, filename, name, w,h,x,y, body, observed, reconstruction):
    parts.append(dict(code=code, file=filename, name=name, width_mm=w,height_mm=h,
                      sheet_x_mm=x,sheet_y_mm=y, body=body,
                      observed=observed, reconstruction=reconstruction))

part('H01','h01-chest-scrolls.svg','胸前双内卷纹',230,140,10,10,
     rect(230,140,'url(#chestTone)') + '''
<path d="M8 8 C44 18 74 17 112 3 L112 137 L108 137 L108 12 C70 26 41 25 8 15Z" fill="#BDA57F"/>
<path d="M222 8 C186 18 156 17 118 3 L118 137 L122 137 L122 12 C160 26 189 25 222 15Z" fill="#BDA57F"/>
<path d="M113 0 L117 0 L117 140 L113 140Z" fill="#F1E0B7"/>
<path d="M119 0 L121 0 L121 140 L119 140Z" fill="#DAC598"/>
<use href="#chestCurl" transform="translate(104 24) scale(-.94 .99)"/>
<use href="#chestCurl" transform="translate(126 24) scale(.94 .99)"/>
<path d="M5 129 C35 139 75 139 104 131 L104 134 C74 142 35 142 5 133Z M126 131 C156 139 196 139 225 129 L225 133 C195 142 156 142 126 134Z" fill="#483944"/>
''', '正面深褐胸片、浅褐向内收卷纹、中央浅金双线可见。',
     '两侧纹样从有透视的单幅立绘手绘展开；左右对称、纹样长度和边距是本次印样排布选择，未读取模型贴图。')

part('H02','h02-red-opening-scrolls.svg','红外衣浅金前缘与暗红内尾纹',240,140,250,10,
     rect(240,140,'url(#redTone)') + '''
<path d="M115 0 L125 0 L125 140 L115 140Z" fill="#B32A20"/>
<use href="#openingCurl" transform="translate(15 28) scale(1.02 1.12)"/>
<path d="M146 16 C157 12 166 20 165 32 C178 19 195 22 195 36 C209 27 223 34 221 46 C220 57 210 63 201 65 C218 66 225 77 219 86 C214 96 201 95 193 90 C199 103 193 116 183 116 C169 115 166 98 162 88 C157 75 145 68 143 54 C141 42 144 30 146 16Z" fill="#A52A23" stroke="#7E1D20" stroke-width="1.8" stroke-linejoin="round"/>
<path d="M151 23 C161 22 161 37 158 44 C175 25 189 28 186 40 C183 48 174 51 166 55 C185 45 210 35 214 45 C217 54 198 59 181 62 C199 61 218 70 213 80 C208 88 194 81 181 75 C188 86 194 102 183 107 C174 107 172 92 168 82 C162 68 151 65 150 52 C148 43 152 34 151 23Z" fill="none" stroke="#7E1D20" stroke-width="1.6" stroke-linejoin="round"/>
<path d="M5 0 L8 0 L8 140 L5 140Z M232 0 L235 0 L235 140 L232 140Z" fill="#85212A"/>
''', '角色右前襟有开口回卷，再分成两道向下延伸的浅金长弧；抬袖后方红长尾内侧可见暗红轮廓的瓣形回卷纹。',
     '左半为可见前缘浅金纹，右半为内侧长尾暗红纹；两个位置合放一块红色印样方便比色，并不代表同一衣片。暗红细节较小，瓣形轮廓为手绘近似展开。')

part('H03','h03-large-hem-scroll.svg','可见侧大下摆回卷纹',230,170,10,160,
     rect(230,170,'#493B48') + '''
<path d="M7 17 C57 -2 145 1 221 43 C213 93 184 131 149 147 C99 170 43 162 10 135Z" fill="#B29F79"/>
<path d="M12 20 C62 4 146 8 215 46 C205 92 180 127 146 141 C101 161 47 155 15 131Z" fill="#F0E3BC"/>
<path d="M17 25 C65 10 145 14 210 49 C200 91 176 122 144 136 C103 155 51 150 20 128Z" fill="#302632"/>
<path d="M21 29 C67 16 142 19 204 52 C193 87 177 105 161 119 C126 141 69 145 26 124Z" fill="#4C3E4B"/>
<path d="M190 50 C165 33 132 23 107 29 C81 35 70 53 78 69 C86 86 111 91 128 80 C142 71 137 56 124 53 C115 50 105 53 102 60 C109 58 119 62 118 68 C116 75 103 75 96 69 C86 59 100 46 117 47 C138 48 155 61 154 78 C152 98 131 107 110 103 C129 113 153 106 171 93 C187 81 193 66 190 50Z" fill="#251724"/>
<path d="M192 49 C203 50 205 53 203 61 C200 76 188 90 176 98 C168 104 168 116 159 126 C150 136 139 139 122 143 C142 131 143 119 140 111 C158 109 180 91 187 74 C192 65 194 57 192 49Z" fill="#251724"/>
<path d="M82 45 C65 42 58 49 57 59 C57 66 61 71 69 74 C62 63 67 53 82 45Z M96 31 C88 27 81 29 78 36 C81 41 83 44 86 44 C86 37 90 33 96 31Z" fill="#251724"/>
''', '立绘画面右侧的大下摆具有浅金包边、深褐底和单向大回卷；卷纹下部连向分叉尾部。',
     '将侧面透视手绘展开为平面定位印花。金色外缘为要印在布上的装饰，不是裁剪线。遮挡处收在净色底，不续画背面。')

part('H04','h04-small-front-hem-scroll.svg','前下摆小回卷纹',135,170,250,160,
     rect(135,170,'#493B48') + '''
<path d="M7 18 C40 6 82 7 127 31 L120 135 C91 155 54 163 14 149Z" fill="#B29F79"/>
<path d="M11 21 C43 11 82 12 123 34 L116 132 C90 150 54 158 18 146Z" fill="#F0E3BC"/>
<path d="M16 27 C46 18 81 18 118 38 L111 129 C88 144 55 152 23 141Z" fill="#332331"/>
<path d="M23 37 C41 26 76 24 107 39 L104 119 C84 133 57 141 28 134Z" fill="#55404E"/>
<path d="M89 42 C62 27 35 39 31 62 C27 84 42 102 62 101 C82 101 94 87 91 72 C88 59 72 54 61 62 C56 66 56 73 60 77 C58 69 67 66 72 71 C80 79 68 89 58 85 C43 79 43 60 57 51 C74 40 95 50 99 68 C104 88 88 104 71 112 C51 122 40 122 29 118 L31 130 C55 131 91 115 104 97 C115 78 109 55 89 42Z" fill="#281925"/>
<path d="M91 42 C101 35 107 42 109 50 L107 66 C106 57 101 49 91 42Z M34 95 C27 97 25 106 29 113 C31 106 36 103 42 102Z" fill="#281925"/>
''', '腰带下方可见的小片前下摆为深褐底浅金边，中央也是单个回卷，与侧片比例不同。',
     '遮挡和透视较强；轮廓边距及长宽为单独纹样打样设计，不作为小玩偶衣片外形。')

part('H05','h05-shoulder-gold-cyan.svg','肩部浅金青蓝纹样试样',95,170,395,160,
     rect(95,170,'url(#redTone)') + '''
<use href="#shoulderEmblem" transform="translate(12 1) scale(1.05 .94)"/>
<use href="#shoulderEmblem" transform="translate(12 85) scale(1.05 .94)"/>
''', '肩头可见浅金/乳白云头状三瓣结构，中部三个青蓝小瓣，下接细长金色分叉。',
     '此处是把可见肩饰表面转为印花的可选方案；原造型含立体层次。两枚同图只供颜色、尺寸试样，不声称左右纹样一致。')

part('H06','h06-blue-sash.svg','蓝色腰带素色试样',480,42,10,340,
     rect(480,42,'url(#blueTone)') + '''
<path d="M0 0 H480 V2.2 H0Z" fill="#A6CEEA"/>
<path d="M0 39.5 H480 V42 H0Z" fill="#355776"/>
''', '交叉腰带为蓝色，有亮浅边和暗边；蝴蝶结扣是立体装饰。',
     '只输出蓝色带材印样与上下边色差，不把金属扣画成布料纹样。带宽 42 mm 是打样尺寸。')

part('H07','h07-pink-sash.svg','粉色腰带素色试样',480,42,10,392,
     rect(480,42,'url(#pinkTone)') + '''
<path d="M0 0 H480 V1.6 H0Z" fill="#FEE6E7"/>
<path d="M0 40.8 H480 V42 H0Z" fill="#D88CA4"/>
''', '腰间有浅粉色长带；花形装饰有独立厚度。',
     '素色带与花形分开，允许后期缠花/缝制叠装；本带材的渐变为试色选择。')

part('H08','h08-pink-flower-applique-print.svg','粉花可选布贴印花',150,146,10,444,
     rect(150,146,'#FFE7E9') + '''
<use href="#blossom" transform="translate(7 8) scale(.94)"/>
<use href="#blossom" transform="translate(80 8) scale(.94)"/>
<use href="#blossom" transform="translate(7 79) scale(.94)"/>
<use href="#blossom" transform="translate(80 79) scale(.94)"/>
''', '腰侧可见浅粉色花形结，深粉描边/花瓣内纹，轮廓受角度与折叠影响。',
     '花结简化为平面五瓣叠贴方案；原件层次建议另缝或缠花。本平面替代并非官方纹样精确描摹。')

part('H09','h09-white-sleeve-flower-print.svg','白袖淡粉花边试样',155,146,170,444,
     rect(155,146,'#FFF8F5') + '''
<g opacity=".53">
<use href="#blossom" transform="translate(14 72) scale(.65)"/>
<use href="#blossom" transform="translate(54 82) scale(.64) rotate(-17 30 30)"/>
<use href="#blossom" transform="translate(94 65) scale(.66) rotate(16 30 30)"/>
</g>
<path d="M0 128 C25 117 44 127 62 125 C89 123 109 107 155 113 L155 116 C109 110 89 126 63 128 C41 131 25 121 0 132Z" fill="#EAC7D5"/>
<path d="M0 138 C28 125 49 136 72 133 C101 130 125 118 155 124 L155 127 C125 121 101 134 73 136 C48 140 28 128 0 142Z" fill="#F1D4DF"/>
''', '抬起的白袖近袖缘有很浅的粉色花形/缎边，局部可见。',
     '这是可见色彩及花形的平面布贴/印花替代试样；原件具体工艺与被遮挡处不确定，没有补画完整一圈。')

part('H10','h10-blue-ribbon-tail-print.svg','蓝垂带浅色边与小花纹',155,146,335,444,
     rect(155,146,'#687D9E') + '''
<path d="M5 0 H10 V146 H5Z M145 0 H150 V146 H145Z" fill="#DADDE0"/>
<path d="M11 0 H13 V146 H11Z M142 0 H144 V146 H142Z" fill="#A5AEC2"/>
<path d="M34 0 C35 14 48 13 47 27 C45 38 24 33 24 48 C24 57 38 57 39 67 C42 82 26 81 24 95 C22 105 36 113 35 124 C34 137 23 137 25 146 H33 C30 137 42 136 43 124 C44 110 31 104 32 95 C33 88 48 83 46 68 C45 54 31 53 32 46 C33 39 52 43 55 28 C57 11 42 11 42 0Z" fill="#C0C5D1"/>
<path d="M45 0 C46 13 59 14 56 30 C54 39 46 43 43 46 C51 44 62 40 63 29 C65 12 51 10 52 0Z" fill="#8F9CB6"/>
<use href="#quatrefoil" transform="translate(59 19) scale(1.2)"/>
<use href="#quatrefoil" transform="translate(90 67) scale(.72)"/>
<use href="#quatrefoil" transform="translate(57 108) scale(.52)"/>
''', '画面右上蓝色垂带有浅边，靠末端有曲折浅色带纹与逐渐缩小的四瓣花。',
     '把一条弯折透视的可见垂带局部整理成矩形纹样试样；并非完整环绕或背面纹样。')

def svg(w,h,body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">' + DEFS + body.replace('href=', 'xlink:href=') + '</svg>\n'

for p in parts:
    (OUT/'components'/p['file']).write_text(svg(p['width_mm'],p['height_mm'],p['body']))
sheet = '<rect width="500" height="600" fill="#FFFFFF"/>'
for p in parts:
    sheet += f'<g transform="translate({p["sheet_x_mm"]} {p["sheet_y_mm"]})">{p["body"]}</g>'
(OUT/'hunt-print-master-v0.1.svg').write_text(svg(500,600,sheet))

manifest = {
    'version':'0.1', 'status':'reference-based placement-print colour proof; unmeasured sample dimensions',
    'character':'三月七 · 巡猎 · 公式服', 'units':'mm', 'canvas_mm':[500,600],
    'no_cut_lines':True, 'no_seam_lines':True, 'no_printed_labels':True,
    'sheet':{'file':'hunt-print-master-v0.1.svg','width_mm':500,'height_mm':600,
             'background':'white','rendered_text':False,'cut_lines':False,'external_images':False},
    'size_status':'All dimensions are chosen for textile proofing. No Bandai body dimensions are implied; no fitted cutting pattern is supplied.',
    'colour_space':'sRGB, unprofiled screen reconstruction; no printer ICC applied',
    'palette':PALETTE,
    'references':[
        {'source':'HoYoLAB official character preview','url':'https://www.hoyolab.com/article/31407362','local':'../references/local/images/hunt-official-preview.jpg'},
        {'source':'HoYoWiki official splash art','url':'https://wiki.hoyolab.com/pc/hsr/entry/2657?lang=en-us','local':'../references/local/images/splash-art.png'},
        {'source':'official model publishing page cover; cover is splash illustration, not a model orthographic view','url':'https://www.aplaybox.com/details/model/KG9eRZVCtc9y','local':'../references/local/official-models/official-model-cover.jpg'},
    ],
    'not_claimed':['official texture extraction','exact scale','verified Bandai fit','reconstructed back view','print colour accuracy','metallic ink'],
    'components':[dict(id=p['code'], file='components/'+p['file'], artwork_size_mm=[p['width_mm'],p['height_mm']], sheet_origin_mm=[p['sheet_x_mm'],p['sheet_y_mm']], mapping=p['name'], scale_status='design sample size, not measured doll or final pattern', observed=p['observed'], reconstruction=p['reconstruction']) for p in parts],
}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')

rows = '\n'.join(f'| {p["code"]} | [{p["name"]}](components/{p["file"]}) | {p["width_mm"]} × {p["height_mm"]} | {p["sheet_x_mm"]}, {p["sheet_y_mm"]} |' for p in parts)
observations = '\n\n'.join(f'### {p["code"]} · {p["name"]}\n\n观察：{p["observed"]}\n\n重绘/制作选择：{p["reconstruction"]}' for p in parts)
mapping = f'''# 三月七巡猎公式服 · 布料定位印花 v0.1

这是根据官方立绘可见花纹手绘的彩色布料印样，交付内容是布上要印的底色和装饰图案。500 × 600 mm 画布及各色块尺寸为**本次打样设计尺寸**，尚未按万代玩偶衣片定尺；没有裁剪线、缝线、对位字、说明文字或尺标印入生产图。金色曲边是服饰装饰图案本身，不应拿来当纸样边界。

## 文件与排布

生产母版：[500 × 600 mm SVG](hunt-print-master-v0.1.svg)。每块独立 SVG 可在矢量软件里单独调整纹样大小和位置，再按照最终衣片放定位印花；不可把整张缩放后假定适配。

坐标从整张左上角计算，单位均为 mm。

| 编号 | 色块/独立母版 | 宽 × 高 | 左上角 x, y |
|---|---|---:|---:|
{rows}

## 观察依据与还原边界

三张参考实际呈现同一姿态的官方立绘；模型发布封面并不是三视图。没有以封面冒充模型贴图，也没有读取到巡猎 PMX 贴图。图案为手绘贝塞尔路径，保留了可见的回卷走向、浅金边、青蓝肩纹、粉花及垂带细节；展开、对称和色值存在重绘判断，不能称为官方原纹理精确拷贝。

{observations}

## 印厂交接

- 先按母版 500 × 600 mm、100% 尺寸出布料色样；文件内白色区为无图案留白，是否打印白墨由底布及厂商工艺决定。
- 源色为空间 sRGB 的屏幕近似值，尚未做印厂 ICC 转换。浅金为普通黄米色油墨的视觉模拟，不会产生金属反光；是否叠加金箔/金色工艺应另外约定。
- 这版可用于比较底布吃色、深褐层次、浅金和淡粉的显色，不应未经打样直接整套量产。立绘光照被尽量简化；梯度是本次印样选择。
- 成衣定位印花仍需把每一块图案放入最终衣片的真实尺寸，并由厂家按具体裁切精度决定出血。此版不写入虚构的出血或缝份。
- 蝴蝶金属扣、发饰和立体花结不在本平面母版内假装复原；H05、H08、H09 的平面替代性质已单独标明。
- 本次没有复原未知背面。原始官方图片保持在忽略的 references/local/ 目录，生产 SVG 仅含本次绘制的矢量图形。

## 来源

- [HoYoLAB 角色前瞻](https://www.hoyolab.com/article/31407362)
- [HoYoWiki 三月七巡猎](https://wiki.hoyolab.com/pc/hsr/entry/2657?lang=en-us)
- [官方模型发布页封面](https://www.aplaybox.com/details/model/KG9eRZVCtc9y)

校验：SVG XML 可解析；没有渲染文字、外部链接图片、裁剪线或纸样标记。物理印布、色准及玩偶适配尚未验证。
'''
(OUT/'mapping.md').write_text(mapping)
for f in OUT.glob('**/*.svg'):
    root=ET.parse(f).getroot()
    assert root.attrib['width'].endswith('mm') and root.attrib['height'].endswith('mm')
    assert not root.findall('.//{http://www.w3.org/2000/svg}text')
    assert not root.findall('.//{http://www.w3.org/2000/svg}image')
for p in parts:
    assert 0<=p['sheet_x_mm'] and p['sheet_x_mm']+p['width_mm']<=500
    assert 0<=p['sheet_y_mm'] and p['sheet_y_mm']+p['height_mm']<=600
print(f'Created 1 sheet, {len(parts)} components, manifest and mapping in {OUT}')
