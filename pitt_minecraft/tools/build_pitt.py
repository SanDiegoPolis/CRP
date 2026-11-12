"""University of Pittsburgh, Oakland. Vanilla Java 26.2, approx 1.1 blocks/metre.
Official campus map supplies street geometry; building photographs supply silhouettes.
"""
from pathlib import Path
import math,json,random,shutil,time,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import geometry as g
import nbt
ROOT=Path(__file__).resolve().parent.parent
SHARED=ROOT.parent/'ccucm_minecraft'
WORLD=ROOT/'Pitt_Oakland_26.2'
W,D,H=1792,1280,208
V=np.zeros((H,D,W),dtype=np.uint8)
DEM=np.zeros((D,W),dtype=np.int16)
LANDMARKS=[];ENTITIES={};CHECKS=[];R=random.Random(1787)
g.V=V;g.W=W;g.Z=D;g.H=H
limestone=g.block('quartz_bricks',(211,207,190))
ivory=g.block('bone_block',(226,222,204),axis='y')
warm=g.block('smooth_sandstone',(213,196,156))
stonebrick=g.block('stone_bricks',(130,133,131))
grayglass=g.block('gray_stained_glass',(78,100,105))
navy=g.block('blue_terracotta',(44,58,100))
redglass=g.block('red_stained_glass',(158,40,52));goldglass=g.block('yellow_stained_glass',(210,168,46))
violet=g.block('purple_stained_glass',(119,77,157));lapis=g.block('lapis_block',(39,68,142))
copper=g.block('waxed_oxidized_copper',(82,139,119))
orangeleaf=g.block('azalea_leaves',(116,143,65),persistent='true',distance='1',waterlogged='false')
COLORS=g.COLORS;PAL=g.PAL

def xy(x,z):return round(x*1.0226-16),round(z*1.0226-64)
def setup(a):g.V=a;g.H,g.Z,g.W=a.shape
def mask_poly(points,pad=0):
    x0=max(0,math.floor(min(x for x,z in points))-pad);x1=min(W,math.ceil(max(x for x,z in points))+pad+1)
    z0=max(0,math.floor(min(z for x,z in points))-pad);z1=min(D,math.ceil(max(z for x,z in points))+pad+1)
    im=Image.new('L',(x1-x0,z1-z0));ImageDraw.Draw(im).polygon([(x-x0,z-z0) for x,z in points],fill=255)
    return x0,z0,np.array(im)>0
