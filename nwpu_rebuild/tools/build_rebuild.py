"""Evidence-led reconstruction on the preserved NWPU illustrated-map registration."""
from pathlib import Path
import math,json,sys,heapq,hashlib
from collections import deque
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
import base as b
import geometry as g

ROOT=b.ROOT; V=b.V; W,D,H=b.W,b.D,b.H
gray=g.block('light_gray_concrete',(186,190,185))
limestone=g.block('smooth_sandstone',(216,209,181))
roof=g.block('gray_terracotta',(78,87,75))
darkstone=g.block('polished_blackstone',(55,60,59))
glazing=g.block('light_blue_stained_glass',(89,147,169))
g.lightterra=gray
b.pinkleaf=g.birchleaves
old_regular=b.regular;old_arena=b.arena;old_teaching=b.teaching;old_museum=b.museum
old_landscape=b.landscape;old_place=b.place
OBJECTS=[];CONNECTORS=[];PROTECTED=np.zeros((D,W),bool)
OWNERS=np.zeros((D,W),np.uint16);COLLISIONS=[]

def block_building(x,z,w,d,floors=5,style='white',kind='classroom'):
    wall=g.quartz if style=='white' else limestone if style=='beige' else g.brick
    top=g.building(x,z,w,d,floors,wall,kind,None,1)
    # Thin horizontal bands and darker recessed stair bays replace generic pink slabs.
    for f in range(floors):
        y=1+6*f
        for xx in range(x+4,x+w-4,7):
            g.box(xx,y+2,z,xx+3,y+4,z,glazing)
            g.box(xx,y+2,z+d-1,xx+3,y+4,z+d-1,glazing)
        for xx in (x+1,x+w-3):g.box(xx,y+1,z+d,xx+1,y+5,z+d,darkstone)
    return top

