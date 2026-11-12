"""Portable regression fixtures; never writes to an actual campus release."""
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
import nbtlib
from schematic_io import write_schematic, read_schematic, decode_varints, AIR
from campus_build import build
from audit_release import audit, digest
from project_state import save, attach, record, status


class Toolkit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.release = self.root/'source'; self.release.mkdir()
        # External nbtlib writer, air deliberately at index 1, negative XYZ offset.
        nbtlib.File({'Version': nbtlib.Int(2), 'DataVersion': nbtlib.Int(4671),
          'Width': nbtlib.Short(2), 'Height': nbtlib.Short(1), 'Length': nbtlib.Short(1),
          'Offset': nbtlib.IntArray([-3,-2,-1]),
          'Palette': nbtlib.Compound({'minecraft:stone': nbtlib.Int(0), AIR: nbtlib.Int(1)}),
          'BlockData': nbtlib.ByteArray([0,1])}, root_name='Schematic').save(self.release/'a.schem',gzipped=True)
        self.row = {'file':'a.schem','sha256':digest(self.release/'a.schem'),
                    'offset_xyz':[-3,-2,-1],'size_xyz':[2,1,1],'non_air_blocks':1}
        self.manifest([self.row])
    def tearDown(self): self.tmp.cleanup()
    def manifest(self, rows):
        (self.release/'manifest.json').write_text(json.dumps({'coordinate_version':'fixture-v1','files':rows}))
    def patch(self, name='p', after=1, before=0):
        p=self.root/(name+'.npz')
        np.savez(p,xyz=np.array([[-3,-2,-1]]),before=np.array([before]),after=np.array([after]),
                 palette=np.array(['minecraft:stone',AIR,'minecraft:dirt']))
        d=self.root/(name+'.json');d.write_text(json.dumps({'npz':p.name,'sha256':digest(p),
          'baseline_manifest_sha256':digest(self.release/'manifest.json'),'coordinate_version':'fixture-v1'}))
        return d
    def test_external_input_air_offset_and_anchor(self):
        build(self.release,self.root/'out','fixture-v1',anchor=(-3,-2,-1))
        a,o,p,d=read_schematic(self.root/'out/campus-complete.schem')
        self.assertEqual(o,[0,0,0]);self.assertEqual([p[i] for i in a.ravel()],['minecraft:stone',AIR])
        self.assertFalse(audit(self.root/'out')['errors'])
    def test_delete_is_preserved(self):
        r=build(self.release,self.root/'out','fixture-v1',[self.patch()])
        a,_,_,_=read_schematic(self.root/'out/campus-complete.schem')
        self.assertEqual(int(a.sum()),0);self.assertEqual(r['changed_positions'],1)
    def test_identical_patches_deduplicated(self):
        r=build(self.release,self.root/'out','fixture-v1',[self.patch('p'),self.patch('q')])
        self.assertEqual(r['duplicate_identical_patch_positions'],1)
    def test_conflicting_patches_rejected(self):
        with self.assertRaisesRegex(ValueError,'Conflicting'):
            build(self.release,self.root/'out','fixture-v1',[self.patch('p'),self.patch('q',2)])
        self.assertFalse((self.root/'out').exists())
    def test_stale_before_rejected(self):
        with self.assertRaisesRegex(ValueError,'before differs'):
            build(self.release,self.root/'out','fixture-v1',[self.patch(before=1)])
    def test_changed_source_rejected(self):
        (self.release/'a.schem').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'hash mismatch'): build(self.release,self.root/'out','fixture-v1')
    def test_coordinate_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError,'coordinate_version'): build(self.release,self.root/'out','wrong')
    def test_overlap_rejected(self):
        (self.release/'b.schem').write_bytes((self.release/'a.schem').read_bytes())
        self.manifest([self.row,dict(self.row,file='b.schem')])
        with self.assertRaisesRegex(ValueError,'Overlapping'): build(self.release,self.root/'out','fixture-v1')
    def test_budget_rejected(self):
        with self.assertRaisesRegex(ValueError,'volume'): build(self.release,self.root/'out','fixture-v1',max_voxels=1)
    def test_existing_output_untouched(self):
        p=self.root/'out';p.mkdir();(p/'keep').write_text('keep')
        with self.assertRaises(FileExistsError): build(self.release,p,'fixture-v1')
        self.assertEqual((p/'keep').read_text(),'keep')
    def test_multibyte_palette(self):
        # Exercises both 2-byte and 3-byte indices.
        palette=[f'minecraft:test_{i}' for i in range(16385)]
        a=np.array([[[0,127,128,16383,16384]]],np.uint16);p=self.root/'large.schem'
        write_schematic(p,a,[0,0,0],palette,4671)
        b,_,_,_=read_schematic(p);self.assertTrue(np.array_equal(a,b))
        raw=nbtlib.load(p)['BlockData'].view(np.uint8).tolist()
        self.assertEqual(raw,[0,127,128,1,255,127,128,128,1])
    def test_truncated_varint(self):
        with self.assertRaises(ValueError):decode_varints(np.array([-128],np.int8),1)
    def test_entities_rejected(self):
        p=self.release/'a.schem';n=nbtlib.load(p);n['Entities']=nbtlib.List[nbtlib.Compound]([nbtlib.Compound()]);n.save(p,gzipped=True)
        with self.assertRaisesRegex(ValueError,'Entities'):read_schematic(p)
    def test_ledger_detects_artifact_and_report_changes(self):
        f=self.root/'state.json';r=self.root/'report.json';r.write_text('{}')
        save(f,{'project':'fixture','coordinate_version':'v1','scope':'exterior','artifacts':{},'checks':{}})
        attach(f,'release',self.release);record(f,'check','files','pass',['release'],r)
        self.assertEqual(status(f)['checks']['check']['evidence'],'CURRENT')
        self.assertIn('game',status(f)['missing_current_pass_evidence'])
        r.write_text('{"changed":true}');self.assertEqual(status(f)['checks']['check']['evidence'],'STALE')
        r.write_text('{}');(self.release/'extra').write_text('change')
        self.assertEqual(status(f)['artifacts']['release'],'CHANGED')
        self.assertEqual(status(f)['checks']['check']['evidence'],'STALE')
    def test_report_hash_checked(self):
        build(self.release,self.root/'out','fixture-v1')
        (self.root/'out/build-validation.json').write_text('{}')
        self.assertTrue(audit(self.root/'out')['errors'])

    def test_utf8_nested_component_and_bom_manifest(self):
        folder=self.release/'教学楼';folder.mkdir()
        (self.release/'a.schem').rename(folder/'图书馆.schem')
        row=dict(self.row,file='教学楼/图书馆.schem')
        version='主校区-底图-v1'
        data={'coordinate_version':version,'files':[row]}
        (self.release/'manifest.json').write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8-sig')
        checks=audit(self.release)
        self.assertFalse(checks['errors'])
        self.assertFalse(any(isinstance(g,dict) and 'unlisted_schem_files_not_audited' in g for g in checks['gaps']))
        output=self.root/'主校区 导出'
        build(self.release,output,version)
        saved=json.loads((output/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(saved['coordinate_version'],version)
        self.assertFalse(audit(output)['errors'])

    def test_missing_coordinate_version_rejected(self):
        (self.release/'manifest.json').write_text(json.dumps({'files':[self.row]}),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'coordinate_version'):
            build(self.release,self.root/'out','unverified-assumption')
        self.assertFalse((self.root/'out').exists())

    def test_utf8_ledger(self):
        state=self.root/'校区 状态.json';report=self.root/'入口检查.json'
        report.write_text('{"status":"PASS"}',encoding='utf-8')
        save(state,{'project':'示例高校 🏫','coordinate_version':'校区-v1','scope':'外观与大厅','artifacts':{},'checks':{}})
        attach(state,'正式组件',self.release)
        record(state,'文件检查','files','pass',['正式组件'],report)
        self.assertEqual(json.loads(state.read_text(encoding='utf-8'))['project'],'示例高校 🏫')
        self.assertEqual(status(state)['checks']['文件检查']['evidence'],'CURRENT')

    def test_world_layouts_are_file_checks_only(self):
        # Deliberately not valid NBT/Anvil: directory auditing must not claim loading.
        layouts=['region','DIM-1/region','dimensions/minecraft/overworld/region','dimensions/campus/custom/wing/region']
        for index,layout in enumerate(layouts):
            with self.subTest(layout=layout):
                world=self.root/f'world-{index}';folder=world/layout;folder.mkdir(parents=True)
                (world/'level.dat').write_bytes(b'fixture')
                (folder/'r.0.0.mca').write_bytes(b'fixture')
                result=audit(self.release,world=world)
                self.assertFalse(result['errors'])
                self.assertEqual(result['world_files']['dimension_region_files'],{layout:1})
                self.assertFalse(result['world_files']['nbt_or_runtime_validated'])

    def test_mixed_overworld_layout_flagged(self):
        world=self.root/'mixed';world.mkdir();(world/'level.dat').write_bytes(b'fixture')
        for layout in ['region','dimensions/minecraft/overworld/region']:
            folder=world/layout;folder.mkdir(parents=True);(folder/'r.0.0.mca').write_bytes(b'fixture')
        result=audit(self.release,world=world)
        self.assertTrue(any('Both legacy and namespaced Overworld' in str(g) for g in result['gaps']))

    def test_bedrock_and_entities_do_not_masquerade_as_java_terrain(self):
        world=self.root/'other';(world/'db').mkdir(parents=True)
        (world/'level.dat').write_bytes(b'fixture');(world/'entities').mkdir()
        (world/'entities/r.0.0.mca').write_bytes(b'fixture')
        result=audit(self.release,world=world)
        self.assertTrue(result['errors'])
        self.assertEqual(result['world_files']['region_files'],0)
        self.assertTrue(any('Bedrock' in str(g) for g in result['gaps']))


if __name__=='__main__': unittest.main(verbosity=2)
