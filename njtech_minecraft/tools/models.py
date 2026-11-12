import geometry as g
import numpy as np
stonewhite=g.block("quartz_bricks",(210,212,207))
silver=g.block("light_gray_concrete",(182,190,192))
roofgreen=g.block("green_terracotta",(108,119,72))
teal=g.block("warped_planks",(57,114,113))

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

