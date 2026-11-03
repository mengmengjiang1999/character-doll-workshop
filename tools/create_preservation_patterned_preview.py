#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply existing authored motifs to unchanged full garment geometry; visual placement proof only."""
from pathlib import Path
import math,json,re,xml.etree.ElementTree as ET
import create_preservation_garment as g
from shapely.geometry import Polygon,LineString
from create_dimension_previews import label
OUT=g.OUT/'patterned';SOURCE=g.OUT.parent/'fabric-print/components'
NS='http://www.w3.org/2000/svg';ET.register_namespace('',NS);ET.register_namespace('xlink','http://www.w3.org/1999/xlink')
source=(SOURCE/'skirt-border-panel.svg').read_text()
DEFS=source[source.index('<defs>')+6:source.index('</defs>')].replace('xlink:href=','href=')
def doc(w,h,body,physical=False):
 return f'<svg xmlns="{NS}" width="{w}{"mm" if physical else "px"}" height="{h}{"mm" if physical else "px"}" viewBox="0 0 {w} {h}"><defs>{DEFS}</defs><rect width="100%" height="100%" fill="white"/>{body}</svg>'
def path(points,stroke,sw):
 return '<path d="M'+' L'.join(f'{x:.3f},{y:.3f}'for x,y in points)+f'" fill="none" stroke="{stroke}" stroke-width="{sw}"/>'
def use(motif,x,y,scale=1):return f'<use href="#{motif}" transform="translate({x} {y}) scale({scale})"/>'
def edge_lines(p,start,stop,offsets):
 edge=LineString(p['net'][start:stop]);out=''
 for off,color,width in offsets:
  q=edge.offset_curve(off,join_style=2)
  if q.geom_type=='LineString':out+=path(q.coords,color,width)
 return out

def art(p,token):
 pid=p['piece_id'];a,b,c,d=Polygon(p['cut']).bounds
 base=g.piece_color(p)
 if pid in ('P-O01','P-O02','P-O03','P-O04','P-O05'):base='#87ADE0'
 if pid=='P-O06':base='url(#jacketGradient)'
 if pid in ('P-A03L','P-A03R'):base='url(#ribbonGradient)'
 if pid in ('P-A01','P-A02'):base='#7ACCE2'
 if pid=='P-O07':base='#f7f3ed'
 cut_id='clip-'+token
 out=f'<defs><clipPath id="{cut_id}">'+g.svgpath(p['cut'])+'</clipPath></defs>'
 out+=f'<g clip-path="url(#{cut_id})">'+g.svgpath(p['cut'],base,'none')
 if pid=='P-B04':
  out+=f'<path d="M-3,2 H63 M-3,11.5 H63" fill="none" stroke="#7199B9" stroke-width=".9"/>'
 if pid=='P-B01':
  out+=path([(0,20),(0,74)],'#c9c4b7',.45)
  for y in (25,35):out+=f'<circle cx="0" cy="{y}" r="1.6" fill="#d7bf87" stroke="#a7936a" stroke-width=".35"/>'
 if pid in ('P-C01','P-C02'):
  out+=edge_lines(p,1,5,[(2.5,'#FAF9F6',1.15),(5,'#FAF9F6',1.15)])
 if pid in ('P-W01','P-W02','P-W03'):
  out+=edge_lines(p,1,27,[(2.2,'#D8C9A5',.8),(3.7,'#26262B',.4)])
 if pid=='P-S01':
  out+='<rect x="-5" y="72" width="430" height="19" fill="#FAF9F6"/><path d="M-5,67 H425" stroke="#FAF9F6" stroke-width="1.4"/>'
  for j in (0,3,6,9,12):out+=use('diamondMotif',j*30+5,61,.84)
  out+=use('outlineFlower',305,60,.19)
 return out+'</g>'

