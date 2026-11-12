from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
from voxel_render import iso,font
ROOT=Path(__file__).resolve().parent.parent

def overview(v,m):
    h,d,w=v.shape
    heights=(h-1-np.argmax((v!=0)[::-1],axis=0)).astype(int)
    ids=v[heights,np.arange(d)[:,None],np.arange(w)[None,:]]
    rgb=np.array(m['colors'],dtype='uint8')[ids].astype(float);shadow=np.zeros((d,w),dtype=bool)
    for s in range(1,40):shadow[s:,s:]|=heights[:-s,:-s]-s*1.6>heights[s:,s:]+1
    rgb[shadow]*=.73;top=Image.fromarray(rgb.astype('uint8'));scale=.62
    im=top.resize((round(w*scale),round(d*scale)),Image.Resampling.NEAREST)
    canvas=Image.new('RGB',(2300,1910),'#172c33');canvas.paste(im,(25,180));dr=ImageDraw.Draw(canvas)
    dr.text((43,32),'南京工业大学 · 江浦校区',font=font(47),fill='#f1ead7')
    dr.text((46,104),'CAMPUS RECONSTRUCTION PROJECT  /  JAVA 26.2  /  约 1.1 : 1',font=font(23),fill='#a6cabb')
    for i,lm in enumerate(m['landmarks'],1):
        x,z=round(25+lm['x']*scale),round(180+lm['z']*scale)
        dr.ellipse((x-12,z-12,x+12,z+12),fill='#172c33',outline='#eec570',width=2)
        s=str(i);bb=dr.textbbox((0,0),s,font=font(14));dr.text((x-(bb[2]-bb[0])/2,z-10),s,font=font(14),fill='white')
        col=(i-1)//23;row=(i-1)%23;tx=1328+col*470;ty=242+row*62
        dr.text((tx,ty),f'{i:02d}  '+lm['name'],font=font(19),fill='#f1ead7')
        label=lm['label'];label=label[:22]+'…' if len(label)>22 else label
        dr.text((tx+33,ty+28),label,font=font(14),fill='#9cbbb3')
    sx,sy,sz=m['spawn'];dr.text((1335,177),'北 N ↑',font=font(27),fill='#eec570')
    dr.text((1340,1715),f'出生点  {sx} / {sy} / {sz}',font=font(23),fill='#eec570')
    dr.text((1340,1755),'南门 → 厚学楼 → 图书馆 → 镜湖 → 仁智楼 → 天宝阁',font=font(18),fill='#a6cabb')
    dr.text((43,1823),'依据官方导览图及公开照片近似还原；建筑间距、地形与室内作了游戏适配。',font=font(23),fill='#a6cabb')
    dr.text((43,1860),'本图由实际存档方块数据绘制，非测绘地图。',font=font(19),fill='#a6cabb')
    canvas.save(ROOT/'校园导览.png')
    top.crop((1070,1090,1305,1325)).resize((64,64),Image.Resampling.LANCZOS).save(ROOT/'NJTech_Jiangpu_26.2/icon.png')

if __name__=='__main__':
    m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'));v=np.load(ROOT/'tools/voxels.npy',mmap_mode='r')
    overview(v,m)
    if '--map-only' not in sys.argv:
        iso(v,m,'逸夫图书馆与镜湖.png',(720,940,1330,1380),2500,rotation=1)
        iso(v,m,'天宝阁与仁智楼.png',(790,520,1115,985),2500)
        iso(v,m,'南门与教学区.png',(1080,1750,1665,2360),2600)
        iso(v,m,'行健体育馆与田径场.png',(1325,1240,1840,1760),2500)
        iso(v,m,'校园鸟瞰.png',width=3000)
    print('Previews complete',flush=True)
