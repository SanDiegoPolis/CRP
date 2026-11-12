"""Northwestern Polytechnical University, Chang'an. Approx. 1.1 blocks per metre.
Geographic layout adapted from the official 2025 illustrated campus map.
"""
from pathlib import Path
import math,json,random,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
import geometry as g
import nbt
ROOT=Path(__file__).resolve().parent.parent
SHARED=ROOT.parent/'ccucm_minecraft';WORLD=ROOT/'NWPU_Changan_Rebuild_26.2'
W,D,H=1536,2560,128
V=np.zeros((H,D,W),dtype=np.uint8);DEM=np.zeros((D,W),dtype=np.int16)
LANDMARKS=[];CHECKS=[];BUILDINGS=[];R=random.Random(1938)
ROAD_SURFACE=None
g.V=V;g.W=W;g.Z=D;g.H=H
stonewhite=g.block('quartz_bricks',(210,212,207))
beige=g.block('smooth_sandstone',(208,196,162))
silver=g.block('light_gray_concrete',(182,190,192))
bluegray=g.block('gray_stained_glass',(74,112,133))
teal=g.block('warped_planks',(57,114,113))
bronze=g.block('waxed_oxidized_copper',(80,125,107))
roofgreen=g.block('green_terracotta',(108,119,72))
pinkleaf=g.block('cherry_leaves',(217,157,177),persistent='true',distance='1',waterlogged='false')
goldleaf=g.block('azalea_leaves',(130,150,66),persistent='true',distance='1',waterlogged='false')
PAL=g.PAL;COLORS=g.COLORS

def xy(u,v):
    # Official drawing is west-up. Rotate to geographic north (-Z) in Minecraft.
    return round(70+(v-375)*2.6),round(60+(1690-u)*1.7)
SPAWN=xy(1108,920)
def setup(a):g.V=a;g.H,g.Z,g.W=a.shape

def poly(points,mat,y=4):
    x0=max(0,int(min(p[0] for p in points)));x1=min(W,int(max(p[0] for p in points))+1)
    z0=max(0,int(min(p[1] for p in points)));z1=min(D,int(max(p[1] for p in points))+1)
    im=Image.new('L',(x1-x0,z1-z0));ImageDraw.Draw(im).polygon([(x-x0,z-z0) for x,z in points],fill=255)
    mask=np.array(im)>0;V[y,z0:z1,x0:x1][mask]=mat
    return x0,z0,mask
def route(points,width,mat,y=4):
    pts=[xy(*p) for p in points]
    im=Image.new('L',(W,D));dr=ImageDraw.Draw(im);dr.line(pts,fill=255,width=width,joint='curve')
    for x,z in pts:dr.ellipse((x-width/2,z-width/2,x+width/2,z+width/2),fill=255)
    mask=np.array(im)>0;V[y][mask]=mat
    return mask
ROADS=[
 ([(322,414),(1490,414),(1666,886),(740,868),(248,660),(322,414)],14),
 ([(756,418),(758,525),(743,684),(727,836)],13),
 ([(1011,422),(1017,553),(990,641),(1040,710),(1020,856)],12),
 ([(1306,430),(1325,549),(1350,657),(1372,852)],14),
 ([(554,508),(754,518),(1011,519),(1309,518),(1517,510)],12),
 ([(768,709),(940,709),(1050,710),(1146,721),(1351,660),(1585,651)],12),
 ([(778,848),(1031,854),(1335,854),(1637,852)],12),
 ([(1372,616),(1541,616)],10),
 ([(1390,766),(1606,792)],10),
 ([(780,618),(990,618)],9),
 ([(1083,425),(1070,517),(1085,592)],8),
 ([(1226,426),(1253,602)],8),
 ([(570,536),(540,578),(521,667),(602,715),(690,745),(727,836)],9),
]

def terrain():
    global ROAD_SURFACE
    xx=np.arange(W)[None,:];zz=np.arange(D)[:,None]
    # Low campus terraces and a small southern foothill backdrop.
    hm=4+38*np.clip((zz-2410)/170,0,1)*(.25+.75*np.clip((750-xx)/700,0,1))
    border=np.minimum(np.minimum(xx,W-1-xx),np.minimum(zz,D-1-zz))
    DEM[:]=np.rint(hm*np.clip(border/28,0,1)).astype('int16')
    for y in range(int(DEM.max())+1):V[y]=np.where(DEM>y,g.stone,np.where(DEM==y,g.grass,0))
    for pts,width in ROADS:
        route(pts,width+8,g.paving);road=route(pts,width,g.asphalt)
        # A painted dashed centre line, following each measured segment.
        for a,b in zip(pts,pts[1:]):
            ax,az=xy(*a);bx,bz=xy(*b);length=math.dist((ax,az),(bx,bz))
            for t in range(0,int(length),16):
                for dt in range(6):
                    q=min(1,(t+dt)/length);g.put(round(ax+(bx-ax)*q),4,round(az+(bz-az)*q),g.white)
    # Qinling-facing edge and the east approach road.
    route([(1090,889),(1090,940)],20,g.asphalt)
    ROAD_SURFACE=V[4].copy()

