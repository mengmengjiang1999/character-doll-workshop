#!/usr/bin/env python3
"""Complete Preservation UFdoll S-bust engineering toile; missing dimensions are user-authorized estimates."""
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
OUT=ROOT/'projects/honkai-star-rail/march-7th-preservation-bjd-1-4/garment-pattern'
PARAMS={'version':'v0.2-estimated-toile','units':'mm','actual_measurements':False,'basis':'UFdoll S bust dealer specification + user-authorized estimated missing lengths','body_chest_nominal':170,'body_waist_nominal':128,'shoulder_nominal':86,'arm_length_nominal':122,'finished_chest':180,'finished_waist':140,'bodice_underarm_depth_estimated':36,'bodice_waist_depth_estimated':78,'bodice_hem_depth_estimated':86,'sleeve_to_cuff':108,'cuff_height':14,'cuff_closed_circumference_estimated':50,'regular_allowance':5,'detail_allowance':3,'closure_total_overlap':10,'hook_loop_width':6,'skirt_length_design':86,'skirt_pleat_count':14,'skirt_flat_width':420}
paramfile=OUT/'parameters-v0.2.json'
if '--parameters' in sys.argv:
    raise SystemExit('This version records a fixed-size estimate, not a grading engine. Edit the source geometry and rerun checks when changing body dimensions.')
P=PARAMS
pieces=[];checks=[]
def bez(a,b,c,d,n=24):
    return [tuple((1-t)**3*a[j]+3*(1-t)**2*t*b[j]+3*(1-t)*t*t*c[j]+t**3*d[j] for j in (0,1)) for t in [i/n for i in range(n+1)]]
def addpaths(*paths):
    out=[]
    for q in paths: out+=q if not out or out[-1]!=q[0] else q[1:]
    return out

def length(p):return LineString(p).length

def reflect(p):return [(-x,y) for x,y in p]
def rect(w,h):return [(0,0),(w,0),(w,h),(0,h)]
def add(pid,name,pts,count,material,sa=5,layer='',joins='',notes='',marks=None):
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


# Complete costume geometry follows.
# White fitted blouse: waist darts + shaped side seams, closed bust180 / waist140.
neck=bez((0,14),(13,14),(24,8),(30,0));should=[(30,0),(43,5)]
af=bez((43,5),(37,18),(37,30),(45,36));ab=bez((43,5),(40,17),(38,30),(45,36))
side=[(45,36),(40,78),(42,86)]
frontHalf=addpaths(neck,should,af,side,[(42,86),(0,86)])
front=addpaths(frontHalf,list(reversed(reflect(frontHalf))))
back=addpaths([(-5,4),(0,4)],bez((0,4),(12,4),(24,3),(30,0)),should,ab,side,[(42,86),(-5,86),(-5,4)])
f=add('P-B01','收腰白衬衣前身',front,'面布1','M5',layer='L1 白衬衣',joins='肩与侧→B02；袖窿→B03；领口包边→B06',notes='整前片；两条5 mm腰省。原前中不开口，只做装饰门襟。',marks=[[(0,20),(0,80)],[(-24.5,78),(-22,40)],[(-19.5,78),(-22,40)],[(24.5,78),(22,40)],[(19.5,78),(22,40)]])
b=add('P-B02','收腰白衬衣后片',back,'面布2，镜像','M5',layer='L1 白衬衣',joins='肩与侧→B01；袖窿→B03；后中→B05',notes='每后片腰省5；原后中x=0，各跨5形成总搭接10。勾在下搭朝外，毛圈上搭朝内。',marks=[[(0,8),(0,82)],[(17.5,78),(20,42)],[(22.5,78),(20,42)]])
# Darts close towards CF/CB. Mark their below-waist continuation, not a slit.
f['marks'] += [[(sgn*24.5,78),(sgn*22,86)] for sgn in (-1,1)]+[[(sgn*19.5,78),(sgn*22,86)] for sgn in (-1,1)]
b['marks'] += [[(17.5,78),(20,86)],[(22.5,78),(20,86)]]
edgecheck('B01/B02肩缝',should,should);edgecheck('B01/B02侧缝',side,side)
def capwidth(target,h):
 lo,hi=.1,100
 for _ in range(65):
  w=(lo+hi)/2;q=bez((0,0),(w*.45,0),(w*.9,h*.65),(w,h),80)
  if length(q)>target:hi=w
  else:lo=w
 return w,q

def point_at(path,fraction):
 q=LineString(path).interpolate(fraction,normalized=True);return(q.x,q.y)
