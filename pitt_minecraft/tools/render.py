"""Preview images from the actual saved-world block array, without texture packs."""
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
    rgb=np.array(m['colors'],dtype='uint8')[ids].astype(float)
    shadow=np.zeros((d,w),dtype=bool)
    for s in range(1,70):
        shadow[s:,s:]|=heights[:-s,:-s]-s*1.6>heights[s:,s:]+1
    rgb[shadow]*=.67
    im=Image.fromarray(rgb.astype('uint8'))
    canvas=Image.new('RGB',(2320,1530),'#091f3e');canvas.paste(im,(35,175));dr=ImageDraw.Draw(canvas)
    dr.text((40,30),'匹兹堡大学 · OAKLAND CAMPUS',font=font(44),fill='#ffcd63')
    dr.text((43,98),'JAVA 26.2 原版存档   /   约 1.1 方块 : 1 米   /   1792 × 1280 方块',font=font(24),fill='#cbd6e8')
    for i,lm in enumerate(m['landmarks'],1):
        x,z=lm['x']+35,lm['z']+175
        dr.ellipse((x-15,z-15,x+15,z+15),fill='#0b2346',outline='#eab446',width=2)
        s=str(i);bb=dr.textbbox((0,0),s,font=font(17));dr.text((x-(bb[2]-bb[0])/2,z-12),s,font=font(17),fill='#ffffff')
        yy=190+(i-1)*44
        dr.text((1860,yy),f'{i:02d}  '+lm['name'],font=font(17),fill='#f0e7d0')
    dr.text((1865,1420),'出生点：1350 / 69 / 648',font=font(18),fill='#ffcd63')
    dr.text((43,1480),'图像直接来自存档方块数据；重点外观参考官方地图与实景，未公开的室内作设计补全。',font=font(20),fill='#cbd6e8')
    canvas.save(ROOT/'校园导览.png')
    return im

def main():
    m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'));v=np.load(ROOT/'tools/voxels.npy',mmap_mode='r')
    top=overview(v,m)
    if '--map-only' in sys.argv:return
    full=iso(v,m,'校园鸟瞰.png',width=2800)
    iso(v,m,'学习大教堂与礼拜堂.png',(1130,260,1510,650),2400)
    iso(v,m,'学生中心与三塔.png',(900,500,1260,830),2200)
    a=np.load(ROOT/'tools/check_Cathedral_of_Learning.npy')
    cut=a[:20].copy();cut[:,:,0:10]=0;cut[:,86:,:]=0
    iso(cut,m,'公共大厅剖面.png',width=2000)
    top.crop((1150,275,1490,615)).resize((64,64),Image.Resampling.LANCZOS).save(ROOT/'Pitt_Oakland_26.2/icon.png')
    print('Previews complete',flush=True)

if __name__=='__main__':main()
