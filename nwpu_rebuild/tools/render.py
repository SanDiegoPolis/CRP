from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
from voxel_render import iso,font
ROOT=Path(__file__).resolve().parent.parent
OLD=ROOT.parent/'nwpu_minecraft'

def guide(v,m):
    h,d,w=v.shape;heights=h-1-np.argmax((v!=0)[::-1],axis=0)
    ids=v[heights,np.arange(d)[:,None],np.arange(w)[None,:]]
    rgb=np.array(m['colors'],dtype='uint8')[ids].astype(float);shade=np.zeros((d,w),bool)
    for s in range(1,30):shade[s:,s:]|=heights[:-s,:-s]-s*1.6>heights[s:,s:]+1
    rgb[shade]*=.73;top=Image.fromarray(rgb.astype('uint8'));scale=.64
    im=Image.new('RGB',(1920,1910),'#182d31');im.paste(top.resize((round(w*scale),round(d*scale))),(35,160));dr=ImageDraw.Draw(im)
    dr.text((40,25),'西北工业大学 · 长安校区重制版',font=font(41),fill='#f1e8d4')
    dr.text((43,89),'CAMPUS RECONSTRUCTION PROJECT  /  JAVA 26.2  /  约 1.1 : 1',font=font(21),fill='#a4c7bc')
    for i,lm in enumerate(m['landmarks'],1):
        x,z=round(35+lm['x']*scale),round(160+lm['z']*scale)
        dr.ellipse((x-12,z-12,x+12,z+12),fill='#182d31',outline='#efd07b',width=2)
        label=str(i);bb=dr.textbbox((0,0),label,font=font(14));dr.text((x-(bb[2]-bb[0])/2,z-10),label,font=font(14),fill='white')
        col=(i-1)//22;row=(i-1)%22;tx=1055+col*420;ty=233+row*60
        dr.text((tx,ty),f'{i:02d} '+lm['name'],font=font(18),fill='#f1e8d4')
        dr.text((tx+28,ty+28),lm['label'][:21],font=font(13),fill='#a4c7bc')
    dr.text((1060,166),'北 N ↑',font=font(26),fill='#efd07b')
    dr.text((1060,1680),'东门 → 何尊广场 → 图书馆 → 教学区',font=font(20),fill='#efd07b')
    dr.text((1060,1720),'→ 生活区 → 启翔楼 → 博物馆',font=font(20),fill='#a4c7bc')
    dr.text((43,1831),'依据官方示意地图与实景近似重建；步道连接和未知室内包含设计补全。',font=font(22),fill='#a4c7bc')
    dr.text((43,1869),'预览来源：独立回读的最终存档方块。',font=font(17),fill='#a4c7bc')
    im.save(ROOT/'校园导览.png')
    top.crop((688,996,899,1207)).resize((64,64),Image.Resampling.LANCZOS).save(ROOT/'NWPU_Changan_Rebuild_26.2/icon.png')

def comparisons():
    # Same geographic crop/projection, showing the actual previous and current models.
    before=Image.open(OLD/'图书馆与启真湖.png').convert('RGB')
    after=Image.open(ROOT/'图书馆与启真湖.png').convert('RGB')
    canvas=Image.new('RGB',(2400,860),'#182d31');dr=ImageDraw.Draw(canvas)
    dr.text((38,22),'图书馆重制 · 相同区域与投影视角',font=font(34),fill='#f1e8d4')
    for im,x,label in [(before,20,'原版：厚屋面与整块体量'),(after,1210,'重制：窄弧形主楼、水平遮阳线与前庭')]:
        im.thumbnail((1165,680));canvas.paste(im,(x,145));dr.text((x+15,95),label,font=font(24),fill='#a4c7bc')
    dr.text((38,813),'这是模型版本对照，不是测量意义上的实景相似度评分。',font=font(21),fill='#a4c7bc')
    canvas.save(ROOT/'重制前后对比.png')
    refs=[('library.png','图书馆与启真湖.png','图书馆：弧形体量 / 低层侧翼 / 细水平线'),('qixiang.png','启翔楼与启翔湖.png','启翔楼：分层屋顶 / 深色檐口 / 中央庭院'),('arena.png','翱翔体育馆.png','体育馆：双馆 / 圆窗 / 屋顶构架'),('east-gate.png','东门与何尊广场.png','东门：柱束 / 连梁 / 浅钵柱头')]
    evidence=Image.new('RGB',(1800,1600),'#182d31');ed=ImageDraw.Draw(evidence)
    for i,(source,model,title) in enumerate(refs):
        y=i*395;ed.text((25,y+12),title,font=font(25),fill='#f1e8d4')
        for p,x in [(ROOT/'research'/source,25),(ROOT/model,900)]:
            im=Image.open(p).convert('RGB');im.thumbnail((850,325));evidence.paste(im,(x,y+60))
    evidence.save(ROOT/'实景与模型核对.png')

if __name__=='__main__':
    m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'))
    pre='--preflight' in sys.argv
    v=np.load(ROOT/('tools/voxels.npy' if pre else 'tools/final_voxels.npy'),mmap_mode='r')
    if pre:
        iso(v,m,'图书馆检查.png',(640,925,1010,1275),2400)
        iso(v,m,'启翔楼检查.png',(640,1730,885,1985),2000)
    else:
        binding=json.loads((ROOT/'planning/final-region-binding.json').read_text())
        for name,digest in binding['regions'].items():assert hashlib.sha256((ROOT/binding['world']/name).read_bytes()).hexdigest()==digest
        guide(v,m)
        iso(v,m,'图书馆与启真湖.png',(640,925,1010,1275),2400)
        iso(v,m,'启翔楼与启翔湖.png',(440,1670,970,2050),2500)
        iso(v,m,'翱翔体育馆.png',(1070,300,1380,615),2300)
        iso(v,m,'东门与何尊广场.png',(945,910,1515,1230),2400)
        iso(v,m,'博物馆航空展区.png',(395,1955,790,2330),2300)
        iso(v,m,'校园鸟瞰.png',width=2800)
        comparisons()
    print('Preview rendering complete',flush=True)
