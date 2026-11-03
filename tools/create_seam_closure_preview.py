#!/usr/bin/env python3
"""Draw sewing/print-coverage and back-closure concepts, never cutting patterns."""
from pathlib import Path
import argparse
import os
import subprocess
import xml.etree.ElementTree as ET

from create_dimension_previews import label, rect, line, horizontal_dimension

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/illustrations/seams-and-back-closure-v0.1.svg'
INK, MUTED = '#233747', '#576A76'
BLUE, LIGHT_BLUE, NAVY = '#8FBCDF', '#C9DFEF', '#334D83'
PINK, ORANGE, GREEN = '#D980A6', '#B95132', '#387F7E'


def path(d, fill='none', stroke='none', width=2, extra=''):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" {extra}/>'


def dashed(x1,y1,x2,y2,color=ORANGE,width=3):
    return path(f'M{x1} {y1} L{x2} {y2}', stroke=color,width=width,extra='stroke-dasharray="10 7"')


def dot(x,y,color=ORANGE):
    return f'<circle cx="{x}" cy="{y}" r="6" fill="{color}"/>'


def leader(x1,y1,x2,y2):
    return line(x1,y1,x2,y2,MUTED,1.6)+dot(x2,y2,MUTED)


def text_lines(x,y,lines,size=24,gap=37,fill=INK):
    return ''.join(label(x,y+i*gap,t,size,fill) for i,t in enumerate(lines))


def card(x,y,w,h,title):
    return rect(x,y,w,h,'#FFFFFF','#D8E0E5',14)+label(x+28,y+49,title,30)


def seam_panel():
    b=card(45,190,1710,560,'01  印花、缝线与裁边：先定缝线，再向外留缝份')
    b+=label(90,285,'局部直线接缝示例 · 两片正面朝上展示',23,MUTED)
    b+=label(1220,285,'首版取样起点',26)
    for x in (100,650):
        b+=rect(x,355,470,250,NAVY,'#425361',extra='stroke-width="3"')
        b+=rect(x,537,470,9,'#FAF9F6')+rect(x,564,470,41,'#FAF9F6')
    # The illustration shows continuing print under the seam allowance overlay.
    for x in (490,650):
        b+=rect(x,355,80,250,'url(#allowanceHatch)')
    b+=dashed(490,355,490,605)+dashed(730,355,730,605)
    for x in (370,850):
        b+=path(f'M{x} 480 l13 19 l-13 19 l-13 -19Z','#B5DAEB')
        b+=path(f'M{x} 480 v19 h-13Z','#F6C9EE')
    for y in (430,542):
        for x in (490,730):
            b+=f'<circle cx="{x}" cy="{y}" r="8" fill="#FFFFFF" stroke="{ORANGE}" stroke-width="3"/>'
        b+=dashed(581,y,639,y,'#B9C4CA',1.5)
    b+=horizontal_dimension(490,333,80,'5 mm',355)
    b+=horizontal_dimension(650,333,80,'5 mm',355)
    b+=label(265,395,'衣片 A',26,'#FFFFFF')+label(890,395,'衣片 B',26,'#FFFFFF')
    b+=label(240,460,'主体图案区',22,'#DBEAF6')+label(855,460,'主体图案区',22,'#DBEAF6')
    b+=label(610,466,'配对',19,MUTED,'middle')
    b+=label(610,492,'接缝',19,MUTED,'middle')
    b+=text_lines(1220,328,['四分：常规缝份 5 mm','细小翻缝：3 mm','坐娃：常规缝份 6 mm','细小翻缝：4 mm'],24,38)
    b+=text_lines(1220,513,['底色延伸到裁边，','接缝处不留白色空带。','花纹按缝线上的对位点衔接；','曲边另按实际衣片外扩。'],23,35,MUTED)
    b+=line(100,653,155,653,'#425361',3)+label(170,661,'裁边',23)
    b+=dashed(300,653,355,653)+label(370,661,'缝线',23)
    b+=rect(500,639,52,24,'url(#allowanceHatch)','#CAB8A5')+label(570,661,'缝份内仍有印花',23)
    b+=label(92,713,'此处 5 mm 只是四分娃的局部示例；对位点、缝线与说明保留在校对层，不印入可见衣面。',23,MUTED)
    return b