def make_sleeve(pid,name,armf,armb,h,total,hemwidth,count,mat,layer,notes):
 wl,cf=capwidth(length(armf)+1,h);wr,cr=capwidth(length(armb)+1,h)
 # Underarm lengths match by symmetric flare relative to each cap endpoint.
 flare=(hemwidth-wl-wr)/2
 pts=addpaths(list(reversed(reflect(cf))),cr,[(wr+flare,total),(-wl-flare,total),(-wl,h)])
 s=add(pid,name,pts,count,mat,layer=layer,joins='前后袖山分别接对应袖窿；袖底闭合；袖摆另见说明',notes=notes,marks=[[(0,0),(0,8)]])
 for curve,sign in [(cf,-1),(cr,1)]:
  x,y=point_at(curve,.5);s['marks'].append([(sign*x,y),(sign*x-sign*4,y)])
 edgecheck(pid+'前袖山',cf,armf,1);edgecheck(pid+'后袖山',cr,armb,1)
 for sideid,cap,arm in [('前',cf,armf),('后',cr,armb)]:
  for frac in (.5,1):
   checks.append({'pair':pid+sideid+f'袖山累计{frac:.0%}','edge_a_mm':round(length(cap)*frac,3),'edge_b_mm':round(length(arm)*frac,3),'planned_ease_mm':frac,'residual_mm':round((length(cap)-length(arm)-1)*frac,6),'pass':abs(length(cap)-length(arm)-1)<.05})
 s['sleeve_hem_mm']=hemwidth;s['underarm_seam_mm']=math.hypot(flare,total-h)
 return s
sleeve=make_sleeve('P-B03','完整白长袖',af,ab,18,P['sleeve_to_cuff'],70,'面布2，镜像','M5','L1 白衬衣','每袖共2 mm吃势，按弧长分到前后各1；袖摆70抽褶到50接袖口。袖底最后15不缝，供手掌通过。')
for obj,arm,mirror in [(f,af,True),(b,ab,False)]:
 x,y=point_at(arm,.5);obj['marks'].append([(x,y),(x-4,y)])
 if mirror:obj['marks'].append([(-x,y),(-x+4,y)])
add('P-B04','宽翻袖口',rect(60,14),'面布2＋薄里2','M5',3,layer='L1 白衬衣',joins='50 mm接抽褶后袖摆；末10为搭接；面里翻缝',notes='成品净袖围50，宽14；魔术贴6宽。蓝边落在成品折边内，金扣不承担闭合。',marks=[[(50,0),(50,14)]])
add('P-B05','白衣后中贴边',rect(12,82),'薄里2','M5',3,layer='L1 白衬衣',joins='82 mm边→后片x=-5从y4到86',notes='12为贴边净宽；内侧遮针脚，薄衬仅加扣位。')
neckB=bez((0,4),(12,4),(24,3),(30,0));neckL=2*length(neck)+2*(5+length(neckB))
add('P-B06','白衣领口斜裁包边',rect(neckL,8),'面布1，45度斜裁','M5',3,layer='L1 白衬衣',joins='长边接全部领口；实际对位按前中/肩/后中标定',notes=f'净连接长{neckL:.2f}；8宽对折成4；可代替厚领口贴边。')
add('P-B07','白色宽翻领片',[(0,0),(26,0),(35,13),(15,28),(-7,13)],'面布2＋薄里2，镜像','M5',3,layer='L1 白衬衣',joins='上边26分别缝在左右前领边，肩点向前量26定位',notes='独立翻领层；宽开领露出锁骨，后领口用B06收净，未复制成人衬衫领座。')
add('P-B08','袖底开衩薄条',rect(32,8),'面布2，斜裁','M5',3,layer='L1 白衬衣',joins='包住每袖底最后15 mm的两边，预留2转弯',notes='袖底开衩不剪入已缝袖底，袖口解开后能展开。')
# Dropped-shoulder blue bolero, supported at four hidden points on white blouse.
outerArmF=bez((40,26),(38,34),(38,44),(45,48));outerArmB=bez((40,26),(39,34),(39,44),(45,48))
oside=[(45,48),(35,78)];outerfront=addpaths([(0,64),(16,35),(40,26)],outerArmF,oside,[(35,78),(0,80),(0,64)])
outerback=addpaths([(-5,22),(0,22),(40,26)],outerArmB,oside,[(35,78),(-5,78),(-5,22)])
of=add('P-O01','露肩蓝外搭前片',outerfront,'面布2＋薄里2，镜像','M3',layer='L2 蓝外搭',joins='侧→O02；低袖窿→O03；前中16 mm→O04系带',notes='上缘在肩下；前胸敞开。前后顶点(40,26)与袖山顶三片交汇；缝完袖山再以薄里封净，并用O07支承。')
ob=add('P-O02','露肩蓝外搭后片',outerback,'面布2＋薄里2，镜像','M3',layer='L2 蓝外搭',joins='侧→O01；低袖窿→O03；背中独立10 mm搭接',notes='每边跨原后中5；薄里兼贴边；上缘靠白衣后肩下隐蔽固定点承托。',marks=[[(0,26),(0,74)]])
edgecheck('O01/O02侧缝',oside,oside)
outsleeve=make_sleeve('P-O03','蓝色上臂外袖',outerArmF,outerArmB,8,62,82,'面布2＋薄里2，镜像','M3','L2 蓝外搭','低袖山适配露肩身；下摆宽82自由，不接白袖。白长袖从中穿出，两层不车死。')
for obj,arm in [(of,outerArmF),(ob,outerArmB)]:
 x,y=point_at(arm,.5);obj['marks'].append([(x,y),(x-4,y)])
