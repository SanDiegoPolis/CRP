"""Nanjing Tech University Jiangpu: official-map layout, vanilla Java 26.2.

Coordinates are traced from research/map-reference.png (1344 x 1824).
The illustrated map is not a survey. Interiors and terrain heights are adapted.
"""
from pathlib import Path
import json,math,random,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
import geometry as g
from models import regular,block_building,hip_roof,spiral,stadium,courts

ROOT=Path(__file__).resolve().parent.parent
SHARED=ROOT.parent/'ccucm_minecraft';WORLD=ROOT/'NJTech_Jiangpu_26.2'
W,D,H=2048,2560,160
V=np.zeros((H,D,W),dtype=np.uint8);DEM=np.zeros((D,W),dtype=np.int16)
PAL=g.PAL;COLORS=g.COLORS;LANDMARKS=[];CHECKS=[];BUILDINGS=[];CATALOG=[]
R=random.Random(1902)
cream=g.block('smooth_sandstone',(218,206,173))
roofred=g.block('red_terracotta',(145,77,66))
roofgray=g.block('gray_terracotta',(80,81,79))
coolglass=g.block('gray_stained_glass',(74,111,122))
pink=g.block('cherry_leaves',(220,156,178),persistent='true',distance='1',waterlogged='false')
goldleaf=g.block('azalea_leaves',(142,151,69),persistent='true',distance='1',waterlogged='false')

def setup(a):g.V=a;g.H,g.Z,g.W=a.shape
setup(V)
def xy(u,v):return round(110+(u-135)*1.65),round(75+(v-270)*1.75)
SPAWN=xy(965,1528)

ROADS=[
 ([(135,687),(180,530),(240,450),(550,325),(675,282),(739,281),(874,346)],22),
 ([(874,346),(885,536),(890,705),(938,774),(993,852),(1030,920),(1130,1060),(1197,1145),(1158,1230),(1060,1340),(982,1488),(950,1585),(900,1634),(839,1621),(760,1540),(701,1436),(650,1300),(615,1130),(541,975),(476,879),(377,801),(135,687)],20),
 ([(951,1512),(908,1450),(852,1373),(808,1302),(777,1234),(737,1155),(713,1100),(684,1051),(632,979),(614,906),(587,806),(551,740),(510,670),(481,604),(480,540),(455,503),(456,400)],14),
 ([(954,1498),(1010,1370),(1042,1290),(1085,1207),(1128,1170),(1064,1130),(996,1110),(930,1150),(893,1230),(827,1356),(852,1373)],13),
 ([(713,1100),(777,1060),(814,985),(882,948),(928,1001),(961,1070),(996,1110)],13),
 ([(684,1051),(735,961),(743,867),(755,819),(721,740),(680,713),(667,649),(646,621),(645,552)],13),
 ([(882,948),(834,911),(803,819),(755,719),(781,672),(849,648),(886,633)],12),
 ([(737,1155),(695,1177),(651,1210),(654,1290),(683,1415),(736,1508),(843,1453)],10),
 ([(852,1373),(775,1422),(719,1417),(695,1344),(694,1276),(671,1256)],10),
 ([(377,801),(370,705),(363,595),(390,510),(397,430),(449,390)],12),
 ([(377,801),(495,777),(528,739),(584,707),(588,649),(549,548),(521,516),(509,449),(509,413),(630,383),(685,336),(723,332),(790,385),(857,414),(879,449)],11),
 ([(495,777),(498,674),(455,624),(444,555),(443,502)],10),
 ([(521,516),(510,540),(510,613),(535,686),(551,740)],10),
 ([(588,649),(614,655),(623,699),(627,756),(624,835),(632,869)],10),
 ([(509,449),(585,439),(653,455),(709,485),(744,493),(779,474),(882,478)],11),
 ([(630,383),(696,369),(749,396),(793,435),(865,438)],9),
 ([(685,336),(713,350),(750,375),(810,410)],8),
 ([(737,1155),(748,1209),(775,1234)],8)
]
LAKES=[
 ('镜湖',[(527,761),(546,770),(561,809),(580,850),(605,877),(568,892),(549,859),(536,813)],3),
 ('镜湖广场水面',[(738,947),(747,980),(741,1020),(772,1050),(744,1080),(720,1080),(706,1050),(723,998),(727,947)],3),
 ('同济湖',[(622,958),(638,972),(649,1004),(664,1024),(632,1039),(617,1021),(609,980)],3),
 ('学府苑湖',[(705,411),(728,417),(745,441),(782,466),(773,489),(732,461)],3),
 ('学府苑东湖',[(797,437),(840,436),(861,451),(854,476),(796,473),(782,465)],3),
 ('学府苑南湖',[(712,485),(750,486),(772,475),(790,493),(779,521),(769,542),(756,542),(758,514),(710,503)],3),
 ('东侧水系',[(1050,1242),(1134,1176),(1160,1160),(1150,1180),(1080,1240),(1040,1310),(1010,1390),(971,1450),(950,1450),(971,1390),(998,1320)],3),
 ('行知湖',[(843,1531),(870,1520),(894,1530),(928,1523),(923,1548),(870,1583),(847,1568)],3),
 ('思源湖',[(673,1268),(692,1265),(700,1287),(679,1293)],3),
 ('北部小湖',[(432,594),(448,591),(455,617),(434,627)],3)
]

def poly_mask(points):
    im=Image.new('L',(W,D));ImageDraw.Draw(im).polygon([xy(*p) for p in points],fill=255)
    return np.asarray(im)>0
