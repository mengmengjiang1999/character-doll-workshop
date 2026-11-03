#!/usr/bin/env python3
"""Complete Hunt seated-plush engineering toile. Dimensions are DESIGN assumptions, not Bandai measurements."""
from pathlib import Path
import sys, math, json, html, os, subprocess
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tmp/garment-python'))
from shapely.geometry import Polygon, LineString
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import fitz
from create_dimension_previews import label
OUT=ROOT/'projects/honkai-star-rail/march-7th-hunt-bandai-sitting-plush/garment-pattern'
PARAMS={'version':'v0.2-engineering-toile','units':'mm','actual_Bandai_measurements':False,'basis':'Independent design dummy; NOT inferred from product height or copied from third-party pattern','chest_circumference_assumed':400,'maximum_abdomen_circumference_assumed':460,'chest_ease':20,'abdomen_ease':20,'shoulder_width_design':148,'front_center_length_design':125,'back_center_length_design':145,'underarm_depth_design':58,'sleeve_length_design':100,'cuff_finished_circumference_design':120,'regular_allowance':6,'turned_detail_allowance':4,'closure_total_overlap':12,'hook_loop_width':8,'neck_half_width_design':36,'base_front_chest_share':0.5238095238,'base_front_belly_share':0.5208333333}
paramfile=OUT/'parameters-v0.2.json'
if '--parameters' in sys.argv:
    PARAMS.update(json.loads(Path(sys.argv[sys.argv.index('--parameters')+1]).read_text()))
P=PARAMS
pieces=[];checks=[]
def bez(a,b,c,d,n=24):
    return [tuple((1-t)**3*a[j]+3*(1-t)**2*t*b[j]+3*(1-t)*t*t*c[j]+t**3*d[j] for j in (0,1)) for t in [i/n for i in range(n+1)]]
def addpaths(*paths):
    out=[]
    for q in paths: out+=q if not out or out[-1]!=q[0] else q[1:]
    return out

def length(p):return LineString(p).length

def along(p,f):
    q=LineString(p).interpolate(f,normalized=True);return (q.x,q.y)
def reflect(p):return [(-x,y) for x,y in p]
def rect(w,h):return [(0,0),(w,0),(w,h),(0,h)]
def add(pid,name,pts,count,material,sa=6,layer='',joins='',notes='',marks=None):
    poly=Polygon(pts)
    assert poly.is_valid,(pid,'invalid net polygon')
    cut=poly.buffer(sa,join_style=2,mitre_limit=2)
    assert cut.is_valid and cut.geom_type=='Polygon',(pid,'invalid cut polygon')
    assert cut.contains(poly),(pid,'allowance does not surround net')
    p={'piece_id':pid,'name':name,'cut_count':count,'material':material,'allowance_mm':sa,'layer':layer,'joins':joins,'notes':notes,'net_bbox_mm':[round(poly.bounds[2]-poly.bounds[0],2),round(poly.bounds[3]-poly.bounds[1],2)],'cut_bbox_mm':[round(cut.bounds[2]-cut.bounds[0],2),round(cut.bounds[3]-cut.bounds[1],2)],'net':list(poly.exterior.coords),'cut':list(cut.exterior.coords),'marks':marks or [],'file':f'pieces/{pid}.svg'}
    pieces.append(p);return p

def edgecheck(name,a,b,ease=0,tol=.15):
    av,bv=length(a),length(b)
    checks.append({'pair':name,'edge_a_mm':round(av,3),'edge_b_mm':round(bv,3),'planned_ease_mm':ease,'residual_mm':round(av-bv-ease,5),'pass':abs(av-bv-ease)<tol})