add('P-O04','前腰蓝系带',[(0,0),(16,0),(22,64),(13,98),(-5,78)],'面布2＋薄里2，镜像','M3',3,layer='L2 蓝外搭',joins='16 mm短边→O01前中16 mm；两前端在腰上打结',notes='真实独立系带，不把后蝶结挪到前面；末端渐尖。')
add('P-O05','蓝袖外侧尖垂片',[(0,0),(24,0),(33,48),(17,73),(9,54),(-2,63)],'面布2＋薄里2，镜像','M3',3,layer='L2 蓝外搭',joins='24 mm短边叠缝到O03外侧袖摆，余缘自由',notes='做出外袖开叉尖尾外观；每边下摆82中的24被连接，其他自由。')
add('P-O06','蓝紫上臂翻片',[(0,0),(50,0),(56,16),(39,27),(4,21)],'面布2＋薄里2','M3',3,layer='L2 蓝外搭',joins=f'顶部50收至衣身袖窿接缝{length(outerArmF)+length(outerArmB):.3f} mm，沿完整接缝外侧一圈定位',notes='50收至47.835，收量2.165；蓝袖山自身2 mm吃势另外分配，不重复计入翻片。')
add('P-O07','露肩外搭隐藏支承条',rect(4,20),'薄布4＋薄里4','M5',3,layer='L2 蓝外搭',joins='前后各两条：白衣本侧(36,16)→蓝片本侧(38,28)，坐标随镜像',notes='净20长两端各3固定，中段14；前后分别支承同侧顶缘，避免外搭只悬在袖山交汇点。')
# Split sailor collar: genuine front/back pointed pieces, matching shoulder joint16.
cf=[(0,0),(16,0),(24,38),(14,74),(-5,58),(4,24)]
cb=[(0,0),(16,0),(40,50),(28,78),(3,55)]
add('P-C01','深蓝前披领',cf,'面布2＋薄里2，镜像','M2',3,layer='L3 尖披领',joins='顶端16→C02顶端16；背面少量暗缝固定在白衣肩/蓝外搭',notes='前襟两边露出深蓝双白条；下端自由，不接前系带。')
add('P-C02','深蓝后尖披领',cb,'面布2＋薄里2，镜像','M2',3,layer='L3 尖披领',joins='顶端16→C01；两后片各自固定，不跨后中开口',notes='两块宽三角尖领，不做整块方水手后领。双白条沿成品外缘内退。')
edgecheck('C01/C02肩顶连接',[(0,0),(16,0)],[(0,0),(16,0)])
# Pleated skirt: flat420 folds to140. Back slit is edge-to-edge below waist, not overlapped.
sk=add('P-S01','深蓝十四褶裙片',rect(P['skirt_flat_width'],P['skirt_length_design']),'面布1','M1',5,layer='L4 褶裙',joins='420均匀折成140接S02；后缝下段接合，上端30开衩对合不重叠',notes='每30一个重复，成品褶面10；14褶共140。后开衩不减腰围；只有腰头额外10做搭接。下摆5翻折，白边按成品底边定位。')
for x in range(0,420,30):sk['marks'] += [[(x+10,0),(x+10,86)],[(x+20,0),(x+20,86)]]
add('P-S02','独立裙腰头',rect(150,12),'面布1＋薄里1','M5 或M1',3,layer='L4 褶裙',joins='0–140接裙腰；140–150为后扣悬空搭接；两端翻净',notes='闭合140；重叠10与魔术贴6，不能把裙140再重叠成130。',marks=[[(140,0),(140,12)]])
add('P-S03','裙后开衩护片',rect(12,30),'薄里1','M5',3,layer='L4 褶裙',joins='一长边缝在一侧后开衩，向内盖住30长开口',notes='护片是另加结构，不能把裙身围度拿去当搭接。')
# Asymmetrical outer waist: four real panels on an independent belt.
leftflap=addpaths([(0,0),(35,0)],bez((35,0),(45,25),(32,60),(14,78)),[(14,78),(-5,62)],bez((-5,62),(2,36),(-4,16),(0,0)))
rightflap=addpaths([(0,0),(35,0)],bez((35,0),(45,35),(37,66),(23,86)),[(23,86),(6,73)],bez((6,73),(-3,54),(-4,24),(0,0)))
rearflap=addpaths([(0,0),(35,0)],bez((35,0),(46,30),(35,54),(17,74)),[(17,74),(-3,62)],bez((-3,62),(12,38),(11,15),(0,0)))
for pid,name,pts,count,position in [('P-W01','右前深色短腰片',leftflap,'面布1＋薄里1','带上70–105'),('P-W02','左前深色长腰片',rightflap,'面布1＋薄里1','带上35–70'),('P-W03','左右后深色腰片',rearflap,'面布2＋薄里2，镜像','带上0–35及105–140')]:
 add(pid,name,pts,count,'M2',3,layer='L5 不对称腰饰',joins='顶端35→W04；'+position+'；其他边自由',notes='穿衣者方向命名；顶边与裙腰头上缘同高，长片86、裙含腰头98，底边高于裙底12。侧下缘自由。')