def line_mask(points,width):
    im=Image.new('L',(W,D));ImageDraw.Draw(im).line([xy(*p) for p in points],fill=255,width=width,joint='curve')
    return np.asarray(im)>0
def surface(mask,mat):
    zz,xx=np.where(mask);V[DEM[zz,xx],zz,xx]=mat

def terrain():
    zz,xx=np.mgrid[:D,:W];uu=135+(xx-110)/1.65;vv=270+(zz-75)/1.75
    hm=np.full((D,W),4.0)
    for u,v,rx,rz,height in [(435,365,140,50,45),(645,835,72,110,43),(814,595,76,70,53),(704,570,60,80,35),(707,1190,54,130,37),(921,918,58,86,34),(675,448,94,57,25)]:
        hm+=height*np.exp(-2*(((uu-u)/rx)**2+((vv-v)/rz)**2))
    # Soften the hills around each authored building and along the street network.
    # This retains the wooded ridges while giving the campus safe, level entrances.
    for b in CATALOG:
        cx,cz=xy(b['u'],b['v']);theta=math.radians(b['angle']);cs,sn=math.cos(theta),math.sin(theta)
        radius=math.ceil(math.hypot(b['w'],b['d'])/2)+45
        x0,x1=max(0,cx-radius),min(W,cx+radius+1);z0,z1=max(0,cz-radius),min(D,cz+radius+1)
        dx=xx[z0:z1,x0:x1]-cx;dz=zz[z0:z1,x0:x1]-cz
        ax=abs(dx*cs+dz*sn)-b['w']/2-10;az=abs(-dx*sn+dz*cs)-b['d']/2-16
        dist=np.sqrt(np.maximum(ax,0)**2+np.maximum(az,0)**2)
        target=b['base']+np.maximum(dist-2,0)*.55
        hm[z0:z1,x0:x1]=np.minimum(hm[z0:z1,x0:x1],target)
    for pts,width in ROADS:
        mask=line_mask(pts,width+18)
        hm[mask]=4
    # Terrain heights are illustrative, not measured elevation data.
    border=np.minimum(np.minimum(xx,W-1-xx),np.minimum(zz,D-1-zz))
    DEM[:]=np.rint(hm*np.clip(border/24,0,1)).astype('int16')
    for y in range(int(DEM.max())+1):V[y]=np.where(DEM>y,g.stone,np.where(DEM==y,g.grass,0))
    for name,pts,level in LAKES:
        mask=poly_mask(pts);V[:,mask]=0;V[:level-1,mask]=g.stone;V[level-1,mask]=g.dirt;V[level,mask]=g.water;DEM[mask]=level
        # A continuous low shore gives the water a contained edge.
        im=Image.fromarray((mask*255).astype('uint8'));rim=(np.asarray(im.filter(ImageFilter.MaxFilter(9)))>0)&~mask
        V[:,rim]=0;V[:4,rim]=g.stone;V[4,rim]=g.paving;DEM[rim]=4
    for pts,width in ROADS:
        edge=line_mask(pts,width+7);road=line_mask(pts,width)
        V[:4,edge]=g.stone;V[4,edge]=g.paving;DEM[edge]=4
        V[4,road]=g.asphalt
        for a,b in zip(pts,pts[1:]):
            ax,az=xy(*a);bx,bz=xy(*b);length=math.dist((ax,az),(bx,bz))
            for t in range(0,int(length),19):
                for dt in range(7):
                    q=min(1,(t+dt)/max(1,length));g.put(round(ax+(bx-ax)*q),4,round(az+(bz-az)*q),g.white)
    print('Terrain and lakes ready, maximum local height',int(DEM.max()),flush=True)