# Inputs express intended circumferences; front/back distribute volume differently.
chest=P['chest_circumference_assumed']+P['chest_ease'];belly=P['maximum_abdomen_circumference_assumed']+P['abdomen_ease']
f=chest*P['base_front_chest_share']/2;b=(chest-2*f)/2
fb=belly*P['base_front_belly_share']/2;bb=(belly-2*fb)/2
# Same translated side curve preserves sewing length; use abdomen distribution compatible with front/back chest difference.
assert abs((fb-f)-(bb-b))<.01,'front and back volume increments must match for paired side seams'
shoulder=P['shoulder_width_design']/2;nh=P['neck_half_width_design'];depth=P['underarm_depth_design'];delta=fb-f
neck=bez((0,22),(15,22),(nh,16),(nh,0))
should=[(nh,0),(shoulder,10)]
armF=bez((shoulder,10),(shoulder-5,32),(f-28,52),(f,depth))
armB=bez((shoulder,10),(shoulder-3,31),(b-17,48),(b,depth))
sideF=bez((f,depth),(f+delta+3,88),(f+delta+3,116),(f+delta-5,140))
sideB=[(x-f+b,y) for x,y in sideF]
hemF=bez(sideF[-1],(95,138),(45,P['front_center_length_design']),(0,P['front_center_length_design']))
frontHalf=addpaths(neck,should,armF,sideF,hemF)
front=addpaths(frontHalf,list(reversed(reflect(frontHalf))))
cb=P['closure_total_overlap']/2
neckB=bez((0,7),(13,7),(nh,5),(nh,0))
back=addpaths([(-cb,7),(0,7)],neckB,should,armB,sideB,bez(sideB[-1],(80,145),(28,P['back_center_length_design']),(-cb,P['back_center_length_design'])))
basefront=add('H-B01','浅色底衣前身',front,'面布 1','M5',layer='L1 基础衣身',joins='左右肩→B02；侧缝→B02；袖窿→B03；领口→B05',notes='完整前片，无中前缝；腹部曲线放量，前中较侧摆短。',marks=[[(0,27),(0,113)]])
baseback=add('H-B02','浅色底衣后片',back,'面布 2，镜像','M5',layer='L1 基础衣身',joins='肩/侧→B01；袖窿→B03；后中→B06贴边',notes='原后中线 x=0；成品边跨线6；左上搭内面软圈，右下搭朝外细勾。',marks=[[(0,15),(0,135)],[(-2,20),(-2,125)]])
edgecheck('B01/B02 肩缝',should,should);edgecheck('B01/B02 侧缝',sideF,sideB)

def capwidth(target,h):
    lo,hi=1,200
    for _ in range(60):
        w=(lo+hi)/2;curve=bez((0,0),(w*.45,0),(w*.9,h*.65),(w,h))
        if length(curve)>target:hi=w
        else:lo=w
    return w,curve

def sleeve(pid,name,af,ab,h,total,flare,count,mat,layer,notes):
    wl,cf=capwidth(length(af)+2,h);wr,cr=capwidth(length(ab)+2,h)
    left=list(reversed(reflect(cf)));right=cr
    pts=addpaths(left,right,[cr[-1],(wr+flare,total),(-wl-flare,total),left[0]])
    s=add(pid,name,pts,count,mat,layer=layer,joins='袖山前段→对应前袖窿；后段→后袖窿；肩点对袖山顶',notes=notes,marks=[[(0,0),(0,10)],[(-wl,h),(-wl+8,h)],[(wr,h),(wr-8,h)]])
    edgecheck(pid+' 前袖山',cf,af,2);edgecheck(pid+' 后袖山',cr,ab,2)
    fp=along(cf,.5);bp1=along(cr,.45);bp2=along(cr,.55)
    s['marks'] += [[(-fp[0],fp[1]),(-fp[0]+5,fp[1])],[bp1,(bp1[0]-5,bp1[1])],[bp2,(bp2[0]-5,bp2[1])]]
    for desc,capcurve,bodycurve,fraction in [('前单',cf,af,.5),('后双1',cr,ab,.45),('后双2',cr,ab,.55)]:
        checks.append({'pair':pid+' '+desc+'记号距肩点','edge_a_mm':round(length(capcurve)*fraction,3),'edge_b_mm':round(length(bodycurve)*fraction,3),'planned_ease_mm':2*fraction,'residual_mm':round((length(capcurve)-length(bodycurve)-2)*fraction,6),'pass':abs(length(capcurve)-length(bodycurve)-2)<.01})
    s['sleeve_hem_mm']=wl+wr+2*flare;s['underarm_seam_mm']=math.hypot(flare,total-h)
    return s,wl,wr