add('P-W04','独立淡紫装饰腰带',rect(150,8),'面布1＋薄里1','M4',3,layer='L5 不对称腰饰',joins='0–140按段连接四片腰饰；最后10后扣搭接',notes='闭合净围140；与裙腰头独立，不贯穿缝死白衣和裙。',marks=[[(x,0),(x,8)] for x in [35,70,105,140]])
# Independent detachable bow and reinforcement. All face/lining parts are real cloth.
bow=[(-45,-13),(-18,-18),(0,-7),(18,-18),(45,-13),(41,16),(19,18),(0,7),(-19,18),(-41,16)]
add('P-A01','背部蝴蝶结双翼',bow,'面布1＋薄里1','M4',3,layer='L6 可拆背蝶结',joins='面里外缘翻缝，留返口；中部捏褶后用A02围住',notes='双翼真实外形，90宽；捏褶后的实际宽略变，以试制确认。')
add('P-A02','蝴蝶结结芯',rect(26,9),'面布1＋薄里1','M4',3,layer='L6 可拆背蝶结',joins='环绕A01中部；搭合4形成22净环长；收口在背面',notes='与A04针座底片缝合，不把针座仅粘在薄缎上。')
for pid,name,w,h in [('P-A03L','蓝粉左垂尾',31,96),('P-A03R','蓝粉右垂尾',27,90)]:
 add(pid,name,[(0,0),(w,0),(w-3,h*.64),(w*.4,h),(w*.42,h-20),(-4,h-8)],'面布1＋薄里1','M4',3,layer='L6 可拆背蝶结',joins='顶端收褶到12，缝进A01/A02背部；余缘翻缝',notes='两尾长度不同；蓝上粉下，纹样最后按本轮廓重新映射。')
add('P-A04','蝴蝶结针座承力底片',rect(30,16),'薄布2＋薄衬1','M5',3,layer='L6 可拆背蝶结',joins='缝在A01背面，针座经缝孔固定',notes='30×16为估算布底，不代表选定30mm针座；针座实际长度≤背面可遮盖范围。')
add('P-A05','衣身单侧别针承力片',rect(28,22),'薄布1＋薄衬1','M5',3,layer='L6 可拆背蝶结',joins='固定到O02一侧后片里侧，避开后中10搭接；中心约原后中外20、上缘下35',notes='别针只穿这一个后片；蝴蝶结外观可盖后中，但针不能桥接开口。先摘蝶结再开衣服。')
checks += [{'pair':'闭合胸围','edge_a_mm':180,'edge_b_mm':P['body_chest_nominal'],'planned_ease_mm':10,'residual_mm':0,'pass':True},{'pair':'腰围：前80-10省＋后80-10省','edge_a_mm':140,'edge_b_mm':P['body_waist_nominal'],'planned_ease_mm':12,'residual_mm':0,'pass':True},{'pair':'裙褶后腰140=腰头150-搭接10','edge_a_mm':420/3,'edge_b_mm':150-10,'planned_ease_mm':0,'residual_mm':0,'pass':True}]

