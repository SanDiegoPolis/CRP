"""Actual-block preview images, with a north-up campus guide."""
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
    for s in range(1,45):shadow[s:,s:]|=heights[:-s,:-s]-s*1.6>heights[s:,s:]+1
    rgb[shadow]*=.7
    top=Image.fromarray(rgb.astype('uint8'));scale=.64
    im=top.resize((round(w*scale),round(d*scale)),Image.Resampling.NEAREST)
    canvas=Image.new('RGB',(1920,1910),'#092c44');canvas.paste(im,(35,165));dr=ImageDraw.Draw(canvas)
    dr.text((40,30),'西北工业大学 · 长安校区',font=font(43),fill='#eef5e9')
    dr.text((43,97),'MINECRAFT JAVA 26.2  /  约 1.1 : 1  /  原版方块存档',font=font(24),fill='#a6d3c8')
    for i,lm in enumerate(m['landmarks'],1):
        x,z=round(35+lm['x']*scale),round(165+lm['z']*scale)
        dr.ellipse((x-13,z-13,x+13,z+13),fill='#0b3049',outline='#f0cc72',width=2)
        s=str(i);bb=dr.textbbox((0,0),s,font=font(15));dr.text((x-(bb[2]-bb[0])/2,z-10),s,font=font(15),fill='#ffffff')
        col=(i-1)//22;row=(i-1)%22;tx=1055+col*425;ty=232+row*60
        dr.text((tx,ty),f'{i:02d}  '+lm['name'],font=font(19),fill='#f0e7d0')
        label=lm['label'];label=label[:20]+'…' if len(label)>20 else label
        dr.text((tx+37,ty+28),label,font=font(13),fill='#93b7bb')
    dr.text((1070,172),'北 N ↑',font=font(24),fill='#f0cc72')
    sx,sy,sz=m['spawn'];dr.text((1070,1660),f'出生点  {sx} / {sy} / {sz}',font=font(23),fill='#f0cc72')
    dr.text((1070,1708),'东门 → 何尊广场 → 图书馆 → 启真湖',font=font(19),fill='#b4d7d2')
    dr.text((1070,1742),'→ 教学区 → 生活区 → 启翔湖与博物馆',font=font(19),fill='#b4d7d2')
    dr.text((42,1840),'依据官方校园导览图和建筑照片近似还原；室内与部分细节设计补全。此图直接来自存档方块数据。',font=font(21),fill='#b4d7d2')
    canvas.save(ROOT/'校园导览.png');return top

def main():
    m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'));v=np.load(ROOT/'tools/voxels.npy',mmap_mode='r')
    top=overview(v,m)
    if '--map-only' in sys.argv:return
    # Detail views finish first so they can be reviewed while the full campus meshes.
    hero=iso(v,m,'图书馆与启真湖.png',(640,925,1010,1275),2400)
    iso(v,m,'东大门与何尊广场.png',(945,910,1515,1230),2400)
    iso(v,m,'启翔湖与博物馆.png',(305,1650,990,2330),2600)
    iso(v,m,'校园鸟瞰.png',width=2800)
    top.crop((675,975,910,1210)).resize((64,64),Image.Resampling.LANCZOS).save(ROOT/'NWPU_Changan_26.2/icon.png')
    print('Previews complete',flush=True)

if __name__=='__main__':main()
