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
WORLD=ROOT/'CCUCM_Jingyue_26.2'
W,Z,H=1152,896,96
V=np.zeros((H,Z,W),dtype=np.uint16) # local y=0 is Minecraft y=64
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

def roadx(z,x1=68,x2=1100,width=12):
    ground(x1,z-width//2-4,x2,z+width//2+4,paving);ground(x1,z-width//2,x2,z+width//2,asphalt)
    for x in range(x1+5,x2,13):ground(x,z,x+5,z,white)
def roadz(x,z1=151,z2=806,width=12):
    ground(x-width//2-4,z1,x+width//2+4,z2,paving);ground(x-width//2,z1,x+width//2,z2,asphalt)
    for z in range(z1+5,z2,13):ground(x,z,x,z+5,white)

def terrain():
    V[0,:,:]=grass
    # river strip: gently sinuous banks, with a broad northwest pool
    for x in range(W):
        mid=110+int(8*math.sin(x/90)+5*math.sin(x/39))
        radius=17+(18 if x<180 else 0)
        box(x,0,mid-radius-3,x,0,mid+radius+3,paving)
        box(x,0,mid-radius,x,0,mid+radius,water)
    ellipse(91,101,70,40,0,water)
    # footpaths beside the north stream
    path([(30,157),(180,147),(300,151),(470,145),(630,152),(845,149),(1120,151)],6,tile)
    # road network and southern street
    roadx(810,30,1120,16);roadx(852,0,1151,24)
    for x in (70,523,875):roadz(x)
    for z in (158,350,483,573):roadx(z)
    roadx(716,85,864,9)
    # Main processional axis
    ground(337,578,401,809,paving)
    ground(348,655,390,744,grass)
    ground(354,662,384,739,grass)
    outline(347,654,391,745,1,quartz)
    path([(370,810),(370,573)],7,quartz)
    for z in range(825,843,4):ground(345,z,395,z+1,white)
    for x in (70,523,875):
        for z in (350,483,573,810):
            for j in range(-5,7,3):ground(x-7,z+j,x+7,z+j+1,white)
    # perimeter, left open at gates
    for x in range(45,1111):
        if not(319<=x<=420 or 857<=x<=892):
            box(x,1,827,x,2,827,granite);put(x,3,827,bars)
    for z in range(166,828):
        for x in (44,1110):
            box(x,1,z,x,2,z,granite);put(x,3,z,bars)
    for x in range(44,1111,15):
        box(x,1,827,x+1,4,827,quartz)

def library():
    x,z,w,d=565,185,249,123
    top=building(x,z,w,d,5,terra,'library',None,podium=5)
    # open reading floors, central atrium and continuous glass curtain front
    for f in range(5):
        yy=5+6*f
        box(x+2,yy+1,z+2,x+w-3,yy+5,z+d-3,air)
        for xx in range(x+14,x+w-13,15):
            for zz in range(z+12,z+d-32,17):
                if 657<xx<721:continue
                box(xx,yy+1,zz,xx+7,yy+3,zz+1,book)
                box(xx,yy+1,zz+5,xx+7,yy+1,zz+8,wood)
                put(xx+3,yy+5,zz+4,sea)
        # west/east broad walkable staircase
        for sx in (x+4,x+w-15):
            box(sx,yy+6,z+d-27,sx+8,yy+6,z+d-22,air)
            for s in range(6):
                box(sx+s,yy+1,z+d-26,sx+s,yy+s+1,z+d-23,quartz)
                box(sx+s,yy+s+2,z+d-26,sx+s,min(top-1,yy+s+4),z+d-23,air)
            if f<4:box(sx+6,yy+6,z+d-26,sx+8,yy+6,z+d-23,quartz)
    box(659,6,z+d-2,720,top-1,z+d-1,glass)
    for xx in range(660,722,6):box(xx,6,z+d,xx,top,z+d,iron)
    for yy in range(5,top,6):box(657,yy,z+d,722,yy,z+d,iron)
    box(680,6,z+d-3,696,11,z+d+1,air)
    for sx in (x+4,x+w-15):stair_stack(sx,z+d-25,5,5)
    box(x,top,z,x+w-1,top,z+d-1,paving)
    # oversized pale frame and rhythmic pillars, as visible in the photograph
    front=z+d+16
    for xx in range(x-2,x+w+1,25):box(xx,5,front,xx+3,top+7,front+3,quartz)
    box(x-2,top+5,front,x+w+2,top+8,front+3,quartz)
    box(x-2,top+5,z-3,x+1,top+8,front+3,quartz)
    box(x+w-1,top+5,z-3,x+w+2,top+8,front+3,quartz)
    for xx in range(x+5,x+w,13):box(xx,top+6,z-3,xx+1,top+6,front+3,quartz)
    box(x-5,4,z+d,x+w+4,4,front+4,paving)
    for s in range(5):box(636,0,front+4+s,742,4-s,front+4+s,quartz)
    textwall('四象城',665,top-3,front+4,gold,9)
    sign(753,2,340,['四象城 · 图书馆','高柱廊 / 阅读大厅','书架与阅览桌可达','位置依据校园导览图'])
    landmark('四象城 · 图书馆',x,z,w,d,'library','柱廊、玻璃幕墙、五层阅览区')
    # theatre block at rear, with curved stepped roof
    for dz in range(38):
        yy=16+round(6*math.sin(math.pi*dz/37))
        box(628,1,165+dz,747,yy,165+dz,lightterra)
        box(629,2,166+dz,746,yy-1,166+dz,air)
        box(626,yy,165+dz,749,yy,165+dz,slate)

def academics():
    # Zhizhi: long brick front, three projecting wings and glazed entrance
    for xx in (231,337,444):building(xx,492,34,28,4,lightterra,'classroom')
    t=building(226,518,254,39,4,lightterra,'classroom','致知楼 · 第一教学楼')
    for xx in (229,465):box(xx,1,554,xx+6,t+3,560,lightterra)
    for xx in range(232,477,15):box(xx,1,560,xx+1,8,563,quartz)
    box(227,8,561,479,9,564,quartz)
    box(343,4,556,366,t+1,557,glass);box(349,2,555,359,5,560,air)
    box(338,t+3,544,371,t+3,562,iron)
    # Xingzhi: classroom wings, white gridded accents and vertical green glass
    building(591,497,40,32,5,terra,'classroom')
    building(774,497,40,32,5,terra,'classroom')
    t=building(579,522,237,35,5,terra,'classroom','行知楼 · 第二教学楼')
    for xx in (593,678,782):
        box(xx,2,557,xx+13,t-1,558,glass)
        box(xx,t-12,557,xx+13,t-6,558,quartz)
        for dx in (2,6,10):
            for dy in (0,3):box(xx+dx,t-11+dy,559,xx+dx+1,t-10+dy,559,glass)
    # Mingde administrative L shape, cylindrical glass roof tower
    t=building(122,749,184,30,4,brick,'office','明德楼 · 行政办公')
    building(122,705,30,45,4,brick,'office')
    cylinder(284,752,15,1,t+8,glass,13)
    for yy in (1,7,13,19,25,t+9):disk(284,752,16,yy,quartz)
    for xx,zz in [(284+int(14*math.cos(a)),752+int(14*math.sin(a))) for a in np.arange(0,6.28,.52)]:box(xx,2,zz,xx,t+11,zz,iron)
    cylinder(284,752,19,t+12,t+13,slate,16)
    # Zhongjing and Shizhen labs near the south edge
    building(508,734,135,45,5,brick,'lab','仲景楼 · 临床实验')
    building(508,699,29,36,5,brick,'lab')
    building(689,742,145,37,5,brick,'lab','时珍楼 · 药学实验')
    building(806,707,28,35,5,brick,'lab')
    # west museum: stepped volumes and rounded corners with green ribbon windows
    t=building(105,621,83,59,3,terra,'museum','启德馆 · 中医药博物馆')
    for cx in (111,182):
        cylinder(cx,667,12,1,t+2,terra)
        for yy in (5,11,17):cylinder(cx,667,12,yy,yy+2,glass,11)
        cylinder(cx,667,13,t+2,t+3,quartz)
    box(130,2,679,165,t-2,680,glass);box(141,2,678,151,5,681,air)
    for xx in (123,165):box(xx,1,657,xx+4,t+7,661,quartz)
    # museum exhibit cabinets, herb samples, reconstructed medicinal cabinets
    for xx in range(116,180,12):
        box(xx,2,632,xx+6,4,634,wood);box(xx,5,632,xx+6,6,634,clearglass)
        put(xx+3,5,633,flower2)
    for xx in range(116,181,4):box(xx,2,625,xx+2,7,626,chest)
    # Rixin and Gewu: white horizontal courses, a domed corner rotunda
    building(908,613,67,101,5,brick,'lab','日新楼')
    building(991,636,92,143,5,terra,'lab','格物楼 · 创新实践中心')
    building(909,748,83,31,5,terra,'lab')
    cx,cz=1007,760
    cylinder(cx,cz,17,1,39,quartz,15)
    for yy in (4,10,16,22,28,34):cylinder(cx,cz,17,yy,yy+3,blueglass,16)
    for a in np.arange(0,2*math.pi,math.pi/4):
        xx=round(cx+17*math.cos(a));zz=round(cz+17*math.sin(a));box(xx,1,zz,xx+1,40,zz+1,quartz)
    disk(cx,cz,19,40,quartz)
    for dy in range(18):disk(cx,cz,max(1,math.sqrt(max(0,18**2-dy**2))),41+dy,white, max(0,math.sqrt(max(0,18**2-dy**2))-1.6))
    box(cx-4,2,cz+14,cx+4,5,cz+19,air)
    # small west support halls, unobtrusive approximations
    building(105,369,58,61,3,lightterra,'office','校园服务楼')
    building(116,460,47,73,4,terra,'lab','教学附楼')

def residence():
    for name,z in [('半夏居',187),('茯苓居',233),('人参居',279)]:
        building(260,z,220,26,6,lightterra,'dorm','新公寓 · '+name)
    building(232,328,248,22,3,white,'office','杏林创客空间')
    for x,name in [(232,'白术居'),(401,'陈皮居')]:
        building(x,378,31,87,6,lightterra,'dorm',name)
        building(x,378,79,26,6,lightterra,'dorm')
        building(x,439,79,26,6,lightterra,'dorm')
    # eastern residence court
    for xx in (658,790):building(xx,377,27,86,6,lightterra,'dorm')
    building(658,377,158,25,6,lightterra,'dorm','六君子居 · 学生公寓')
    building(658,440,158,23,6,lightterra,'dorm')
    # cut through the south wing for walkable courtyard gate
    box(727,2,438,742,6,465,air)
    ground(715,403,757,439,paving);flowerbed(721,412,752,431)
    # canteen with white grid facade and dining floors
    t=building(568,383,68,77,3,quartz,'canteen','杏林餐厅')
    for f in range(3):
        yy=1+6*f
        box(570,yy+1,385,633,yy+5,457,air)
        for zz in range(391,451,9):
            for xx in range(575,625,10):
                box(xx,yy+2,zz,xx+4,yy+2,zz+2,wood)
                box(xx,yy+1,zz-1,xx+4,yy+1,zz-1,spruce);box(xx,yy+1,zz+3,xx+4,yy+1,zz+3,spruce)
        box(572,yy+1,386,629,yy+2,388,quartz)
        for xx in range(576,629,10):put(xx,yy+3,387,chest)
        # accessible staircase at east side
        box(627,yy+6,426,633,yy+6,434,air)
        for s in range(6):box(629,yy+1,427+s,632,yy+s+1,427+s,quartz)
        if f<2:box(629,yy+6,433,632,yy+6,434,quartz)
    textwall('杏林餐厅',579,12,461,slate,8)
    for yy in (1,7,13):box(627,yy,426,633,yy,435,quartz)
    box(568,19,383,635,19,459,paving)
    box(629,2,427,632,18,434,air)
    for f in range(2):
        yy=1+f*6
        for s in range(6):box(629,yy+s+1,427+s,632,yy+s+1,427+s,quartz)
        box(629,yy+6,433,632,yy+6,434,quartz)

def taiji(cx,cz,r):
    disk(cx,cz,r+8,0,paving);disk(cx,cz,r+3,0,quartz);disk(cx,cz,r,0,white)
    for z in range(cz-r,cz+r+1):
        for x in range(cx-r,cx+r+1):
            if (x-cx)**2+(z-cz)**2>r*r:continue
            blackside=x<cx
            if (x-cx)**2+(z-(cz-r/2))**2<(r/2)**2:blackside=False
            if (x-cx)**2+(z-(cz+r/2))**2<(r/2)**2:blackside=True
            put(x,0,z,dark if blackside else white)
    disk(cx,cz-r/2,r/8,0,dark);disk(cx,cz+r/2,r/8,0,white)
    # eight trigrams as paving, two are continuous and six broken
    for k in range(8):
        a=k*math.pi/4
        for row in range(3):
            radius=r+7+row*3
            for s in range(-8,9):
                if not(k&(1<<row)) and abs(s)<2:continue
                xx=round(cx+math.cos(a)*radius-math.sin(a)*s);zz=round(cz+math.sin(a)*radius+math.cos(a)*s)
                put(xx,0,zz,dark)

def sports():
    # Xingde gym opens west towards the Taiji plaza
    x,z,w,d=737,604,86,76
    box(x,1,z,x+w-1,24,z+d-1,lightterra);box(x+1,2,z+1,x+w-2,23,z+d-2,air)
    ground(x-8,z-8,x+w+7,z+d+7,paving);ground(x+2,z+2,x+w-3,z+d-3,wood)
    for xx in range(x+7,x+w-2,10):
        box(xx,8,z,xx+5,17,z,glass);box(xx,8,z+d-1,xx+5,17,z+d-1,glass)
    # arched roof, three blocks thick, concrete ribs
    for xx in range(x-5,x+w+5):
        rel=(xx-(x+w/2))/(w/2+5);yy=24+round(8*max(0,1-rel*rel))
        box(xx,yy,z-4,xx,yy+1,z+d+3,slate)
        for zz in (z-3,z+12,z+28,z+44,z+60,z+d+2):box(xx,yy+2,zz,xx,yy+2,zz,white)
    for zz in range(z+8,z+d-5,15):box(x,5,zz,x,21,zz+6,glass)
    box(x,3,z+27,x,15,z+48,glass);box(x-1,2,z+33,x+1,7,z+42,air)
    box(x-6,9,z+26,x-1,9,z+49,quartz)
    for s in range(4):box(x-5+s,0,z+25,x-5+s,s,z+50,quartz)
    # indoor court
    outline(x+12,z+12,x+w-13,z+d-13,1,white)
    box(x+w//2,1,z+12,x+w//2,1,z+d-13,white)
    disk(x+w//2,z+d//2,10,1,white,9)
    for xx in (x+11,x+w-12):
        box(xx,2,z+d//2,xx,7,z+d//2,iron);box(xx,7,z+d//2-4,xx,11,z+d//2+4,white)
    for xx in range(x+10,x+w-9,15):put(xx,22,z+d//2,sea)
    ground(580,588,728,701,paving);taiji(651,645,31)
    sign(723,2,688,['行德馆 · 体育馆','西侧主入口','八卦广场','可进入室内球场'])
    landmark('行德馆 · 八卦广场',x,z,w,d,'gym')
    # 400m class stadium track with straight sides and semicircular ends
    cx,cz=1031,462;r=47;straight=51
    def capsule(rad,material):
        ground(cx-rad,cz-straight,cx+rad,cz+straight,material)
        disk(cx,cz-straight,rad,0,material);disk(cx,cz+straight,rad,0,material)
    capsule(r+4,paving);capsule(r,red)
    for rr in range(r,r-12,-2):
        # all lanes run around the whole capsule
        for zp in (cz-straight,cz+straight):
            for zz in range(zp-rr,zp+rr+1):
                if zp==cz-straight and zz>zp:continue
                if zp==cz+straight and zz<zp:continue
                dx=round(math.sqrt(max(0,rr*rr-(zz-zp)**2)))
                put(cx-dx,0,zz,white);put(cx+dx,0,zz,white)
        ground(cx-rr,cz-straight,cx-rr,cz+straight,white);ground(cx+rr,cz-straight,cx+rr,cz+straight,white)
    capsule(r-13,green)
    for zz in range(cz-64,cz+65,12):ground(cx-29,zz,cx+29,zz+5,lime)
    outline(cx-31,cz-65,cx+31,cz+65,0,white)
    ground(cx-31,cz,cx+31,cz,white);disk(cx,cz,12,0,white,11)
    for zz in (cz-65,cz+65):
        dz=1 if zz<cz else -1
        outline(cx-18,min(zz,zz+dz*20),cx+18,max(zz,zz+dz*20),0,white)
        box(cx-7,1,zz,cx-7,5,zz,white);box(cx+7,1,zz,cx+7,5,zz,white);box(cx-7,6,zz,cx+7,6,zz,white)
        box(cx-7,1,zz-dz*3,cx+7,5,zz-dz*3,bars)
    # east bleachers and curved canopy
    for s in range(8):
        box(1084+s*2,1,398,1085+s*2,s+1,526,paving)
        box(1084+s*2,s+2,398,1085+s*2,s+2,526,blue if s%2 else white)
    for zz in range(398,530,20):box(1101,1,zz,1102,19,zz,iron)
    box(1081,20,393,1104,21,533,quartz)
    for zz in (380,546):
        for xx in (978,1090):
            box(xx,1,zz,xx,21,zz,iron);box(xx-3,22,zz,xx+3,23,zz,sea)
    sign(1005,2,578,['体育场','红色环形跑道','足球场 / 看台','约 1.25 方块 / 米'])
    landmark('体育场 · 环形跑道',980,364,122,214,'stadium')
    # basketball and volleyball courts on the west side of the stadium
    for z0 in (371,423):
        ground(907,z0,960,z0+43,red);ground(913,z0+5,954,z0+38,blue)
        outline(913,z0+5,954,z0+38,0,white);ground(933,z0+5,933,z0+38,white)
        disk(933,z0+21,6,0,white,5)
        for xx in (914,953):
            box(xx,1,z0+21,xx,6,z0+21,iron);box(xx,7,z0+17,xx,10,z0+25,white)
            put(xx+1 if xx==914 else xx-1,7,z0+21,red)
    for z0 in (492,535):
        ground(907,z0,960,z0+34,orange);outline(912,z0+5,955,z0+29,0,white)
        ground(933,z0+5,933,z0+29,white)
        box(933,1,z0+3,933,5,z0+3,iron);box(933,1,z0+31,933,5,z0+31,iron)
        box(933,4,z0+4,933,5,z0+30,bars)

def gardens():
    # Seven Stars herb garden, winding path and specimen plots
    ground(902,176,1092,327,grass)
    outline(902,176,1092,327,1,leaves,2)
    path([(908,309),(937,300),(940,253),(983,234),(1017,204),(1078,187)],5,paving)
    path([(913,188),(940,214),(970,269),(1015,290),(1083,312)],5,paving)
    stars=[(919,207),(943,229),(966,236),(988,253),(1016,268),(1042,280),(1069,301)]
    for j,(cx,cz) in enumerate(stars):
        disk(cx,cz,12,0,quartz);disk(cx,cz,10,0,grass);disk(cx,cz,3,0,gold)
        for angle in np.arange(0,6.28,1.05):
            xx=round(cx+7*math.cos(angle));zz=round(cz+7*math.sin(angle));put(xx,1,zz,flower2)
    names=['人参','黄芪','薄荷','桔梗','白术','茯苓','甘草','当归','金银花','柴胡','黄芩','半夏']
    idx=0
    for zz in (185,265,301):
        for xx in (919,960,1001,1042):
            if any(abs(xx-cx)<16 and abs(zz-cz)<15 for cx,cz in stars):continue
            ground(xx,zz,xx+24,zz+12,farmland)
            for x in range(xx+1,xx+24,2):
                for z in range(zz+1,zz+12,2):put(x,1,z,R.choice([wheat,carrots,beets]))
            ground(xx+12,zz,xx+12,zz+12,water)
            sign(xx+3,2,zz+14,[names[idx%len(names)],'药用植物展示区','原版作物示意','非植物学模型']);idx+=1
    sign(1040,2,325,['七星百草园','药用植物 / 曲径','七星景观','可沿步道游览'])
    landmark('七星百草园',902,176,190,151,'garden')
    # Nine-grid fountain before Zhizhi
    ground(331,597,407,648,paving)
    ellipse(369,622,35,22,0,quartz);ellipse(369,622,31,19,0,water)
    for xx in (350,368,386):
        for zz in (609,622,635):
            put(xx,0,zz,sea);box(xx,1,zz,xx,2 if xx!=368 else 4,zz,water)
    sign(411,2,626,['九宫喷泉','致知楼前广场','启古纳今','厚德精术'])
    landmark('九宫喷泉',333,597,76,51,'fountain')
    # gate name wall beside the entrance, not an invented arch
    ground(229,794,333,817,paving)
    box(237,1,799,328,2,803,quartz);box(240,3,799,327,13,802,granite)
    textwall('长春中医药大学',244,2,803,gold,10)
    flowerbed(238,805,331,810)
    # retractable gates leave a broad pedestrian entrance
    box(320,1,813,339,3,813,bars);box(401,1,813,420,3,813,bars)
    building(418,788,20,18,1,lightterra,'office','南门门卫室')
    for x in (349,369,389):
        box(x,1,783,x,21,783,iron);box(x+1,17,783,x+8,21,783,red)
    sign(400,2,792,['长春中医药大学','净月校区 · 南门','向北：致知楼 / 图书馆','向东：八卦广场 / 体育场'])
    sign(403,2,797,['参观提示','创造模式 · 双击空格飞行','原版 Java 26.2','祝你漫游愉快'])
    landmark('南门 · 校名石',237,791,204,29,'gate')
    # motto stone, sculptural rough granite
    sphere(371,4,684,13,4,4,granite)
    textwall('启古纳今',354,2,689,gold,8)
    sign(389,2,692,['校训','启古纳今','厚德精术','CCUCM'])
    # Fuxi footbridge crosses Qinglong river to the northern training zone
    for z in range(72,159):
        y=2+round(3*math.sin(math.pi*(z-72)/87))
        box(516,y,z,531,y,z,quartz)
        for x in (516,531):put(x,y+1,z,bars)
    for step in range(3):ground(516,159+step,531,159+step,paving)
    box(518,1,158,529,2,160,quartz)
    sign(538,2,146,['伏羲桥','青龙河','北侧：三才轩','校园北部景观'])
    # north buildings are represented in compact form
    building(106,25,256,29,2,white,'classroom','三才轩')
    building(813,27,102,39,2,terra,'office','杏林苑')
    # five-sided pavilion to the northwest, Wuxing palace
    cx,cz=128,245
    for y in range(1,15):
        for dz in range(-25,26):
            for dx in range(-29,30):
                a=math.atan2(dz,dx);r=25*math.cos(math.pi/5)/math.cos((a+math.pi/5)%(2*math.pi/5)-math.pi/5)
                dist=math.hypot(dx,dz)
                if dist<r and (dist>r-2 or y in (1,14)):put(cx+dx,y,cz+dz,quartz if y in (1,14) else terra)
    for y in range(15,24):disk(cx,cz,28-(y-15)*2,y,slate, max(0,26-(y-15)*2))
    box(cx-3,2,cz+17,cx+3,6,cz+28,air)
    sign(cx+17,2,cz+30,['五行宫','形制为示意重建','参照导览图位置','北部景观区'])
    landmark('五行宫',99,220,58,55,'pavilion','外形为示意')
    # quadrant gardens, paths and street furniture
    for x1,z1,x2,z2 in [(216,692,317,720),(428,607,493,681),(573,689,621,709),(693,691,816,711),(101,552,171,591),(281,586,321,684),(417,741,481,778)]:
        outline(x1,z1,x2,z2,0,paving,3)
        path([(x1,(z1+z2)//2),(x2,(z1+z2)//2)],4,paving)
        path([((x1+x2)//2,z1),((x1+x2)//2,z2)],4,paving)
        flowerbed(x1+7,z1+7,x1+19,z1+19)
    # main campus greenery, preserving access and sightlines
    for x in range(87,1090,19):
        for z in (143,173,338,364,470,497,587,703,796):
            tree(x,z,R.randint(8,12),R.choice([0,0,1,2]))
    for z in range(181,792,20):
        for x in (58,86,504,542,856,894,1099):tree(x,z,R.randint(9,13),R.choice([0,1,2]))
    for _ in range(450):
        x,z=R.randint(93,1090),R.randint(175,790)
        if V[0,z,x]==grass and not np.any(V[1:12,z-7:z+8,x-7:x+8]!=air):tree(x,z,R.randint(7,11),R.choice([0,1,2]))
    for x in range(90,1110,38):
        for z in (166,359,490,582,818):light(x,z)
    for z in range(188,810,38):
        for x in (79,532,884):light(x,z)
    for x,z in [(313,684),(421,629),(613,694),(694,694),(961,315),(811,324),(601,335),(407,774),(280,708)]:bench(x,z)
    # parking bays and modest vehicles
    for x,z,n in [(196,730,8),(572,565,12),(91,588,7)]:
        ground(x,z,x+n*9,z+13,asphalt)
        for j in range(n+1):ground(x+j*9,z,x+j*9,z+13,white)
        for j in range(n):
            if j%3==0:continue
            xx=x+j*9+2;mat=R.choice([white,blue,red,asphalt])
            box(xx,1,z+2,xx+4,2,z+9,mat);box(xx+1,3,z+4,xx+3,3,z+7,blueglass)
            for dx,dz in [(0,3),(4,3),(0,8),(4,8)]:put(xx+dx,1,z+dz,dark)

def pack_values(arr,bits):
    """Minecraft's padded, little-bit-order values inside big-endian NBT longs."""
    values=np.asarray(arr,dtype=np.uint64).ravel();per=64//bits
    padded=np.zeros(math.ceil(len(values)/per)*per,dtype=np.uint64);padded[:len(values)]=values
    packed=np.bitwise_or.reduce(padded.reshape(-1,per) << (np.arange(per,dtype=np.uint64)*bits),axis=1)
    return [int(x) for x in packed]

def palette_nbt(p):
    d={'Name':nbt.T(p['Name'])}
    if 'Properties' in p:d['Properties']=nbt.C({k:nbt.T(v) for k,v in p['Properties'].items()})
    return d

def section(sy,arr):
    unique,inv=np.unique(arr,return_inverse=True)
    bs={'palette':nbt.LS(10,[palette_nbt(PAL[int(i)]) for i in unique])}
    if len(unique)>1:bs['data']=nbt.LA(pack_values(inv,max(4,(len(unique)-1).bit_length())))
    return {'Y':nbt.B(sy),'block_states':nbt.C(bs),'biomes':nbt.C({'palette':nbt.LS(8,['minecraft:plains'])})}

def export_world():
    print('Writing Anvil regions...',flush=True)
    template=ROOT/'validation/template'
    WORLD.mkdir(exist_ok=True)
    # Use 26.2's own generated global data as the schema source.
    shutil.copytree(template/'data',WORLD/'data',dirs_exist_ok=True)
    level=nbt.load(template/'level.dat');d=level['Data'][1]
    d['LevelName']=nbt.T('长春中医药大学｜净月校区 1.25:1')
    d['allowCommands']=nbt.B(1);d['GameType']=nbt.I(1);d['Time']=nbt.L(6000)
    d['spawn']=nbt.C({'pos':nbt.IA([370,65,800]),'yaw':nbt.F(180),'pitch':nbt.F(0),'dimension':nbt.T('minecraft:overworld')})
    d['LastPlayed']=nbt.L(int(time.time()*1000));nbt.save(WORLD/'level.dat',level)
    rules=nbt.load(WORLD/'data/minecraft/game_rules.dat');rd=rules['data'][1]
    for k in ['advance_time','advance_weather','spawn_mobs','spawn_monsters','spawn_patrols','spawn_phantoms','spawn_wandering_traders','mob_griefing','raids','pvp']:
        rd['minecraft:'+k]=nbt.B(0)
    rd['minecraft:random_tick_speed']=nbt.I(0);rd['minecraft:respawn_radius']=nbt.I(0)
    rd['minecraft:fire_spread_radius_around_player']=nbt.I(0)
    nbt.save(WORLD/'data/minecraft/game_rules.dat',rules)
    # Validate each generated state against the official version registry.
    report=ROOT/'tools/generated/reports/blocks.json'
    registry=json.loads(report.read_text())
    for p in PAL:
        assert p['Name'] in registry,p
        valid=registry[p['Name']].get('properties',{})
        for k,v in p.get('Properties',{}).items():assert k in valid and v in valid[k],p
    hmaps=np.max(np.where(V!=0,np.arange(H)[:,None,None]+129,0),axis=0).astype(np.uint16)
    chunks_by_region={};n=0
    fixed=[]
    for sy in range(-4,4):
        arr=np.full((16,16,16),stone,dtype=np.uint16)
        if sy==-4:arr[0]=bedrock
        if sy==3:arr[12:]=dirt
        fixed.append(section(sy,arr))
    airsec=[section(sy,np.zeros((16,16,16),dtype=np.uint16)) for sy in range(10,20)]
    for cz in range(Z//16):
        for cx in range(W//16):
            sections=list(fixed)
            for sy in range(4,10):sections.append(section(sy,V[(sy-4)*16:(sy-3)*16,cz*16:cz*16+16,cx*16:cx*16+16]))
            sections+=airsec
            hm=nbt.LA(pack_values(hmaps[cz*16:cz*16+16,cx*16:cx*16+16],9))
            entitylist=[b for b in BE.get((cx,cz),[]) if PAL[int(V[b['y'][1]-64,b['z'][1],b['x'][1]])]['Name'].endswith('_sign')]
            c={'DataVersion':nbt.I(4903),'xPos':nbt.I(cx),'zPos':nbt.I(cz),'yPos':nbt.I(-4),'Status':nbt.T('minecraft:full'),
                'LastUpdate':nbt.L(0),'InhabitedTime':nbt.L(0),'isLightOn':nbt.B(0),'sections':nbt.LS(10,sections),
                'Heightmaps':nbt.C({'WORLD_SURFACE':hm,'MOTION_BLOCKING':hm,'MOTION_BLOCKING_NO_LEAVES':hm,'OCEAN_FLOOR':hm}),
                'block_entities':nbt.LS(10,entitylist),'block_ticks':nbt.LS(10,[]),'fluid_ticks':nbt.LS(10,[]),
                'PostProcessing':nbt.LS(9,[(2,[]) for _ in range(24)]),'structures':nbt.C({'starts':nbt.C({}),'References':nbt.C({})})}
            r=(cx//32,cz//32);idx=(cx%32)+(cz%32)*32
            chunks_by_region.setdefault(r,{})[idx]=c;n+=1
        if cz%8==7: print(f'  {n} / {(W//16)*(Z//16)} chunks',flush=True)
    for (rx,rz),chunks in chunks_by_region.items():nbt.write_region(WORLD/f'dimensions/minecraft/overworld/region/r.{rx}.{rz}.mca',chunks)
    # Save actual voxel scene and metadata for independent previews and checking.
    np.save(ROOT/'tools/voxels.npy',V)
    metadata={'title':'长春中医药大学 · 净月校区','version':'26.2','data_version':4903,'scale':'约 1.25 方块 / 现实 1 米（估算）','dimensions':[W,H,Z],
        'spawn':[370,65,800],'chunks':n,'palette':PAL,'colors':COLORS,'landmarks':LANDMARKS,'block_count_above_ground':int(np.count_nonzero(V[1:]))}
    (ROOT/'build_manifest.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in metadata.items() if k not in ['palette','colors','landmarks']},ensure_ascii=False),flush=True)

def main():
    for fun in (terrain,library,academics,residence,sports,gardens):
        print(fun.__name__,flush=True);fun()
    export_world()
    import validate
    validate.main()

if __name__=='__main__':
    import sys
    if '--preview' in sys.argv:
        import preview;preview.main()
    elif '--validate' in sys.argv:
        import validate;validate.main()
    elif '--package' in sys.argv:
        import deliver;deliver.main()
    else:main()
