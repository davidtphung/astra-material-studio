"""Run: blender --background --factory-startup --python tests/blender_smoke.py"""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import bpy
import astra
from astra import materials,scenes,textures,validation,compatibility
out=ROOT/'artifacts'
out.mkdir(exist_ok=True)
checks=[]
def check(condition,message):
    assert condition,message
    checks.append(message)
    print('PASS:',message,flush=True)
astra.register()
check(hasattr(bpy.types.Scene,'astra'),'Add-on registration')
original=bpy.context.scene
for kind in materials.PRESETS:
    m=materials.create_material(kind)
    check(m.node_tree.nodes['Surface output'].inputs['Surface'].is_linked,kind+' surface graph linked')
    check(m.node_tree.nodes['Surface controls'].inputs['Scale'].default_value==1,kind+' controls exposed')
    count=len(bpy.data.materials)
    check(materials.create_material(kind)==m and len(bpy.data.materials)==count,kind+' resource reuse')
cube=bpy.context.active_object
materials.assign(materials.create_material('metal'),[cube])
check(cube.active_material.get('astra_kind')=='metal','Material assignment')
fixture=out/'fixture'
fixture.mkdir(exist_ok=True)
for name in ['tile_basecolor','tile_normal','tile_roughness','tile_height','tile_ao']:
    img=bpy.data.images.new(name,width=8,height=8)
    img.generated_color=(.5,.5,1,1) if 'normal' in name else (.5,.5,.5,1)
    img.filepath_raw=str(fixture/(name+'.png'))
    img.file_format='PNG'
    img.save()
maps,messages=textures.detect(fixture)
check(len(maps)==5,'PBR filename detection')
pbr=textures.import_pbr(maps,channels={'roughness':'G'},directx=True,multiply_ao=True)
check(pbr.node_tree.nodes['Principled BSDF'].inputs['Normal'].is_linked,'Normal and bump map composition')
check(pbr.node_tree.nodes['Base Color'].image.colorspace_settings.name=='sRGB','Base color interpretation')
check(pbr.node_tree.nodes['Normal'].image.colorspace_settings.name=='Non-Color','Normal data interpretation')
check(pbr.node_tree.nodes.get('Invert green only') is not None,'DirectX green inversion')
check(pbr.node_tree.nodes.get('roughness packed channel') is not None,'Explicit packed channel')
# Missing paths and ambiguity are rejected, rather than silently choosing a file.
check(any('metallic' in m for m in messages),'Missing map reporting')
try:
    textures.import_pbr({'normal':str(fixture/'missing.png')})
    raise AssertionError('Missing image accepted')
except ValueError:
    checks.append('Missing image rejected')
settings={'schema':'astra.look.v1','material':'wood','color':'#885331','roughness':.48,'scale':1.7,'bump':.35,'lighting':'daylight','seed':42}
settings_file=out/'look.json'
settings_file.write_text(json.dumps(settings))
check(bpy.ops.astra.import_settings(filepath=str(settings_file))=={'FINISHED'},'Browser settings import')
check(abs(original.astra.scale-1.7)<.001 and original.astra.material=='wood','Imported settings applied')
old_engine=original.render.engine
scenes.quality(original,'final')
check(original.cycles.samples==256,'Final quality preset')
scenes.restore(original)
check(original.render.engine==old_engine,'Render settings restoration')
scene=scenes.demo()
check(original.name in bpy.data.scenes and cube.name in original.objects,'Demo preserves original scene')
count=len(scene.objects)
meshes=len(bpy.data.meshes)
scenes.demo()
check(len(scene.objects)==count and len(bpy.data.meshes)==meshes,'Repeated demo has no object or mesh duplication')
check(len([o for o in scene.objects if o.type=='LIGHT'])==3,'Editable studio lighting rig')
check(len([o for o in scene.objects if o.type=='CAMERA'])==2,'Overview and close-up cameras')
glass=scene.objects.get('ASTRA / Demo / glass')
check(any(m.type=='SOLIDIFY' and m.thickness>0 for m in glass.modifiers),'Glass has actual wall thickness')
check(not [m for m in validation.validate(scene) if m[0]=='ERROR'],'No scene validation errors')
check(scene.cycles.device=='CPU','Safe CPU render device')
# Remove temporary fixture datablocks before saving the downloadable scene.
for m in list(bpy.data.materials):
    if m.users==0:
        bpy.data.materials.remove(m)
for img in list(bpy.data.images):
    if img.users==0 and img.source=='FILE':
        bpy.data.images.remove(img)
file=ROOT/'web/downloads/astra-demo.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(file))
bpy.ops.wm.open_mainfile(filepath=str(file))
check(bpy.context.scene.name=='ASTRA Demonstration','Demo saved and reopened')
scene=bpy.context.scene
scene.render.resolution_x=800
scene.render.resolution_y=600
scene.cycles.samples=24
scene.render.filepath=str(out/'blender-preview.png')
bpy.ops.render.render(write_still=True)
check((out/'blender-preview.png').is_file(),'Actual Cycles smoke render')
report={'blender':bpy.app.version_string,'devices':compatibility.devices(),'checks':checks,'warnings':validation.validate(scene),'render':'800 × 600, 24 samples, Cycles CPU'}
astra.unregister()
check(not hasattr(bpy.types.Scene,'astra'),'Add-on unregistration')
astra.register()
astra.unregister()
check(not hasattr(bpy.types.Scene,'astra'),'Repeated register/unregister')
report['checks']=checks
(out/'validation.json').write_text(json.dumps(report,indent=2))
print('ASTRA_ALL_CHECKS_PASSED',len(checks),flush=True)
