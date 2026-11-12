from pathlib import Path
import json,numpy as np
import validate
from check_exterior import check
ROOT=Path(__file__).resolve().parent.parent
m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'))
report=json.loads((ROOT/'validation_report.json').read_text(encoding='utf-8'))
assert report['official_server']['result']=='PASS' and report['official_server']['clean_shutdown']
assert all(c['result']=='PASS' for c in report['walking_routes'])
v=np.load(ROOT/'tools/voxels.npy',mmap_mode='r')
report['final_saved_world_readback']=validate.audit_nbt(v,m,cache=True)
final=np.load(ROOT/'tools/final_voxels.npy',mmap_mode='r')
exterior=check(final,m);assert exterior['result']=='PASS',exterior
report['exterior_paved_routes']={k:v for k,v in exterior.items() if k!='routes'}
report['building_overlap_review']=json.loads((ROOT/'planning/building-collision-review.json').read_text(encoding='utf-8'))
(ROOT/'planning/exterior-route-validation.json').write_text(json.dumps(exterior,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'validation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('FINAL WORLD VALIDATION PASS',json.dumps(report['final_saved_world_readback']),flush=True)