def lakes():
    outline=[(645,528),(684,522),(708,529),(730,523),(748,534),(735,560),(713,568),(722,586),(709,615),(687,620),(674,597),(651,585),(631,585),(606,602),(591,629),(571,654),(574,678),(596,688),(648,690),(674,683),(696,697),(682,711),(644,710),(610,720),(578,714),(558,696),(555,667),(539,650),(540,619),(555,598),(588,579),(620,568),(638,551)]
    x,z,mask=poly([xy(*p) for p in outline],g.water,3)
    V[4:7,z:z+mask.shape[0],x:x+mask.shape[1]][:,mask]=0
    # Meandering Qizhen Lake linking the eastern teaching area and library.
    paths=[([(980,635),(1015,653),(1044,672),(1050,699),(1090,707),(1115,702),(1130,674),(1170,653),(1238,663),(1310,650)],35),
           ([(996,619),(1031,614),(1080,618),(1090,629)],30),
           ([(1090,710),(1105,734)],36)]
    for pts,width in paths:
        route(pts,width+7,g.paving)
        mask=route(pts,width,g.water,3);V[4:7][:,mask]=0
    for u,v,r in [(1117,699,35),(650,540,26),(713,554,38),(1008,648,28)]:
        x,z=xy(u,v);g.disk(x,z,r,3,g.water);g.disk(x,z,r,4,0)

def spiral(x,z,base,top):
    g.box(x-2,base+1,z-2,x+12,top+3,z+12,0)
    course=[(i,0) for i in range(10)]+[(10,i) for i in range(10)]+[(10-i,10) for i in range(10)]+[(0,10-i) for i in range(10)]
    for t in range((top-base)*10+1):
        dx,dz=course[t%40];y=base+t//10;g.box(x+dx-1,y,z+dz-1,x+dx+1,y,z+dz+1,g.quartz)
    for y in range(base,top+1,4):g.box(x-4,y,z-2,x-2,y,z+3,g.quartz);g.put(x+5,y+2,z+5,g.sea)

def block_building(x,z,w,d,floors=5,style='white',kind='classroom'):
    wall=stonewhite if style=='white' else g.lightterra if style=='beige' else g.brick
    g.building(x,z,w,d,floors,wall,kind,None,1)
    # Modern vertical piers and contrasting stair towers.
    for xx in (x+2,x+w-5):
        g.box(xx,2,z-1,xx+2,floors*6,z-1,silver)
    for zz in (z+1,z+d-4):g.box(x-1,2,zz,x-1,floors*6,zz+2,silver)
    return 1+floors*6

def regular(w,d,floors=5,style='white',kind='classroom'):
    block_building(5,5,w-10,d-15,floors,style,kind)