sleeve1,swl,swr=sleeve('H-B03','蓬白袖',armF,armB,30,P['sleeve_length_design'],20,'面布 2，镜像','M5','L1 基础衣身','每袖山有4 mm吃势；袖下整段可开，用两侧窄贴边及小段魔术贴；袖摆抽褶接120 mm净袖口，保留12 mm袖扣搭接。')
cuff=P['cuff_finished_circumference_design'];add('H-B04','白袖口／深色腕带基底',rect(cuff+12,18),'面布 2＋薄里 2','M5；深色外层可用M2',4,layer='L1 基础衣身',joins='0–120 mm接B03抽褶后的袖摆；末12 mm为袖扣搭接',notes='两端不缝成环；外侧叠深色腕带。',marks=[[(cuff,0),(cuff,18)]])
neckL=2*length(neck)+2*(length(neckB)+cb)
add('H-B05','浅色立领',rect(neckL,14),'面布 1＋薄里 1','M5',4,layer='L1 基础衣身',joins='下长边→B01+B02全部领口；两端随后中开口',notes=f'含后中搭接的接领边 {neckL:.2f} mm；不按想象颈围再缩放。')
checks.append({'pair':'B05 接领边/衣身领口','edge_a_mm':round(neckL,3),'edge_b_mm':round(2*length(neck)+2*(length(neckB)+cb),3),'planned_ease_mm':0,'residual_mm':0,'pass':True})
add('H-B06','底衣后中薄贴边',[(0,7),(16,6),(16,143),(0,145)],'薄里 2，镜像','M5',4,layer='L1 基础衣身',joins='0边→B02成品开口边；外边反面固定',notes='贴边净宽16；上缘接领前修齐；后扣段设计20–65和85–125，避免整条变硬。')
fp=along(armF,.5);bp1=along(armB,.45);bp2=along(armB,.55)
basefront['marks'] += [[fp,(fp[0]-5,fp[1])],[(-fp[0],fp[1]),(-fp[0]+5,fp[1])]]
baseback['marks'] += [[bp1,(bp1[0]-5,bp1[1])],[bp2,(bp2[0]-5,bp2[1])]]
add('H-B07','白袖下开口贴边',rect(16,sleeve1['underarm_seam_mm']),'薄里 4','M5',4,layer='L1 基础衣身',joins='长边→B03袖下两边',notes='两侧用贴边收净；下搭侧另加B08延伸12 mm，上搭侧内面软圈；净袖下线合拢时不损失围度。')
add('H-B08','白袖下开口搭接条',rect(12,sleeve1['underarm_seam_mm']),'面布 2＋薄里 2','M5',4,layer='L1 基础衣身',joins='一长边接B03下搭侧净袖下线；另边翻净后伸入上搭侧12 mm',notes='本条提供袖下开口的额外12 mm搭接，成品袖围不减；8 mm细勾朝外，两边各2 mm净空。')
# Chest panel has shaped top and bottom, independent lining.
chestPanel=addpaths(bez((-82,9),(-55,-4),(-22,14),(0,19)),bez((0,19),(22,14),(55,-4),(82,9)),bez((82,9),(91,40),(78,75),(60,90)),bez((60,90),(35,96),(15,106),(0,110)),bez((0,110),(-15,106),(-35,96),(-60,90)),bez((-60,90),(-78,75),(-91,40),(-82,9)))
add('H-C01','弧形深褐胸片',chestPanel,'面布 1＋薄里 1','M2 面＋M3 薄里',4,layer='L2 深色胸身',joins='面里外缘翻缝；肩下/侧边少量暗缝附在B01',notes='胸片不是衣身替代物；完整底衣仍在下层。曲线边按衣片定金边，前中卷纹映射H01。')
# Red bolero: real front/back/sleeve/tails.
rneck=bez((24,35),(20,20),(30,8),(34,0));rshould=[(34,0),(77,12)]
raF=bez((77,12),(73,35),(93,56),(114,62));raB=bez((77,12),(75,34),(90,53),(104,62))
rsF=[(114,62),(120,108)];rsB=[(104,62),(110,108)]
rf=addpaths(rneck,rshould,raF,rsF,bez((120,108),(102,116),(87,121),(72,120)),bez((72,120),(64,99),(42,79),(24,35)))
rb=addpaths([(-6,7),(0,7)],bez((0,7),(12,7),(25,4),(34,0)),rshould,raB,rsB,[(110,108),(-6,108),(-6,7)])
redfront=add('H-R01','红短外搭前片',rf,'红面 2＋薄里 2，镜像','M3',layer='L3 红肩外搭',joins='肩/侧→R02；袖窿→R03；曲形前门襟包在薄里内',notes='前襟敞开露胸片，肩部覆盖上臂；左右花纹分别核对。')
redback=add('H-R02','红短外搭后片',rb,'红面 2＋薄里 2，镜像','M3',layer='L3 红肩外搭',joins='肩/侧→R01；袖窿→R03；后中独立12 mm搭接',notes='背面形状为坐娃工程设计，未经官方背面复核。每半后中跨6；薄里兼作后中贴边。',marks=[[(0,15),(0,98)]])
fp=along(raF,.5);bp1=along(raB,.45);bp2=along(raB,.55)
redfront['marks'] += [[fp,(fp[0]-5,fp[1])]]
redback['marks'] += [[bp1,(bp1[0]-5,bp1[1])],[bp2,(bp2[0]-5,bp2[1])]]
edgecheck('R01/R02 肩缝',rshould,rshould);edgecheck('R01/R02 侧缝',rsF,rsB)
redsleeve,rwl,rwr=sleeve('H-R03','红短肩袖',raF,raB,25,65,5,'红面 2＋薄里 2，镜像','M3','L3 红肩外搭','先面里分别组袖；袖底可开，用贴边/少量扣点；后侧袖口60 mm接R04衣尾，其他袖口与里布翻缝。')
add('H-R04','红尖长衣尾',addpaths([(0,0),(60,0)],bez((60,0),(69,50),(85,129),(54,190)),[(54,190),(29,160),(5,178)],bez((5,178),(-5,120),(5,38),(0,0))),'红面 2＋暗粉里 2，镜像','M3',4,layer='L3 红肩外搭',joins='顶端60 mm接R03后侧袖口；余边面里翻缝',notes='前缘浅金纹与里侧暗红纹分开定位，H02样块两区域不相缝；实际衣尾落点可移到侧腰，但须复核坐姿。')
add('H-R05','红肩袖下开口贴边',rect(14,redsleeve['underarm_seam_mm']),'薄里 4','M3',4,layer='L3 红肩外搭',joins='长边→R03袖下两边',notes='给独立红外搭保留穿脱；不与白袖穿透车死。')
add('H-R06','红肩袖下开口搭接条',rect(12,redsleeve['underarm_seam_mm']),'红面 2＋薄里 2','M3',4,layer='L3 红肩外搭',joins='一长边接R03下搭侧袖下线；另边伸入上搭侧12 mm',notes='与R05贴边配合；细勾在本条朝外面，上搭内面为软圈，不夹住白袖。')
# Soft split lower layers have real pink and white cloth, never a printed stripe.
sidePetal=addpaths([(0,0),(80,0)],bez((80,0),(106,28),(108,83),(82,118)),bez((82,118),(52,137),(19,117),(4,92)),bez((4,92),(-8,60),(-6,25),(0,0)))
frontPetal=addpaths([(0,0),(70,0)],bez((70,0),(78,36),(63,66),(36,87)),bez((36,87),(14,78),(-9,44),(0,0)))
add('H-S01','深色侧裙瓣',sidePetal,'面布 2＋薄里 2，镜像','M2 面＋M3 薄里',4,layer='L4 分瓣裙',joins='上端80 mm→S03腰头左右侧；其余边自由',notes='金边按外缘成品线内退，H03纹样定位置；两侧裙瓣不缝成筒。')
add('H-S02','深色前裙瓣',frontPetal,'面布 1＋薄里 1','M2 面＋M3 薄里',4,layer='L4 分瓣裙',joins='上端70 mm→S03前中；其余边自由',notes='前端呈弧尖，给腿间留位；映射H04纹样。')
waist=belly
waistpiece=add('H-S03','独立柔软裙腰头',rect(waist+12,18),'面布 1＋薄里 1','M5 或M3',4,layer='L4 分瓣裙',joins='前中70和两侧各80接裙瓣；同腰头下叠粉白衬摆；后端12 mm搭接',notes='闭合净围480为本设计原型值；后段不缝死基础上衣。',marks=[[(12,0),(12,18)],[(waist,0),(waist,18)]])
waistpiece['marks'] += [[(x,0),(x,8)] for x in (80,125,180,205,240,275,300,355,400)]
waistpiece['notch_coordinates_mm']={'front_center':240,'dark_front':[205,275],'dark_sides':[[125,205],[275,355]],'pink_white_front':[180,300],'pink_white_sides':[[80,180],[300,400]],'closed_range':[0,480],'overlap_extension':[480,492]}
for pid,name,w,h,n,mat,target in [('H-S04','粉色前衬摆',180,95,1,'M3',120),('H-S05','粉色侧衬摆',150,134,2,'M3',100),('H-S06','白色前衬摆',180,102,1,'M5',120),('H-S07','白色侧衬摆',150,141,2,'M5',100)]:
    add(pid,name,rect(w,h),f'面布 {n}，薄里同数','M3' if mat=='M3' else 'M5',4,layer='L4 分瓣裙',joins=f'上缘{w}均匀抽褶到{target} mm，接S03前/侧；两端收净，后部留空',notes='真实独立粉/白布层；与深色裙瓣错层，下缘露出。小样太厚可改窄卷边并重新标折量。',marks=[[(w/2,0),(w/2,8)]])