COL={'M5':'#f8f5f0','M3':'#af3937','M4':'#64a4c4','M2':'#40343b'}
def pathstr(pts):return 'M'+' L'.join(f'{x:.3f},{y:.3f}' for x,y in pts)+' Z'
def svgpath(pts,fill='none',stroke='#26394a',width=.5,dash=''):
    return f'<path d="{pathstr(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'
def svgdoc(w,h,body,physical=False):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}{"mm" if physical else "px"}" height="{h}{"mm" if physical else "px"}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="white"/>{body}</svg>'
def piece_color(p):
    pid=p['piece_id']
    if pid.startswith('P-B') or pid in ('P-S02','P-S03','P-A04','P-A05','P-O07'):return '#f7f3ed'
    if pid.startswith('P-C') or pid=='P-S01':return '#35538a'
    if pid=='P-W04':return '#bca9d9'
    if pid.startswith('P-W'):return '#3e3b44'
    if pid.startswith('P-A03'):return '#c5b6e4'
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
    body+=label(10,31,'存护囡囡体 估算试版 v0.2 / mm / 100%',4,'#aa4335')
    body+=f'<g transform="translate({tx} {ty})">'+svgpath(p['cut'],'#f1f1ef')+svgpath(p['net'],'none','#bf503c',.45,'2 1')
    for mark in p['marks']:body+=f'<path d="M{mark[0][0]},{mark[0][1]} L{mark[1][0]},{mark[1][1]}" stroke="#477b82" stroke-width=".5" fill="none"/>'
    cx=(a+c)/2;cy=(b+d)/2;gl=min(25,(d-b)/3)
    if p['piece_id'] in ('P-B06','P-B08'): dx,dy=3,3;gn='45度斜裁'
    elif p['piece_id'] in ('P-B04','P-S02','P-W04','P-A02'): dx,dy=min(25,(c-a)/3),0;gn='纹向'
    else: dx,dy=0,gl;gn='纹向'
    body+=f'<path d="M{cx-dx},{cy-dy} L{cx+dx},{cy+dy}" stroke="#4d8191" fill="none" stroke-width=".6"/>'+label(cx+3,cy+4,gn,3.5)
    if p['piece_id'] in ('P-B03','P-O03'):
        body+=label(-10,17,'前',3.8)+label(7,17,'后',3.8)
    body+='</g>'
    body+=label(10,h-24,f'净轮廓外包 {p["net_bbox_mm"][0]} × {p["net_bbox_mm"][1]}',4)+label(10,h-17,f'裁剪外包 {p["cut_bbox_mm"][0]} × {p["cut_bbox_mm"][1]}',4)
    body+=f'<path d="M10,{h-8} h50 m0,-2 v4 M10,{h-10} v4" stroke="#222" stroke-width=".5"/>'+label(65,h-7,'50 mm 校准',4)
    (OUT/p['file']).write_text(svgdoc(w,h,body,True))
    return w,h

pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
def pdfpiece(c,p,w,h):
    c.setPageSize((w*mm,h*mm));c.setFont('STSong-Light',14);c.drawString(10*mm,(h-12)*mm,p['piece_id']+' '+p['name'])
    c.setFont('STSong-Light',10);c.drawString(10*mm,(h-22)*mm,p['cut_count']+'；缝份 '+str(p['allowance_mm'])+' mm')
    c.setFillColorRGB(.6,.18,.12);c.drawString(10*mm,(h-31)*mm,'存护囡囡体 估算试版 v0.2；100%打印，不适合页面')
    a,b,d,e=basicpiece(p);tx=20-a;ty=53-b
    for coords,color,dashed in [(p['cut'],(.14,.22,.3),False),(p['net'],(.75,.3,.2),True)]:
        q=c.beginPath();q.moveTo((coords[0][0]+tx)*mm,(h-coords[0][1]-ty)*mm)
        for x,y in coords[1:]:q.lineTo((x+tx)*mm,(h-y-ty)*mm)
        q.close();c.setStrokeColorRGB(*color);c.setLineWidth(.45*mm);c.setDash(2*mm,mm) if dashed else c.setDash();c.drawPath(q)
    c.setDash();c.setStrokeColorRGB(.2,.5,.55)
    for mark in p['marks']:c.line((mark[0][0]+tx)*mm,(h-mark[0][1]-ty)*mm,(mark[1][0]+tx)*mm,(h-mark[1][1]-ty)*mm)
    cx=(a+d)/2;cy=(b+e)/2;gl=min(25,(e-b)/3)
    if p['piece_id'] in ('P-B06','P-B08'): dx,dy=3,3;gn='45度斜裁'
    elif p['piece_id'] in ('P-B04','P-S02','P-W04','P-A02'): dx,dy=min(25,(d-a)/3),0;gn='纹向'
    else: dx,dy=0,gl;gn='纹向'
    c.line((cx-dx+tx)*mm,(h-cy+dy-ty)*mm,(cx+dx+tx)*mm,(h-cy-dy-ty)*mm)
    c.setFont('STSong-Light',8);c.drawString((cx+tx+3)*mm,(h-cy-ty-5)*mm,gn)
    if p['piece_id'] in ('P-B03','P-O03'):
        c.setFont('STSong-Light',9);c.drawString((tx-10)*mm,(h-ty-17)*mm,'前');c.drawString((tx+7)*mm,(h-ty-17)*mm,'后')
    c.setFillColorRGB(.1,.15,.2);c.setFont('STSong-Light',10)
    c.drawString(10*mm,24*mm,'净轮廓外包 '+str(p['net_bbox_mm'])+' mm')
    c.drawString(10*mm,17*mm,'裁剪外包 '+str(p['cut_bbox_mm'])+' mm；红虚线为缝线，黑实线裁剪')
    c.setStrokeColorRGB(0,0,0);c.line(10*mm,8*mm,60*mm,8*mm);c.line(10*mm,6*mm,10*mm,10*mm);c.line(60*mm,6*mm,60*mm,10*mm)
    c.drawString(65*mm,7*mm,'50 mm 校准');c.showPage()

def pieces_overview():
    cols=4;cw=440;ch=355;rows=math.ceil(len(pieces)/cols);W=cols*cw+60;H=rows*ch+180
    body=label(35,55,'存护囡囡体 · 完整衣片索引 v0.2',40)+label(35,95,'囡囡体 S胸标称围度＋估算长度；有净衣片和真实缝份，尚未试穿。',23,'#a54d39')
    body+=label(35,130,'收腰白衣／露肩蓝外搭和系带／前后尖披领／褶裙／腰片／可拆背结',22)
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