def closure_panel():
    b=card(45,780,1710,710,'02  后中魔术贴：留净搭接区，勾面与圈面相向')
    b+=label(90,875,'展开看两侧贴位（分别画出需要缝贴的那一面）',24,MUTED)
    b+=label(1000,875,'闭合层次（层间拉开、厚度放大示意）',24,MUTED)
    # Two separately viewed flap surfaces. Only the overlap band has a dimension.
    b+=rect(115,970,300,225,LIGHT_BLUE,'#607F96',extra='stroke-width="2"')
    b+=rect(485,970,300,225,'#DDE9F3','#607F96',extra='stroke-width="2"')
    for x in (155,525):
        b+=rect(x,970,220,225,'#EFCABA',extra='opacity=".55"')
        b+=rect(x+44,995,132,175,PINK,'#A75175',4)
        for y in range(1006,1160,18):
            if x==525:
                for xx in range(x+54,x+168,15):
                    b+=path(f'M{xx} {y+8} v-6 q5 -5 8 0',stroke='#8D3C63',width=1.4)
            else:
                for xx in range(x+54,x+168,15):
                    b+=path(f'M{xx} {y+8} q-4 -13 4 -13 q7 0 6 13',stroke='#8D3C63',width=1.1)
        b+=horizontal_dimension(x,935,220,'净搭接 10 mm',970)
    b+=label(265,1025,'软毛圈',25,'#FFFFFF','middle')
    b+=label(635,1025,'细勾面',25,'#FFFFFF','middle')
    b+=label(265,1230,'A 外搭片的内面',24,INK,'middle')
    b+=label(635,1230,'B 内搭片朝外一面',24,INK,'middle')
    b+=label(265,1267,'贴宽 6 mm，左右各留 2 mm',21,MUTED,'middle')
    b+=label(635,1267,'贴宽 6 mm，左右各留 2 mm',21,MUTED,'middle')
    # Outer flap has soft loops on its inside; lower flap hooks point up.
    b+=label(1005,925,'衣服外侧',22,MUTED)
    b+=rect(1010,1000,515,18,LIGHT_BLUE,'#607F96',extra='stroke-width="2"')
    b+=rect(1285,1120,410,18,'#DDE9F3','#607F96',extra='stroke-width="2"')
    b+=rect(1333,1033,144,13,PINK)
    for xx in range(1340,1470,18):
        b+=path(f'M{xx} 1046 q-5 36 6 36 q13 0 10 -36',stroke='#A75175',width=2.5)
    b+=rect(1333,1093,144,13,PINK)
    for xx in range(1342,1470,17):
        b+=path(f'M{xx} 1093 v-25 q0 -13 10 -13 q10 0 10 10',stroke='#A75175',width=3)
    b+=dashed(1285,977,1285,1160,'#A2AFB7',1.5)+dashed(1525,977,1525,1160,'#A2AFB7',1.5)
    b+=dashed(1405,965,1405,1160,GREEN,1.5)
    b+=horizontal_dimension(1285,964,240,'闭合总搭接 10 mm',1000)
    b+=rect(1040,1177,650,16,'#E9D6BD','#A78A68',extra='stroke-width="1.5"')
    b+=label(1015,1233,'柔软薄护里／挡片，隔开贴背与娃体',23)
    b+=leader(1260,1210,1260,1185)
    b+=label(1010,1270,'娃体侧',22,MUTED)
    b+=label(1405,1324,'绿色虚线＝原后中对位线',22,GREEN,'middle')
    b+=text_lines(90,1357,['四分：两侧各跨后中 5 mm，形成 10 mm 净搭接；魔术贴宽 6 mm。',
                            '坐娃：两侧各跨后中 6 mm，形成 12 mm 净搭接；魔术贴宽 8 mm。',
                            '净搭接不包含翻折、贴边或护里的工艺余量；这些余量按最终做法另加。'],23,38)
    return b


