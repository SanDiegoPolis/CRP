"""Repeat server loading with empty-server pause disabled; preserve earlier evidence."""
import json,shutil,numpy as np
import validate
ROOT=validate.ROOT
m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'))
v=np.load(ROOT/'tools/voxels.npy',mmap_mode='r')
report=json.loads((ROOT/'validation_report.json').read_text(encoding='utf-8'))
assert report['nbt_round_trip']['result']=='PASS'
assert all(c['result']=='PASS' for c in report['walking_routes'])
if (ROOT/'validation/campus-26.2.log').exists():shutil.copyfile(ROOT/'validation/campus-26.2.log',ROOT/'validation/campus-26.2-paused.log')
report['official_server']=validate.server_check(v,m)
(ROOT/'validation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
validate.review_completed_run()
print('VALIDATION PASS',flush=True)