def hip_roof(x,z,w,d,y,mat=roofgreen,height=8):
    for k in range(height):
        inset=min(k,min(w,d)//2-1)
        g.box(x+inset,y+k,z+inset,x+w-1-inset,y+k,z+d-1-inset,mat)
    g.outline(x-2,z-2,x+w+1,z+d+1,y,teal,2)

def courtyard(w,d,floors=5,roof=False):
    wing=22
    block_building(5,5,w-10,wing,floors,'white','office')
    block_building(5,d-wing-9,w-10,wing,floors,'white','office')
    block_building(5,30,wing,d-65,floors,'white','office')
    block_building(w-wing-5,30,wing,d-65,floors,'white','office')
    g.ground(28,29,w-29,d-wing-11,g.grass)
    g.box(w//2-4,2,d-wing-11,w//2+4,5,d-8,0)
    g.box(w//2-4,1,d-wing-11,w//2+4,1,d-8,g.quartz)
    if roof:
        for x,z,ww,dd in [(3,3,w-6,26),(3,d-wing-11,w-6,26),(3,27,26,d-54),(w-29,27,26,d-54)]:hip_roof(x,z,ww,dd,2+floors*6)

def qixiang(w,d):
    courtyard(w,d,4,True)
    # Four tall pavilion corners, broad dark roof overhangs and the lower front hall.
    for x,z in [(3,3),(w-36,3),(3,d-42),(w-36,d-42)]:
        block_building(x+3,z+3,29,30,6,'white','office');hip_roof(x,z,36,38,39,height=8)
    g.box(w//2-20,1,d-31,w//2+20,18,d-4,stonewhite)
    g.box(w//2-17,2,d-30,w//2+17,17,d-5,0)
    g.box(w//2-5,2,d-5,w//2+5,9,d,0)
    for x in range(w//2-18,w//2+19,6):g.box(x,3,d-4,x+3,12,d-4,bluegray)
    g.box(w//2-5,2,d-5,w//2+5,8,d,0)
    hip_roof(w//2-23,d-33,47,34,20,height=6)
    g.box(w//2-4,2,d-39,w//2+4,7,d-1,0)
    g.box(w//2-4,1,d-40,w//2+4,1,d-1,g.quartz)

def library(w,d):
    g.ground(0,0,w-1,d-1,g.paving)
    # Qizhen's low rectangular wing shares the lawn with the taller sloping library.
    block_building(3,6,71,39,3,'white','office')
    g.box(7,7,46,70,18,47,bluegray)
    for x in range(8,73,9):g.box(x,1,45,x+1,8,47,g.quartz)
    h,dz,wx=g.V.shape;zz,xx=np.mgrid[0:dz,0:wx]
    cx=141;cz=78;rx=60;rz=61
    footprint=(xx>=82)&(xx<=201)&(zz>=8)&(((zz<=cz)&(zz>=8))|((((xx-cx)/rx)**2+((zz-cz)/rz)**2<=1)&(zz>=cz)))
    eroded=np.array(Image.fromarray((footprint*255).astype('uint8')).filter(ImageFilter.MinFilter(5)))>0
    shell=footprint&(~eroded);top=np.clip(23+(xx-82)*.37,23,69).astype(int)
    for y in range(1,70):
        mask=footprint&(top>=y);g.V[y][mask]=0
        edge=shell&(top>=y);g.V[y][edge]=bluegray
        if y%6==1:g.V[y][mask]=g.quartz
        roof=footprint&(top==y);g.V[y][roof]=g.quartz
        g.V[y][edge&(((xx//2)%8==0)|((zz//2)%8==0))]=g.iron
    # Interior tables, stacks and strip lighting on the seven principal levels.
    for y in range(1,44,6):
        for x in range(93,192,18):
            for z in range(19,101,17):
                if y+5<top[z,x]:
                    g.box(x,y+1,z,x+8,y+3,z+2,g.book);g.box(x,y+1,z+7,x+7,y+1,z+9,g.wood);g.put(x+5,y+4,z+9,g.sea)
    g.box(132,2,134,150,8,144,0);g.box(132,1,126,150,1,149,g.quartz)
    # Side door has a direct route to the broad central stair.
    g.box(81,2,61,86,8,75,0);g.box(77,1,61,92,1,75,g.quartz)
    spiral(136,53,1,43)
    g.box(134,47,51,148,47,65,g.blueglass)
    g.outline(133,50,149,66,47,g.white)
    # Tall vertical spine and rooftop mast at the high end.
    g.box(201,1,77,203,72,79,g.iron);g.box(202,73,78,202,94,78,g.iron)
    g.ground(12,60,67,119,g.grass)
    for k in range(9):g.box(25+k,1+k,80+k,54-k,1+k,107-k,g.blueglass)
    g.textwall('图书馆',159,8,136,g.gold,10)

def arena(w,d):
    # Twin halls, circular upper windows, tilted piers and a broad raised entrance.
    for x,z,ww,dd,high in [(5,14,65,d-32,24),(76,5,w-82,d-12,31)]:
        g.box(x,1,z,x+ww-1,high,z+dd-1,stonewhite)
        g.box(x+2,2,z+2,x+ww-3,high-1,z+dd-3,0)
        g.box(x+3,1,z+3,x+ww-4,1,z+dd-4,g.wood)
        for xx in range(x+8,x+ww-5,13):
            g.box(xx,3,z+dd-1,xx+6,12,z+dd-1,bluegray)
            g.sphere(xx+3,high-6,z+dd-1,3,3,1,bluegray)
        for zz in range(z+7,z+dd-4,11):g.box(x,4,zz,x,high-10,zz+5,bluegray)
        for xx in range(x-3,x+ww+3):
            y=high+2+round(5*math.sin(math.pi*(xx-x+3)/(ww+6)))
            g.box(xx,y,z-3,xx,y+1,z+dd+2,g.white)
        for xx in range(x+3,x+ww,11):g.box(xx,high+4,z+dd,xx,high+12,z+dd,g.iron)
        for xx in range(x+3,x+ww-3,16):
            for y in range(2,high):
                dz=(y-2)//7;g.box(xx,y,z+dd+dz,xx+2,y,z+dd+dz,g.quartz)
    cx=76+(w-82)//2;cz=d//2
    g.outline(cx-18,cz-31,cx+18,cz+31,2,g.white)
    g.box(cx-18,2,cz,cx+18,2,cz,g.white);g.disk(cx,cz,7,2,g.white,6)
    for j in range(7):
        for side in (-1,1):g.box(cx+side*(23+j*2),2+j,cz-35,cx+side*(24+j*2),2+j,cz+35,g.blue)
    for z in (cz-31,cz+31):g.box(cx,2,z,cx,8,z,g.iron);g.box(cx-4,9,z,cx+4,11,z,g.white)
    # Door corridor extends through the seating bowl to the playing floor.
    g.box(cx-5,2,d//2+19,cx+5,9,d-1,0)
    g.box(cx-5,1,d//2+19,cx+5,1,d-1,g.quartz)
    g.box(26,2,d-24,43,7,d,0)
    for x in range(82,w-6,15):g.put(x,27,d//2,g.sea)

def swimming(w,d):
    regular(w,d,2,'white','office')
    g.box(12,2,12,w-13,11,d-22,0)
    g.box(18,0,17,w-19,0,d-27,g.quartz)
    g.box(20,1,19,w-21,1,d-29,g.water)
    for x in range(24,w-22,8):g.box(x,1,20,x,1,d-30,g.blue)
    for x in range(3,w-3):
        y=14+round(7*math.sin(math.pi*(x-3)/(w-6)));g.box(x,y,4,x,y+1,d-8,g.white)

def dining(w,d):
    regular(w,d,3,'beige','office')
    for y in (2,8,14):
        for x in range(14,w-15,14):
            for z in range(16,d-15,12):
                g.box(x,y,z,x+7,y,z+3,g.wood)
                g.box(x,y,z-1,x+7,y,z-1,g.blue);g.box(x,y,z+4,x+7,y,z+4,g.blue)
    g.box(8,4,d-11,w-9,15,d-10,g.blueglass)
    g.box(w//2-4,2,d-13,w//2+4,6,d-7,0)

def teaching(w,d):
    # Four wings enclose a linked teaching courtyard.
    for x,z,ww,dd in [(4,5,w//2-9,32),(w//2+5,5,w//2-9,32),(4,d-47,w//2-9,32),(w//2+5,d-47,w//2-9,32)]:
        block_building(x,z,ww,dd,5,'beige')
    for x in (12,w-22):block_building(x,38,18,d-85,3,'white','office')
    g.box(w//2-8,1,18,w//2+8,19,28,g.blueglass);g.box(w//2-6,2,17,w//2+6,15,29,0)
    g.ground(34,44,w-34,d-52,g.grass)
    g.box(w//2-5,1,40,w//2+5,1,d-1,g.paving)
    for x,z in [(30,37),(w-34,37),(30,d-52),(w-34,d-52)]:
        g.cylinder(x,z,8,1,22,g.blueglass,6);g.disk(x,z,9,23,g.quartz)
    # Clear ground-level passages connect the courtyard and each wing.
    for x in (w//4,3*w//4):g.box(x-3,2,d-49,x+3,5,d-12,0)

def haitian(w,d):
    courtyard(w,d,6)
    for x,z in [(w//2-19,5),(w//2-19,d-43),(5,d//2-18),(w-41,d//2-18)]:
        block_building(x,z,36,36,8,'beige','office')
    g.box(w//2-4,2,d-43,w//2+4,7,d-5,0)

def student_center(w,d):
    courtyard(w,d,3)
    # Terraced lawn and a central outdoor stair.
    g.ground(31,33,w-32,d-40,g.grass)
    for x,z,ww,dd in [(5,5,w-10,22),(5,d-32,w-10,22)]:g.box(x,20,z,x+ww-1,20,z+dd-1,g.grass)
    for j in range(8):g.box(w//2-14,1+j,d-16-j,w//2+14,1+j,d-16-j,g.quartz)
    g.box(w//2-5,2,d-33,w//2+5,9,d-1,0)
    g.box(w//2-5,1,d-34,w//2+5,1,d-1,g.paving)

def plane(cx,cz,length=29,span=22,kind='jet'):
    body=7
    g.sphere(cx,body,cz,2.3,2,length/2,g.iron)
    g.box(cx-1,body+1,cz-length//2+4,cx+1,body+3,cz-3,g.blueglass)
    for dx in range(-span//2,span//2+1):
        z=cz+round(abs(dx)*.55)
        g.box(cx+dx,body,cz-2+round(abs(dx)*.55),cx+dx,body,z+3,g.white)
    for dx in range(-6,7):g.box(cx+dx,body,cz+length//2-7+abs(dx)//2,cx+dx,body,cz+length//2-4+abs(dx)//2,g.white)
    for y in range(1,8):g.box(cx,body+y,cz+length//2-9+y//2,cx,body+y,cz+length//2-3,g.white)
    g.box(cx,2,cz-7,cx,body-2,cz-7,g.dark)
    for dx in (-4,4):g.box(cx+dx,2,cz+5,cx+dx,body-2,cz+5,g.dark)
    if kind=='transport':
        for dx in (-span//3,span//3):g.box(cx+dx,body-3,cz-2,cx+dx+2,body-1,cz+4,g.iron)
    for dx in (-span//3,span//3):g.put(cx+dx,body+1,cz+abs(dx)//2,g.red)

def museum(w,d):
    # Public museum exterior with a central glazed gallery and four low wings.
    for x,z,ww,dd in [(9,8,w//2-17,37),(w//2+8,8,w//2-17,37),(9,60,w//2-17,40),(w//2+8,60,w//2-17,40)]:
        g.box(x,1,z,x+ww-1,18,z+dd-1,stonewhite);g.box(x+2,2,z+2,x+ww-3,17,z+dd-3,0)
        for xx in range(x+2,x+ww-1,4):g.box(xx,2,z-1,xx,18,z-1,g.white)
        g.box(x+4,3,z+dd-1,x+ww-5,13,z+dd-1,bluegray)
        for xx in range(x,x+ww):
            yy=19+round(5*math.sin(math.pi*(xx-x)/ww));g.box(xx,yy,z,xx,yy,z+dd-1,g.white)
    g.box(w//2-7,1,17,w//2+7,17,99,g.blueglass);g.box(w//2-5,2,18,w//2+5,16,101,0)
    g.box(w//2-5,1,95,w//2+5,1,d-1,g.paving)
    for x,z in [(37,126),(83,147),(34,181),(85,196),(w-35,127),(w-81,148),(w-35,182),(w-81,195)]:
        g.ground(x-18,z-21,x+18,z+21,g.grass);plane(x,z,29 if x<w//2 else 34,23 if x<w//2 else 30,'jet' if x<w//2 else 'transport')
    # Static rocket monument and helicopter: display geometry only.
    cx=w//2;cz=d-25
    g.cylinder(cx,cz,3,1,22,g.white)
    for y in range(5):g.disk(cx,cz,max(.2,3-y*.6),23+y,g.white)
    for dx,dz in [(4,0),(-4,0),(0,4),(0,-4)]:g.box(cx+dx,2,cz+dz,cx+dx,8,cz+dz,g.red)

def east_gate(w,d):
    # Six paired-column pylons with the broad, shallow bowls seen at the entrance.
    for x in (14,42,70,w-70,w-42,w-14):
        g.box(x-6,1,8,x+6,3,21,g.quartz)
        for dx,dz in [(-4,-3),(4,-3),(-4,3),(4,3)]:g.cylinder(x+dx,14+dz,2,4,22,g.quartz)
        g.box(x-7,23,7,x+7,26,22,g.quartz)
        for y in range(5):g.disk(x,14,4+y,27+y,beige)
    for x1,x2 in [(14,70),(w-70,w-14)]:g.box(x1,23,11,x2,25,18,g.quartz)
    g.box(1,1,4,8,18,25,g.quartz);g.box(w-9,1,4,w-2,18,25,g.quartz)
    g.box(w//2-38,1,0,w//2+38,9,3,g.quartz)
    g.textwall('西北工业大学',w//2-34,2,4,g.gold,9)
    # Keep two vehicular openings and a central walk through the colonnade.
    g.box(w//2-5,1,0,w//2+5,5,5,0)

def stadium(w,d):
    cx=w//2;cz=d//2
    # Straightaways plus semicircular ends; 400-metre track approximated at 1.1:1.
    long=max(10,w//2-d//2);outer=d//2-5
    zz,xx=np.mgrid[:d,:w];dist=np.sqrt(np.maximum(abs(xx-cx)-long,0)**2+(zz-cz)**2)
    g.V[0,:d,:w][dist<outer]=g.red
    for r in range(outer-1,outer-17,-2):g.V[0,:d,:w][(dist>r-.55)&(dist<r+.55)]=g.white
    g.V[0,:d,:w][dist<outer-18]=g.green
    g.box(cx-53,0,cz-28,cx+53,0,cz+28,g.lime)
    for x in range(cx-50,cx+54,12):g.box(x,0,cz-28,x+5,0,cz+28,g.green)
    g.outline(cx-52,cz-28,cx+52,cz+28,1,g.white);g.box(cx,1,cz-28,cx,1,cz+28,g.white);g.disk(cx,cz,10,1,g.white,9)
    for x in (cx-52,cx+52):
        g.box(x,1,cz-8,x,6,cz-8,g.iron);g.box(x,1,cz+8,x,6,cz+8,g.iron);g.box(x,6,cz-8,x,6,cz+8,g.iron)
    for j in range(8):g.box(20,1+j,d-3-j,w-21,1+j,d-3-j,g.blue if j%3 else g.white)
    g.box(17,14,d-14,w-18,15,d-1,g.white)

def courts(w,d):
    g.ground(0,0,w-1,d-1,g.green)
    for x in range(4,w-29,34):
        for z in range(4,d-45,49):
            g.ground(x,z,x+28,z+43,g.red);g.outline(x+2,z+2,x+26,z+41,1,g.white)
            g.box(x+2,1,z+22,x+26,1,z+22,g.white);g.disk(x+14,z+22,5,1,g.white,4)
            for zz in (z+3,z+40):g.box(x+14,1,zz,x+14,5,zz,g.iron);g.box(x+11,6,zz,x+17,8,zz,g.white)

def place(name,u,v,w,d,fun,targets=None,note='',angle=-90):
    global LAST_PLACEMENT
    cx,cz=xy(u,v);base=4
    temp=np.zeros((H-base,d+8,w+8),dtype=np.uint8)
    saved=g.BE;g.BE={};setup(temp);g.ground(0,0,w-1,d-1,g.paving)
    fun(w,d)
    g.sign(w//2+9,2,d-2,[name,note[:24],'西北工业大学 · 长安','Java 26.2 原版'])
    theta=math.radians(angle);cs,sn=math.cos(theta),math.sin(theta)
    r=math.ceil(math.hypot(w+8,d+8)/2)+3
    x0=max(0,cx-r);x1=min(W,cx+r+1);z0=max(0,cz-r);z1=min(D,cz+r+1)
    zz,xx=np.mgrid[z0:z1,x0:x1];dx=xx-cx;dz=zz-cz
    lx=np.rint(dx*cs+dz*sn+w//2).astype(int);lz=np.rint(-dx*sn+dz*cs+d//2).astype(int)
    valid=(lx>=0)&(lx<temp.shape[2])&(lz>=0)&(lz<temp.shape[1]);lx=np.clip(lx,0,temp.shape[2]-1);lz=np.clip(lz,0,temp.shape[1]-1)
    mask=valid&np.any(temp!=0,axis=0)[lz,lx];high=int(np.max(np.where(temp!=0)[0]))+1
    LAST_PLACEMENT=(x0,z0,x1,z1,mask.copy())
    for y in range(base):V[y,z0:z1,x0:x1][mask]=g.stone
    for y in range(base,H):V[y,z0:z1,x0:x1][mask]=temp[y-base,lz,lx][mask] if y-base<high else 0
    DEM[z0:z1,x0:x1][mask]=base
    localbe=g.BE;g.BE=saved;setup(V)
    for entries in localbe.values():
        for e in entries:
            sx,sz=e['x'][1]-w//2,e['z'][1]-d//2
            x=round(cx+sx*cs-sz*sn);z=round(cz+sx*sn+sz*cs);y=e['y'][1]-64+base
            g.sign(x,y,z,e['front_text'][1]['messages'][1][1],str(round(8+angle/22.5)%16))
    ex=round(cx-(d/2+7)*sn);ez=round(cz+(d/2+7)*cs)
    lm={'name':name,'label':note,'x':cx,'z':cz,'base':base,'width':w,'depth':d,'height':high,'angle':angle,'entrance':[ex,base+65,ez]}
    BUILDINGS.append(lm)
    if targets or not name.startswith(('海天苑公寓','云天苑公寓','星天苑公寓','配套楼')):LANDMARKS.append(lm)
    if targets:
        CHECKS.append({'name':name,'template_shape':list(temp.shape),'width':w,'depth':d,'targets':targets})
        np.save(ROOT/'tools'/('check_'+name.replace(' ','_')+'.npy'),temp)
    print(name,'at',cx,cz,'height',high,flush=True)

def buildings():
    place('图书馆与启真楼',1091,650,210,150,library,[2,8,14,20,26,32,38],'斜坡玻璃立面 / 阅览区')
    place('启翔楼',635,638,144,116,qixiang,[2,8,14,20,26,32],'中式屋顶 / 庭院')
    place('军工素质教育实践中心',463,562,210,248,museum,[2],'博物馆 / 静态航空展品')
    place('航空宇航支撑学科创新中心',568,464,142,118,lambda w,d:courtyard(w,d,6),note='现代院落组团')
    place('海天苑大楼',851,617,192,170,haitian,note='学院楼群 / 设计补全内装')
    place('海天苑餐厅',833,481,78,69,dining,note='餐饮空间')
    place('艺术教育中心',788,479,57,58,lambda w,d:regular(w,d,3),note='艺术教育')
    place('南山苑国际学术交流中心',810,799,141,124,lambda w,d:courtyard(w,d,4,True),note='坡屋顶 / 院落')
    place('翱翔游泳馆',1097,477,85,118,swimming,note='室内泳池')
    place('综合训练馆',1236,446,56,66,lambda w,d:regular(w,d,2),note='体育训练空间')
    place('学生体质监测中心',1096,420,58,31,lambda w,d:regular(w,d,2),note='体育配套')
    place('星天苑田径场',1187,487,197,112,stadium,note='跑道 / 足球场 / 看台')
    place('实验大楼',1045,557,63,65,lambda w,d:regular(w,d,5,'white','lab'),note='教学实验')
    place('教学西楼',1167,577,178,156,teaching,[2,8,14,20,26],'连廊 / 四翼教学楼')
    place('教学东楼',1270,716,175,158,teaching,note='连廊 / 四翼教学楼')
    place('翱翔学生中心',1400,643,137,105,student_center,note='中央庭院 / 屋顶绿化')
    place('数字化大楼',1285,561,82,71,lambda w,d:courtyard(w,d,4),note='校园服务')
    place('云天苑餐厅',1398,718,82,71,dining,[2,8,14],'三层餐厅')
    place('翱翔体育馆',1461,815,187,138,arena,[2],'双馆 / 篮球场 / 看台')
    place('云天苑田径场',1598,832,210,118,stadium,note='跑道 / 足球场 / 看台')
    place('星天苑南餐厅',1346,530,73,69,dining,note='星天苑餐饮')
    place('星天苑北餐厅',1510,526,61,68,dining,note='星天苑餐饮')
    place('大学生双创楼',1497,477,60,58,lambda w,d:regular(w,d,4),note='创新创业空间')
    place('东大门',1108,889,220,42,east_gate,note='入口 / 参观出生区')
    institutes=[
        ('物理科学与技术学院',891,767,52,99),('化学与化工学院',935,756,52,100),
        ('自动化学院',978,763,64,110),('电子信息与微电子学院',1045,784,63,105),
        ('力学与土木建筑学院',1238,777,63,72),('管理学院',1158,768,65,75),
        ('动力与能源学院',1193,823,75,75),('计算机学院',1258,821,75,76),
        ('公共政策与管理学院',1313,824,61,75),('马克思主义学院',1331,780,50,55),
        ('网络空间安全学院',1383,617,112,32),('工程实践训练中心',1360,430,80,43)]
    for name,u,v,w,d in institutes:place(name,u,v,w,d,lambda w,d:regular(w,d,5,'beige','office'),note='学院与教学配套')
    # Student accommodation, with distinct groups following the labelled map.
    idx=0
    for row in range(2):
        for col in range(4):
            idx+=1;u=677+col*24;v=462+row*20
            place(f'海天苑公寓南区{idx}',u,v,31,49,lambda w,d:regular(w,d,6,'beige','dorm'),note='学生宿舍')
    for idx,(u,v) in enumerate([(781,444),(807,440),(833,444),(861,442),(891,449),(902,475)],1):
        place(f'海天苑公寓北区{idx}',u,v,32,61,lambda w,d:regular(w,d,7,'white','dorm'),[2,8,14,20,26,32,38] if idx==1 else None,'学生宿舍 / 示例内装')
    idx=0
    for row in range(2):
        for col in range(6):
            idx+=1;u=1331+col*28+row*20;v=461+row*121
            # First row groups on the map are compact; staggered second row forms the avenue.
            place(f'星天苑公寓{idx:02d}',u,v,34,75,lambda w,d:regular(w,d,6,'white','dorm'),note='学生宿舍')
    idx=0
    for row in range(2):
        for col in range(4):
            idx+=1;u=1436+col*43+row*12;v=708+row*61
            place(f'云天苑公寓{idx:02d}',u,v,42,83,lambda w,d:regular(w,d,6,'white','dorm'),note='学生宿舍')
    place('星天苑篮球场',1272,489,90,96,courts,note='篮球场组团')
    place('海天苑运动场',637,465,56,190,courts,note='室外球场')
    for idx,(u,v,w,d) in enumerate([(356,454,118,78),(422,456,45,91),(493,453,56,154),(359,503,95,37),(895,421,67,32),(1311,437,42,41),(1444,438,42,42)],1):
        place(f'配套楼{idx}',u,v,w,d,lambda w,d:regular(w,d,4,'white','lab'),note='按地图补全外观')

def marker(name,u,v,extra):
    x,z=xy(u,v);LANDMARKS.append({'name':name,'label':extra,'x':x,'z':z,'base':4,'width':40,'depth':40,'height':2,'angle':-90,'entrance':[x,69,z]})

def landscape():
    setup(V)
    # He Zun plaza, warrior sculpture and six industry-themed totem pillars.
    cx,cz=xy(1108,778)
    g.box(cx-61,4,cz-38,cx+88,4,cz+38,g.paving)
    for x in range(cx-57,cx+89,12):g.box(x,4,cz-38,x+1,4,cz+38,g.quartz)
    g.box(cx-49,5,cz-11,cx-32,7,cz+11,g.quartz)
    for y,r in [(8,6),(9,7),(10,7),(11,8),(12,9),(13,10),(14,10),(15,9),(16,8),(17,7),(18,9),(19,11),(20,12)]:g.disk(cx-41,cz,r,y,bronze)
    g.cylinder(cx-41,cz,9,21,23,bronze,7)
    for signz in (cz-9,cz+9):g.box(cx-45,12,signz,cx-37,16,signz,teal)
    # Abstract stone head and two hands, preserving the recognizable low sculpture.
    hx=cx-17;g.sphere(hx,10,cz,8,6,9,g.quartz)
    g.box(hx+6,6,cz-2,hx+10,11,cz+2,g.quartz)
    for dz in (-7,7):g.box(hx+5,11,cz+dz-2,hx+6,12,cz+dz,g.slate)
    for dz in (-26,26):g.sphere(hx+1,8,cz+dz,7,5,4,g.quartz)
    g.box(hx+4,7,cz-36,hx+7,8,cz+36,g.quartz)
    for dz in (-30,-18,-6,6,18,30):
        g.cylinder(cx+57,cz+dz,3,5,19,beige);g.disk(cx+57,cz+dz,4,20,g.quartz)
    for dz in (-24,24):g.box(cx+11,4,cz+dz-7,cx+39,4,cz+dz+7,g.water)
    marker('何尊与勇士广场',1108,778,'何尊 / 勇士组雕 / 六大军工图腾柱')
    g.sign(cx+3,6,cz+35,['何尊—勇士组雕','六大军工图腾柱','东风广场','西北工业大学'])
    # Major shaded pedestrian links and bridges across lake arms.
    walks=[([(1059,711),(1108,739),(1108,879)],9),([(541,521),(576,534),(620,545)],6),
           ([(716,590),(730,636),(724,688),(683,722),(616,725),(571,701)],7),
           ([(655,685),(683,691),(712,704)],5),([(934,636),(977,666),(1005,685),(1048,705)],7),
           ([(1143,668),(1175,680),(1237,666),(1321,666)],7)]
    for pts,width in walks:
        mask=route(pts,width,g.paving,4)
        # Raised boardwalk section with real two-block-clearance approach.
        wet=(V[3]==g.water)&mask;V[4][wet]=g.wood
    for u,v in [(746,699),(1050,704),(1125,706),(581,683)]:
        x,z=xy(u,v);g.box(x-15,4,z-4,x+15,4,z+4,g.wood)
        for xx in range(x-15,x+16,5):g.box(xx,5,z-4,xx,7,z-4,g.fence);g.box(xx,5,z+4,xx,7,z+4,g.fence)
        g.box(x-15,7,z-4,x+15,7,z-4,g.spruce);g.box(x-15,7,z+4,x+15,7,z+4,g.spruce)
    marker('启真湖',1001,653,'沿湖步道 / 小桥')
    marker('启翔湖',692,563,'湖畔园林')
    marker('校友林',671,758,'林荫步道')
    # Reinstate bridges where the water outlines cross the original street network.
    wet=(V[3]==g.water)&np.isin(ROAD_SURFACE,[g.paving,g.asphalt,g.white])
    V[4][wet]=ROAD_SURFACE[wet]
    # Visible south-side mountain scenery, simplified to keep the playable campus level.
    # Plant varied foliage only on open ground, never in buildings, water or roads.
    count=0
    for i in range(16000):
        if count>=3500:break
        x,z=R.randrange(35,W-35),R.randrange(40,D-35);y=int(DEM[z,x])
        if V[y,z,x]!=g.grass or np.any(V[y+1:y+18,z-5:z+6,x-5:x+6]):continue
        if any(abs(x-b['x'])<b['depth']/2+6 and abs(z-b['z'])<b['width']/2+6 for b in BUILDINGS):continue
        h=R.randint(8,14);leaf=R.choice([g.leaves,g.birchleaves,g.pine,pinkleaf,goldleaf])
        g.sphere(x,y+h,z,4,4,4,leaf);g.sphere(x+2,y+h+1,z+1,3,3,3,leaf);g.box(x,y+1,z,x,y+h,z,g.log);count+=1
    for pts,width in ROADS:
        for a,b in zip(pts,pts[1:]):
            ax,az=xy(*a);bx,bz=xy(*b);length=math.dist((ax,az),(bx,bz))
            for t in range(12,int(length)-8,37):
                q=t/length;x=round(ax+(bx-ax)*q+(width/2+4));z=round(az+(bz-az)*q)
                if not(10<x<W-10 and 10<z<D-10) or np.any(V[5:16,z-2:z+3,x-2:x+3]):continue
                g.box(x,5,z,x,12,z,g.iron);g.box(x-2,13,z,x+2,13,z,g.slate);g.put(x-2,12,z,g.sea);g.put(x+2,12,z,g.sea)
    sx,sz=SPAWN
    g.box(sx-4,4,sz-4,sx+4,4,sz+4,g.quartz);g.box(sx-3,5,sz-3,sx+3,9,sz+3,0)
    g.sign(sx-6,6,sz+7,['西北工业大学 · 长安校区','面向西：东大门与图书馆','创造模式 / 双击空格飞行','Minecraft Java 26.2'])
    marker('出生点',1108,920,'东门外 / 创造模式')
    print('Landscape:',count,'trees;',len(BUILDINGS),'building groups;',len(LANDMARKS),'guide landmarks',flush=True)

def export():
    import exporter as e
    for k in ('ROOT','SHARED','WORLD','W','D','H','V','DEM','LANDMARKS','CHECKS','SPAWN','PAL','COLORS','g'):setattr(e,k,globals()[k])
    e.export()
    m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'));m['building_groups']=BUILDINGS
    (ROOT/'build_manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')

def build():
    terrain();lakes();buildings();landscape();export()

if __name__=='__main__':
    mode=sys.argv[1] if len(sys.argv)>1 else 'build'
    if mode=='build':build()
    elif mode=='templates':
        buildings()
        from navigation import navigability
        print(json.dumps(navigability(None,{'palette':PAL,'navigation_checks':CHECKS}),ensure_ascii=False,indent=2),flush=True)
