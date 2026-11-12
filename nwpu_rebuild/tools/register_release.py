from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser();parser.add_argument('--skill',type=Path,required=True);parser.add_argument('--installed',type=Path)
args=parser.parse_args();sys.path.insert(0,str(args.skill/'scripts'))
from audit_release import audit,digest
from project_state import save,attach,record,status
world=ROOT/'NWPU_Changan_Rebuild_26.2'
delivery=json.loads((ROOT/'delivery_manifest.json').read_text(encoding='utf-8'))
result=audit(ROOT,world,[Path(delivery['archive'])]);assert not result['errors'],result
report=ROOT/'planning/file-audit.json';report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
state=ROOT/'planning/project-state.json'
if not state.exists():
    save(state,{'schema_version':1,'project':'NWPU Changan reconstruction 20260924','coordinate_version':'nwpu-illustrated-map-2025-north-up-v1','scope':'Whole campus approximate exterior, designed key interiors and paved routes','artifacts':{},'checks':{},'backlog':[]})
for name,path in [('world',world),('release_zip',Path(delivery['archive'])),('release_manifest',ROOT/'manifest.json')]:attach(state,name,path)
record(state,'release-file-identity','files','pass',['world','release_zip','release_manifest'],report)
record(state,'world-readback-and-overlap','geometry','pass',['world'],ROOT/'validation_report.json')
record(state,'paved-exterior-routes','routes','pass',['world'],ROOT/'planning/exterior-route-validation.json')
record(state,'photographic-feature-review','visual','partial',['world'],ROOT/'planning/visual-review.json')
runtime=ROOT/'planning/runtime-scope.json'
runtime.write_text(json.dumps({'status':'partial','official_server':'PASS','client_visuals':'NOT_RUN','night_and_performance':'NOT_RUN','official_validation_report_sha256':digest(ROOT/'validation_report.json')}),encoding='utf-8')
record(state,'runtime-scope','game','partial',['world'],runtime)
if args.installed:
    sync=json.loads((ROOT/'game_sync_manifest.json').read_text(encoding='utf-8-sig'))
    assert args.installed.resolve()==Path(sync['target']).resolve()
    attach(state,'installed',args.installed)
    record(state,'installed-copy-identity','files','pass',['installed'],ROOT/'game_sync_manifest.json')
out=status(state)
(ROOT/'planning/status.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'audit':result['status'],'verified_files':result['verified_components'],'audit_gaps':result['gaps'],'artifacts':out['artifacts'],'limits':out['missing_current_pass_evidence']},ensure_ascii=False),flush=True)