# Belts, ribbons, sleeve flounce.
add('H-W01','蓝色斜交腰带',rect(260,24),'面布 2＋薄里 2','M4',4,layer='L5 腰带垂饰',joins='两条前端交叠于前中扣位；后端分别固定在本侧S03，留20 mm可调尾',notes='蓝带走斜线，不是粉带同位置的水平套圈；260为斜带设计长度，试穿调端点后再印。')
add('H-W02','粉色横腰带',rect(waist+12,25),'面布 1＋薄里 1','M4',4,layer='L5 腰带垂饰',joins='闭合净围480，后中12搭接；花结安装侧前',notes='盖过上层腰接缝；独立开合不固定两后片。',marks=[[(waist,0),(waist,25)]])
add('H-W03','蓝色渐尖垂尾',[(0,0),(46,0),(64,112),(38,172),(23,148),(4,163),(-8,80)],'面布 2＋薄里 2，镜像','M4',4,layer='L5 腰带垂饰',joins='顶端46 mm收褶到20 mm，接蓝带侧前扣点',notes='配H10局部纹样；尾尖避坐底；面里方向分别定位。')
add('H-W04','粉色侧垂带',[(0,0),(38,0),(48,108),(24,139),(3,120)],'面布 2＋薄里 2','M4',4,layer='L5 腰带垂饰',joins='顶端38 mm收褶到20 mm接W02侧前花结',notes='花饰可用缠花或布贴；不承受后扣拉力。')
add('H-T01','粉色袖顶褶边',rect(180,20),'面布 2＋薄里 2','M3',4,layer='L1 基础衣身',joins=f'上缘180抽褶至袖山全长{length(armF)+length(armB):.1f} mm，夹在白袖接缝外侧',notes='粉色荷叶边有独立布层；抽褶后先试厚度，不把完整袖山吃势再计入这条褶边。')
# Output utilities
COL={'M5':'#f8f5f0','M3':'#af3937','M4':'#64a4c4','M2':'#40343b'}
def pathstr(pts):return 'M'+' L'.join(f'{x:.3f},{y:.3f}' for x,y in pts)+' Z'
def svgpath(pts,fill='none',stroke='#26394a',width=.5,dash=''):
    return f'<path d="{pathstr(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'
