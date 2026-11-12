from pathlib import Path
import json
from html.parser import HTMLParser
import pdfplumber
ROOT=Path(__file__).resolve().parent.parent
class Images(HTMLParser):
    def __init__(self):super().__init__();self.images=[]
    def handle_starttag(self,tag,attrs):
        if tag=='img':self.images.append(dict(attrs))
s=Images();s.feed((ROOT/'research/photos.html').read_text(encoding='utf-8'))
items=[]
for img in s.images:
    src=img.get('src','');alt=img.get('alt','')
    if 'wps_doc_' in alt:
        num=int(alt.split('_')[-1].split('.')[0])
        if num>=76:items.append({'number':num,'url':'https://www.nwpu.edu.cn'+src if src.startswith('/') else src,'alt':alt})
(ROOT/'research/photos-index.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
with pdfplumber.open(ROOT/'research/official-map.pdf') as doc:
    for i,p in enumerate(doc.pages):
        t=p.extract_text() or ''
        print(i+1,p.width,p.height,len(p.images),len(p.curves),t[:85].replace('\n',' '),flush=True)
        if 'MAP OF NPU' in t or '平面' in t:
            (ROOT/f'research/map-page-{i+1}.txt').write_text(t,encoding='utf-8')
