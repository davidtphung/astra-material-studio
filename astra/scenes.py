import math
import bpy
from mathutils import Vector
from .materials import create_material, PRESETS

LIGHTS = {
    'studio': [((-3,-4,5), 700, 4, (1,.9,.76)),((4,-1,3),250,3,(.78,.87,1)),((1,4,4),600,2,(1,1,1))],
    'daylight': [((-3,-3,6),1100,6,(1,.95,.85)),((3,1,4),400,5,(.78,.88,1))],
    'noir': [((-3,-3,5),850,2,(1,.88,.7)),((3,4,3),130,2,(.6,.72,1))],
    'neon': [((-3,-2,4),600,2,(1,.18,.5)),((3,1,3),800,2,(.15,1,.7))],
}

def collection(scene):
    name = 'ASTRA / '+scene.name
    col = bpy.data.collections.get(name)
    if col is None or not col.get('astra'):
        col = bpy.data.collections.new(name)
        col['astra'] = True
        scene.collection.children.link(col)
    elif col.name not in scene.collection.children:
        scene.collection.children.link(col)
    return col

def owned_object(col, name, kind, datablocks):
    existing = col.objects.get(name)
    if existing and existing.get('astra'):
        return existing
    data = datablocks.new(name,kind) if kind else datablocks.new(name)
    obj = bpy.data.objects.new(name,data)
    obj['astra'] = True
    col.objects.link(obj)
    return obj