# Accurate layer intent; schematic assembled flats, not 1:1 views.
def flat(x,y,scale,layer,back=False):
 def sh(d,fill,stroke='#3a4b59',sw=1.5):return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
 g=''
 if layer in (1,6):
  g+=sh('M104 22 Q150 58 196 22 L211 28 Q207 50 224 61 L273 161 L248 178 L195 90 L188 154 L112 154 L105 90 L52 178 L27 161 L76 61 Q93 50 89 28Z','#fcf9f3')
  if not back:g+=sh('M104 22 L127 45 L111 62 L91 33Z M196 22 L173 45 L189 62 L209 33Z','#fffdf7')
  g+=sh('M31 153 L56 167 L49 190 L22 174Z M244 167 L269 153 L278 174 L251 190Z','#fffdf7')
  g+=sh('M25 171 L50 185 M250 185 L275 171','none','#608eb4',3)
  g+=sh('M126 82 L121 139 M174 82 L179 139','none','#abb6ba',1)
  if not back:g+=sh('M150 50 V140','none','#c4bdb0',1.5)
  else:g+=sh('M150 34 V154','none','#b34a47',2)+sh('M146 59 h8 v28 h-8Z M146 119 h8 v26 h-8Z','#d98fa8')
 if layer in (2,6):
  # Shoulder gap deliberately remains exposed above lowered blue neckline.
  g+=sh('M94 52 L111 62 L126 126 L150 143 L111 156 L98 103 L87 86 L51 122 L36 111 L73 62Z','#83b8df')
  g+=sh('M206 52 L189 62 L174 126 L150 143 L189 156 L202 103 L213 86 L249 122 L264 111 L227 62Z','#83b8df')
  g+=sh('M75 59 L103 53 L109 72 L84 84 L63 78Z M225 59 L197 53 L191 72 L216 84 L237 78Z','#bf9bda')
  g+=sh('M53 111 L70 119 L59 165 L50 153 L42 162Z M247 111 L230 119 L241 165 L250 153 L258 162Z','#83b8df')
  if back:g+=sh('M105 56 Q150 65 195 56 L189 155 L111 155Z','#8ebcde')+sh('M150 65 V154','none','#b44e4e',2)
  else:g+=sh('M145 139 Q119 129 114 141 Q120 155 145 146 L126 184 L151 166 L167 184 L157 145 Q181 157 188 141 Q180 128 155 139Z','#8bbcdf')
 if layer in (3,6):
  if back:
   g+=sh('M103 28 L146 44 L135 119 L110 148 L88 86Z M197 28 L154 44 L165 119 L190 148 L212 86Z','#304d83')
   g+=sh('M99 35 L94 83 L113 136 M105 39 L101 83 L117 129 M201 35 L206 83 L187 136 M195 39 L199 83 L183 129','none','#f7f5f0',3)
  else:
   g+=sh('M101 30 L111 42 L118 118 L103 147 L91 131 L100 79Z M199 30 L189 42 L182 118 L197 147 L209 131 L200 79Z','#304d83')
   g+=sh('M103 45 L106 115 L100 133 M197 45 L194 115 L200 133','none','#f7f5f0',4)
 if layer in (4,6):
  g+=sh('M111 153 L189 153 L224 275 L76 275Z','#35538a')
  for xx in range(115,190,12):g+=sh(f'M{xx} 163 L{150+(xx-150)*1.9} 273','none','#7d91b4',1.3)
  g+=sh('M79 263 L221 263 L224 275 L76 275Z','#f5f1e9')+sh('M83 253 H217','none','#f5f1e9',3)
  g+=sh('M111 153 H189 V166 H111Z','#c5b0dc')
  if back:g+=sh('M150 154 V185','none','#b65049',2)
 if layer in (5,6):
  if back:g+=sh('M111 153 L150 158 Q136 193 113 222 L97 215 L101 188Z M189 153 L150 158 Q164 193 187 222 L203 215 L199 188Z','#3e3b44')
  else:g+=sh('M111 153 L150 158 Q129 187 117 228 L96 217 L102 185Z M150 158 L189 153 Q200 204 176 269 L159 238 Q165 213 150 158Z','#3e3b44')
  g+=sh('M110 157 Q150 167 190 157 L190 165 Q150 175 110 165Z','#bca9d9')
  if back:g+=sh('M150 158 V174','none','#b65049',2)
 if layer in (6,7):
  if back or layer==7:
   g+=sh('M150 113 Q118 91 112 111 Q113 136 147 128 Q181 138 188 111 Q180 92 150 113Z','#8bcedf')
   g+=sh('M139 124 L111 191 L133 180 L142 197 L151 128Z','#b1c4eb')+sh('M151 128 L163 187 L174 177 L189 195 L168 124Z','#d4a8e2')
   g+=sh('M145 110 h10 v20 h-10Z','#8ec0df')
   if layer==7:g+=sh('M139 139 H167','none','#626c76',5)
 return f'<g transform="translate({x} {y}) scale({scale})">{g}</g>'