def svgdoc(w,h,body,physical=False):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}{"mm" if physical else "px"}" height="{h}{"mm" if physical else "px"}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="white"/>{body}</svg>'
def piece_color(p):
    if '粉' in p['name']:return '#ecb5cb'
    if '白' in p['name'] or '浅色' in p['name'] or '贴边' in p['name'] or '腰头' in p['name']:return '#f7f3ed'
    if '深' in p['name']:return '#514049'
    if '红' in p['name']:return '#b84442'
    return '#8ec5dc'
def render(svg,png,width=None):
    js="const s=require('sharp');let p=s(process.argv[2],{density:72});if(process.argv[4])p=p.resize(+process.argv[4]);p.flatten({background:'#fff'}).png().toFile(process.argv[3]);"
    subprocess.run([os.environ.get('FABRIC_NODE_BIN','node'),'-',str(svg),str(png)]+([str(width)]if width else[]),input=js,text=True,check=True)
def basicpiece(p):
    xmin,ymin,xmax,ymax=Polygon(p['cut']).bounds
    return xmin,ymin,xmax,ymax

def draw_piece_svg(p):
    a,b,c,d=basicpiece(p);w=max(c-a+40,185);h=d-b+94
    tx=20-a;ty=53-b
    body=label(10,12,p['piece_id']+' '+p['name'],6)+label(10,22,p['cut_count']+'；缝份 '+str(p['allowance_mm'])+' mm',4.5)
    body+=label(10,31,'巡猎坐娃 假设尺寸试版 v0.2 / mm / 100%',4,'#aa4335')
    body+=f'<g transform="translate({tx} {ty})">'+svgpath(p['cut'],'#f1f1ef')+svgpath(p['net'],'none','#bf503c',.45,'2 1')
    for mark in p['marks']:body+=f'<path d="M{mark[0][0]},{mark[0][1]} L{mark[1][0]},{mark[1][1]}" stroke="#477b82" stroke-width=".5" fill="none"/>'
    cx=(a+c)/2;cy=(b+d)/2;gl=min(25,(d-b)/3)
    body+=f'<path d="M{cx},{cy-gl} v{gl*2} m-2,-4 l2,4 l2,-4" stroke="#4d8191" fill="none" stroke-width=".6"/>'+label(cx+3,cy,'纹向',3.5)
    body+='</g>'
    body+=label(10,h-24,f'净轮廓外包 {p["net_bbox_mm"][0]} × {p["net_bbox_mm"][1]}',4)+label(10,h-17,f'裁剪外包 {p["cut_bbox_mm"][0]} × {p["cut_bbox_mm"][1]}',4)
    body+=f'<path d="M10,{h-8} h50 m0,-2 v4 M10,{h-10} v4" stroke="#222" stroke-width=".5"/>'+label(65,h-7,'50 mm 校准',4)
    (OUT/p['file']).write_text(svgdoc(w,h,body,True))
    return w,h

pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
def pdfpiece(c,p,w,h):
    c.setPageSize((w*mm,h*mm));c.setFont('STSong-Light',14);c.drawString(10*mm,(h-12)*mm,p['piece_id']+' '+p['name'])
    c.setFont('STSong-Light',10);c.drawString(10*mm,(h-22)*mm,p['cut_count']+'；缝份 '+str(p['allowance_mm'])+' mm')
    c.setFillColorRGB(.6,.18,.12);c.drawString(10*mm,(h-31)*mm,'巡猎坐娃 假设尺寸试版 v0.2；100%打印，不适合页面')
    a,b,d,e=basicpiece(p);tx=20-a;ty=53-b
    for coords,color,dashed in [(p['cut'],(.14,.22,.3),False),(p['net'],(.75,.3,.2),True)]:
        q=c.beginPath();q.moveTo((coords[0][0]+tx)*mm,(h-coords[0][1]-ty)*mm)
        for x,y in coords[1:]:q.lineTo((x+tx)*mm,(h-y-ty)*mm)
        q.close();c.setStrokeColorRGB(*color);c.setLineWidth(.45*mm);c.setDash(2*mm,mm) if dashed else c.setDash();c.drawPath(q)
    c.setDash();c.setStrokeColorRGB(.2,.5,.55)
    for mark in p['marks']:c.line((mark[0][0]+tx)*mm,(h-mark[0][1]-ty)*mm,(mark[1][0]+tx)*mm,(h-mark[1][1]-ty)*mm)
    cx=(a+d)/2;cy=(b+e)/2;gl=min(25,(e-b)/3)
    c.line((cx+tx)*mm,(h-cy+gl-ty)*mm,(cx+tx)*mm,(h-cy-gl-ty)*mm)
    c.line((cx+tx)*mm,(h-cy-gl-ty)*mm,(cx+tx-2)*mm,(h-cy-gl-ty+4)*mm)
    c.line((cx+tx)*mm,(h-cy-gl-ty)*mm,(cx+tx+2)*mm,(h-cy-gl-ty+4)*mm)
    c.setFillColorRGB(.1,.15,.2);c.setFont('STSong-Light',10)
    c.drawString(10*mm,24*mm,'净轮廓外包 '+str(p['net_bbox_mm'])+' mm')
    c.drawString(10*mm,17*mm,'裁剪外包 '+str(p['cut_bbox_mm'])+' mm；红虚线为缝线，黑实线裁剪')
    c.setStrokeColorRGB(0,0,0);c.line(10*mm,8*mm,60*mm,8*mm);c.line(10*mm,6*mm,10*mm,10*mm);c.line(60*mm,6*mm,60*mm,10*mm)
    c.drawString(65*mm,7*mm,'50 mm 校准');c.showPage()

