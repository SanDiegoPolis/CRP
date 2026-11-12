from crp_runtime import java_executable, font_path
"""CCUCM Jingyue campus, all vanilla blocks. Approx. 1.25 blocks / metre.
Layout derived from the 2022 campus guide, facades from referenced photographs.
Unknown interiors are designed for Minecraft exploration, not surveyed plans.
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math, random, json, shutil, time
import nbt

ROOT=Path(__file__).resolve().parent.parent
WORLD=ROOT/'Pitt_Oakland_26.2'
W,Z,H=1,1,1
V=np.zeros((H,Z,W),dtype=np.uint8) # local y=0 is Minecraft y=64
PAL=[]; IDS={}; COLORS=[]; BE={}; LANDMARKS=[]
R=random.Random(1958)

def block(name,color,**props):
    key=name+str(sorted(props.items()))
    if key not in IDS:
        IDS[key]=len(PAL);PAL.append({'Name':'minecraft:'+name,**({'Properties':{k:str(v) for k,v in props.items()}} if props else {})});COLORS.append(color)
    return IDS[key]
air=block('air',(0,0,0)); grass=block('grass_block',(103,147,74),snowy='false')
stone=block('stone',(119,121,122)); dirt=block('dirt',(129,95,66)); bedrock=block('bedrock',(69,69,69))
quartz=block('smooth_quartz',(231,228,219)); white=block('white_concrete',(212,214,213))
brick=block('bricks',(162,94,80)); terra=block('terracotta',(158,108,81))
lightterra=block('white_terracotta',(202,173,163)); granite=block('polished_granite',(151,107,93))
slate=block('polished_deepslate',(65,66,71)); asphalt=block('gray_concrete',(69,72,78))
paving=block('smooth_stone',(160,161,160)); tile=block('polished_andesite',(135,138,138))
dark=block('black_concrete',(35,37,40)); glass=block('cyan_stained_glass',(70,131,140))
clearglass=block('glass',(168,201,205)); blueglass=block('light_blue_stained_glass',(92,158,190))
water=block('water',(61,128,179),level=0); wood=block('oak_planks',(167,130,76))
spruce=block('spruce_planks',(111,82,48)); log=block('oak_log',(113,89,54),axis='y')
leaves=block('oak_leaves',(62,115,49),persistent='true',distance=1,waterlogged='false')
birchleaves=block('birch_leaves',(93,138,66),persistent='true',distance=1,waterlogged='false')
pine=block('spruce_leaves',(45,91,59),persistent='true',distance=1,waterlogged='false')
birchlog=block('birch_log',(213,209,181),axis='y'); pineLog=block('spruce_log',(92,71,45),axis='y')
red=block('red_concrete',(167,54,51)); yellow=block('yellow_concrete',(227,175,40)); gold=block('gold_block',(238,200,63))
green=block('green_concrete',(75,107,50)); lime=block('lime_concrete',(119,161,47)); blue=block('blue_concrete',(63,83,154))
orange=block('orange_terracotta',(158,80,45)); sea=block('sea_lantern',(174,211,197)); lamp=block('glowstone',(199,164,93))
iron=block('iron_block',(209,211,210)); bars=block('iron_bars',(149,155,157),north='true',south='true',east='true',west='true',waterlogged='false')
fence=block('oak_fence',(137,108,63),north='true',south='true',east='true',west='true',waterlogged='false')
book=block('bookshelf',(147,116,68)); chest=block('barrel',(128,98,57),facing='up',open='false')
flower1=block('poppy',(203,62,52)); flower2=block('dandelion',(241,206,54)); flower3=block('azure_bluet',(230,230,219))
shortgrass=block('short_grass',(87,131,60)); farmland=block('farmland',(110,75,44),moisture=7)
wheat=block('wheat',(192,178,68),age=7); carrots=block('carrots',(88,143,54),age=7)
beets=block('beetroots',(116,136,58),age=3); fern=block('fern',(74,123,57))

def box(x1,y1,z1,x2,y2,z2,b):
    x1,x2=sorted((int(x1),int(x2)));y1,y2=sorted((int(y1),int(y2)));z1,z2=sorted((int(z1),int(z2)))
    V[max(0,y1):min(H,y2+1),max(0,z1):min(Z,z2+1),max(0,x1):min(W,x2+1)]=b
def put(x,y,z,b):
    if 0<=x<W and 0<=z<Z and 0<=y<H: V[y,z,x]=b
def ground(x1,z1,x2,z2,b=paving): box(x1,0,z1,x2,0,z2,b)
def disk(x,z,r,y,b,inner=0):
    a,bx=max(0,int(x-r)),min(W,int(x+r+1));c,d=max(0,int(z-r)),min(Z,int(z+r+1))
    zz,xx=np.ogrid[c:d,a:bx]; mask=(xx-x)**2+(zz-z)**2<=r*r
    if inner:mask&=(xx-x)**2+(zz-z)**2>=inner*inner
    V[y,c:d,a:bx][mask]=b
def ellipse(x,z,rx,rz,y,b,inner=0):
    x1,x2=max(0,int(x-rx)),min(W,int(x+rx+1));z1,z2=max(0,int(z-rz)),min(Z,int(z+rz+1))
    zz,xx=np.ogrid[z1:z2,x1:x2]; f=((xx-x)/rx)**2+((zz-z)/rz)**2
    mask=f<=1
    if inner:mask&=f>=inner*inner
    V[y,z1:z2,x1:x2][mask]=b
def path(points,width,b=paving,y=0):
    for (x1,z1),(x2,z2) in zip(points,points[1:]):
        length=max(abs(x2-x1),abs(z2-z1),1)
        for j in range(length+1): disk(round(x1+(x2-x1)*j/length),round(z1+(z2-z1)*j/length),width/2,y,b)
def outline(x1,z1,x2,z2,y,b,thick=1):
    box(x1,y,z1,x2,y,z1+thick-1,b);box(x1,y,z2-thick+1,x2,y,z2,b)
    box(x1,y,z1,x1+thick-1,y,z2,b);box(x2-thick+1,y,z1,x2,y,z2,b)
def sphere(x,y,z,rx,ry,rz,b,hollow=False):
    x1,x2=max(0,int(x-rx)),min(W,int(x+rx+1));z1,z2=max(0,int(z-rz)),min(Z,int(z+rz+1));y1,y2=max(0,int(y-ry)),min(H,int(y+ry+1))
    yy,zz,xx=np.ogrid[y1:y2,z1:z2,x1:x2];s=((xx-x)/rx)**2+((yy-y)/ry)**2+((zz-z)/rz)**2
    mask=s<=1
    if hollow: mask&=s>=.80
    V[y1:y2,z1:z2,x1:x2][mask]=b
def cylinder(x,z,r,y1,y2,b,inner=0):
    for y in range(y1,y2+1):disk(x,z,r,y,b,inner)

def textwall(text,x,y,z,b=gold,size=10):
    font=ImageFont.truetype(font_path(),size)
    im=Image.new('L',(len(text)*(size+1)+4,size+4));dr=ImageDraw.Draw(im);dr.text((0,-1),text,font=font,fill=255,spacing=1)
    arr=np.asarray(im)>110
    for j,i in zip(*np.where(arr)):put(x+int(i),y+im.height-1-int(j),z,b)
def sign(x,y,z,lines,rot='8'):
    b=block('oak_sign',(155,125,78),rotation=rot,waterlogged='false');put(x,y,z,b)
    message=[nbt.T(s) for s in []]
    BE[(x//16,z//16)]=BE.get((x//16,z//16),[])+[{
        'id':nbt.T('minecraft:sign'),'x':nbt.I(x),'y':nbt.I(y+64),'z':nbt.I(z),
        'is_waxed':nbt.B(1),'front_text':nbt.C({'messages':nbt.LS(8,(lines+['']*4)[:4]),'color':nbt.T('black'),'has_glowing_text':nbt.B(0)}),
        'back_text':nbt.C({'messages':nbt.LS(8,['']*4),'color':nbt.T('black'),'has_glowing_text':nbt.B(0)})}]
def landmark(name,x,z,width,depth,kind,extra=''):
    LANDMARKS.append(dict(name=name,x=x,z=z,width=width,depth=depth,kind=kind,note=extra))
def tree(x,z,h=9,kind=0):
    if x<8 or z<8 or x>=W-8 or z>=Z-8:return
    if V[0,z,x]!=grass or np.any(V[1:5,z-3:z+4,x-3:x+4]!=air):return
    trunk,leaf=(log,leaves) if kind==0 else (birchlog,birchleaves) if kind==1 else (pineLog,pine)
    if kind==2:
        for dy in range(4,h+4):disk(x,z,max(1,(h+4-dy)//2),dy,leaf)
    else:
        sphere(x,h,z,4+(h>10),4,4,leaf)
        sphere(x+2,h+1,z-1,3,3,3,leaf)
    box(x,1,z,x,h,z,trunk)
def light(x,z):
    if V[1,z,x]!=air:return
    box(x,1,z,x,6,z,iron);box(x-2,7,z,x+2,7,z,slate)
    put(x-2,6,z,sea);put(x+2,6,z,sea)
def bench(x,z):
    box(x,1,z,x+4,1,z,slate);box(x,2,z,x+4,2,z,spruce);box(x,3,z+1,x+4,3,z+1,spruce)
def flowerbed(x1,z1,x2,z2):
    outline(x1,z1,x2,z2,1,quartz)
    for z in range(z1+1,z2,2):
        for x in range(x1+1,x2,2):
            if V[0,z,x] in [grass,dirt]:put(x,1,z,R.choice([flower1,flower2,flower3]))

def stairs_south(x,z,width,height):
    for j in range(height):box(x,1,z-j,x+width-1,height-j,z-j,quartz)
    # step treads rise towards north
    for j in range(height):box(x,1,z+height-1-j,x+width-1,j+1,z+height-1-j,quartz)
def stair_stack(sx,cz,base,floors):
    # Open stairwell and one-block-thick flights leave clearance beneath each flight.
    box(sx,base+1,cz-1,sx+8,base+floors*6-1,cz+1,air)
    for f in range(floors-1):
        y=base+f*6
        for s in range(6):box(sx+s,y+s+1,cz-1,sx+s,y+s+1,cz+1,quartz)
        box(sx+6,y+6,cz-1,sx+8,y+6,cz+1,quartz)
def building(x,z,w,d,floors=5,wall=brick,kind='classroom',name=None,podium=1):
    top=podium+floors*6
    ground(x-4,z-4,x+w+3,z+d+6,paving)
    box(x,1,z,x+w-1,top,z+d-1,wall)
    box(x+1,podium+1,z+1,x+w-2,top-1,z+d-2,air)
    # limestone ground storey and horizontal bands
    for f in range(floors+1):
        y=podium+f*6
        box(x,y,z,x+w-1,y,z+d-1,quartz if f in (0,floors) else lightterra)
        if f==floors:continue
        for xx in range(x+4,x+w-4,7):
            box(xx,y+2,z,xx+3,y+4,z,glass);box(xx,y+2,z+d-1,xx+3,y+4,z+d-1,glass)
            box(xx-1,y+1,z+d,xx+4,y+1,z+d,quartz)
        for zz in range(z+4,z+d-4,7):
            box(x,y+2,zz,x,y+4,zz+3,glass);box(x+w-1,y+2,zz,x+w-1,y+4,zz+3,glass)
        # longitudinal corridor, partitioned rooms on either side
        cz=z+d//2
        for xx in range(x+3,x+w-8,14):
            for side in (0,1):
                za,zb=(z+2,cz-3) if side==0 else (cz+3,z+d-3)
                if zb-za<5:continue
                box(xx,y+1,za,xx,y+5,zb,lightterra)
                box(xx,y+1,cz-3 if side==0 else cz+3,xx+13,y+5,cz-3 if side==0 else cz+3,white)
                box(xx+5,y+1,cz-3 if side==0 else cz+3,xx+7,y+3,cz-3 if side==0 else cz+3,air)
                if kind=='dorm':
                    for bx in (xx+2,xx+9):
                        box(bx,y+1,za+1,bx+2,y+1,za+4,spruce);box(bx,y+2,za+1,bx+2,y+2,za+3,blue)
                        box(bx,y+2,za+4,bx+2,y+2,za+4,white)
                        box(bx,y+4,za+1,bx+2,y+4,za+3,spruce);box(bx,y+5,za+1,bx+2,y+5,za+3,red)
                elif kind in ['classroom','lab']:
                    board_z=za if side==0 else zb
                    box(xx+2,y+2,board_z,xx+10,y+4,board_z,green)
                    for tz in range(za+4,zb-1,4):
                        for tx in range(xx+3,xx+12,4):
                            put(tx,y+1,tz,fence);put(tx,y+2,tz,wood if kind=='classroom' else quartz)
                            put(tx,y+1,tz+1,spruce)
                elif kind=='office':
                    box(xx+2,y+1,za+1,xx+9,y+1,za+2,wood);box(xx+2,y+2,za+1,xx+9,y+2,za+2,spruce)
                    box(xx+10,y+1,zb-1,xx+11,y+4,zb,book)
        for xx in range(x+7,x+w-4,14):put(xx,y+5,cz,sea)
        # full-height stairs at the west and east ends; floor holes preserve headroom
        for sx in [x+2,x+w-11]:
            box(sx,y+6,cz-2,sx+8,y+6,cz+2,air)
            for s in range(6):
                box(sx+s,y+1,cz-1,sx+s,y+s+1,cz+1,quartz)
                box(sx+s,y+s+2,cz-1,sx+s,min(top-1,y+s+4),cz+1,air)
            if f<floors-1:box(sx+6,y+6,cz-1,sx+8,y+6,cz+1,quartz)
    # roof cap and parapet
    box(x,top,z,x+w-1,top,z+d-1,paving)
    outline(x-1,z-1,x+w,z+d,top+1,quartz)
    for xx in range(x+10,x+w-5,27):box(xx,top+1,z+6,xx+4,top+2,z+9,iron)
    for sx in [x+2,x+w-11]:stair_stack(sx,z+d//2,podium,floors)
    # distinctive glazing and entrance through the south facade
    cx=x+w//2
    box(cx-6,podium+1,z+d-1,cx+6,top-3,z+d-1,glass)
    box(cx-3,podium+1,z+d-2,cx+3,podium+4,z+d,air)
    box(cx-9,podium+5,z+d,cx+9,podium+5,z+d+4,quartz)
    box(cx-3,0,z+d,cx+3,podium,z+d+1,quartz)
    if name:
        sign(cx+8,2,z+d+5,[name,'可进入参观','楼梯在走廊两端','CCUCM · 净月校区'])
        landmark(name,x,z,w,d,kind)
    return top

