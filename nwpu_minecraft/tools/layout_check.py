import build_nwpu as b
import json
b.buildings()
out=[]
for i,a in enumerate(b.BUILDINGS):
    for c in b.BUILDINGS[i+1:]:
        ox=(a['depth']+c['depth'])/2-abs(a['x']-c['x']);oz=(a['width']+c['width'])/2-abs(a['z']-c['z'])
        if ox>4 and oz>4:out.append({'a':a['name'],'b':c['name'],'overlap':[round(ox),round(oz)]})
(b.ROOT/'layout-overlaps.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('OVERLAPS',json.dumps(out,ensure_ascii=False),flush=True)
