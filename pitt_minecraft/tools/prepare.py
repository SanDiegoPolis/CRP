"""Extract clean roads/building outlines from Pitt's official vector campus map."""
from pathlib import Path
import json, math
from PIL import Image,ImageDraw
import pdfplumber

ROOT=Path(__file__).resolve().parent.parent
old=ROOT.parent/'ccucm_minecraft/tools/build_campus.py'
text=old.read_text(encoding='utf-8').split('def roadx(')[0]
text=text.replace("WORLD=ROOT/'CCUCM_Jingyue_26.2'","WORLD=ROOT/'Pitt_Oakland_26.2'")
text=text.replace('W,Z,H=1152,896,96','W,Z,H=1,1,1').replace('dtype=np.uint16','dtype=np.uint8')
(ROOT/'tools/geometry.py').write_text(text,encoding='utf-8')

def xy(p):return (p[0]*2.299-16,p[1]*2.299-64)
def points(path):
    result=[];last=None
    for op in path:
        if op[0] in ('m','l'):
            last=op[1];result.append(xy(last))
        elif op[0]=='c':
            p0=last;p1,p2,p3=op[1:]
            for j in range(1,17):
                t=j/16;u=1-t
                result.append(xy(tuple(u**3*p0[k]+3*u*u*t*p1[k]+3*u*t*t*p2[k]+t**3*p3[k] for k in (0,1))))
            last=p3
        elif op[0]=='h' and result:result.append(result[0])
    return result

page=pdfplumber.open(ROOT/'research/Pitt_Campus_Map.pdf').pages[0]
roads=Image.new('L',(1792,1280));dr=ImageDraw.Draw(roads);shapes=[]
for i,c in enumerate(page.curves+page.rects):
    color=c.get('non_stroking_color');stroke=c.get('stroking_color')
    pts=points(c['path']) if 'path' in c else [xy(p) for p in c.get('pts',[])]
    if len(pts)<2:continue
    if c['stroke'] and stroke==(0.,0.,0.,.2):dr.line(pts,fill=255,width=max(1,round(c['linewidth']*2.299)),joint='curve')
    if c['fill'] and color==(0.,0.,0.,.2):dr.polygon(pts,fill=255)
    if c['fill'] and color in [(0.,0.,0.,1.),(0.,0.,0.,.5)]:
        area=abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:]+pts[:1])))/2
        if 130<area<42000 and c['width']<200 and c['height']<200:
            shapes.append({'index':i,'points':pts,'area':area,'university':color[-1]==1.,'center':xy(((c['x0']+c['x1'])/2,(c['top']+c['bottom'])/2))})
roads.save(ROOT/'research/roads.png')
(ROOT/'research/building_footprints.json').write_text(json.dumps(shapes),encoding='utf-8')
print('Extracted',len(shapes),'building polygons and the campus street network')
