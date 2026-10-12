"""Verify shared environment, persistence, settings import, preservation and render."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import bpy
from mathutils import Vector
import astra
from astra.environment import create_rooftop,AXIS
from astra.world_data import build_world

out=ROOT/'artifacts'
out.mkdir(exist_ok=True)
checks=[]
def check(condition,message):
    assert condition,message
    checks.append(message)
    print('PASS:',message,flush=True)
astra.register()
original=bpy.context.scene
original_cube=original.objects.get('Cube')
world=build_world()
check(world==build_world(),'Deterministic world definition')
check(len(world['objects'])>2000,'Complete workshop and surrounding neighbourhood')
check(json.loads((ROOT/'web/world.json').read_text())==world,'Browser and Blender share exact scene definition')
settings={'schema':'astra.look.v1','material':'metal','color':'#b7bbb5','roughness':.32,'scale':1,'bump':.3,'seed':42,'lighting':'daylight','environment':'rooftop','view':'bench','shape':'sculpture','wetness':.55,'haze':.3}
settings_file=out/'rooftop-look.json'
settings_file.write_text(json.dumps(settings))
check(bpy.ops.astra.import_settings(filepath=str(settings_file))=={'FINISHED'},'Environment settings import')
check(abs(original.astra.wetness-.55)<.0001 and original.astra.view=='bench','Environment parameters restored')
check(bpy.ops.astra.generate_rooftop()=={'FINISHED'},'Rooftop UI operator executes')
scene=bpy.context.scene
check(original_cube in list(original.objects),'Original user scene preserved')
check(scene.unit_settings.scale_length==1 and scene['astra_world_units']=='metres','Metre-scale world')
hero=next(o for o in scene.objects if o.get('astra_hero'))
check(hero.active_material.get('astra_kind')=='metal','Hero material applied')
minimum=min((hero.matrix_world @ Vector(c)).z for c in hero.bound_box)
check(abs(minimum-.99)<.003,'Hero contacts the 0.99 metre support exactly')
check(len([o for o in scene.objects if o.type=='CAMERA'])==3,'Three contextual camera presets')
check(len([o for o in scene.objects if o.type=='LIGHT'])==3,'Motivated sky, task lamp and sign lights')
check(any('Atmospheric' in o.name or 'atmospheric' in o.name for o in scene.objects),'Bounded atmospheric haze')
col=next(c for c in scene.collection.children if c.get('astra_rooftop_collection'))
unowned=bpy.data.objects.new('User object — retain me',None)
col.objects.link(unowned)
settings=json.loads(scene['astra_world_settings'])
counts={key:len(getattr(bpy.data,key)) for key in ['objects','meshes','materials','lights','cameras','curves']}
scene=create_rooftop(settings)
check(unowned in list(scene.objects),'User objects inside generated collection preserved')
after={key:len(getattr(bpy.data,key)) for key in counts}
check(counts==after,f'Regeneration keeps all datablock counts stable: {counts} → {after}')
# Every base mesh is shared across repeated building instances.
check(len({o.data for o in scene.objects if o.type=='MESH'})<65,'Efficient shared geometry')
bpy.data.objects.remove(unowned,do_unlink=True)
path=ROOT/'web/downloads/astra-rooftop.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path))
bpy.ops.wm.open_mainfile(filepath=str(path))
scene=bpy.context.scene
check(scene.get('astra_rooftop_scene'),'Rooftop saved and reopened')
check(scene.camera is not None and scene.camera.type=='CAMERA','Active contextual camera persists')
scene.render.resolution_x=1200
scene.render.resolution_y=900
scene.cycles.samples=40
scene.render.filepath=str(out/'rooftop-preview.png')
bpy.ops.render.render(write_still=True)
check((out/'rooftop-preview.png').is_file(),'Actual Cycles rooftop render')
astra.unregister()
check(not hasattr(bpy.types.Scene,'astra'),'Clean add-on unregistration')
(out/'rooftop-validation.json').write_text(json.dumps({'blender':bpy.app.version_string,'checks':checks,'objects':len(world['objects']),'render':'1200 x 900, Cycles CPU, 40 samples','scope':'Fictional procedural rooftop. Desktop/mobile browser previews are approximations.'},indent=2))
print('ASTRA_ROOFTOP_CHECKS_PASSED',len(checks),flush=True)
