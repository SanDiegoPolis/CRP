"""Platform-specific executables/fonts, with optional explicit environment overrides."""
from pathlib import Path
import os,shutil
def java_executable():
    value=os.environ.get('CRP_JAVA') or shutil.which('java')
    if value:return value
    root=Path(__file__).resolve().parents[2]
    for name in ('java','java.exe'):
        for p in (root/'ccucm_minecraft/tools/java25').glob('*/bin/'+name):return str(p)
    raise RuntimeError('Install Java 25 or set CRP_JAVA to its executable.')
def font_path():
    values=[os.environ.get('CRP_FONT'),'C:/Windows/Fonts/simhei.ttf','C:/Windows/Fonts/msyh.ttc',
      '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc','/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
      '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    for value in values:
        if value and Path(value).is_file():return value
    raise RuntimeError('Install a CJK font or set CRP_FONT to a .ttf/.ttc font.')
