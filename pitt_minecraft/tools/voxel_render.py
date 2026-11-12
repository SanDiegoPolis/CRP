from crp_runtime import java_executable, font_path
"""Orthographic views rendered directly from the exported block array."""
import json, math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parent.parent
FONT=font_path()

def font(n):return ImageFont.truetype(FONT,n)

def greedy_rows(a):
    """Merge equal-color row runs over successive rows into rectangles."""
    active={};rects=[]
    for r,row in enumerate(a):
        change=np.r_[True,row[1:]!=row[:-1],True];edges=np.flatnonzero(change)
        present={}
        for j in range(len(edges)-1):
            start,end=int(edges[j]),int(edges[j+1]);val=int(row[start])
            if not val:continue
            key=(start,end,val)
            present[key]=active.pop(key,(r,r+1))[0],r+1
        for (start,end,val),(r0,r1) in active.items():rects.append((start,r0,end,r1,val))
        active=present
    for (start,end,val),(r0,r1) in active.items():rects.append((start,r0,end,r1,val))
    # Long rectangles break painter ordering at intersecting roof/wall planes.
    # Small coplanar tiles keep occlusion local while preserving actual geometry.
    tiles=[]
    for x0,y0,x1,y1,b in rects:
        for y in range(y0,y1,5):
            for x in range(x0,x1,5):tiles.append((x,y,min(x+5,x1),min(y+5,y1),b))
    return tiles

def iso(v,m,out,bounds=None,width=2400):
    if bounds:
        x0,z0,x1,z1=bounds;v=v[:,z0:z1,x0:x1]
    h,d,w=v.shape
    # Render top, south, east faces. All pixels derive from actual block states.
    # Tiny foliage/crop plants are represented by block-colored voxels in this preview.
    faces=[];colors=m['colors']
    print('Meshing',out,flush=True)
    for y in range(h):
        a=v[y];ex=(a!=0)&((v[y+1]==0) if y+1<h else True)
        arr=np.where(ex,a,0)
        for xa,za,xb,zb,b in greedy_rows(arr):
            faces.append(((xa+xb+za+zb)*.5+(y+1)*1.3,[(xa,y+1,za),(xb,y+1,za),(xb,y+1,zb),(xa,y+1,zb)],b,1.0))
    for z in range(d):
        a=v[:,z,:];ex=(a!=0)&((v[:,z+1,:]==0) if z+1<d else True)
        ex[0]=False
        for xa,ya,xb,yb,b in greedy_rows(np.where(ex,a,0)):
            faces.append(((xa+xb)*.5+z+1+(ya+yb)*.65,[(xa,ya,z+1),(xb,ya,z+1),(xb,yb,z+1),(xa,yb,z+1)],b,.78))
    for x in range(w):
        a=v[:,:,x];ex=(a!=0)&((v[:,:,x+1]==0) if x+1<w else True)
        ex[0]=False
        for za,ya,zb,yb,b in greedy_rows(np.where(ex,a,0)):
            faces.append((x+1+(za+zb)*.5+(ya+yb)*.65,[(x+1,ya,za),(x+1,ya,zb),(x+1,yb,zb),(x+1,yb,za)],b,.62))
    scale=(width-120)/(w+d);height=int((w+d)*scale*.51+h*scale*1.12+150)
    im=Image.new('RGB',(width,height),'#172c33');dr=ImageDraw.Draw(im)
    def proj(p):
        x,y,z=p;return (60+(x-z+d)*scale,80+h*scale+(x+z)*scale*.49-y*scale*1.1)
    faces.sort(key=lambda f:f[0])
    print('Faces',len(faces),flush=True)
    for _,points,b,shade in faces:
        c=tuple(int(c*shade) for c in colors[b]);dr.polygon([proj(p) for p in points],fill=c)
    # Crop unused sky while preserving a separate, readable title band.
    from PIL import ImageChops
    bb=ImageChops.difference(im,Image.new('RGB',im.size,'#172c33')).getbbox()
    if bb:
        crop=im.crop((0,max(0,bb[1]-18),width,min(height,bb[3]+30)))
        im=Image.new('RGB',(width,crop.height+115),'#172c33');im.paste(crop,(0,115));dr=ImageDraw.Draw(im)
    dr.text((45,25),'匹兹堡大学 · '+out.removesuffix('.png'),font=font(28),fill='#f5e9cf')
    dr.text((45,65),'由真实存档方块数据渲染  |  Java 26.2 原版  |  约 1.1 : 1',font=font(17),fill='#a8c5bd')
    im.save(ROOT/out)
    return im

