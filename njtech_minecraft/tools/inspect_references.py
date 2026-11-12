from pathlib import Path
from pypdf import PdfReader
from html.parser import HTMLParser
from urllib.parse import urljoin
import json
ROOT=Path(__file__).resolve().parent.parent
class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='img' and '__local' in a.get('src',''): print(urljoin('https://ngsj.njtech.edu.cn/',a['src']))
Links().feed((ROOT/'research/library.html').read_text(encoding='utf-8'))
r=PdfReader(ROOT/'research/official-guide.pdf')
for i,p in enumerate(r.pages):
    t=p.extract_text() or ''
    if '功能导览图' in t or '总平面' in t:
        print('MAP PAGE',i+1,t[:350])
        (ROOT/f'research/page-{i+1}.txt').write_text(t,encoding='utf-8')