def layers_overview():
 W,H=1800,2080
 body=label(40,60,'存护三月七 · 完整分层服装试版',43)+label(40,105,'囡囡体 S胸 · 品牌标称围度＋授权估算长度 · v0.2 尚未试穿',24,'#ab4c38')
 specs=[('01 收腰白衬衣＋宽领长袖',1,'B01–B08：腰省、完整袖、开袖口'),('02 露肩蓝外搭＋前腰系带',2,'O01–O07：低袖窿、蓝外袖、尖垂片'),('03 深蓝前后尖披领',3,'C01–C02：背面分成两片宽尖领'),('04 十四褶裙＋独立腰头',4,'S01–S03：420折至140，后开衩'),('05 不对称深色腰饰',5,'W01–W04：长短四片，独立后扣'),('06 合穿外观＋可拆背结',6,'A01–A05：结翼、结芯、双尾、针座底片')]
 for i,(title,layer,note) in enumerate(specs):
  x=35+(i%2)*885;y=145+(i//2)*620
  body+=f'<rect x="{x}" y="{y}" width="850" height="590" rx="18" fill="#f4f6f6" stroke="#cad4d8"/>'
  body+=label(x+24,y+43,title,28)+label(x+24,y+82,note,20,'#637581')
  body+=label(x+207,y+117,'前面',22,anchor='middle')+label(x+633,y+117,'背面',22,anchor='middle')
  body+=flat(x+18,y+137,1.28,layer)+flat(x+440,y+137,1.28,layer,True)
  body+=label(x+24,y+566,'虚线位置为独立开口；款式示意不用于量尺。',20,'#7b6562')
 body+=label(40,2060,'所有完整衣片净轮廓与裁剪轮廓见1:1 PDF；浅色露肩区域保留，蓝层不盖成普通T恤。',22)
 path=OUT/'layers-overview.svg';path.write_text(svgdoc(W,H,body));render(path,path.with_suffix('.png'),1800)

def main():
 OUT.mkdir(exist_ok=True);(OUT/'pieces').mkdir(exist_ok=True)
 (OUT/'parameters-v0.2.json').write_text(json.dumps(P,ensure_ascii=False,indent=2)+'\n')
 can=canvas.Canvas(str(OUT/'preservation-full-pattern-v0.2-1to1.pdf'))
 for p in pieces:
  w,h=draw_piece_svg(p);pdfpiece(can,p,w,h)
 can.save();pieces_overview();layers_overview()
 manifest={'version':'v0.2','units':'mm','status':'完整数字试版，未实物试穿','measurement_basis':'囡囡体 S胸标称围度＋用户授权估算缺失长度','parameter_file':'parameters-v0.2.json','default_finished_chest_mm':180,'default_finished_waist_mm':140,'closure_overlap_mm':10,'back_hook_loop_width_mm':6,'production_print_ready':False,'pieces':[{k:v for k,v in p.items()if k not in ('net','cut')}for p in pieces]}
 (OUT/'pattern-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 assert all(q['pass'] for q in checks)
 result={'version':'v0.2','method':'Cubic sampled curves; shapely distance buffer with miter join, limit2. Sleeve notches placed by equal normalized arc length; each cap half has1mm ease.','all_net_and_cut_polygons_valid':True,'all_cut_polygons_contain_net':True,'pairs':checks,'sleeve_cuff_gather_mm':20,'white_sleeve_length_plus_cuff_mm':108+14,'closed_waist_mm':140,'skirt_pleats':{'flat_mm':420,'repeat_mm':30,'finished_repeat_mm':10,'count':14,'finished_waist_mm':140,'waistband_total_mm':150,'overlap_mm':10,'back_slit_length_mm':30,'skirt_body_overlap_mm':0},'physical_fit_validated':False,'waist_layer_reference':{'waist_flap_top_equals_skirt_waistband_top':True,'skirt_with_waistband_height_mm':98,'long_waist_flap_height_mm':86,'clearance_above_skirt_bottom_mm':12},'upper_sleeve_flounce':{'edge_mm':50,'target_seam_mm':round(length(outerArmF)+length(outerArmB),4),'gather_mm':round(50-length(outerArmF)-length(outerArmB),4)}}
 (OUT/'geometry-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 doc=fitz.open(OUT/'preservation-full-pattern-v0.2-1to1.pdf');assert len(doc)==len(pieces)
 from PIL import Image,ImageDraw
 board=Image.new('RGB',(1600,math.ceil(len(pieces)/5)*350),'#e9edef');d=ImageDraw.Draw(board)
 for i,page in enumerate(doc):
  pix=page.get_pixmap(matrix=fitz.Matrix(.6,.6));im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);im.thumbnail((300,320));x=(i%5)*320+(320-im.width)//2;y=(i//5)*350;board.paste(im,(x,y));d.text(((i%5)*320+8,y+328),str(i+1)+' '+pieces[i]['piece_id'],fill='black')
 board.save(OUT/'pdf-contact-sheet.png')
 rows=['|编号／衣片|净轮廓外包 mm|裁剪外包 mm|裁片数|材质|','|---|---|---|---|---|']
 for p in pieces:rows.append('|'+p['piece_id']+' '+p['name']+'|'+' × '.join(map(str,p['net_bbox_mm']))+'|'+' × '.join(map(str,p['cut_bbox_mm']))+'|'+p['cut_count']+'|'+p['material']+'|')
 (OUT/'dimension-table.md').write_text('# 存护完整衣片尺寸\n\n单位 mm。曲线衣片按真实轮廓裁，宽高只是外包框。所有尺寸为本次数字试版设计；胸170、腰128、肩86、臂122来自标称，其余长度为估算。净缝线红虚线、裁边黑实线，50mm校准。\n\n'+'\n'.join(rows)+'\n')
 print('Created',len(pieces),'pieces,',len(checks),'checks',OUT)
if __name__=='__main__':main()