def regular(w,d,floors=5,style='white',kind='classroom'):
    if kind=='office' and w>=52 and d>=72:
        # U-shaped institute typology, inferred from the illustrated plan/aerial.
        block_building(5,5,w-10,23,floors,style,kind)
        for x in (5,w-24):block_building(x,31,19,d-44,floors,style,kind)
        g.ground(27,32,w-27,d-13,g.grass)
        g.box(w//2-3,0,29,w//2+3,0,d-1,g.paving)
        g.box(w//2-3,1,24,w//2+3,1,32,g.quartz)
        g.box(w//2-3,2,24,w//2+3,5,33,0)
    else:block_building(5,5,w-10,d-15,floors,style,kind)
    if kind=='dorm':
        # Recessed dark bays, white framing and window canopies; interior stays accessible.
        for x in range(8,w-8,14):
            g.box(x,2,d-10,x+4,floors*6,d-10,darkstone)
            for f in range(floors):
                y=1+f*6;g.box(x,y+2,d-9,x+3,y+4,d-9,glazing)
                g.box(x-1,y+5,d-9,x+4,y+5,d-8,g.quartz)
        g.box(w//2-4,2,d-14,w//2+4,5,d-6,0)
        g.box(w//2-4,1,d-14,w//2+4,1,d-6,g.quartz)

def library(w,d):
    # Slender curved reading wing, descending to the low Qizhen wing.
    h,dz,wx=g.V.shape;zz,xx=np.mgrid[:dz,:wx]
    front=128-((xx-135)/83)**2*10
    back=front-43
    mask=(xx>=69)&(xx<=201)&(zz>=back)&(zz<=front)
    edge=mask&~(np.asarray(Image.fromarray((mask*255).astype('uint8')).filter(ImageFilter.MinFilter(3)))>0)
    tops=np.clip(14+(xx-69)*.292,14,53).astype(int)
    for y in range(1,54):
        active=mask&(tops>=y);g.V[y][active]=0
        g.V[y][edge&(tops>=y)]=glazing
        if y in (1,7,13,19,25,31,37):g.V[y][active]=g.quartz
        g.V[y][mask&(tops==y)]=gray
        # Two thin horizontal shading lines per storey, continuous along the curve.
        if y>=7 and y%3==1:g.V[y][edge&(tops>=y)]=g.quartz if y%6==1 else g.iron
        g.V[y][edge&(xx%13==0)&(tops>=y)]=g.iron
    # Rounded tall end, mullions and a slim mast visible above the roofline.
    for x in range(197,207):
        rad=math.sqrt(max(0,10**2-(x-197)**2))
        z1,z2=round(99-rad*1.7),round(99+rad*1.7)
        for y in range(1,53):
            g.box(x,y,z1,x,y,z2,glazing if x==206 or y%6 not in (1,) else g.quartz)
            if x<205:g.box(x,y,z1+1,x,y,z2-1,0)
        g.box(x,53,z1,x,54,z2,g.quartz)
    g.box(207,1,99,208,57,100,g.quartz);g.box(208,58,99,208,77,99,g.iron)
    # Elevated low wing with an open colonnade facing the forecourt.
    g.box(5,7,15,62,8,64,g.quartz);g.box(5,9,15,62,24,64,glazing)
    g.box(7,9,17,60,23,62,0);g.box(4,25,14,63,26,65,g.quartz)
    for y in (13,19):g.box(5,y,15,62,y,64,g.quartz)
    for x in range(8,62,9):g.box(x,1,62,x+1,7,63,g.quartz);g.box(x,9,65,x,24,65,g.iron)
    g.box(58,1,16,72,19,31,g.quartz);g.box(60,2,18,70,18,29,0)
    for y in (1,7,13):g.box(58,y,16,72,y,31,g.quartz)
    # Designed stacks and tables on seven accessible levels of the tall wing.
    for y in (1,7,13,19,25,31,37):
        for x in range(84,192,17):
            for z in (99,118):
                if tops[z,x]<y+5 or not mask[z,x]:continue
                g.box(x,y+1,z,x+7,y+3,z+1,g.book)
                g.box(x,y+1,z+5,x+7,y+1,z+6,g.wood)
                g.put(x+3,y+4,z+3,g.sea)
    # Main east-side entry, continuous indoor aisle and central stair.
    g.box(96,1,124,113,1,d-1,g.quartz);g.box(96,2,119,113,8,d-1,0)
    g.box(99,2,108,190,5,114,0);g.box(99,1,108,190,1,114,g.quartz)
    b.spiral(177,92,1,37)
    for x in range(175,191):
        for z in range(90,106):
            if mask[z,x]:g.put(x,int(tops[z,x]),z,gray)
    g.box(94,10,129,119,10,139,glazing)
    for x in (94,118):g.box(x,1,137,x,9,137,g.quartz)
    # Forecourt and faceted blue skylight are independent of the roof.
    g.ground(8,70,86,139,g.grass)
    for k in range(10):g.box(28+k,1+k,88+k,57-k,1+k,119-k,glazing)
    g.box(9,0,77,93,0,81,g.paving);g.box(83,0,77,93,0,145,g.paving)
    g.ground(72,4,201,68,g.grass)
    g.path([(79,12),(190,12),(190,63)],5,g.paving,0)
    for x,z in ((96,32),(134,30),(173,32)):g.tree(x,z,8,1)
    g.textwall('图书馆',136,8,132,g.gold,9)

def hip(x,z,w,d,y,height=6):
    # Broad projecting eaves with a lower dark fascia, closer to the real layered roof.
    g.box(x-3,y,z-3,x+w+2,y,z+d+2,darkstone)
    for k in range(height):g.box(x+k,y+1+k,z+k,x+w-1-k,y+1+k,z+d-1-k,roof)
    g.box(x+height,y+height+1,z+height,x+w-height-1,y+height+1,z+d-height-1,roof)

def qixiang(w,d):
    b.courtyard(w,d,4,False)
    for x,z,ww,dd in [(4,4,w-8,27),(4,d-35,w-8,27),(4,30,24,d-65),(w-28,30,24,d-65)]:hip(x,z,ww,dd,27)
    for x,z in [(6,6),(w-38,6),(6,d-44),(w-38,d-44)]:
        block_building(x,z,31,32,6,'white','office')
        g.box(x,32,z,x+30,37,z+31,darkstone)
        for xx in range(x+3,x+28,6):g.box(xx,33,z+32,xx+2,36,z+32,glazing)
        hip(x-1,z-1,33,34,38,6)
    # Three-storey entrance hall, glazed porch and planted central courtyard.
    g.box(w//2-22,1,d-31,w//2+22,19,d-9,g.quartz)
    g.box(w//2-20,2,d-30,w//2+20,18,d-10,0)
    for x in range(w//2-20,w//2+20,7):g.box(x,9,d-8,x+3,16,d-8,glazing)
    g.box(w//2-6,2,d-31,w//2+6,7,d-1,0);g.box(w//2-6,1,d-31,w//2+6,1,d-1,g.quartz)
    hip(w//2-24,d-35,49,28,20,5)
    g.box(w//2-20,8,d-5,w//2+20,8,d-1,roof)
    for x in (w//2-18,w//2+18):g.box(x,1,d-2,x+1,7,d-2,g.quartz)
    g.ground(43,42,w-44,d-43,g.grass)
    g.box(w//2-3,0,37,w//2+3,0,d-37,g.paving)
    # A continuous public stair in the southwest corner connects the upper floors.
    g.box(9,2,d-40,13,7,d-1,0);g.box(9,1,d-40,13,1,d-1,g.quartz)
    b.spiral(15,d-39,1,31)

def arena(w,d):
    old_arena(w,d)
    # Two distinct hall roofs with exposed thin truss ribs and terrace approaches.
    for x,z,ww,dd,high in [(5,14,65,d-32,24),(76,5,w-82,d-12,31)]:
        for k in range(0,ww+2,9):
            for zz in range(z-2,z+dd+2):
                yy=high+3+round(5*math.sin(math.pi*(k+3)/(ww+6)))
                g.put(x+k,yy+2,zz,g.iron)
        for zz in (z-2,z+dd+1):
            for k in range(ww+1):
                yy=high+3+round(5*math.sin(math.pi*(k+3)/(ww+6)))
                g.put(x+k,yy+4,zz,g.iron)
    # Circular high windows in the smaller hall and stone terrace railing.
    for x in range(12,65,12):g.sphere(x,18,d-18,3,3,1,glazing)
    for x in range(8,67,10):g.box(x,1,d-9,x+1,10,d-9,g.quartz)
    g.box(8,10,d-9,69,10,d-9,g.iron)
    for x in range(79,w-5,16):
        for y in range(5,28):g.box(x,y,d-11+(y-5)//7,x+2,y,d-11+(y-5)//7,g.quartz)
    cx=76+(w-82)//2
    g.box(cx-7,2,d-25,cx+7,9,d-1,0);g.box(cx-7,1,d-25,cx+7,1,d-1,g.quartz)
    for x in (cx-24,cx+20):g.box(x,1,d-11,x+4,2,d-2,g.grass)

def east_gate(w,d):
    # Six bundles of white piers, linked lintels and shallow bowl capitals.
    for x in (14,42,70,w-70,w-42,w-14):
        g.box(x-6,1,9,x+6,2,21,g.quartz)
        for dx in (-4,0,4):g.box(x+dx,3,12,x+dx+1,21,17,g.quartz)
        g.box(x-7,22,8,x+7,24,22,g.quartz)
        g.box(x-6,25,9,x+6,25,21,limestone)
        for y in range(4):g.disk(x,15,4+y,26+y,limestone,max(0,2+y))
    for x1,x2 in ((14,70),(w-70,w-14)):g.box(x1,22,11,x2,24,18,g.quartz)
    g.box(w//2-39,1,4,w//2+39,7,8,g.quartz)
    g.textwall('西北工业大学',w//2-35,0,9,g.gold,9)
    for x in (0,w-8):g.box(x,1,7,x+7,18,21,g.quartz)
    # The side passage remains open; the name wall is no longer cut down its middle.
    for x in (29,w-29):
        g.box(x-6,1,0,x+6,1,d-1,g.paving)
    for x in range(12,w-10,10):
        if 82<x<138:continue
        g.box(x,0,d-10,x+4,0,d-7,g.white)
    g.box(w//2-5,0,d-2,w//2+5,0,d+7,g.paving)

def teaching(w,d):
    old_teaching(w,d)
    # Real courtyards and covered links retain the four-wing organization.
    for x in (35,w-43):
        for z in range(52,d-58,8):g.box(x,1,z,x+6,2,z+4,g.grass)
    for x in (w//2-17,w//2+17):
        g.box(x,9,46,x+1,10,d-52,g.quartz)
        for z in range(47,d-50,12):g.box(x,1,z,x+1,8,z+1,g.quartz)
    g.box(w//2-14,10,45,w//2+14,10,50,glazing)
    for xx in (w//4,3*w//4):
        g.box(xx-4,1,d-50,xx+4,1,d-10,g.quartz)
        g.box(xx-4,2,d-50,xx+4,5,d-10,0)

def museum(w,d):
    old_museum(w,d)
    # Low faceted gallery roofs and open crossing paths between static exhibits.
    for z in (15,67):
        for x in range(12,w-10):
            y=21+int((x%48)/10);g.box(x,y,z,x,y,z+26,g.white)
    for z in (117,169,214):g.box(7,0,z,w-8,0,z+5,g.paving)
    g.box(w//2-7,0,95,w//2+7,0,d-1,g.paving)

def place(name,u,v,w,d,fun,targets=None,note='',angle=-90):
    adjustment={}
    if name in {'海天苑公寓南区1','海天苑公寓南区2','海天苑公寓南区3','海天苑公寓南区4','配套楼7'}:
        angle=90;adjustment={'entry_orientation':'west-facing; avoids the opposing plot','basis':'circulation adaptation, facade orientation not surveyed'}
    if name=='网络空间安全学院':
        v-=16/2.6;adjustment={'dx_blocks':-16,'basis':'clearance from adjacent student-center plot'}
    cx,cz=b.xy(u,v);radius=math.ceil(math.hypot(w+8,d+8)/2)+3
    xa,xb=max(0,cx-radius),min(W,cx+radius+1);za,zb=max(0,cz-radius),min(D,cz+radius+1)
    before=b.V[5:,za:zb,xa:xb].copy()
    old_place(name,u,v,w,d,fun,targets,note,angle)
    x0,z0,x1,z1,mask=b.LAST_PLACEMENT;assert (xa,za,xb,zb)==(x0,z0,x1,z1)
    owner=OWNERS[z0:z1,x0:x1]
    overlap=mask&(owner>0)&np.any(before!=0,axis=0)
    for idx in np.unique(owner[overlap]):
        hit=overlap&(owner==idx)
        changed=np.count_nonzero((before!=b.V[5:,z0:z1,x0:x1])[:,hit])
        COLLISIONS.append({'earlier':b.BUILDINGS[int(idx)-1]['name'],'later':name,'occupied_columns':int(hit.sum()),'changed_upper_voxels':int(changed)})
    owner[mask]=len(b.BUILDINGS)
    lm=b.BUILDINGS[-1];lm['object_id']=f'B{len(b.BUILDINGS):03d}'
    lm['model_source']='rebuild' if fun in (library,qixiang,arena,east_gate,teaching,museum) else 'adapted campus typology'
    # Preserve the external boundary: connector fitting never enters a building plot.
    cx,cz=lm['x'],lm['z'];theta=math.radians(angle);cs,sn=math.cos(theta),math.sin(theta)
    pts=[(cx+x*cs-z*sn,cz+x*sn+z*cs) for x,z in [(-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2)]]
    im=Image.new('L',(W,D));ImageDraw.Draw(im).polygon(pts,fill=255)
    PROTECTED[:]|=np.asarray(im)>0
    OBJECTS.append(dict(lm,map_uv=[u,v],adaptation=adjustment,evidence='B: official map plus photos for landmarks; C: inferred ordinary facade/interior'))

def connect_paths():
    """Connect plot entrances to the existing street/footpath network outside plots."""
    surface=b.V[4]
    road=np.isin(surface,[g.asphalt,g.paving,g.white,g.quartz,g.wood])&~PROTECTED
    blocked=PROTECTED|((b.V[3]==g.water)&(surface==0))|(b.DEM>5)
    blocked|=np.any(b.V[5:8]!=0,axis=0)
    step=3;gz=(D+step-1)//step;gx=(W+step-1)//step
    # Conservative whole-cell blocking, avoiding narrow corner cuts.
    padded=np.ones((gz*step,gx*step),bool);padded[:D,:W]=blocked
    block=padded.reshape(gz,step,gx,step).any(axis=(1,3))
    roadpad=np.zeros_like(padded);roadpad[:D,:W]=road
    sources=roadpad.reshape(gz,step,gx,step).all(axis=(1,3))&~block
    prev=np.full((gz,gx),-1,np.int32);q=deque()
    # Only the established main connected paved network is seeded, not isolated pads.
    rootx,rootz=b.xy(1108,879)
    candidates=np.argwhere(sources)
    root=min(candidates,key=lambda p:(p[0]*step-rootz)**2+(p[1]*step-rootx)**2)
    connected=np.zeros_like(sources);qq=deque([tuple(root)]);connected[tuple(root)]=True
    while qq:
        z,x=qq.popleft()
        for dz,dx in ((1,0),(-1,0),(0,1),(0,-1)):
            nz,nx=z+dz,x+dx
            if 0<=nz<gz and 0<=nx<gx and sources[nz,nx] and not connected[nz,nx]:connected[nz,nx]=True;qq.append((nz,nx))
    for z,x in np.argwhere(connected):prev[z,x]=z*gx+x;q.append((int(z),int(x)))
    while q:
        z,x=q.popleft()
        for dz,dx in ((1,0),(-1,0),(0,1),(0,-1)):
            nz,nx=z+dz,x+dx
            if 0<=nz<gz and 0<=nx<gx and not block[nz,nx] and prev[nz,nx]<0:
                prev[nz,nx]=z*gx+x;q.append((nz,nx))
    routeim=Image.new('L',(W,D));dr=ImageDraw.Draw(routeim)
    for lm in b.BUILDINGS:
        ex,_,ez=lm['entrance'];cx,cz=round(ex/step),round(ez/step)
        starts=[]
        for z in range(max(0,cz-6),min(gz,cz+7)):
            for x in range(max(0,cx-6),min(gx,cx+7)):
                if prev[z,x]>=0:starts.append(((x*step-ex)**2+(z*step-ez)**2,z,x))
        if not starts:CONNECTORS.append({'name':lm['name'],'result':'NO_EXTERIOR_ROUTE'});continue
        _,z,x=min(starts);nodes=[]
        for _ in range(gx*gz):
            nodes.append((x*step+1,z*step+1));nxt=int(prev[z,x]);nz,nx=divmod(nxt,gx)
            if (nz,nx)==(z,x):break
            z,x=nz,nx
        # Fitting stops at the plot; entrance thresholds are checked separately in 3-D.
        dr.line([(ex,ez)]+nodes,fill=255,width=5,joint='curve')
        CONNECTORS.append({'name':lm['name'],'arrival':[ex,69,ez],'nodes':len(nodes),'start_adjustment_blocks':round(math.sqrt(min(starts)[0]),2),'result':'ROUTE_BUILT'})
    mask=(np.asarray(routeim)>0)&~blocked
    b.V[4][mask]=g.paving
    np.save(ROOT/'tools/exterior_protection.npy',PROTECTED)
    np.save(ROOT/'tools/connector_mask.npy',mask)
    (ROOT/'planning/entrance-connectors.json').write_text(json.dumps(CONNECTORS,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Exterior connector planning',len(CONNECTORS),'plots;',sum(c['result']=='ROUTE_BUILT' for c in CONNECTORS),'connected',flush=True)

def landscape():
    old_landscape()
    # Street edges receive orderly tree rows; new paths are fitted after existing trees.
    for pts,width in b.ROADS:
        for p1,p2 in zip(pts,pts[1:]):
            ax,az=b.xy(*p1);bx,bz=b.xy(*p2);length=math.dist((ax,az),(bx,bz))
            for t in range(15,int(length)-15,26):
                for side in (-1,1):
                    q=t/length;x=round(ax+(bx-ax)*q+side*(width/2+12));z=round(az+(bz-az)*q)
                    if not(12<x<W-12 and 12<z<D-12) or PROTECTED[z,x]:continue
                    if V[4,z,x]!=g.grass or np.any(V[5:20,z-5:z+6,x-5:x+6]):continue
                    g.box(x,5,z,x,15,z,g.log);g.sphere(x,16,z,4,4,4,g.birchleaves)
    # A walkable cross-axis from the east gate through the shared plaza.
    connect_paths()

def main():
    b.block_building=block_building;b.regular=regular;b.library=library;b.qixiang=qixiang
    b.arena=arena;b.east_gate=east_gate;b.teaching=teaching;b.museum=museum;b.place=place;b.landscape=landscape
    if '--templates' in sys.argv:
        b.buildings()
        from navigation import navigability
        result=navigability(None,{'palette':g.PAL,'navigation_checks':b.CHECKS})
        (ROOT/'planning/template-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        (ROOT/'planning/building-collision-review.json').write_text(json.dumps({'collisions':COLLISIONS,'result':'PASS' if not COLLISIONS else 'REVIEW'},ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False),flush=True)
        print('Collision audit',json.dumps(COLLISIONS,ensure_ascii=False),flush=True)
    else:
        b.terrain();b.lakes()
        b.route([(1108,920),(1108,900)],9,g.paving)
        # Bridge to the library forecourt; alignment is a documented visitor-route adaptation.
        g.box(861,4,1074,1006,4,1082,g.wood)
        for x in range(871,1000,16):
            if V[3,1078,x]==g.water:
                for z in (1074,1082):g.box(x,1,z,x,3,z,g.stone)
        b.buildings();landscape();b.export()
        m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'))
        m['coordinate_version']='nwpu-illustrated-map-2025-north-up-v1';m['release']='NWPU-rebuild-20260924'
        m['title']='西北工业大学 · 长安校区重制版';m['objects']=OBJECTS
        (ROOT/'build_manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
        (ROOT/'planning/objects.json').write_text(json.dumps(OBJECTS,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