def pieces_overview():
    cols=4;cw=440;ch=355;rows=math.ceil(len(pieces)/cols);W=cols*cw+60;H=rows*ch+180
    body=label(35,55,'巡猎坐娃 · 完整衣片索引 v0.2',40)+label(35,95,'假设尺寸试版；下列尺寸是完整净衣片与裁片外包框，不是纹样块。',23,'#a54d39')
    body+=label(35,130,'肩斜／袖窿／腹部放量／短外搭长衣尾／真实粉白衬摆／独立后开腰带',22)
    for i,p in enumerate(pieces):
        x=30+(i%cols)*cw;y=165+(i//cols)*ch
        body+=f'<rect x="{x}" y="{y}" width="420" height="337" rx="12" fill="#f7f7f3" stroke="#c6d0d5"/>'
        body+=label(x+14,y+28,p['piece_id']+' '+p['name'],21)
        a,b,c,d=basicpiece(p);s=min(360/(c-a),170/(d-b),2)
        tx=x+210-(a+c)/2*s;ty=y+132-(b+d)/2*s
        body+=f'<g transform="translate({tx} {ty}) scale({s})">'+svgpath(p['cut'],'#e8e6e1','#768792',.6)+svgpath(p['net'],piece_color(p),'#333c44',.45)+'</g>'
        body+=label(x+14,y+239,'净 '+str(p['net_bbox_mm'][0])+' × '+str(p['net_bbox_mm'][1])+' mm',20)
        body+=label(x+14,y+269,'裁 '+str(p['cut_bbox_mm'][0])+' × '+str(p['cut_bbox_mm'][1])+' mm',19)
        body+=label(x+14,y+298,p['cut_count']+' / 缝份 '+str(p['allowance_mm'])+' mm',18)
        body+=label(x+14,y+323,p['layer'],17,'#61727e')
    f=OUT/'pieces-overview.svg';f.write_text(svgdoc(W,H,body));render(f,f.with_suffix('.png'),1800)

# Costume engineering flats: schematic front/back assembled layers, not official back reconstruction.
def flat(x,y,scale,layer,back=False):
    g=''
    def shape(d,fill,stroke='#34414d',sw=1.4):return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    # mini drawings use 300 x 260 local coordinate space.
    if layer in (1,6):
        g+=shape('M108 25 Q150 45 192 25 L227 38 Q225 73 251 89 L276 147 Q254 171 234 163 L205 108 L218 194 Q150 213 82 194 L95 108 L66 163 Q42 170 24 147 L49 89 Q75 73 73 38Z','#f6f1e9')
        g+=shape('M108 25 L108 10 Q150 22 192 10 L192 25 Q150 45 108 25Z','#fff9f0')
        for sx in (36,230):g+=shape(f'M{sx} 146 l33 10 l-3 17 l-34 -9Z','#3e3542')
        g+=shape('M53 88 Q71 95 88 83 L91 94 Q74 109 50 100Z','#e8b5d0')+shape('M209 83 Q228 94 247 88 L250 100 Q225 109 209 94Z','#e8b5d0')
        if back:g+=shape('M150 32 L150 199','none','#be594b',2)+shape('M145 50 h10 v43 h-10Z M145 124 h10 v42 h-10Z','#dc8eb3')
    if layer in (2,6):
        if not back:
            g+=shape('M96 60 Q117 48 150 69 Q183 48 204 60 Q211 116 185 153 L150 172 L115 153 Q89 116 96 60Z','#4c3940')
            g+=shape('M101 65 Q121 58 150 76 Q179 58 199 65 M150 76 L150 158','none','#e4c9a1',3)
        else:g+=shape('M90 42 Q150 22 210 42 L218 190 Q150 204 82 190Z','#e9e5dd')+shape('M150 35 V200','none','#bc574c',2)
    if layer in (3,6):
        g+=shape('M108 25 L75 32 L38 91 L73 111 L94 77 L98 122 L122 115 L120 60Z','#ad3835')
        g+=shape('M192 25 L225 32 L262 91 L227 111 L206 77 L202 122 L178 115 L180 60Z','#ad3835')
        g+=shape('M62 105 Q33 162 48 232 L77 206 L89 222 L97 125Z','#9d302f')
        g+=shape('M238 105 Q267 162 252 232 L223 206 L211 222 L203 125Z','#9d302f')
        g+=shape('M74 113 Q47 169 58 218 L74 200 L83 209 L91 128Z','#6f3f51')+shape('M226 113 Q253 169 242 218 L226 200 L217 209 L209 128Z','#6f3f51')
        if back:g+=shape('M108 25 Q150 35 192 25 L204 120 Q150 140 96 120Z','#ad3835')+shape('M150 32 V130','none','#ecb0b4',2)
    if layer in (4,6):
        # Lower silhouette extends beyond mini upper body baseline and leaves rear gap.
        g+=shape('M86 162 Q150 177 214 162 L224 218 Q210 239 192 221 Q171 243 151 225 Q128 242 106 223 Q85 235 75 216Z','#faf1ea')
        g+=shape('M86 160 Q150 175 214 160 L221 205 Q205 227 187 212 Q170 233 151 216 Q129 232 108 211 Q88 224 78 204Z','#ecb1c7')
        g+=shape('M84 158 L121 171 Q120 216 88 225 Q62 213 66 186Z','#49363e')
        g+=shape('M216 158 L179 171 Q180 216 212 225 Q238 213 234 186Z','#49363e')
        g+=shape('M120 171 L180 171 Q185 204 150 225 Q115 204 120 171Z','#49363e')
        g+=shape('M80 161 Q64 201 87 219 Q115 212 116 177 M220 161 Q236 201 213 219 Q185 212 184 177 M125 177 Q122 202 150 217 Q178 202 175 177','none','#dbc092',3)
        if back:g+=shape('M120 170 L180 170 L186 236 L113 236Z','#ffffff','#ffffff',0)+shape('M82 155 Q150 173 218 155 L218 169 Q150 187 82 169Z','#c5b3b6')+shape('M150 165 V181','none','#b74e4b',2)
    if layer in (5,6):
        g+=shape('M82 140 L158 182 L219 139 L223 154 L158 199 L77 155Z','#65a4cb')
        g+=shape('M77 174 Q148 199 223 173 L224 188 Q150 216 76 190Z','#eab0c5')
        g+=shape('M90 183 L70 232 L47 259 L45 235 L29 247 L69 181Z','#70b0cf')
        g+=shape('M211 183 L228 234 L249 259 L252 237 L268 247 L232 180Z','#70b0cf')
        g+=shape('M205 185 L211 232 L230 248 L233 225 L224 187Z','#eab0c5')
        if not back:g+=shape('M150 181 l-17 -16 l-5 18 l22 12 l22 -12 l-5 -18Z','#d3bb85')
        else:g+=shape('M150 175 V204','none','#b74e4b',2)
    return f'<g transform="translate({x} {y}) scale({scale})">{g}</g>'

def layers_overview():
    W,H=1800,1980
    body=label(40,60,'巡猎三月七 · 从里到外的完整服装方案',43)
    body+=label(40,104,'假设尺寸试版 v0.2｜坐姿改造设计；后背为工程方案，不是官方背面复原',24,'#a84c39')
    specs=[('01 浅色底衣＋蓬白袖',1,'B01–B08＋T01：后开口、可开袖底'),('02 弧形深胸片',2,'C01：完整底衣上加薄胸片'),('03 红肩外搭＋尖长衣尾',3,'R01–R06：短肩袖与长尾分开'),('04 分瓣裙＋粉白衬摆',4,'S01–S07：真实三层，后下方让坐底'),('05 蓝斜带＋粉横带＋垂尾',5,'W01–W04：各自开合，不锁住衣身'),('06 合穿外观',6,'前短后开；分瓣与衣尾避开坐底')]
    for i,(title,layer,subtitle) in enumerate(specs):
        x=35+(i%2)*885;y=145+(i//2)*590
        body+=f'<rect x="{x}" y="{y}" width="850" height="560" rx="18" fill="#f4f5f4" stroke="#c5d1d5"/>'
        body+=label(x+24,y+42,title,29)+label(x+24,y+78,subtitle,20,'#5f707c')
        body+=label(x+207,y+116,'前面',22,anchor='middle')+label(x+633,y+116,'背面',22,anchor='middle')
        body+=flat(x+16,y+135,1.28,layer)+flat(x+442,y+135,1.28,layer,True)
        body+=label(x+24,y+535,'后中虚线＝可开；裙摆后部留空，穿脱不经过头部',19,'#7e625d')
    body+=label(40,1960,'完整尺寸及对应接缝见 pattern-manifest.json 和一比一 PDF；此页示意不用于量尺寸。',22)
    f=OUT/'layers-overview.svg';f.write_text(svgdoc(W,H,body));render(f,f.with_suffix('.png'),1800)

def main():
    OUT.mkdir(exist_ok=True);(OUT/'pieces').mkdir(exist_ok=True)
    (OUT/'parameters-v0.2.json').write_text(json.dumps(P,ensure_ascii=False,indent=2)+'\n')
    can=canvas.Canvas(str(OUT/'hunt-full-pattern-v0.2-1to1.pdf'))
    for p in pieces:
        w,h=draw_piece_svg(p);pdfpiece(can,p,w,h)
    can.save();pieces_overview();layers_overview()
    manifest={'version':'v0.2','status':'complete digital engineering toile; no fit or fabric validation','units':'mm','measurement_basis':'independent assumed dummy; not actual Bandai measurements','parameter_file':'parameters-v0.2.json','default_finished_chest_mm':chest,'default_finished_maximum_abdomen_mm':belly,'closure_overlap_mm':12,'back_hook_loop_width_mm':8,'production_print_ready':False,'pieces':[{k:v for k,v in p.items()if k not in ('net','cut')} for p in pieces]}
    (OUT/'pattern-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    result={'version':'v0.2','method':'Cubic curves sampled at 24 intervals; shapely true distance offset with miter joins; lengths measured on sampled seam paths','all_net_and_cut_polygons_valid':True,'all_cut_polygons_contain_net':True,'pairs':checks,'closed_chest_mm':chest,'closed_max_abdomen_mm':belly,'waistband_closed_length_mm':waist,'cuff_gathering':{'sleeve_edge_mm':round(sleeve1['sleeve_hem_mm'],3),'cuff_join_mm':cuff,'fullness_mm':round(sleeve1['sleeve_hem_mm']-cuff,3)},'underlayer_join':{'front_gathered_mm':120,'sides_gathered_mm':200,'total_coverage_mm':320,'rear_uncovered_mm':waist-320},'lining_reveal_design_mm':{'front_pink_beyond_dark':95-87,'front_white_beyond_pink':102-95,'side_pink_beyond_dark':round(134-Polygon(sidePetal).bounds[3],3),'side_white_beyond_pink':141-134},'physical_fit_validated':False}
    assert all(q['pass']for q in checks)
    assert sleeve1['sleeve_hem_mm']>cuff
    (OUT/'geometry-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    doc=fitz.open(OUT/'hunt-full-pattern-v0.2-1to1.pdf')
    assert len(doc)==len(pieces)
    previews=[]
    for i,page in enumerate(doc):
        pix=page.get_pixmap(matrix=fitz.Matrix(.55,.55));previews.append(pix)
    from PIL import Image,ImageOps,ImageDraw
    board=Image.new('RGB',(1600,math.ceil(len(previews)/5)*350),'#e9edef');d=ImageDraw.Draw(board)
    for i,pix in enumerate(previews):
        im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);im.thumbnail((300,320));x=(i%5)*320+(320-im.width)//2;y=(i//5)*350
        board.paste(im,(x,y));d.text(((i%5)*320+8,y+328),str(i+1)+' '+pieces[i]['piece_id'],fill='black')
    board.save(OUT/'pdf-contact-sheet.png')
    rows=['|编号／衣片|净轮廓外包 mm|含缝份裁片外包 mm|裁片数|材质|','|---|---|---|---|---|']
    for p in pieces:rows.append('|'+p['piece_id']+' '+p['name']+'|'+' × '.join(map(str,p['net_bbox_mm']))+'|'+' × '.join(map(str,p['cut_bbox_mm']))+'|'+p['cut_count']+'|'+p['material']+'|')
    (OUT/'dimension-table.md').write_text('# 巡猎完整衣片尺寸表\n\n单位 mm；下列是本假设原型的实数设计尺寸，不是万代娃体实测。曲形衣片的宽高是外包框，不能当矩形裁剪；以 SVG/PDF 实际轮廓为准。PDF 黑实线为含缝份裁边、红虚线为净缝线，所有衣片单页全幅 1:1。\n\n'+'\n'.join(rows)+'\n')
    print('Created',len(pieces),'complete piece types and',len(checks),'paired-edge checks',OUT)
if __name__=='__main__':main()