def write_piece(p):
 original=g.OUT/p['file'];root=ET.fromstring(original.read_text())
 defs=ET.fromstring('<defs xmlns="'+NS+'">'+DEFS+'</defs>');root.insert(0,defs)
 for group in root.findall('{'+NS+'}g'):
  if group.get('transform','').startswith('translate(') and not group.get('aria-label'):
   fragment=ET.fromstring('<g xmlns="'+NS+'">'+art(p,p['piece_id'])+'</g>');group.insert(1,fragment);break
 else:raise AssertionError('Missing original geometry group')
 caption=ET.fromstring(label(10,41,'花纹定位预览 / 非生产印布；圆点仅示意扣位',3.5,'#a44838'))
 root.append(caption)
 f=OUT/p['file'];f.parent.mkdir(parents=True,exist_ok=True);ET.ElementTree(root).write(f,encoding='unicode',xml_declaration=False)
 # Geometry must be byte-identical in SVG d coordinate content.
 oldpaths={n.get('d')for n in ET.fromstring(original.read_text()).iter()if n.tag.endswith('path')}
 newpaths={n.get('d')for n in root.iter()if n.tag.endswith('path')}
 assert oldpaths<=newpaths,p['piece_id']


def pieces_overview():
 cols=4;cw=440;ch=370;rows=math.ceil(len(g.pieces)/cols);W=1820;H=rows*ch+195
 body=label(35,55,'存护三月七 · 带花纹的完整衣片',40)+label(35,96,'原30片几何不变：先看花纹落位、衣片编号，再看净尺寸与裁剪尺寸。',23)
 body+=label(35,135,'定位预览，非定版印布：底色覆盖缝份，白边／金边按成品线内退；背面未知处留净色。',21,'#a34e38')
 for i,p in enumerate(g.pieces):
  x=30+(i%cols)*cw;y=180+(i//cols)*ch;a,b,c,d=Polygon(p['cut']).bounds;s=min(360/(c-a),175/(d-b),2)
  body+=f'<rect x="{x}" y="{y}" width="420" height="352" rx="12" fill="#f5f7f7" stroke="#c6d0d5"/>'+label(x+14,y+28,p['piece_id']+' '+p['name'],20)
  tx=x+210-(a+c)/2*s;ty=y+135-(b+d)/2*s
  body+=f'<g transform="translate({tx} {ty}) scale({s})">'+art(p,'board-'+p['piece_id'])+g.svgpath(p['cut'],'none','#465763',.65)+g.svgpath(p['net'],'none','#c85b43',.4,'2 1')
  for mark in p['marks']:body+=path(mark,'#3c7882',.3)
  body+='</g>'+label(x+14,y+243,f'净 {p["net_bbox_mm"][0]} × {p["net_bbox_mm"][1]} mm',20)+label(x+14,y+272,f'裁 {p["cut_bbox_mm"][0]} × {p["cut_bbox_mm"][1]} mm',19)
  body+=label(x+14,y+302,p['cut_count']+' / 缝份 '+str(p['allowance_mm'])+' mm',18)+label(x+14,y+331,p['layer'],17,'#607480')
 f=OUT/'pieces-overview.svg';f.write_text(doc(W,H,body));g.render(f,f.with_suffix('.png'),1800)


def flat(x,y,scale,layer,back=False):
 # Reuse the original garment silhouette, add existing motifs and visible part IDs.
 original=g.flat(0,0,1,layer,back)
 original=original.replace('fill="#bf9bda"','fill="url(#jacketGradient)"').replace('fill="#b1c4eb"','fill="url(#ribbonGradient)"').replace('fill="#d4a8e2"','fill="url(#ribbonGradient)"')
 original=original.replace('stroke-width="4"','stroke-width="1.8"').replace('fill="#c5b0dc"','fill="#f7f3ed"')
 extra=''
 if layer in (1,6) and not back:
  for cy in (60,73):extra+=f'<circle cx="150" cy="{cy}" r="2.6" fill="#d7bf87" stroke="#a7936a" stroke-width=".65"/>'
 if layer in (3,6) and not back:
  extra+=path([(97,44),(100,114),(95,132)],'#FAF9F6',1.8)+path([(203,44),(200,114),(205,132)],'#FAF9F6',1.8)
 if layer in (4,6):
  if back:extra+=use('diamondMotif',150,244,.7)+use('outlineFlower',198,242,.27)
  else:
   for xx in (118,150,182):extra+=use('diamondMotif',xx,244,.7)
 if layer in (5,6):
  if back:
   extra+=path([(113,172),(107,191),(101,211),(112,217),(122,210)],'#D8C9A5',1.5)+path([(187,172),(193,191),(199,211),(188,217),(178,210)],'#D8C9A5',1.5)
  else:
   extra+=path([(111,175),(105,192),(101,213),(114,221),(120,215)],'#D8C9A5',1.5)+path([(187,173),(192,204),(175,247),(165,236)],'#D8C9A5',1.5)
 if layer==6:
  # Applied flowers are shown assembled, not printed onto hidden support pieces.
  if back:extra+=use('coloredFlower',150,95,.33)
  else:extra+=use('coloredFlower',212,79,.34)
 tags=[]
 if layer==1:tags=[(150,102,'P-B02'if back else'P-B01','#31495b'),(58,135,'P-B03','#31495b'),(26,199,'P-B04','#31495b')]
 if layer==2:tags=[(150,104,'P-O02','#31495b')]if back else[(111,119,'P-O01','#31495b'),(182,178,'P-O04','#31495b')];tags +=[(62,102,'P-O03','#31495b'),(82,47,'P-O06','#31495b')]
 if layer==3:tags=[(150,166,'P-C02'if back else'P-C01','#31495b')]
 if layer==4:tags=[(150,220,'P-S01','#ffffff'),(150,148,'P-S02','#31495b')]
 if layer==5:tags=[(112,197,'P-W03'if back else'P-W01','#ffffff'),(178,216,'P-W03'if back else'P-W02','#ffffff'),(150,147,'P-W04','#31495b')]
 if layer==6:tags=[(150,89,'P-B02'if back else'P-B01','#31495b'),(150,224,'P-S01','#ffffff'),(213,198,'P-W02','#31495b')]
 if layer==6 and back:tags=[t for t in tags if not t[2].startswith('P-W')]
 if layer==6:tags.append((150,166,'P-W04','#31495b'))
 for xx,yy,txt,color in tags:
  extra+=f'<rect x="{xx-20}" y="{yy-10}" width="40" height="13" rx="2" fill="white" opacity=".88"/>'+label(xx,yy,txt,9,'#31495b','middle')
 if layer==6 and back:
  for xx,yy,txt in [(150,115,'P-A01'),(107,184,'P-A03L'),(197,198,'P-A03R')]:
   extra+=f'<rect x="{xx-21}" y="{yy-9}" width="42" height="12" rx="2" fill="white" opacity=".9"/>'+label(xx,yy,txt,8,'#34566b','middle')
 return f'<g transform="translate({x} {y}) scale({scale})">{original}{extra}</g>'

def layers_overview():
 W,H=1800,2140
 body=label(40,60,'存护三月七 · 花纹与衣片编号直接看',43)+label(40,104,'各层前后＋完整合穿；P编号对应下方衣片图；工程花纹预览，未试穿定版',23,'#a34e38')
 specs=[('01 白衬衣：扣位与蓝线袖口',1,'P-B01–P-B08｜贴边、包边、支承保持本白'),('02 蓝外搭：浅蓝身与紫粉翻片',2,'P-O01–P-O07｜紫粉集中于上臂翻片O06'),('03 深蓝尖披领：双白条',3,'P-C01–P-C02｜白条沿本轮成品外缘内退'),('04 十四褶裙：白边与菱形',4,'P-S01–P-S03｜标志排在成品可见褶面'),('05 不对称腰饰：深灰金边',5,'P-W01–P-W04｜金边走可见侧下边'),('06 合穿：背结上蓝下粉',6,'P-A01–P-A05｜四瓣花为外加饰物位置示意')]
 for i,(title,ly,sub) in enumerate(specs):
  x=35+(i%2)*885;y=145+(i//2)*635
  body+=f'<rect x="{x}" y="{y}" width="850" height="605" rx="18" fill="#f3f6f6" stroke="#cad4d8"/>'+label(x+24,y+43,title,28)+label(x+24,y+82,sub,20,'#637581')
  body+=label(x+207,y+117,'前面',22,anchor='middle')+label(x+633,y+117,'背面',22,anchor='middle')
  body+=flat(x+18,y+137,1.28,ly)+flat(x+440,y+137,1.28,ly,True)
  body+=label(x+24,y+575,'图中有编号与工艺信息，仅供校对；不是厂家印布图。',20,'#7b6562')
 body+=label(40,2110,'净轮廓、裁剪线及毫米尺寸沿用v0.2；未知背部花纹保持净色，定位后仍需检查褶量与缝口。',22)
 f=OUT/'layers-overview.svg';f.write_text(doc(W,H,body));g.render(f,f.with_suffix('.png'),1800)

def main():
 OUT.mkdir(exist_ok=True)
 for p in g.pieces:write_piece(p)
 pieces_overview();layers_overview()
 report={'status':'patterned visual placement proof only','units':'mm','original_piece_count':len(g.pieces),'original_piece_path_commands_preserved':True,'original_geometry_modified':False,'original_pdfs_modified':False,'production_print_ready':False,'sources':['../../fabric-print/components/skirt-border-panel.svg','../../fabric-print/components/collar-left.svg','../../fabric-print/components/waist-panel-left.svg','../../fabric-print/components/back-ribbon-left.svg'],'skirt_visible_pleat_faces':'each 30mm repeat leaves first10mm visible; diamonds centered at5,95,185,275,365; flower305','plain_hidden_parts':['P-B05','P-B06','P-B08','P-O07','P-S03','P-A04','P-A05'],'source_geometry':'../pattern-manifest.json','pieces':[{'piece_id':p['piece_id'],'file':p['file'],'net_bbox_mm':p['net_bbox_mm'],'cut_bbox_mm':p['cut_bbox_mm']}for p in g.pieces]}
 (OUT/'preview-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 (OUT/'README.md').write_text('# 存护完整衣片花纹预览\n\n[分层前后与合穿](layers-overview.png) · [30片花纹尺寸图](pieces-overview.png) · [逐片SVG](pieces/)\n\n本目录在v0.2实际衣片轮廓上直接显示花纹和编号，原净线、裁线、尺寸与PDF没有改动。底色延伸至原裁剪边，装饰白边、金边按成品边向内定位。所有字、编号、缝线均为校对内容，不能将本预览直接交厂印布。\n\n披领双白条、裙白宽边/细线/菱形/四瓣、袖口蓝线、上臂翻片蓝紫渐变、背结尾蓝粉渐变和腰饰金边来自现有自主绘制花型并按新轮廓重新定位。紫粉集中在肩翻片，蓝衣身保持浅蓝；未见背部纹样不由正面复制。白内衣、薄里、隐蔽支承保持净色。\n\n裙展开每30mm重复中的前10mm暂定为可见褶面，菱形和花形居中置于这些区域；仍须纸折和试布确认最终褶向。合穿图中花饰、扣位为外加配饰的定位示意，不代表要印在白衬衣或支承片上。\n\n图中P-B01等编号与[原完整衣片清单](../pattern-manifest.json)一一对应。[检查记录](preview-checks.json)核对30片原SVG路径均保留；尚未实物试穿或印样。\n')
 print('Created patterned proof for',len(g.pieces),'unchanged pieces',OUT)
if __name__=='__main__':main()
