from pathlib import Path
import json,hashlib,ast
ROOT=Path(__file__).resolve().parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cases=[
 ('B001','library.png','图书馆与启真湖.png',[640,925,1010,1275],2400,
  '弧形较窄主楼、低层柱廊、水平玻璃分带与采光体可辨认，旧版过厚屋面已减小。',
  '尺寸、弧率、背面及室内为估算；不是按照片透视逐像素配准。'),
 ('B002','qixiang.png','启翔楼与启翔湖.png',[440,1670,970,2050],2500,
  '较高四角、低檐门厅、深色挑檐、院落与坡顶层次可辨认。',
  '门窗节奏和角楼比例为近似，未核对每一侧实测尺寸。'),
 ('B019','arena.png','翱翔体育馆.png',[1070,300,1380,615],2300,
  '双馆的高低体量、圆形上窗和细屋顶构架已区分，球场入口保持可通行。',
  '圆窗为体素近似，主入口台阶/台地高差采用平接适配，未按实测恢复。'),
 ('B024','east-gate.png','东门与何尊广场.png',[945,910,1515,1230],2400,
  '成束柱组、連梁、浅钵柱头与连续校名墙可辨认；门区开放通道可通过。',
  '附属侧门和精确字形未逐项测量复刻。'),
 ('B003','aircraft.png','博物馆航空展区.png',[395,1955,790,2330],2300,
  '低层展馆与航空展示前庭的主要关系保留，模型按静态展品制作。',
  '展机为简化类型，不作为具体机型、数量与陈列朝向的精确记录。')]
rows=[]
binding=ROOT/'planning/final-region-binding.json'
for obj,src,out,crop,width,observation,gap in cases:
    rows.append({'object_id':obj,'source':'research/'+src,'source_sha256':sha(ROOT/'research'/src),
      'render':out,'render_sha256':sha(ROOT/out),'target_world_binding_sha256':sha(binding),
      'camera':{'projection':'orthographic SE','world_crop_xz':crop,'width':width,'vertical_projection_factor':1.1},
      'observations':observation,'unverified':gap,'decision':'partial; identified exterior features reviewed'})
review={'status':'PARTIAL','delivery_decision':'READY_WITH_DECLARED_APPROXIMATIONS','reviewed_at':'2026-09-24',
 'method':'Model-visible inspection of final voxel renderings, official photographs, source map and fixed-view before/after comparison.',
 'same_camera_before_after':'重制前后对比.png','source_photo_camera_alignment':'Qualitative feature comparison, not a calibrated perspective fit.',
 'rows':rows,'client_runtime_visual_review':'NOT_RUN','night_and_performance':'NOT_RUN',
 'limits':'Ordinary facades, interiors, terrain and some entrance grading remain inferred; no realism percentage claimed.'}
(ROOT/'planning/visual-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
for p in (ROOT/'tools').glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
print('Visual observations recorded for',len(rows),'landmark views; approximations retained explicitly.')