def back_openings():
    b=card(45,1520,1710,815,'03  背部开口位置：上衣、腰头分别闭合，避开装饰和坐底')
    b+=label(90,1610,'存护／四分 BJD',28)
    b+=label(940,1610,'巡猎／坐姿棉花娃',28)
    # Garment silhouettes describe construction positions, not official back-view art.
    b+=path('M178 1688 L265 1655 Q292 1672 318 1655 L405 1688 L459 1776 L409 1815 L374 1751 L374 1946 L208 1946 L208 1751 L174 1815 L123 1776Z',LIGHT_BLUE,'#6E8CA0',2)
    b+=path('M265 1655 L292 1690 L318 1655 L338 1734 L306 1768 L292 1714 L278 1768 L245 1734Z',NAVY)
    b+=rect(208,1954,166,24,'#B9A3D8','#7C6B9A')
    b+=path('M208 1985 L374 1985 L412 2118 L170 2118Z',NAVY,'#50638C',2)
    for x in (208,240,274,309,342,374):
        b+=line(x,1985,x+(x-292)*.3,2118,'#7087B0',1.8)
    b+=rect(174,2095,234,12,'#FAF9F6')
    b+=dashed(292,1665,292,1944,ORANGE,4)
    b+=rect(282,1776,20,92,PINK,extra='opacity=".85"')
    b+=rect(282,1900,20,38,PINK,extra='opacity=".85"')
    b+=rect(282,1958,20,16,PINK)
    # A locking pin fixes the removable bow onto only one reinforced back piece.
    b+=rect(315,1788,54,85,'#D6E8CF',GREEN,3,extra='stroke-dasharray="6 4"')
    b+=path('M341 1805 Q299 1776 317 1829 Q332 1843 342 1820 Q355 1844 372 1828 Q389 1783 341 1805Z','#AADDEB','#5FA2B8',2)
    b+=path('M335 1820 L317 1892 L341 1870 L350 1892 L350 1820Z','#D6B6E6')
    b+=dot(346,1816,GREEN)
    b+=text_lines(485,1705,['上衣后中贯通开口','开口长度：按实际衣片确定'],23,37)
    b+=leader(470,1732,292,1728)
    b+=text_lines(485,1810,['可拆别针蝴蝶结','别在一侧承力区，避开后中','穿脱先取下，不穿透两侧开口'],23,37)
    b+=leader(470,1832,351,1816)
    b+=text_lines(485,1935,['腰头独立闭合','裙后开口按穿脱需要确定'],23,37)
    b+=leader(470,1960,299,1966)
    b+=label(485,2023,'蝴蝶结背面：别针底座与锁扣',22,MUTED)
    b+=rect(505,2040,310,60,'#D7DADF','#87939D',12)
    b+=f'<circle cx="538" cy="2070" r="13" fill="#9DA9B6" stroke="#697886" stroke-width="2"/>'
    b+=line(551,2070,785,2070,'#697886',5)
    b+=path('M776 2052 L800 2052 L800 2088 L776 2088Z','#AAB7C2','#697886',2)
    b+=path('M779 2059 H792 V2081 H779',stroke='#F9FBFC',width=3)
    b+=label(493,2138,'针座',20,MUTED)+leader(533,2115,538,2083)
    b+=label(770,2138,'锁扣',20,MUTED)+leader(792,2115,791,2087)
    b+=label(485,2180,'衣服内侧加承力布片／薄衬。',22,MUTED)
    b+=label(485,2215,'针座规格随实物选定，不预填尺寸。',22,MUTED)
    b+=label(90,2260,'上衣与裙腰不要一起缝死；别针只固定蝴蝶结，不能代替两侧开口的闭合。',23,MUTED)
    # Seated plush rear silhouette with pressure area below the fastening.
    b+=f'<ellipse cx="1095" cy="1970" rx="154" ry="158" fill="#EEE1D1" stroke="#D1BDA6" stroke-width="2"/>'
    b+=f'<ellipse cx="1095" cy="2100" rx="178" ry="47" fill="#DDC5AA" opacity=".72"/>'
    b+=path('M982 1680 L1060 1658 Q1095 1675 1130 1658 L1208 1680 L1267 1771 L1217 1811 L1183 1759 L1188 1955 Q1095 1993 1002 1955 L1007 1759 L973 1811 L923 1771Z','#B43E32','#81392F',2)
    b+=path('M1030 1913 Q1095 1944 1160 1913 L1173 1976 Q1095 2009 1017 1976Z','#6D5A6A','#493C4A',2)
    b+=path('M1005 1927 Q1095 1963 1185 1927 L1188 1948 Q1095 1986 1002 1948Z','#EBAFC1')
    b+=dashed(1095,1668,1095,1954,ORANGE,5)
    b+=rect(1084,1745,22,125,PINK,extra='opacity=".9"')
    b+=rect(1084,1891,22,49,PINK,extra='opacity=".9"')
    b+=label(1095,2110,'坐底受压区',23,'#7A5941','middle')
    b+=text_lines(1320,1705,['衣身从背部展开','避免整件硬套过大头'],23,37)
    b+=leader(1305,1730,1107,1746)
    b+=text_lines(1320,1848,['贴位停在衣身闭合段','下端位置随坐姿试穿确认'],23,37)
    b+=leader(1305,1875,1106,1923)
    b+=text_lines(1320,1993,['不把硬贴延到坐底','不把上下层勒成一条硬带'],23,37)
    b+=leader(1305,2015,1195,2080)
    b+=label(90,2303,'背部图仅表达开口关系，不是官方背面复原；花纹被遮挡区、贴边翻折和衬层需在最终衣片上确认。',23,MUTED)
    return b


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render',action='store_true')
    args=parser.parse_args()
    b=rect(0,0,1800,2500,'#F3F5F5')
    b+=label(55,70,'娃衣拼接与背部魔术贴规划',42)
    b+=label(58,118,'彩色结构示意 v0.1 · 尺寸单位 mm · 规划示意，非等比例裁片／已合身版',25,MUTED)
    b+=label(58,160,'当前印花稿是纹样样块；先映射实际衣片，再加入缝份、搭接与出血，不能按样块矩形直接裁缝。',23,ORANGE)
    b+=seam_panel()+closure_panel()+back_openings()
    b+=text_lines(57,2390,['此页尺寸为取样起点：缝份、搭接净宽与魔术贴宽度分别计算；背开口长度和正式版型仍需实物确认。',
                          '正式交厂：保留独立校对层；印花底色覆盖缝份，纹样主体避开翻折与搭接遮挡区。'],24,40,MUTED)
    document=f'<svg xmlns="http://www.w3.org/2000/svg" width="1800px" height="2500px" viewBox="0 0 1800 2500"><title>娃衣拼接与背部魔术贴规划 v0.1</title><desc>Concept diagrams, not to scale and not cutting patterns. Allowance and closure dimensions are initial sampling choices; garment dimensions remain unverified.</desc><defs><pattern id="allowanceHatch" width="14" height="14" patternUnits="userSpaceOnUse"><rect width="14" height="14" fill="#E8B98E" opacity=".28"/><path d="M-3 3 L3 -3 M0 14 L14 0 M11 17 L17 11" stroke="#DCA071" stroke-width="2" opacity=".65"/></pattern></defs>{b}</svg>\n'
    ET.fromstring(document)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(document)
    print(OUT)
    if args.render:
        js="const sharp=require('sharp');sharp(process.argv[2],{density:72}).flatten({background:'#fff'}).removeAlpha().withIccProfile('srgb').png().toFile(process.argv[2].replace(/\\.svg$/,'.png')).then(()=>console.log('PNG created'));"
        subprocess.run([os.environ.get('FABRIC_NODE_BIN','node'),'-',str(OUT)],input=js,text=True,check=True)


if __name__=='__main__':
    main()