def aim(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def lighting(scene, preset='studio', target=(0,0,.7), size=1):
    col = collection(scene)
    # Each explicitly applied rig updates only ASTRA-owned lights in this scene.
    for obj in list(col.objects):
        if obj.type == 'LIGHT' and obj.get('astra'):
            data = obj.data
            bpy.data.objects.remove(obj,do_unlink=True)
            if data.users == 0:
                bpy.data.lights.remove(data)
    for i,(position,power,area,color) in enumerate(LIGHTS[preset]):
        lamp = owned_object(col,f'ASTRA / {scene.name} / Light {i}','AREA',bpy.data.lights)
        lamp.location = Vector(target)+Vector(position)*size
        lamp.data.energy = power*size*size
        lamp.data.shape = 'DISK'
        lamp.data.size = area*size
        lamp.data.color = color
        aim(lamp,target)
    return col

def bounds(objects):
    corners = [o.matrix_world @ Vector(c) for o in objects if o.type == 'MESH' for c in o.bound_box]
    if not corners:
        return Vector((0,0,.6)),1
    minimum = Vector([min(c[i] for c in corners) for i in range(3)])
    maximum = Vector([max(c[i] for c in corners) for i in range(3)])
    return (minimum+maximum)*.5,max((maximum-minimum).length*.5,.1)

def camera(scene, objects=(), preset='hero'):
    col = collection(scene)
    cam = owned_object(col,f'ASTRA / {scene.name} / Camera / {preset}',None,bpy.data.cameras)
    center, radius = bounds(objects)
    cam.data.lens = {'close':85,'hero':55,'medium':45,'wide':32}[preset]
    # Fit a bounding sphere to the narrow field of view, including portrait aspects.
    aspect = scene.render.resolution_x/scene.render.resolution_y
    fov = 2*math.atan((cam.data.sensor_width/min(max(aspect,1),10)) / (2*cam.data.lens))
    distance = radius/max(math.sin(fov*.5),.05)*1.2
    cam.location = center+Vector((1,-1.8,1)).normalized()*distance
    aim(cam,center)
    cam.data.dof.use_dof = False
    cam.data.dof.focus_distance = distance
    cam.data.show_composition_thirds = True
    scene.camera = cam
    return cam

def quality(scene, preset='draft'):
    if 'astra_original_render' not in scene:
        scene['astra_original_render'] = {'engine':scene.render.engine,'samples':scene.cycles.samples,'device':scene.cycles.device,'denoise':scene.cycles.use_denoising}
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = {'draft':16,'lookdev':64,'final':256}[preset]
    scene.cycles.use_denoising = True

def restore(scene):
    saved = scene.get('astra_original_render')
    if saved:
        scene.render.engine = saved['engine']
        scene.cycles.samples = saved['samples']
        scene.cycles.device = saved['device']
        scene.cycles.use_denoising = saved['denoise']
        del scene['astra_original_render']

def demo():
    name = 'ASTRA Demonstration'
    scene = bpy.data.scenes.get(name)
    if scene and not scene.get('astra'):
        scene = None
    if scene is None:
        scene = bpy.data.scenes.new(name)
        scene['astra'] = True
    if bpy.context.window:
        bpy.context.window.scene = scene
    col = collection(scene)
    # Explicit demo regeneration replaces only this toolkit's owned demonstration objects.
    for obj in list(col.objects):
        if obj.get('astra'):
            data = obj.data
            kind = obj.type
            bpy.data.objects.remove(obj,do_unlink=True)
            if data and data.users == 0:
                pools = {'MESH':bpy.data.meshes,'FONT':bpy.data.curves,'LIGHT':bpy.data.lights,'CAMERA':bpy.data.cameras}
                if kind in pools:
                    pools[kind].remove(data)
    objects=[]
    def adopt(obj):
        for parent in list(obj.users_collection):
            parent.objects.unlink(obj)
        col.objects.link(obj)
        obj['astra']=True
        return obj
    for i,kind in enumerate(PRESETS):
        x = (i%3-1)*1.9
        y = (i//3)*2
        material = create_material(kind)
        if kind == 'glass':
            bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=.54,location=(x,y,.54))
            obj=adopt(bpy.context.object)
            shell=obj.modifiers.new('Actual glass wall — 20 mm','SOLIDIFY')
            shell.thickness=.02
        else:
            bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,.5))
            obj=adopt(bpy.context.object)
            bevel=obj.modifiers.new('Rounded edges — 80 mm','BEVEL')
            bevel.width=.08
            bevel.segments=5
            obj.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
        obj.name='ASTRA / Demo / '+kind
        obj.data.materials.append(material)
        for p in obj.data.polygons:
            p.use_smooth=True
        objects.append(obj)
        bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y-.72,.02))
        tile=adopt(bpy.context.object)
        tile.name='ASTRA / Flat sample / '+kind
        tile.scale=(1.2,.35,.04)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        tile.data.materials.append(material)
        bpy.ops.object.text_add(location=(x-.62,y-.98,.003))
        text=adopt(bpy.context.object)
        text.name='ASTRA / Label / '+kind
        text.data.body=PRESETS[kind][0]
        text.data.size=.12
        text.data.extrude=.001
        label_mat=bpy.data.materials.get('ASTRA / Label ink') or bpy.data.materials.new('ASTRA / Label ink')
        label_mat.diffuse_color=(.025,.035,.025,1)
        label_mat.use_nodes=True
        label_mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.025,.035,.025,1)
        text.data.materials.append(label_mat)
    bpy.ops.mesh.primitive_plane_add(size=200)
    floor=adopt(bpy.context.object)
    floor.name='ASTRA / Neutral backdrop'
    floor_mat=bpy.data.materials.get('ASTRA / Backdrop') or bpy.data.materials.new('ASTRA / Backdrop')
    floor_mat.diffuse_color=(.24,.26,.22,1)
    floor_mat.use_nodes=True
    floor_mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.24,.26,.22,1)
    floor_mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.8
    floor.data.materials.append(floor_mat)
    if not scene.world or not scene.world.get('astra'):
        world=bpy.data.worlds.new('ASTRA / Studio world')
        world['astra']=True
        scene.world=world
    scene.world.use_nodes=True
    scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.22,.25,.2,1)
    scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.25
    scene.unit_settings.system='METRIC'
    scene.unit_settings.scale_length=1
    scene.render.resolution_x=1200
    scene.render.resolution_y=900
    scene.render.resolution_percentage=100
    lighting(scene,'studio',target=(0,1,.6),size=1.4)
    camera(scene,[objects[0]],'close')
    camera(scene,objects,'hero')
    quality(scene,'lookdev')
    return scene