def pavilion(w,d):
    for x in (5,w-6):
        for z in (5,d-6):g.box(x,1,z,x+1,9,z+1,g.red)
    hip_roof(1,1,w-2,d-2,10,roofgray,6)
    g.box(8,1,d//2,w-9,1,d//2,g.wood)

def library(w,d):
    # Long terraced composition, projecting glazed reading rooms and white frames.
    for x,z,ww,dd,f in [(8,8,65,52,5),(w-75,7,66,48,4),(76,13,w-154,45,3)]:
        block_building(x,z,ww,dd,f,'white','office')
    # Main reading hall joins the stepped wings; six traversable levels.
    x1,x2,z1,z2=17,w-18,32,d-35
    g.box(x1,1,z1,x2,37,z2,g.quartz);g.box(x1+2,2,z1+2,x2-2,36,z2-2,0)
    for f in range(6):
        y=1+f*6;g.box(x1,y,z1,x2,y,z2,g.quartz)
        for x in range(x1+5,x2-4,18):
            for z in range(z1+6,z2-10,19):
                if abs(x-w//2)<17:continue
                g.box(x,y+1,z,x+9,y+3,z+1,g.book)
                g.box(x,y+1,z+7,x+9,y+1,z+9,g.wood)
                g.put(x+3,y+5,z+6,g.sea)
    g.box(x1+2,3,z2,x2-2,35,z2,coolglass)
    for x in range(x1+2,x2,5):g.box(x,2,z2+1,x,37,z2+1,g.white)
    # The suspended front reading box is the characteristic library facade.
    g.box(20,22,z2+1,82,24,z2+12,g.quartz)
    g.box(20,25,z2+1,82,35,z2+12,coolglass);g.box(22,25,z2+2,80,34,z2+10,0)
    g.box(18,36,z2-1,84,38,z2+14,g.quartz)
    for x in (22,50,80):g.box(x,1,z2+8,x+1,21,z2+9,g.quartz)
    for x in range(23,81,6):g.box(x,25,z2+13,x,35,z2+13,g.iron)
    g.box(w//2-6,2,z2-4,w//2+6,8,z2+3,0)
    g.box(w//2-7,1,z2-4,w//2+7,1,d-1,g.quartz)
    g.box(w//2-12,10,z2+3,w//2+23,10,z2+19,g.blueglass)
    for x in (w//2-11,w//2+22):g.box(x,1,z2+16,x,9,z2+16,g.iron)
    spiral(w//2-3,z1+12,1,31)
    g.box(w//2-5,36,z1+10,w//2+9,37,z1+24,g.quartz)
    for x in range(8,w-8,13):
        for z in (d-10,d-6):
            if abs(x-w//2)>18:g.box(x,1,z,x+7,2,z+2,g.grass)
    g.textwall('逸夫图书馆',w-82,11,z2+2,g.gold,9)

def tower(w,d):
    cx=w//2;cz=d//2-7
    block_building(cx-30,cz-22,61,48,2,'white','office')
    hip_roof(cx-32,cz-24,65,52,15,roofgray,4)
    # Fluted concrete shaft, open central stair and the square glazed lantern.
    g.box(cx-9,15,cz-9,cx+9,76,cz+9,g.quartz)
    for dx in (-8,-4,0,4,8):g.box(cx+dx,20,cz+10,cx+dx,76,cz+10,g.iron)
    g.box(cx-15,74,cz-15,cx+15,77,cz+15,cream)
    g.box(cx-14,78,cz-14,cx+14,96,cz+14,cream)
    g.box(cx-12,78,cz-12,cx+12,95,cz+12,0)
    g.box(cx-12,88,cz+14,cx+12,95,cz+14,coolglass)
    for x in range(cx-12,cx+13,4):g.box(x,88,cz+15,x,95,cz+15,g.iron)
    g.box(cx-16,97,cz-16,cx+16,99,cz+16,g.quartz)
    hip_roof(cx-13,cz-13,27,27,100,roofgray,12)
    g.box(cx,112,cz,cx,121,cz,g.iron)
    spiral(cx-5,cz-5,1,89)
    g.box(cx-4,2,cz+5,cx+4,7,cz+29,0);g.box(cx-4,1,cz+5,cx+4,1,d-1,g.quartz)
    # Emblem and a readable full name on the ground-level sign.
    g.box(cx-5,80,cz+15,cx+5,87,cz+15,g.gold)
    g.box(cx-3,81,cz+16,cx+3,85,cz+16,roofred)
    for i,ch in enumerate('南工大'):g.textwall(ch,cx-4,62-i*11,cz+11,g.red,9)
    g.box(cx-7,94,cz-7,cx+7,95,cz+7,g.quartz)

def teaching(w,d,floors=5,style='white',roof=False):
    # Three parallel blocks and two broad links give the comb-shaped plan.
    if d<88:
        regular(w,d,floors,style,'classroom')
        if roof:hip_roof(3,3,w-6,d-11,2+floors*6,roofgray,5)
        return
    wing=24
    for z in (6,(d-wing)//2,d-wing-12):block_building(6,z,w-12,wing,floors,style,'classroom')
    for x in (w//3,2*w//3):
        g.box(x-6,1,10,x+6,1+floors*6,d-20,g.quartz)
        g.box(x-4,2,10,x+4,floors*6,d-19,0)
        for f in range(floors):g.box(x-5,1+f*6,10,x+5,1+f*6,d-20,g.quartz)
    if roof:
        for z in (4,(d-wing)//2-2,d-wing-14):hip_roof(4,z,w-8,28,2+floors*6,roofgray,5)
    # Clear a route from the front block to both links on each floor.
    for f in range(floors):
        y=2+f*6
        g.box(w//2-4,y,d-wing-18,w//2+4,y+3,d-wing+8,0)
        g.box(w//2-4,y-1,d-wing-18,w//2+4,y-1,d-wing+8,g.quartz)
    g.box(w//2-5,2,d-15,w//2+5,6,d-1,0)
    g.box(w//2-5,1,d-21,w//2+5,1,d-1,g.quartz)

def mingde(w,d):
    regular(w,d,5,'beige','office')
    for x in range(9,w-9,11):g.box(x,2,d-10,x+1,30,d-10,g.quartz)
    cx=w//2
    block_building(cx-12,6,25,23,7,'white','office')
    hip_roof(cx-15,3,31,29,45,roofred,9)
    g.textwall('明德',cx-9,33,29,g.gold,8)

def arena(w,d,pool=False):
    g.box(7,1,7,w-8,26,d-16,g.quartz);g.box(9,2,9,w-10,25,d-18,0)
    g.box(10,1,10,w-11,1,d-19,g.wood)
    for x in range(8,w-7):
        y=27+round(7*math.sin(math.pi*(x-8)/(w-15)))
        g.box(x,y,3,x,y+1,d-11,g.white)
    g.box(9,6,d-15,w-10,27,d-15,coolglass)
    for x in range(10,w-8,10):g.box(x,2,d-14,x+1,29,d-14,g.quartz)
    g.box(w//2-5,2,d-16,w//2+5,6,d,0);g.box(w//2-5,1,d-16,w//2+5,1,d,g.quartz)
    if pool:
        g.box(18,0,18,w-19,0,d-25,g.blue);g.box(18,1,18,w-19,1,d-25,g.water)
        for x in range(23,w-18,7):g.box(x,1,18,x,1,d-25,g.white)
    else:
        cx=w//2;cz=(d-9)//2
        g.outline(cx-18,cz-31,cx+18,cz+31,2,g.white);g.disk(cx,cz,7,2,g.white,6)
        g.box(cx-18,2,cz,cx+18,2,cz,g.white)
        for z in (cz-28,cz+28):g.box(cx,2,z,cx,8,z,g.iron);g.box(cx-3,9,z,cx+3,12,z,g.white)
        for j in range(7):
            g.box(10+j,2+j,14,10+j,2+j,d-22,g.blue)
            g.box(w-11-j,2+j,14,w-11-j,2+j,d-22,g.red)

def dining(w,d):
    regular(w,d,3,'beige','office')
    for y in (2,8,14):
        for x in range(15,w-12,14):
            for z in range(11,d-18,12):
                if abs(z-(d-10)//2)<6:continue
                g.box(x,y,z,x+5,y,z+2,g.wood)
    g.box(9,7,d-9,w-10,10,d-9,roofred)

def dorm(w,d,floors=6,roof=True):
    regular(w,d,floors,'beige','dorm')
    if roof:hip_roof(4,4,w-8,d-13,2+floors*6,roofgray,4)

def villa(w,d):
    g.box(3,1,3,w-4,13,d-6,g.lightterra);g.box(5,2,5,w-6,12,d-8,0)
    g.box(5,7,5,w-6,7,d-8,g.quartz)
    for x in range(6,w-4,6):
        for y in (3,9):g.box(x,y,d-6,x+2,y+2,d-6,g.blueglass)
    g.box(w//2-1,2,d-7,w//2+1,5,d-1,0);g.box(w//2-1,1,d-7,w//2+1,1,d-1,g.quartz)
    hip_roof(1,1,w-2,d-5,14,roofred,5)

def gate(w,d):
    # Broad white name wall and separated vehicle/walking entrances.
    g.box(8,1,5,w//2+28,10,10,g.quartz)
    g.textwall('南京工业大学',14,1,11,g.gold,11)
    for x in (w-48,w-14):
        g.box(x,1,5,x+4,15,10,g.quartz)
    g.box(w-52,16,2,w-6,18,14,g.quartz)
    g.box(w-43,1,0,w-23,1,d-1,g.asphalt)
    g.box(4,1,18,20,7,29,coolglass);g.box(3,8,17,21,9,30,g.white)

def softball(w,d):
    cx=w//2;cz=d-24
    g.ground(2,2,w-3,d-3,g.green)
    for r in range(8,min(w,d)-10):
        for t in np.linspace(-math.pi*.82,-math.pi*.18,max(20,r*4)):
            x=round(cx+math.cos(t)*r);z=round(cz+math.sin(t)*r)
            g.put(x,0,z,cream if r<42 else g.green)
    for a,b in [((cx,cz),(cx-29,cz-29)),((cx-29,cz-29),(cx,cz-58)),((cx,cz-58),(cx+29,cz-29)),((cx+29,cz-29),(cx,cz))]:g.path([a,b],2,g.white,1)
    for x,z in [(cx,cz),(cx-29,cz-29),(cx+29,cz-29),(cx,cz-58)]:g.box(x-1,1,z-1,x+1,1,z+1,g.white)
    g.box(3,8,3,w-4,8,3,g.bars)
    for x in range(3,w-3,10):g.box(x,1,3,x,8,3,g.iron)

def add(name,u,v,w,d,kind='regular',angle=-25,base=4,targets=None,note='',guide=True,**opts):
    CATALOG.append(dict(name=name,u=u,v=v,w=w,d=d,kind=kind,angle=angle,base=base,targets=targets,note=note,guide=guide,opts=opts))

def catalog():
    add('逸夫图书馆',779,898,186,130,'library',angle=90,targets=[2,8,14,20,26,32],note='悬挑阅览体块 / 白色框架 / 六层室内')
    add('进学楼',786,849,84,54,angle=90,note='图书馆北侧教学配套')
    add('天宝阁（南工塔）',645,582,86,93,'tower',angle=0,targets=[2,14,30,50,78,90],note='竖向塔身 / 观景层 / 步行楼梯')
    add('仁智楼',645,670,177,145,'teaching',angle=0,targets=[2,8,14,20,26],roof=True,note='连廊与多翼教学组团')
    add('同和楼',615,738,125,88,'teaching',angle=0,roof=True,note='教学楼 / 灰色坡屋顶')
    add('厚学楼',915,1388,150,108,'teaching',targets=[2,8,14,20,26],note='白色教学楼 / 中央入口')
    add('笃学楼',961,1299,150,108,'teaching',style='beige',targets=[2,8,14,20,26],note='浦江教学组团 / 玻璃门厅')
    add('明德楼',831,1429,108,58,'mingde',targets=[2,8,14,20,26],note='行政楼 / 红色塔楼屋顶')
    add('笃行楼',851,1274,109,86,'teaching',floors=4,style='beige',note='院落教学楼')
    add('崇德楼',850,1190,140,94,'teaching',floors=5,style='beige',note='A—E 学科楼组团')
    add('尚德楼',913,1250,128,93,'teaching',floors=5,style='beige',note='学科楼组团')
    add('弘毅楼',812,1311,122,108,'teaching',floors=4,note='四翼学院楼群')
    add('沉毅楼',871,1329,76,68,'teaching',floors=4,style='beige',note='教学与实验空间')
    add('沉毅南楼',887,1361,52,41,angle=-25,floors=4,style='beige',note='教学配套',guide=False)
    add('地坤楼',737,750,78,69,angle=-25,floors=5,note='东侧学科楼')
    add('天工楼',769,793,70,67,angle=-25,floors=5,note='东侧学科楼')
    add('立德楼',802,721,55,53,'mingde',note='学科楼')
    add('浦德楼',837,767,113,72,'teaching',floors=4,style='beige',note='东侧学院楼')
    add('厚德楼',835,822,73,38,style='beige',floors=4,note='学科楼',guide=False)
    add('国家生化工程技术研究中心',885,823,130,92,'teaching',floors=4,note='科研楼组团')
    add('江苏省工业生物技术创新中心',980,882,108,94,'teaching',floors=4,note='科研配套')
    add('热科学与工程实验楼',1040,916,54,34,floors=3,note='科研配套',guide=False)
    add('天佑楼',1030,977,44,50,floors=4,note='校园配套',guide=False)
    add('行健体育馆',1075,1170,136,122,'arena',targets=[2],note='弧形屋顶 / 玻璃立面 / 球场看台')
    add('游泳馆',1123,1142,92,89,'arena',pool=True,note='室内泳池 / 分道线')
    add('行健综合馆',1045,1135,110,44,floors=3,note='多功能运动空间')
    add('行健田径场',973,1035,201,122,'stadium',angle=67,note='田径跑道 / 足球场 / 看台')
    add('行健篮球场',1001,1104,98,91,'courts',angle=-25,note='室外篮球场')
    add('卓远棒球场',879,984,132,117,'softball',angle=-25,note='棒球场地')
    add('卓远垒球场',715,1430,112,111,'softball',angle=-30,note='垒球特色运动场')
    add('亚青田径场',405,746,178,104,'stadium',angle=90,note='亚青村田径场')
    add('亚青村餐厅',458,686,86,52,'dining',angle=0,note='学生餐厅')
    add('亚青网球场',400,692,64,40,'courts',angle=0,note='运动配套',guide=False)
    add('象山苑餐厅',549,723,62,64,'dining',angle=-15,note='镜湖北侧餐饮')
    add('北苑食堂',674,1033,64,42,'dining',angle=-25,note='学生餐厅')
    add('西苑食堂',705,1253,65,54,'dining',angle=-20,note='学生餐厅')
    add('南苑食堂',744,1390,73,42,'dining',angle=-20,note='学生餐厅')
    add('1902餐厅',1085,1125,55,30,'dining',note='餐饮空间',guide=False)
    add('乐苑体育馆',756,1208,77,71,'arena',angle=-25,note='学生服务片区体育馆')
    add('学生事务中心',786,1215,53,50,floors=4,note='学生服务')
    add('雅集馆',782,1379,63,44,'mingde',note='校园文化空间',guide=False)
    add('博雅堂',848,1451,88,36,floors=3,style='beige',note='教务办公')
    add('博学楼',860,1473,104,40,floors=5,style='beige',note='教学办公')
    add('明正楼',866,1506,108,60,'teaching',floors=4,style='beige',note='行政办公')
    add('南门',947,1512,169,40,'gate',angle=-35,note='校名墙 / 入校广场')
    add('西门',378,800,65,28,'gate',angle=90,note='亚青村入口',guide=False)
    add('校医院',586,943,74,49,'teaching',floors=3,style='beige',note='校园医院')
    add('东苑网球场',753,1108,86,86,'courts',note='网球场组团',guide=False)
    add('东苑器械场',778,1160,80,62,'courts',note='健身运动区',guide=False)
    # Student accommodation follows the labelled regions of the official map.
    idx=0
    for row,v in enumerate([552,576,600,625,651,676,701]):
        for col,u in enumerate([332,361,397,429]):
            idx+=1;add(f'亚青村公寓{idx:02d}',u-(row*2 if col<2 else 0),v,35 if col<2 else 44,25,'dorm',angle=0,floors=6,guide=False)
    for i,(u,v,w) in enumerate([(348,734,72),(427,441,73),(426,466,69),(411,492,75),(363,518,44),(418,518,57),(347,535,48),(392,534,43),(460,514,65),(472,540,70),(477,715,80),(477,742,79),(477,770,80)],29):
        add(f'亚青村公寓{i:02d}',u,v,w,29,'dorm',angle=0,floors=6,guide=False)
    for i,(u,v) in enumerate([(456,562),(455,586),(450,612),(452,640),(468,660),(484,674),(486,641),(500,616),(506,654),(507,683)],1):
        add(f'象山苑公寓{i:02d}',u,v,41,26,'dorm',angle=-15,floors=6,guide=False)
    for i,(u,v) in enumerate([(548,667),(569,669),(547,644),(570,644),(547,618),(569,618),(546,594),(570,595),(548,572),(570,572),(557,551)],1):
        add(f'檀香苑公寓{i:02d}',u,v,35 if i<11 else 73,27,'dorm',angle=0,floors=6,guide=False)
    # Northwestern hillside housing: compact pale walls and red pitched roofs.
    faculty=[(528,410),(555,405),(584,399),(612,391),(652,392),(627,408),(598,423),(567,426),(539,430),
      (686,333),(708,329),(734,333),(752,350),(763,368),(778,389),(803,400),(830,398),(850,404),
      (690,368),(705,388),(726,397),(746,413),(764,429),(791,416),(810,430),
      (530,454),(556,453),(587,461),(616,467),(645,481),(672,493),(697,498),(719,493),(680,474),(660,464),
      (541,479),(532,496),(532,515),(640,454),(656,461),(671,463),(689,473),
      (829,556),(852,584),(826,584),(804,596),(784,666),(805,665),(826,653),(846,646),
      (813,699),(835,688),(856,677)]
    for i,(u,v) in enumerate(faculty,1):add(f'学府苑住宅组团{i:02d}',u,v,31,24,'villa',angle=-15 if v<440 else 15,guide=False)
    north=[(795,1040),(815,1040),(835,1039),(850,1009),(829,1007),(809,1006),(794,995),(780,971),(781,950),(789,933),(799,915),(812,902),(830,920),
      (599,1069),(610,1044),(627,1037),(642,1035),(629,999),(615,980),(601,960),(591,942)]
    # Correct the north/east courtyard coordinates to the region below the library.
    north=[(795,1040),(815,1040),(835,1039),(850,1011),(829,1008),(809,1007),(794,996),(780,980),(780,964),(792,945),(810,937),(811,918),(828,924),
      (605,1060),(624,1052),(642,1047),(607,1037),(613,1022),(606,1008),(599,991),(596,976)]
    for i,(u,v) in enumerate(north,1):add(f'北苑公寓{i:02d}',u,v,30,22,'villa',angle=-25,guide=False)
    for i,(u,v) in enumerate([(691,1090),(711,1112),(717,1136),(725,1159),(750,1149),(753,1181),(696,1172),(686,1197),(705,1207),(718,1231),(737,1210)],1):
        add(f'东苑公寓{i:02d}',u,v,57,28,'dorm',floors=6,guide=False)
    for i,(u,v) in enumerate([(646,1144),(660,1158),(646,1176),(663,1187),(648,1211),(667,1227),(653,1244),(676,1247),(668,1285)],1):
        add(f'西苑公寓{i:02d}',u,v,32,26,'dorm',floors=6,guide=False)
    for i,(u,v) in enumerate([(696,1317),(725,1310),(708,1345),(735,1337),(717,1371),(735,1355),(726,1396),(747,1461),(753,1482),(789,1499)],1):
        add(f'南苑公寓{i:02d}',u,v,45,25,'dorm',floors=6,targets=[2,8,14,20,26,32] if i==1 else None,guide=i==1,note='六层宿舍 / 示例内装')
    for i,(u,v) in enumerate([(1050,1018),(1077,1034),(1125,1050),(1098,1073),(1039,1078),(1037,1048)],1):
        add(f'景星苑公寓{i:02d}',u,v,80,27,'dorm',angle=10,floors=8,roof=False,guide=False)
    # Refine measured centers and local dimensions before resolving tight clearances.
    overrides={
      '逸夫图书馆':dict(v=910), '进学楼':dict(v=831,w=58,d=45),
      '笃行楼':dict(w=95,d=64), '弘毅楼':dict(u=807,w=98,d=95),
      '沉毅南楼':dict(u=882,v=1354,w=46,d=32),
      '游泳馆':dict(u=1140,v=1141,w=90,d=78),
      '行健综合馆':dict(u=1039,v=1126,w=103,d=36),
      '行健篮球场':dict(v=1117,w=85,d=70),
      '亚青网球场':dict(u=401,v=684,w=47,d=25),
      '1902餐厅':dict(u=1081,v=1110,w=45,d=26),
      '学生事务中心':dict(u=796,v=1200,w=48,d=37),
      '西门':dict(u=365,v=812,w=60,d=24),
      '亚青村公寓23':dict(v=666), '亚青村公寓24':dict(v=663),
      '亚青村公寓27':dict(u=331,v=717), '亚青村公寓28':dict(u=360,v=717),
    }
    for b in CATALOG:
        if b['name'] in overrides:b.update(overrides[b['name']])
        if b['name'].startswith('北苑公寓'):
            idx=int(b['name'][-2:])
            if idx<=13:
                pts=[(786,1045),(809,1042),(832,1040),(850,1024),(829,1021),(809,1019),(790,1006),(781,988),(789,970),(799,955),(815,962),(805,980),(826,987)]
                b['u'],b['v']=pts[idx-1]
    resolve_positions()

def resolve_positions():
    """Small documented translations preserve separations on a coarse voxel grid."""
    occupied=np.zeros((D,W),dtype=bool)
    for _,points,_ in LAKES:occupied|=poly_mask(points)
    adjustments=[]
    for b in CATALOG:
        cx,cz=xy(b['u'],b['v']);theta=math.radians(b['angle']);cs,sn=math.cos(theta),math.sin(theta)
        local=[(-b['w']/2-4,-b['d']/2-4),(b['w']/2+12,-b['d']/2-4),(b['w']/2+12,b['d']/2+12),(-b['w']/2-4,b['d']/2+12)]
        pts=[(x*cs-z*sn,x*sn+z*cs) for x,z in local]
        x0=int(math.floor(min(p[0] for p in pts)));z0=int(math.floor(min(p[1] for p in pts)))
        ww=int(math.ceil(max(p[0] for p in pts)))-x0+1;dd=int(math.ceil(max(p[1] for p in pts)))-z0+1
        im=Image.new('L',(ww,dd));ImageDraw.Draw(im).polygon([(x-x0,z-z0) for x,z in pts],fill=255);mask=np.asarray(im)>0
        offsets=[(dx*dx+dz*dz,dx,dz) for dz in range(-160,161,4) for dx in range(-160,161,4)]
        for _,dx,dz in sorted(offsets):
            ax,az=cx+x0+dx,cz+z0+dz
            if ax<0 or az<0 or ax+ww>=W or az+dd>=D:continue
            part=occupied[az:az+dd,ax:ax+ww]
            if np.any(part[mask]):continue
            part[mask]=True
            if dx or dz:
                adjustments.append({'name':b['name'],'dx_blocks':dx,'dz_blocks':dz})
                b['u']+=dx/1.65;b['v']+=dz/1.75
            break
        else:raise RuntimeError('No clear placement near '+b['name'])
    (ROOT/'tools/layout-adjustments.json').write_text(json.dumps(adjustments,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Adjusted spacing for',len(adjustments),'of',len(CATALOG),'groups',flush=True)

def place(b):
    name=b['name'];w,d,base=b['w'],b['d'],b['base'];cx,cz=xy(b['u'],b['v']);angle=b['angle']
    temp=np.zeros((H-base,d+8,w+8),dtype=np.uint8)
    saved=g.BE;g.BE={};setup(temp);g.ground(0,0,w+7,d+7,g.paving)
    funcs={'regular':regular,'library':library,'tower':tower,'teaching':teaching,'mingde':mingde,'arena':arena,'dining':dining,'dorm':dorm,'villa':villa,'gate':gate,'stadium':stadium,'courts':courts,'softball':softball,'pavilion':pavilion}
    funcs[b['kind']](w,d,**b['opts'])
    g.sign(w//2+10,2,d-1,[name,b['note'][:25],'南京工业大学 · 江浦','Java 26.2 原版'])
    theta=math.radians(angle);cs,sn=math.cos(theta),math.sin(theta);r=math.ceil(math.hypot(w+8,d+8)/2)+3
    x0,x1=max(0,cx-r),min(W,cx+r+1);z0,z1=max(0,cz-r),min(D,cz+r+1)
    zz,xx=np.mgrid[z0:z1,x0:x1];dx=xx-cx;dz=zz-cz
    # Integer centers prevent banker's rounding from dropping alternate columns
    # when a cardinally aligned template has an odd width or depth.
    lx=np.rint(dx*cs+dz*sn+w//2).astype(int);lz=np.rint(-dx*sn+dz*cs+d//2).astype(int)
    valid=(lx>=0)&(lx<temp.shape[2])&(lz>=0)&(lz<temp.shape[1]);lx=np.clip(lx,0,temp.shape[2]-1);lz=np.clip(lz,0,temp.shape[1]-1)
    high=int(np.max(np.where(temp!=0)[0]))+1
    for y in range(base):V[y,z0:z1,x0:x1][valid]=g.stone
    for y in range(base,H):V[y,z0:z1,x0:x1][valid]=temp[y-base,lz,lx][valid] if y-base<high else 0
    DEM[z0:z1,x0:x1][valid]=base
    localbe=g.BE;g.BE=saved;setup(V)
    for entries in localbe.values():
        for e in entries:
            sx,sz=e['x'][1]-w//2,e['z'][1]-d//2
            x=round(cx+sx*cs-sz*sn);z=round(cz+sx*sn+sz*cs);y=e['y'][1]-64+base
            g.sign(x,y,z,e['front_text'][1]['messages'][1][1],str(round(8+angle/22.5)%16))
    ex=round(cx-(d/2+6)*sn);ez=round(cz+(d/2+6)*cs)
    lm={'name':name,'label':b['note'],'x':cx,'z':cz,'base':base,'width':w,'depth':d,'height':high,'angle':angle,'entrance':[ex,base+65,ez]}
    BUILDINGS.append(lm)
    if b['guide'] or b['targets']:LANDMARKS.append(lm)
    if b['targets']:
        CHECKS.append({'name':name,'template_shape':list(temp.shape),'width':w,'depth':d,'targets':b['targets']})
        np.save(ROOT/'tools'/('check_'+name.replace(' ','_')+'.npy'),temp)
    print(name,cx,cz,'height',high,flush=True)

def marker(name,u,v,note):
    x,z=xy(u,v);LANDMARKS.append(dict(name=name,label=note,x=x,z=z,base=int(DEM[z,x]),width=30,depth=30,height=2,angle=0,entrance=[x,int(DEM[z,x])+65,z]))

def landscape():
    setup(V)
    # Lake promenade and the main southern entrance lawn, keeping water visible.
    for pts in [[(526,756),(548,759),(576,817),(614,880),(609,896),(566,902),(540,854),(522,785),(526,756)],[(929,1500),(906,1460),(878,1417)],[(630,780),(654,820),(690,865),(727,904)],[(644,623),(645,637)],[(640,574),(630,607),(612,637)]]:
        mask=line_mask(pts,6);zz,xx=np.where(mask);V[DEM[zz,xx],zz,xx]=g.paving
    for u,v in [(530,766),(588,830),(644,975),(907,1551)]:
        x,z=xy(u,v);g.box(x-8,4,z-6,x+8,4,z+6,g.wood)
        for dz in (-6,6):
            g.box(x-8,7,z+dz,x+8,7,z+dz,g.spruce)
            for dx in (-8,0,8):g.box(x+dx,5,z+dz,x+dx,7,z+dz,g.fence)
    # A contained fountain at the southern entrance, close to the name wall.
    cx,cz=xy(901,1463)
    g.disk(cx,cz,16,4,g.quartz);g.disk(cx,cz,13,4,g.water);g.cylinder(cx,cz,3,5,8,g.quartz)
    g.disk(cx,cz,7,9,g.quartz);g.disk(cx,cz,6,10,g.water)
    for u,v in [(651,821),(703,851),(718,1191),(853,876)]:
        x,z=xy(u,v);y=int(DEM[z,x]);g.box(x-5,y,z-5,x+5,y,z+5,g.paving)
        for dx,dz in [(-4,-4),(4,-4),(-4,4),(4,4)]:g.box(x+dx,y+1,z+dz,x+dx,y+7,z+dz,g.red)
        for k in range(5):g.box(x-7+k,y+8+k,z-7+k,x+7-k,y+8+k,z+7-k,roofgray)
    for nm,u,v,note in [('镜湖',563,832,'长湖 / 湖滨步道'),('同济湖',636,1006,'北苑湖景'),('学府苑湖区',795,460,'北部住宅与水系'),('行知湖',890,1550,'南门西侧湖景'),('象山与林间步道',688,832,'山地园林 / 高差适配')]:marker(nm,u,v,note)
    count=0
    for i in range(38000):
        if count>=6200:break
        x,z=R.randrange(40,W-40),R.randrange(40,D-40);y=int(DEM[z,x])
        if V[y,z,x]!=g.grass or np.any(V[y+6:y+19,z-6:z+7,x-6:x+7]):continue
        if np.any(V[y+1:y+6,z,x]):continue
        # Keep the road shoulders open, with denser woodland on the slopes.
        if np.any(np.isin(V[max(0,y-1):y+2,z-4:z+5,x-4:x+5],[g.asphalt,g.white,g.water])):continue
        height=R.randint(8,15);leaf=R.choice([g.leaves,g.leaves,g.pine,g.birchleaves,pink,goldleaf])
        g.sphere(x,y+height,z,4,4,4,leaf);g.sphere(x+2,y+height+1,z-1,3,3,3,leaf);g.box(x,y+1,z,x,y+height,z,g.log);count+=1
    # Dense mixed woodland on the central ridges, as in the official aerial photos.
    wooded=0
    for i in range(15000):
        x,z=R.randrange(100,W-100),R.randrange(100,D-100);y=int(DEM[z,x])
        if y<8 or V[y,z,x]!=g.grass or np.any(V[y+5:y+20,z-4:z+5,x-4:x+5]):continue
        if np.any(V[y+1:y+5,z,x]):continue
        height=R.randint(8,14);leaf=R.choice([g.leaves,g.leaves,g.pine,g.birchleaves])
        g.sphere(x,y+height,z,4,4,4,leaf);g.box(x,y+1,z,x,y+height,z,g.log);count+=1;wooded+=1
    print('Additional woodland trees',wooded,flush=True)
    for pts,width in ROADS:
        for a,b in zip(pts,pts[1:]):
            ax,az=xy(*a);bx,bz=xy(*b);length=math.dist((ax,az),(bx,bz))
            for t in range(14,int(length)-8,42):
                q=t/length;x=round(ax+(bx-ax)*q+width/2+5);z=round(az+(bz-az)*q)
                if not(8<x<W-8 and 8<z<D-8):continue
                y=int(DEM[z,x])
                if np.any(V[y+1:y+13,z-3:z+4,x-3:x+4]):continue
                g.box(x,y+1,z,x,y+8,z,g.iron);g.box(x-2,y+9,z,x+2,y+9,z,g.slate);g.put(x-2,y+8,z,g.sea);g.put(x+2,y+8,z,g.sea)
    sx,sz=SPAWN;g.box(sx-5,4,sz-5,sx+5,4,sz+5,g.quartz);g.box(sx-5,5,sz-5,sx+5,10,sz+5,0);DEM[sz-5:sz+6,sx-5:sx+6]=4
    g.sign(sx+7,6,sz+3,['南京工业大学 · 江浦校区','南门出发 / 厚学楼 / 图书馆','创造模式 / 双击空格飞行','Campus Reconstruction Project'])
    marker('出生点',965,1528,'南门外 / 面向校园')
    print('Landscape:',count,'trees;',len(BUILDINGS),'building groups;',len(LANDMARKS),'guide landmarks',flush=True)
    return count

def export(trees):
    import exporter as e
    for k in ('ROOT','SHARED','WORLD','W','D','H','V','DEM','LANDMARKS','CHECKS','SPAWN','PAL','COLORS','g'):setattr(e,k,globals()[k])
    e.export()
    m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'));m['building_groups']=BUILDINGS;m['trees']=trees
    m['source_map']='南京工业大学 2023 学业指南，第 75 页（PDF 第 79 页）';m['spawn_yaw']=150;m['spawn_pitch']=-8
    (ROOT/'build_manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':
    catalog()
    if len(sys.argv)>1 and sys.argv[1]=='catalog':
        (ROOT/'tools/catalog.json').write_text(json.dumps(CATALOG,ensure_ascii=False,indent=2),encoding='utf-8');print(len(CATALOG),'groups')
    else:
        terrain()
        for b in CATALOG:place(b)
        trees=landscape();export(trees)
