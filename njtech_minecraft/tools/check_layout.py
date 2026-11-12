from crp_runtime import java_executable, font_path
import json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import build_njtech as b
from navigation import navigability
b.catalog()
root=b.ROOT; canvas=Image.open(root/'research/map-reference.png').convert('RGB')
dr=ImageDraw.Draw(canvas);font=ImageFont.truetype(font_path(),9)
occupied=np.zeros((b.D,b.W),dtype=np.uint16);overlaps=[]
for i,c in enumerate(b.CATALOG,1):
    cx,cz=b.xy(c['u'],c['v']);theta=math.radians(c['angle']);cs,sn=math.cos(theta),math.sin(theta)
    pts=[(cx+x*cs-z*sn,cz+x*sn+z*cs) for x,z in [(-c['w']/2,-c['d']/2),(c['w']/2,-c['d']/2),(c['w']/2,c['d']/2),(-c['w']/2,c['d']/2)]]
    x0=max(0,int(min(p[0] for p in pts)));x1=min(b.W,int(max(p[0] for p in pts))+1)
    z0=max(0,int(min(p[1] for p in pts)));z1=min(b.D,int(max(p[1] for p in pts))+1)
    im=Image.new('L',(x1-x0,z1-z0));ImageDraw.Draw(im).polygon([(x-x0,z-z0) for x,z in pts],fill=255);mask=np.asarray(im)>0
    occ=occupied[z0:z1,x0:x1];ids,counts=np.unique(occ[mask],return_counts=True)
    for idx,count in zip(ids,counts):
        if idx>0 and count>80:overlaps.append([b.CATALOG[idx-1]['name'],c['name'],int(count)])
    occ[mask]=i
    q=[(135+(x-110)/1.65,270+(z-75)/1.75) for x,z in pts]
    dr.polygon(q,outline='red',width=1);dr.text((c['u'],c['v']),str(i),font=font,fill='black')
canvas.save(root/'research/layout-audit.png')
(root/'tools/layout-overlaps.json').write_text(json.dumps(overlaps,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(overlaps,ensure_ascii=False),flush=True)
for c in b.CATALOG:
    if c['targets']:b.place(c)
print(json.dumps(navigability(None,{'navigation_checks':b.CHECKS,'palette':b.PAL}),ensure_ascii=False,indent=2),flush=True)