def plateau(cx,cz,w,d,height):
    x0=max(0,cx-w//2);x1=min(W,cx+w//2+1);z0=max(0,cz-d//2);z1=min(D,cz+d//2+1)
    for y in range(height+1):V[y,z0:z1,x0:x1]=g.stone if y<height else g.grass
    V[height+1:,z0:z1,x0:x1]=0;DEM[z0:z1,x0:x1]=height
def surface_path(points,width,material):
    im=Image.new('L',(W,D));dr=ImageDraw.Draw(im);dr.line(points,fill=255,width=width,joint='curve')
    mask=np.array(im)>0;zz,xx=np.where(mask);V[DEM[zz,xx],zz,xx]=material

def terrain():
    xx=np.arange(W)[None,:];zz=np.arange(D)[:,None]
    height=4+50*np.clip((1140-xx)/980,0,1)*np.clip((1020-zz)/920,0,1)
    border=np.minimum(np.minimum(xx,W-1-xx),np.minimum(zz,D-1-zz))
    DEM[:]=np.rint(height*np.clip(border/40,0,1)).astype('int16')
    for y in range(int(DEM.max())+1):
        V[y]=np.where(DEM>y,g.stone,np.where(DEM==y,g.grass,0))
    roads=Image.open(ROOT/'research/roads.png')
    # Remove the printed map margin; use just the vector street geometry.
    arr=np.array(roads)>0;arr[:35]=False;arr[-40:]=False;arr[:,:45]=False;arr[:,-50:]=False
    shoulders=np.array(Image.fromarray((arr*255).astype('uint8')).filter(ImageFilter.MaxFilter(9)))>0
    zi,xi=np.where(shoulders);V[DEM[zi,xi],zi,xi]=g.paving
    zi,xi=np.where(arr);V[DEM[zi,xi],zi,xi]=g.asphalt
    np.save(ROOT/'tools/road_mask.npy',arr)
    # A few dash marks follow the major avenue centre lines.
    for points in [[xy(324,1205),xy(688,916),xy(960,715),xy(1217,493),xy(1397,298)],
                   [xy(475,1230),xy(940,837),xy(1262,621),xy(1710,498)]]:
        for a,b in zip(points,points[1:]):
            length=int(math.dist(a,b))
            for t in range(0,length,15):
                x=round(a[0]+(b[0]-a[0])*t/length);z=round(a[1]+(b[1]-a[1])*t/length)
                if 0<x<W and 0<z<D and arr[z,x]:V[DEM[z,x],z,x]=g.yellow

def arch(cx,bottom,z,half,stem,tip,mat,axis='z',depth=1):
    for u in range(-half,half+1):
        top=bottom+stem+round(tip*(max(0,1-abs(u)/(half+.2)))**.65)
        if axis=='z':g.box(cx+u,bottom,z,cx+u,top,z+depth-1,mat)
        else:g.box(z,bottom,cx+u,z+depth-1,top,cx+u,mat)

def buttress(x,z,height,width=2):
    g.box(x,1,z,x+width-1,height,z+width-1,ivory)
    for j in range(4):g.box(x-j%2,height+j,z-j%2,x+width-1+j%2,height+j,z+width-1+j%2,limestone)
    g.box(x,height+4,z,x,height+8,z,ivory)

def gothic_shell(x,z,w,d,bottom,top,windows=True):
    g.box(x,bottom,z,x+w-1,top,z+d-1,limestone)
    g.box(x+2,bottom+1,z+2,x+w-3,top-1,z+d-3,0)
    g.box(x,top,z,x+w-1,top,z+d-1,g.paving)
    if windows:
        for f in range(bottom+2,top-3,4):
            for u in range(x+4,x+w-4,6):
                g.box(u,f,z,u+2,f+2,z,grayglass);g.box(u,f,z+d-1,u+2,f+2,z+d-1,grayglass)
            for u in range(z+4,z+d-4,6):
                g.box(x,f,u,x,f+2,u+2,grayglass);g.box(x+w-1,f,u,x+w-1,f+2,u+2,grayglass)
    for u in range(x+1,x+w,6):
        g.box(u,bottom,z-1,u,top+1,z-1,ivory);g.box(u,bottom,z+d,u,top+1,z+d,ivory)
    for u in range(z+1,z+d,6):
        g.box(x-1,bottom,u,x-1,top+1,u,ivory);g.box(x+w,bottom,u,x+w,top+1,u,ivory)

def spiral_stairs(x,z,base,top):
    # Three-block-wide square spiral, four blocks rise per revolution.
    g.box(x-2,base+1,z-2,x+12,top+3,z+12,0)
    course=[(i,0) for i in range(10)]+[(10,i) for i in range(10)]+[(10-i,10) for i in range(10)]+[(0,10-i) for i in range(10)]
    for t in range((top-base)*10+1):
        dx,dz=course[t%40];y=base+t//10
        g.box(x+dx-1,y,z+dz-1,x+dx+1,y,z+dz+1,g.quartz)
    for y in range(base,top+1,4):
        g.box(x-4,y,z-2,x-2,y,z+3,g.quartz)
        g.box(x+4,y,z+4,x+6,y+3,z+6,limestone)
        g.put(x+5,y+3,z+3,g.sea)

def classic(w,d,floors=6,style='brick',interior='office'):
    wall=g.brick if style=='brick' else limestone if style=='stone' else g.white
    b=3;top=2+floors*5
    g.ground(0,0,w-1,d-1,g.paving)
    g.box(b,1,b,w-b-1,top,d-b-1,wall);g.box(b+1,3,b+1,w-b-2,top-1,d-b-2,0)
    for f in range(floors):
        y=2+5*f;g.box(b,y,b,w-b-1,y,d-b-1,g.wood if f>0 else g.quartz)
        for xx in range(b+3,w-b-3,6):
            g.box(xx,y+1,b,xx+2,y+3,b,grayglass);g.box(xx,y+1,d-b-1,xx+2,y+3,d-b-1,grayglass)
            g.box(xx-1,y+4,d-b,xx+3,y+4,d-b,ivory)
        for zz in range(b+3,d-b-3,6):
            g.box(b,y+1,zz,b,y+3,zz+2,grayglass);g.box(w-b-1,y+1,zz,w-b-1,y+3,zz+2,grayglass)
        if f in [0,floors-1]:g.outline(b-1,b-1,w-b,d-b,y,ivory)
        for xx in range(9,w-11,12):
            for zz in range(10,d-9,13):
                if abs(xx-w/2)<10:continue
                g.box(xx,y+1,zz,xx+5,y+1,zz+2,g.wood)
                if interior=='library':g.box(xx,y+1,zz+5,xx+6,y+3,zz+5,g.book)
                elif interior=='dorm':g.box(xx,y+1,zz+5,xx+2,y+1,zz+8,navy);g.put(xx,y+2,zz+8,g.white)
                g.put(xx+3,y+4,zz+3,g.sea)
    g.box(3,top,3,w-4,top,d-4,g.paving)
    g.outline(2,2,w-3,d-3,top+1,ivory)
    for xx in range(10,w-7,20):g.box(xx,top+1,8,xx+4,top+2,12,g.iron)
    cx=w//2;g.box(cx-3,3,d-5,cx+3,6,d-1,0)
    g.box(cx-6,7,d-4,cx+6,7,d-1,ivory)
    g.box(cx-3,1,d-1,cx+3,1,d-1,g.quartz)
    g.box(cx-3,1,d-3,cx+3,2,d-2,g.quartz)
    spiral_stairs(w//2-5,d//2-5,2,2+(floors-1)*5)

def cathedral(w,d):
    # Cruciform lower mass, stepped shoulders and a flat Gothic crown.
    g.ground(0,0,w-1,d-1,g.paving)
    gothic_shell(8,8,w-16,d-16,1,21,False)
    for x,z,ww,dd,lo,hi in [(15,15,66,66,21,57),(22,22,52,52,57,137),(25,25,46,46,137,154),(28,28,40,40,154,173)]:
        gothic_shell(x,z,ww,dd,lo,hi)
        for xx,zz in [(x-1,z-1),(x+ww-1,z-1),(x-1,z+dd-1),(x+ww-1,z+dd-1)]:
            g.box(xx,lo,zz,xx+1,hi+3,zz+1,ivory)
            g.put(xx,hi+4,zz,ivory)
    # Actual 42-storey rhythm: 4 virtual lower storeys around the tall Commons.
    for level in range(1,42):
        y=1+level*4
        if y<21:continue
        inset=15 if y<57 else 22 if y<137 else 25 if y<154 else 28
        g.box(inset+2,y,inset+2,95-inset-2,y,95-inset-2,g.quartz)
        for xx in range(inset+6,90-inset,14):g.put(xx,y+3,inset+7,g.sea)
    # Deep tall arches on all four elevations and recessed bronze gates.
    for c in (23,47,71):
        for zf in (8,d-9):
            arch(c,3,zf-1,8,8,7,ivory,depth=3);arch(c,3,zf-1,6,8,5,grayglass,depth=3)
        for xf in (8,w-9):
            arch(c,3,xf-1,8,8,7,ivory,'x',3);arch(c,3,xf-1,6,8,5,grayglass,'x',3)
    for c in (8,32,63,85):
        buttress(c,7,22,2);buttress(c,d-9,22,2)
        buttress(7,c,22,2);buttress(w-9,c,22,2)
    for xx,zz in [(28,28),(65,28),(28,65),(65,65)]:
        g.box(xx,172,zz,xx+2,177,zz+2,ivory);g.put(xx+1,180,zz+1,ivory);g.box(xx+1,178,zz+1,xx+1,179,zz+1,ivory)
    # Commons Room, four storeys high, green slate floor and clustered piers.
    g.box(11,2,11,84,19,84,0);g.box(11,1,11,84,1,84,stonebrick)
    for xx in (23,47,71):
        for zz in (23,47,71):
            g.box(xx,2,zz,xx+1,14,zz+1,ivory)
            for dx,dz in [(-1,0),(2,0),(0,-1),(0,2)]:g.box(xx+dx,2,zz+dz,xx+dx,12,zz+dz,limestone)
    # Curved pointed ribs join piers overhead, repeated along each nave.
    for xx in (23,47,71):
        for z0 in (23,47):
            for t in range(25):
                yy=12+round(7*math.sin(math.pi*t/24))
                g.box(xx,yy,z0+t,xx+1,yy+1,z0+t,ivory)
    for zz in (23,47,71):
        for x0 in (23,47):
            for t in range(25):
                yy=12+round(7*math.sin(math.pi*t/24));g.box(x0+t,yy,zz,x0+t,yy+1,zz+1,ivory)
    for xx in (17,32,61,77):
        for zz in (32,60):
            g.box(xx,2,zz,xx+7,2,zz+3,g.spruce)
            for tx in (xx,xx+3,xx+6):g.put(tx,2,zz-1,g.spruce);g.put(tx,2,zz+4,g.spruce)
    for xx,zz in [(35,36),(63,36),(35,65),(63,65)]:
        g.box(xx,13,zz,xx,17,zz,g.bars);g.disk(xx,zz,2,12,g.lamp)
    # Two designed classroom alcoves suggest the Nationality Rooms without claiming exact interiors.
    for x,z in [(12,12),(64,12),(12,67),(65,67)]:
        g.outline(x,z,x+18,z+13,2,g.spruce)
        for zz in range(z+3,z+12,4):
            for xx in range(x+3,x+17,5):g.box(xx,2,zz,xx+2,2,zz+1,g.wood)
    # Entrances on the main axes, broad enough after rotation.
    for zf in (6,85):g.box(42,2,zf,52,9,zf+4,0)
    for xf in (6,85):g.box(xf,2,42,xf+4,9,52,0)
    spiral_stairs(43,37,1,169)
    # Observation landing below the crown.
    g.box(31,169,31,64,169,64,g.quartz)
    spiral_stairs(43,37,1,169)
    g.sign(58,2,91,['Cathedral of Learning','学习大教堂','Commons + 楼梯','约 180 格高'])
    g.sign(34,170,56,['Observation Level','观景层','Oakland Campus','Hail to Pitt'])

def chapel(w,d):
    g.ground(0,0,w-1,d-1,g.paving)
    x0,x1,z0,z1=12,w-13,7,d-9
    gothic_shell(x0,z0,x1-x0+1,z1-z0+1,1,24,False)
    # Nave and transepts, steep slate roof, central spire.
    g.box(5,1,d//2-8,w-6,25,d//2+8,limestone)
    g.box(7,2,d//2-6,w-8,24,d//2+6,0)
    for x in range(x0-2,x1+3):
        yy=25+round(18*(1-abs(x-w/2)/(w/2-10)))
        g.box(x,yy,z0-2,x,yy+1,z1+2,g.slate)
    for zz in range(z0+7,z1,10):
        for xf in (x0,x1):
            arch(zz,5,xf,3,11,7,grayglass,'x')
            for dy in range(3,18):
                mat=[g.blueglass,redglass,goldglass,violet][(dy+zz)%4]
                g.put(xf,5+dy,zz,mat)
        for xf in (x0-3,x1+2):buttress(xf,zz-3,25,2)
    arch(w//2,3,z1,8,12,10,ivory);arch(w//2,3,z1+1,6,12,8,g.blueglass)
    arch(w//2,2,z1+1,3,5,3,0,depth=2)
    # Tall lancet windows at each transept end.
    for xf in (5,w-6):
        arch(d//2,5,xf,6,12,8,grayglass,'x')
        for u in range(-4,5):
            for y in range(7,24):g.put(xf,y,d//2+u,[redglass,goldglass,g.blueglass,violet][(u+y//3)%4])
    # Bell tower, flanking pinnacles and slender pointed spire.
    cx=w//2;cz=d//2
    g.box(cx-7,27,cz-7,cx+7,50,cz+7,limestone)
    for zf in (cz-7,cz+7):arch(cx,36,zf,4,7,4,grayglass)
    for dy in range(29):
        r=max(0,7-dy//4);g.box(cx-r,51+dy,cz-r,cx+r,51+dy,cz+r,g.slate)
    g.put(cx,81,cz,g.iron)
    for xx in (cx-8,cx+7):
        for zz in (cz-8,cz+7):buttress(xx,zz,49)
    g.box(x0+2,1,z0+2,x1-2,1,z1-2,g.wood)
    for zz in range(z0+12,z1-7,4):
        g.box(x0+3,2,zz,cx-3,2,zz,g.spruce);g.box(cx+3,2,zz,x1-3,2,zz,g.spruce)
    for xx in (x0+4,x1-4):
        for zz in range(z0+9,z1-5,13):g.put(xx,20,zz,g.lamp)
    g.box(cx-7,2,z0+4,cx+7,3,z0+7,g.spruce)
    # Cut through both the outer tracery and the original two-block nave wall.
    g.box(cx-3,2,z1-2,cx+3,7,d-1,0)
    g.box(cx-3,1,z1-2,cx+3,1,d-1,g.wood)
    g.sign(cx+6,2,d-4,['Heinz Memorial Chapel','亨氏纪念礼拜堂','彩色玻璃 / 长椅','入口在南端'])

def towers(w,d):
    g.ground(0,0,w-1,d-1,g.paving)
    g.box(5,1,5,w-6,7,d-6,limestone);g.box(7,2,7,w-8,6,d-8,0)
    for cx,cz,r,levels in [(30,30,19,19),(77,35,20,21),(52,79,16,17)]:
        high=8+levels*4
        g.cylinder(cx,cz,r,8,high,ivory,r-2)
        for y in range(8,high+1,4):g.disk(cx,cz,r,y,g.paving)
        for a in np.arange(0,2*math.pi,math.pi/16):
            x=round(cx+r*math.cos(a));z=round(cz+r*math.sin(a))
            for y in range(9,high-2,4):g.box(x,y,z,x,y+2,z,grayglass)
            if round(a*16/math.pi)%2==0:g.box(x,8,z,x,high+2,z,limestone)
        g.cylinder(cx,cz,r+1,high+1,high+2,g.paving);g.cylinder(cx,cz,r*.53,high+3,high+5,ivory)
        spiral_stairs(cx-5,cz-5,8,high-4)
    g.box(w//2-5,2,d-7,w//2+5,5,d-1,0)
    g.sign(w//2+9,2,d-3,['Litchfield Towers','A / B / C','圆形学生宿舍塔','Panther Central'])

def union(w,d):
    classic(w,d,9,'brick')
    # Hotel Schenley proportions, heavy cornices, arched piano nobile.
    for y in (8,33,44,48):g.outline(1,1,w-2,d-2,y,warm,2)
    for xx in range(11,w-10,11):arch(xx,31,d-3,4,5,3,warm);arch(xx,32,d-2,2,4,2,grayglass)
    g.box(8,7,d-1,w-9,7,d+1,g.slate)
    g.textwall('WILLIAM PITT UNION',8,5,d-1,g.gold,5)
    g.sign(w//2+8,2,d-2,['William Pitt Union','学生中心','原 Schenley 酒店','大堂可进入'])

def hillman(w,d):
    classic(w,d,5,'stone','library')
    # Retain the concrete body and add the current northeast glass entry volume.
    for floor in range(3):
        yy=1+floor*8;xa=w-39+floor*2
        g.box(xa,yy,2,w-2,yy+7,34,g.blueglass)
        g.box(xa+1,yy+1,3,w-3,yy+6,33,0)
        g.box(xa,yy,2,w-2,yy,34,g.quartz)
        for xx in range(xa,w-1,6):g.box(xx,yy,2,xx,yy+7,2,g.iron)
        for zz in range(2,35,6):g.box(w-2,yy,zz,w-2,yy+7,zz,g.iron)
    g.box(w-25,2,1,w-14,6,4,0)
    g.textwall('HILLMAN',w-38,23,1,navy,5)
    for xx in range(12,w-42,10):g.box(xx,28,12,xx+7,28,d-12,navy)
    g.sign(w//2+8,2,d-2,['Hillman Library','希尔曼图书馆','阅览空间 / 玻璃入口','外形参考 2025 年改造'])

def arena(w,d):
    cx,cz=w//2,d//2
    g.ground(0,0,w-1,d-1,g.paving)
    for y in range(1,33):g.ellipse(cx,cz,w*.46,d*.43,y,limestone, .94)
    for y in (4,12,20,28):g.ellipse(cx,cz,w*.46,d*.43,y,g.blueglass,.95)
    # Indoor basketball court with a full bowl of blue and gold seats.
    g.ground(cx-21,cz-33,cx+21,cz+33,g.wood)
    g.outline(cx-20,cz-32,cx+20,cz+32,1,g.white);g.box(cx-20,1,cz,cx+20,1,cz,g.white)
    g.disk(cx,cz,8,1,g.white,7)
    for j in range(11):
        xrad=26+j*3;zrad=38+j*2
        g.outline(cx-xrad,cz-zrad,cx+xrad,cz+zrad,3+j,navy if j%3 else g.gold,2)
    for zz in (cz-32,cz+32):
        g.box(cx,1,zz,cx,7,zz,g.iron);g.box(cx-5,8,zz,cx+5,11,zz,g.white)
    # Domed roof and front curtain wall, concrete colonnade.
    for zz in range(d):
        for xx in range(w):
            q=((xx-cx)/(w*.47))**2+((zz-cz)/(d*.44))**2
            if q<=1:
                yy=33+round(11*math.sqrt(1-q))
                g.box(xx,yy-2,zz,xx,yy,zz,g.slate)
    g.box(17,1,d-19,w-18,29,d-13,g.blueglass)
    for xx in range(17,w-15,17):g.box(xx,1,d-23,xx+2,32,d-21,warm)
    g.box(15,30,d-23,w-16,33,d-20,warm)
    g.box(cx-7,2,d-21,cx+7,7,d-10,0)
    g.textwall('PETERSEN',cx-25,25,d-12,g.gold,6)
    g.sign(cx+10,2,d-9,['Petersen Events Center','篮球馆 / Panthers','看台与球场可进入','Oakland Zoo'])

def frick(w,d):
    classic(w,d,2,'stone')
    g.box(20,1,19,w-21,13,d-20,0);g.ground(20,19,w-21,d-20,g.grass)
    for zf in (15,d-16):
        for xx in range(13,w-12,11):g.box(xx,2,zf,xx+1,9,zf,ivory)
    for yy in range(4):g.outline(2+yy,2+yy,w-3-yy,d-3-yy,13+yy,g.orange,3)
    cx=w//2
    g.cylinder(cx,d//2,10,12,21,warm,8)
    for y in range(6):g.disk(cx,d//2,11-y,22+y,g.orange)
    g.box(cx-3,2,d-4,cx+3,6,d-1,0)
    g.sign(cx+7,2,d-2,['Frick Fine Arts','弗里克艺术楼','中庭 / 回廊','Schenley Fountain'])

def memorial(w,d,caption='SOLDIERS SAILORS'):
    classic(w,d,3,'stone')
    for xx in range(13,w-12,11):g.box(xx,1,d-1,xx+2,20,d+1,ivory)
    g.box(10,21,d-1,w-11,23,d+2,limestone)
    for y in range(10):g.box(10+y*3,24+y,d-2,w-11-y*3,24+y,d+2,limestone)
    g.box(w//2-5,3,d-5,w//2+5,9,d-1,0)
    g.textwall(caption,10,17,d+3,g.gold,5)

def foster(w,d):
    g.ground(0,0,w-1,d-1,g.paving)
    gothic_shell(5,5,w-10,d-10,1,19,False)
    for xx in range(12,w-9,10):arch(xx,4,d-6,3,7,5,grayglass)
    for xx in range(3,w-2):
        y=20+round(10*(1-abs(xx-w/2)/(w/2)))
        g.box(xx,y,3,xx,y+1,d-4,g.slate)
    g.box(w//2-3,2,d-7,w//2+3,7,d-1,0)
    for z in range(12,d-10,4):g.box(10,2,z,w-11,2,z,g.spruce)

# Main footprints, positioned from the official map; rotation follows local streets.
SPECS=[
 ('Cathedral of Learning',1280,536,96,96,-40,cathedral,'学习大教堂'),
 ('Heinz Memorial Chapel',1395,418,54,88,40,chapel,'亨氏纪念礼拜堂'),
 ('William Pitt Union',1127,621,86,65,-40,union,'学生中心'),
 ('Litchfield Towers',980,712,111,112,-40,towers,'三座圆形宿舍塔'),
 ('Hillman Library',1192,720,101,87,-16,hillman,'希尔曼图书馆'),
 ('Petersen Events Center',477,553,159,140,-40,arena,'篮球馆'),
 ('Frick Fine Arts',1466,823,86,71,30,frick,'艺术楼'),
 ('Soldiers & Sailors',991,444,107,81,-40,memorial,'周边地标 · 纪念馆'),
 ('Alumni Hall',1230,377,85,55,-40,lambda w,d:classic(w,d,5,'stone'),'校友楼'),
 ('Wesley W. Posvar Hall',1208,832,128,89,-16,lambda w,d:classic(w,d,5,'stone'),'波斯瓦尔楼'),
 ('Stephen Foster Memorial',1307,584,58,47,-15,foster,'纪念剧院 · 示意内装'),
 ('Benedum Hall',791,581,111,60,-40,lambda w,d:classic(w,d,14,'stone'),'工程楼'),
 ('Chevron Science Center',887,335,92,52,-40,lambda w,d:classic(w,d,15,'stone'),'化学科学中心'),
 ('Sutherland Hall',445,311,109,48,20,lambda w,d:classic(w,d,8,'brick','dorm'),'上校区宿舍'),
 ('Panther Hall',510,386,124,37,0,lambda w,d:classic(w,d,8,'brick','dorm'),'黑豹宿舍'),
 ('Irvis Hall',626,435,123,42,-10,lambda w,d:classic(w,d,6,'brick','dorm'),'学生宿舍'),
 ('Salk Hall',409,673,99,76,-40,lambda w,d:classic(w,d,12,'stone'),'萨尔克楼'),
 ('Scaife Hall',549,667,118,64,-40,lambda w,d:classic(w,d,10,'stone'),'医学院'),
 ('Biomedical Science Towers',479,770,106,65,37,lambda w,d:classic(w,d,15,'modern'),'生物医学楼群'),
 ('Biomedical Science Tower 3',649,885,100,65,37,lambda w,d:classic(w,d,12,'modern'),'生物医学三号塔'),
 ('Sennott Square',998,840,93,60,-40,lambda w,d:classic(w,d,7,'brick'),'教学与科研楼'),
 ('Barco Law Building',1054,784,62,48,-40,lambda w,d:classic(w,d,6,'stone'),'法学院'),
 ('Mervis Hall',1252,914,88,40,-10,lambda w,d:classic(w,d,4,'brick'),'商学院'),
 ('Bellefield Hall',1486,409,71,49,0,lambda w,d:classic(w,d,4,'brick'),'贝尔菲尔德楼'),
 ('Carnegie Museum & Library',1558,650,208,135,-16,lambda w,d:classic(w,d,4,'stone'),'周边地标 · 卡内基博物馆'),
 ('Mellon Institute',1477,326,108,93,-10,lambda w,d:memorial(w,d,'MELLON INSTITUTE'),'周边地标 · 梅隆研究所'),
]

def place(spec):
    name,mx,mz,w,d,angle,fun,note=spec;cx,cz=xy(mx,mz)
    base=int(DEM[cz,cx]);temp=np.zeros((H-base,d+8,w+8),dtype=np.uint8)
    savedbe=g.BE;g.BE={};g.LANDMARKS=[];setup(temp)
    fun(w,d)
    if fun not in (cathedral,chapel,towers,union,hillman,arena,frick):g.sign(w//2+7,3,d-1,[name[:24],note,'University of Pittsburgh','Oakland Campus'])
    nonzero=np.any(temp!=0,axis=0);maxy=int(np.max(np.where(temp!=0)[0]))+1
    theta=math.radians(angle);cs,sn=math.cos(theta),math.sin(theta)
    radius=math.ceil(math.hypot(w+8,d+8)/2)+2
    x0=max(0,cx-radius);x1=min(W,cx+radius+1);z0=max(0,cz-radius);z1=min(D,cz+radius+1)
    zz,xx=np.mgrid[z0:z1,x0:x1];dx=xx-cx;dz=zz-cz
    lx=np.rint(dx*cs+dz*sn+w/2).astype(int);lz=np.rint(-dx*sn+dz*cs+d/2).astype(int)
    valid=(lx>=0)&(lz>=0)&(lx<temp.shape[2])&(lz<temp.shape[1]);lx=np.clip(lx,0,temp.shape[2]-1);lz=np.clip(lz,0,temp.shape[1]-1)
    mask=valid&nonzero[lz,lx]
    localbe=g.BE;g.BE=savedbe;setup(V)
    for y in range(base):V[y,z0:z1,x0:x1][mask]=g.stone
    for y in range(base,H):V[y,z0:z1,x0:x1][mask]=temp[y-base,lz,lx][mask] if y-base<maxy else 0
    DEM[z0:z1,x0:x1][mask]=base
    for entries in localbe.values():
        for e in entries:
            sx,sz=e['x'][1]-w/2,e['z'][1]-d/2
            x=round(cx+sx*cs-sz*sn);z=round(cz+sx*sn+sz*cs);y=e['y'][1]-64+base
            g.sign(x,y,z,[s for s in e['front_text'][1]['messages'][1][1]],str(round(8+angle/22.5)%16))
    # Front arrival point on the surrounding paving; automatically found later if obstructed.
    ex=round(cx-(d/2+7)*sn);ez=round(cz+(d/2+7)*cs)
    LANDMARKS.append({'name':name,'label':note,'x':cx,'z':cz,'base':base,'width':w,'depth':d,'height':maxy,'angle':angle,'entrance':[ex,base+65,ez]})
    if fun in (cathedral,chapel,hillman,arena,union):
        CHECKS.append({'name':name,'template_shape':list(temp.shape),'targets':([2,22,82,166,170] if fun==cathedral else [2] if fun in (chapel,arena) else [3,8,13,18,23] if fun==hillman else [3,8,13,18,23,28,33,38,43]),'width':w,'depth':d})
        np.save(ROOT/'tools'/('check_'+name.replace(' ','_')+'.npy'),temp)
    print(name,base,maxy,flush=True)

def context_buildings():
    shapes=json.loads((ROOT/'research/building_footprints.json').read_text())
    count=0
    for sh in shapes:
        cx,cz=sh['center']
        # Reserve real named buildings for their detailed individual models.
        if any(math.dist((cx,cz),xy(sp[1],sp[2]))<math.hypot(sp[3],sp[4])*.56+12 for sp in SPECS):continue
        if cx<65 or cx>1720 or cz<55 or cz>1180:continue
        if cx<450 and cz>1010:continue
        # The map's perspective Cathedral drawing includes shadows that resemble buildings.
        px=[p[0] for p in sh['points']];pz=[p[1] for p in sh['points']]
        if max(px)>1160 and min(px)<1460 and max(pz)>270 and min(pz)<576:continue
        x,z,mask=mask_poly(sh['points']);hh,ww=mask.shape
        if hh<6 or ww<6:continue
        base=int(np.median(DEM[z:z+hh,x:x+ww][mask]));height=R.choice([15,20,25,30]) if sh['university'] else R.choice([12,16,20,24])
        eroded=np.array(Image.fromarray((mask*255).astype('uint8')).filter(ImageFilter.MinFilter(5)))>0
        wall=mask&(~eroded)
        mat=R.choice([g.brick,g.terra,limestone,g.lightterra])
        for y in range(base+1):V[y,z:z+hh,x:x+ww][mask]=g.stone if y<base else g.paving
        for dy in range(1,height+1):
            a=V[base+dy,z:z+hh,x:x+ww];a[mask]=0
            a[wall]=mat
            if dy%5==0 or dy==1:a[mask]=g.paving
            elif dy%5 in (2,3):
                iz,ix=np.indices(mask.shape);win=wall&(((ix+iz)//3)%2==0);a[win]=grayglass
        V[base+height,z:z+hh,x:x+ww][mask]=g.paving
        DEM[z:z+hh,x:x+ww][mask]=base;count+=1
    print('Context building outlines:',count,flush=True)

def greens():
    # Schenley Plaza is a lawn, although shown as a gray shape on the map.
    poly=[xy(x,z) for x,z in [(1269,648),(1372,626),(1391,714),(1302,760)]]
    x,z,mask=mask_poly(poly);h,w=mask.shape
    for y in range(5):V[y,z:z+h,x:x+w][mask]=g.grass if y==4 else g.stone
    V[5:,z:z+h,x:x+w][:,mask]=0;DEM[z:z+h,x:x+w][mask]=4
    for a,b in zip(poly,poly[1:]+poly[:1]):surface_path([a,b],7,g.paving)
    c=xy(1336,696)
    surface_path([poly[0],poly[2]],5,g.paving);surface_path([poly[1],poly[3]],5,g.paving)
    g.disk(*c,10,4,g.quartz)
    LANDMARKS.append({'name':'Schenley Plaza','label':'申利广场 · 出生区','x':c[0],'z':c[1],'base':4,'width':100,'depth':95,'height':1,'angle':0,'entrance':[c[0],69,c[1]]})
    # Garden and fountain before Frick Fine Arts.
    fx,fz=xy(1392,778);base=int(DEM[fz,fx])
    for y in range(base+1):g.disk(fx,fz,21,y,g.stone)
    g.disk(fx,fz,21,base,g.paving);g.disk(fx,fz,16,base+1,g.quartz)
    g.disk(fx,fz,14,base+1,g.water);g.cylinder(fx,fz,3,base+2,base+7,ivory)
    g.disk(fx,fz,7,base+8,g.quartz);g.disk(fx,fz,6,base+9,g.water)
    g.box(fx-1,base+10,fz-1,fx+1,base+15,fz+1,copper)
    # Cathedral lawn paths, kept clear of both Gothic buildings.
    for pts in [[(1219,493),(1243,538),(1258,611)],[(1260,613),(1336,557),(1450,545)],[(1226,488),(1316,429),(1354,380)],[(1334,556),(1390,483),(1400,430)]]:
        surface_path([xy(x,z) for x,z in pts],6,g.paving)
    # Schenley carousel, a small recognizable plaza feature.
    cx,cz=xy(1361,733);base=4
    g.cylinder(cx,cz,8,base,base+2,g.wood)
    for a in np.arange(0,2*math.pi,math.pi/4):
        x=round(cx+6*math.cos(a));z=round(cz+6*math.sin(a));g.box(x,base+2,z,x,base+7,z,g.gold)
    for y in range(5):g.disk(cx,cz,11-y,base+8+y,g.red if y%2 else ivory)
    g.put(cx,base+14,cz,g.gold)
    g.sign(c[0]+7,6,c[1]+9,['University of Pittsburgh','匹兹堡大学 · 奥克兰','北侧：学习大教堂','创造模式 / 26.2'])
    # Pitt pennants and lamps along main streets.
    road=np.load(ROOT/'tools/road_mask.npy');near=np.array(Image.fromarray((road*255).astype('uint8')).filter(ImageFilter.MaxFilter(25)))>0
    for z in range(80,D-80,29):
        for x in range(80,W-80,29):
            y=int(DEM[z,x])
            if near[z,x] and V[y,z,x] in (g.paving,g.grass) and not np.any(V[y+1:y+13,z-2:z+3,x-2:x+3]):
                g.box(x,y+1,z,x,y+8,z,g.slate);g.put(x,y+9,z,g.lamp)
                if (x+z)%3==0:
                    g.box(x+1,y+4,z,x+3,y+7,z,navy);g.put(x+2,y+6,z,g.gold)
    trees=0
    for i in range(5000):
        x,z=R.randrange(60,W-60),R.randrange(60,D-60);y=int(DEM[z,x])
        park=x>1420 and z>850
        lawn=1180<x<1470 and 260<z<550
        if not (near[z,x] or park or lawn or R.random()<.22):continue
        if V[y,z,x]!=g.grass or np.any(V[y+1:y+17,z-5:z+6,x-5:x+6]):continue
        height=R.randrange(8,14);leaf=R.choice([g.leaves,g.birchleaves,g.pine,orangeleaf])
        g.sphere(x,y+height,z,4,4,4,leaf);g.sphere(x+2,y+height+1,z,3,3,3,leaf)
        g.box(x,y+1,z,x,y+height,z,g.log);trees+=1
    # White bus shelters on Fifth / Forbes and locally parked cars.
    for mx,mz in [(1128,529),(1192,591),(1285,621),(973,747),(838,751)]:
        x,z=xy(mx,mz);y=int(DEM[z,x])
        if np.any(V[y+1:y+6,z-3:z+4,x-6:x+7]):continue
        g.box(x-5,y+1,z,x+5,y+4,z,g.clearglass);g.box(x-6,y+5,z-3,x+6,y+5,z+1,g.quartz)
    print('Landscape trees:',trees,flush=True)

def pack_values(arr,bits):
    a=np.asarray(arr,dtype=np.uint64).ravel();per=64//bits
    b=np.zeros(math.ceil(len(a)/per)*per,dtype=np.uint64);b[:len(a)]=a
    return np.bitwise_or.reduce(b.reshape(-1,per)<<(np.arange(per,dtype=np.uint64)*bits),axis=1).tolist()
def pnbt(p):
    d={'Name':nbt.T(p['Name'])}
    if p.get('Properties'):d['Properties']=nbt.C({k:nbt.T(v) for k,v in p['Properties'].items()})
    return d
def section(sy,arr):
    uniq,inv=np.unique(arr,return_inverse=True);bs={'palette':nbt.LS(10,[pnbt(PAL[int(i)]) for i in uniq])}
    if len(uniq)>1:bs['data']=nbt.LA(pack_values(inv,max(4,(len(uniq)-1).bit_length())))
    return {'Y':nbt.B(sy),'block_states':nbt.C(bs),'biomes':nbt.C({'palette':nbt.LS(8,['minecraft:plains'])})}

def export():
    print('Exporting 26.2 Anvil world...',flush=True)
    assert len(PAL)<256
    registry=json.loads((SHARED/'tools/generated/reports/blocks.json').read_text())
    for p in PAL:
        assert p['Name'] in registry,p
        for k,v in p.get('Properties',{}).items():assert v in registry[p['Name']]['properties'][k],p
    template=SHARED/'validation/template';WORLD.mkdir(exist_ok=True)
    shutil.copytree(template/'data',WORLD/'data',dirs_exist_ok=True)
    level=nbt.load(template/'level.dat');d=level['Data'][1]
    d['LevelName']=nbt.T('匹兹堡大学｜Oakland 1.1:1');d['GameType']=nbt.I(1);d['allowCommands']=nbt.B(1)
    sx,sz=xy(1336,696);sy=int(DEM[sz,sx])+65
    d['spawn']=nbt.C({'pos':nbt.IA([sx,sy,sz]),'yaw':nbt.F(150),'pitch':nbt.F(-12),'dimension':nbt.T('minecraft:overworld')})
    d['LastPlayed']=nbt.L(int(time.time()*1000));nbt.save(WORLD/'level.dat',level)
    rules=nbt.load(WORLD/'data/minecraft/game_rules.dat');r=rules['data'][1]
    for k in ['advance_time','advance_weather','spawn_mobs','spawn_monsters','spawn_patrols','spawn_phantoms','spawn_wandering_traders','mob_griefing','raids','pvp']:r['minecraft:'+k]=nbt.B(0)
    r['minecraft:random_tick_speed']=nbt.I(0);r['minecraft:respawn_radius']=nbt.I(0);r['minecraft:fire_spread_radius_around_player']=nbt.I(0)
    nbt.save(WORLD/'data/minecraft/game_rules.dat',rules)
    fixed=[]
    for syc in range(-4,4):
        a=np.full((16,16,16),g.stone,dtype=np.uint8)
        if syc==-4:a[0]=g.bedrock
        if syc==3:a[12:]=g.dirt
        fixed.append(section(syc,a))
    upperair=[section(s,np.zeros((16,16,16),dtype=np.uint8)) for s in range(4+H//16,20)]
    total=0
    # Serialize one region at a time to keep peak memory bounded.
    for rz in range(math.ceil(D/512)):
        for rx in range(math.ceil(W/512)):
            chunks={}
            for cz in range(rz*32,min((rz+1)*32,D//16)):
                for cx in range(rx*32,min((rx+1)*32,W//16)):
                    a=V[:,cz*16:cz*16+16,cx*16:cx*16+16]
                    hm=129+(H-1-np.argmax((a!=0)[::-1],axis=0));height=nbt.LA(pack_values(hm,9))
                    sections=fixed+[section(4+s,a[s*16:(s+1)*16]) for s in range(H//16)]+upperair
                    bes=[e for e in g.BE.get((cx,cz),[]) if PAL[int(V[e['y'][1]-64,e['z'][1],e['x'][1]])]['Name'].endswith('_sign')]
                    c={'DataVersion':nbt.I(4903),'xPos':nbt.I(cx),'zPos':nbt.I(cz),'yPos':nbt.I(-4),'Status':nbt.T('minecraft:full'),'LastUpdate':nbt.L(0),'InhabitedTime':nbt.L(0),'isLightOn':nbt.B(0),
                       'sections':nbt.LS(10,sections),'Heightmaps':nbt.C({k:height for k in ['WORLD_SURFACE','OCEAN_FLOOR','MOTION_BLOCKING','MOTION_BLOCKING_NO_LEAVES']}),
                       'block_entities':nbt.LS(10,bes),'block_ticks':nbt.LS(10,[]),'fluid_ticks':nbt.LS(10,[]),'PostProcessing':nbt.LS(9,[(2,[]) for _ in range(24)]),
                       'structures':nbt.C({'starts':nbt.C({}),'References':nbt.C({})})}
                    chunks[cx%32+32*(cz%32)]=c;total+=1
            nbt.write_region(WORLD/f'dimensions/minecraft/overworld/region/r.{rx}.{rz}.mca',chunks)
            print('Region',rx,rz,'chunks',total,flush=True)
    np.save(ROOT/'tools/voxels.npy',V);np.save(ROOT/'tools/terrain.npy',DEM)
    manifest={'title':'匹兹堡大学 · 奥克兰主校区','version':'26.2','data_version':4903,'scale':'约 1.1 方块 / 米，局部体量适配','dimensions':[W,H,D],'spawn':[sx,sy,sz],'chunks':total,
              'palette':PAL,'colors':COLORS,'landmarks':LANDMARKS,'navigation_checks':CHECKS,'above_terrain_blocks':int(sum(np.count_nonzero(V[y][DEM<y]) for y in range(1,H)))}
    (ROOT/'build_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Export complete:',total,'chunks',flush=True)

def build():
    terrain();context_buildings()
    for spec in SPECS:place(spec)
    greens();export()

if __name__=='__main__':
    mode=sys.argv[1] if len(sys.argv)>1 else 'build'
    if mode=='build':build()
    elif mode=='preview':
        import render;render.main()
    elif mode=='validate':
        import validate;validate.main()
    elif mode=='package':
        import deliver;deliver.main()
