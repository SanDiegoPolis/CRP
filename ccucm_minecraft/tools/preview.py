from crp_runtime import java_executable, font_path
"""Orthographic views rendered directly from the exported block array."""
import json, math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parent.parent
FONT=font_path()

def font(n):return ImageFont.truetype(FONT,n)

def overview(v,m):
    h,z,w=v.shape;colors=np.asarray(m['colors'],dtype=np.uint8)
    heights=(h-1-np.argmax((v!=0)[::-1],axis=0)).astype(int)
    ids=v[heights,np.arange(z)[:,None],np.arange(w)[None,:]]
    rgb=colors[ids].astype(float)
    # soften patterned foliage and add actual height-derived cast shadows
    shadow=np.zeros((z,w),dtype=bool)
    for d in range(1,42):
        shifted=np.zeros_like(heights);shifted[d:,d:]=heights[:-d,:-d]-d*1.2
        shadow|=shifted>heights+1
    rgb[shadow]*=.73
    # a modest elevation edge shade
    edge=np.zeros_like(shadow);edge[1:]=heights[1:]<heights[:-1];rgb[edge]*=.85
    im=Image.fromarray(np.clip(rgb,0,255).astype('uint8')).resize((1440,1120),Image.Resampling.NEAREST)
    canvas=Image.new('RGB',(1680,1390),'#10262b');dr=ImageDraw.Draw(canvas)
    dr.text((55,33),'长春中医药大学 · 净月校区',font=font(39),fill='#f3e9cf')
    dr.text((58,87),'MINECRAFT JAVA 26.2  /  约 1.25 : 1  /  原版方块存档',font=font(20),fill='#a8c5bd')
    canvas.paste(im,(50,138));dr=ImageDraw.Draw(canvas)
    labels=[('四象城 · 图书馆',685,244),('致知楼',351,536),('行知楼',700,540),('明德楼',222,767),('仲景楼',573,760),('时珍楼',757,760),('启德馆',146,650),('行德馆',782,637),('八卦广场',649,645),('格物楼',1034,716),('日新楼',942,657),('杏林餐厅',603,416),('六君子居',739,417),('新公寓',366,254),('七星百草园',1000,245),('体育场',1030,462),('九宫喷泉',369,622),('南门',370,802),('青龙河',682,107),('三才轩',235,41),('五行宫',129,246)]
    for text,x,z in labels:
        cx=50+int(x*1.25);cy=138+int(z*1.25)
        f=font(17);bb=dr.textbbox((0,0),text,font=f);ww=bb[2]-bb[0]
        dr.rounded_rectangle((cx-ww/2-7,cy-14,cx+ww/2+7,cy+15),6,fill='#173532',outline='#9fab83',width=1)
        dr.text((cx-ww/2,cy-12),text,font=f,fill='#fff8e9')
    dr.text((1520,144),'北 N',font=font(22),fill='#f3e9cf');dr.line((1547,245,1547,193),fill='#f3e9cf',width=3)
    dr.polygon([(1547,181),(1538,198),(1556,198)],fill='#f3e9cf')
    dr.text((1515,310),'出生点',font=font(19),fill='#f3e9cf');dr.text((1509,345),'370\n65\n800',font=font(21),fill='#a8c5bd',spacing=9)
    dr.text((56,1282),'参观路线：南门 → 校训石 → 九宫喷泉 → 致知楼 → 四象城 → 百草园 → 体育场 → 八卦广场',font=font(20),fill='#f3e9cf')
    dr.text((56,1324),'依据公开校园导览图与实景照片重建；布局与尺度作游戏适配，未知室内为设计补全。此图由存档方块数据渲染。',font=font(17),fill='#9eb8b1')
    canvas.save(ROOT/'校园导览.png')
    return im

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
    dr.text((45,25),'长春中医药大学 · '+out.removesuffix('.png'),font=font(28),fill='#f5e9cf')
    dr.text((45,65),'由真实存档方块数据渲染  |  Java 26.2 原版  |  约 1.25 : 1',font=font(17),fill='#a8c5bd')
    im.save(ROOT/out)
    return im

def main():
    m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'))
    v=np.load(ROOT/'tools/voxels.npy',mmap_mode='r')
    top=overview(v,m)
    full=iso(v,m,'校园鸟瞰.png')
    iso(v,m,'图书馆与教学区.png',(202,165,845,584),2200)
    iso(v,m,'南门与八卦广场.png',(89,583,1090,834),2400)
    icon=top.crop((250,190,1030,970)).resize((64,64),Image.Resampling.LANCZOS)
    icon.save(ROOT/'CCUCM_Jingyue_26.2/icon.png')
    print('Previews complete',flush=True)

if __name__=='__main__':main()
