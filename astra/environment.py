"""Editable, non-destructive rooftop scene built from the shared world definition."""
import math
import hashlib
import json
import bpy
import bmesh
from mathutils import Matrix, Vector
from .world_data import build_world
from .materials import create_material, linear_color
from .scenes import aim, quality

PREFIX='ASTRA / Rooftop / '
AXIS=Matrix.Rotation(math.pi/2,4,'X')

def primitive_mesh(kind,name):
    mesh=bpy.data.meshes.new(name)
    bm=bmesh.new()
    if kind=='box':
        bmesh.ops.create_cube(bm,size=1)
    elif kind=='sphere':
        bmesh.ops.create_uvsphere(bm,u_segments=16,v_segments=10,radius=.5)
    else:
        bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=16 if kind!='rod' else 8,radius1=.5,radius2=0 if kind=='cone' else .5,depth=1)
        # Base cylinders use Y-up to match the shared data.
        bmesh.ops.rotate(bm,cent=(0,0,0),matrix=Matrix.Rotation(-math.pi/2,3,'X'),verts=bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    if kind!='box':
        for p in mesh.polygons:
            p.use_smooth=len(p.vertices)==4
    return mesh

def make_palette(data,wetness,lighting):
    result={}
    night=lighting in {'noir','neon'}
    signature=hashlib.sha256(json.dumps([wetness,lighting]).encode()).hexdigest()[:6]
    for key,value in data['palette'].items():
        name=PREFIX+'Material / '+key+' / '+signature
        m=bpy.data.materials.get(name)
        if m and m.get('astra_rooftop'):
            result[key]=m
            continue
        m=bpy.data.materials.new(name)
        m['astra_rooftop']=True
        m.use_nodes=True
        t=m.node_tree
        b=t.nodes.get('Principled BSDF')
        color=linear_color(value['color'])
        damp=key in {'tile','tile2','concrete','wood','wood2'}
        color=tuple(v*(1-wetness*.2) for v in color[:3])+(1,)
        b.inputs['Base Color'].default_value=color
        m.diffuse_color=color
        b.inputs['Roughness'].default_value=(value['roughness']*(1-wetness)+.24*wetness) if damp else value['roughness']
        b.inputs['Metallic'].default_value=value.get('metalness',0)
        if value.get('emissive'):
            b.inputs['Emission Color'].default_value=linear_color(value['emissive'])
            b.inputs['Emission Strength'].default_value=value['emission']*(1.7 if night else .45)
        if key=='water':
            b.inputs['Transmission Weight'].default_value=.45
            b.inputs['IOR'].default_value=1.333
            b.inputs['Alpha'].default_value=max(wetness*.7,.001)
        if value.get('surface'):
            tex=t.nodes.new('ShaderNodeTexNoise')
            tex.name=tex.label='World-scale weathering'
            tex.location=(-500,0)
            tex.inputs['Scale'].default_value=8 if value['surface']=='wood' else 35
            coord=t.nodes.new('ShaderNodeTexCoord')
            coord.location=(-750,0)
            # Shared empty provides fixed world-space density without applying user transforms.
            coord.object=data['_coordinate_object']
            t.links.new(coord.outputs['Object'],tex.inputs['Vector'])
            bump=t.nodes.new('ShaderNodeBump')
            bump.inputs['Strength'].default_value=.18
            bump.inputs['Distance'].default_value=.002
            bump.location=(-180,-150)
            t.links.new(tex.outputs['Fac'],bump.inputs['Height'])
            t.links.new(bump.outputs['Normal'],b.inputs['Normal'])
            ramp=t.nodes.new('ShaderNodeValToRGB')
            ramp.location=(-230,150)
            ramp.color_ramp.elements[0].color=tuple(v*.72 for v in color[:3])+(1,)
            ramp.color_ramp.elements[1].color=color
            t.links.new(tex.outputs['Fac'],ramp.inputs['Fac'])
            t.links.new(ramp.outputs['Color'],b.inputs['Base Color'])
        result[key]=m
    return result

def make_knot():
    vertices=[]
    faces=[]
    segments,radial=160,24
    def curve(u):
        return Vector((.77*(2+math.cos(1.5*u))*.5*math.cos(u),.77*(2+math.cos(1.5*u))*.5*math.sin(u),.77*math.sin(1.5*u)*.5))
    for i in range(segments):
        u=i/segments*4*math.pi
        p=curve(u)
        ahead=curve(u+.01)
        tangent=ahead-p
        normal=ahead+p
        binormal=tangent.cross(normal).normalized()
        normal=binormal.cross(tangent).normalized()
        for j in range(radial):
            v=j/radial*2*math.pi
            vertices.append(p-.29*math.cos(v)*normal+.29*math.sin(v)*binormal)
    for i in range(segments):
        for j in range(radial):
            a=i*radial+j
            b=((i+1)%segments)*radial+j
            c=((i+1)%segments)*radial+(j+1)%radial
            d=i*radial+(j+1)%radial
            faces.append((a,b,c,d))
    mesh=bpy.data.meshes.new(PREFIX+'Hero knot mesh')
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    for p in mesh.polygons:
        p.use_smooth=True
    return mesh

def create_rooftop(settings=None):
    settings=settings or {}
    lighting=settings.get('lighting','daylight')
    wetness=settings.get('wetness',.45)
    haze=settings.get('haze',.3)
    data=build_world()
    scene=next((s for s in bpy.data.scenes if s.get('astra_rooftop_scene')),None)
    if scene is None:
        scene=bpy.data.scenes.new('ASTRA Rooftop Workshop')
        scene['astra_rooftop_scene']=True
    if bpy.context.window:
        bpy.context.window.scene=scene
    col=next((c for c in scene.collection.children if c.get('astra_rooftop_collection')),None)
    if col is None:
        col=bpy.data.collections.new(PREFIX+'Environment')
        col['astra_rooftop_collection']=True
        scene.collection.children.link(col)
    for obj in list(col.objects):
        if obj.get('astra_rooftop'):
            bpy.data.objects.remove(obj,do_unlink=True)
    for pool in [bpy.data.meshes,bpy.data.curves,bpy.data.lights,bpy.data.cameras]:
        for block in list(pool):
            if block.name.startswith(PREFIX) and block.users==0:
                pool.remove(block)
    # Preserve unowned objects even inside the toolkit collection.
    def own(name,block=None):
        obj=bpy.data.objects.new(PREFIX+name,block)
        obj['astra_rooftop']=True
        col.objects.link(obj)
        return obj
    coordinates=own('World coordinates')
    data['_coordinate_object']=coordinates
    palette=make_palette(data,wetness,lighting)
    # Rebind existing materials when regeneration replaces the coordinate empty.
    for m in palette.values():
        for n in m.node_tree.nodes:
            if n.type=='TEX_COORD':
                n.object=coordinates
    templates={}
    for item in data['objects']:
        key=item['geometry']+':'+item['material']
        if key not in templates:
            mesh=primitive_mesh(item['geometry'],PREFIX+'Mesh / '+key)
            mesh.materials.append(palette[item['material']])
            templates[key]=mesh
        obj=own(item['name'],templates[key])
        if item['geometry']=='rod':
            start,end=Vector(item['start']),Vector(item['end'])
            delta=end-start
            matrix=Matrix.Translation((start+end)*.5) @ Vector((0,1,0)).rotation_difference(delta).to_matrix().to_4x4() @ Matrix.Diagonal((item['radius']*2,delta.length,item['radius']*2,1))
        else:
            matrix=Matrix.Translation(Vector(item['position']))
            for angle,axis in zip(item.get('rotation',[0,0,0]),['X','Y','Z']):
                matrix=matrix @ Matrix.Rotation(angle,4,axis)
            matrix=matrix @ Matrix.Diagonal((*item['size'],1))
        obj.matrix_world=AXIS @ matrix
    for label in data['labels']:
        curve=bpy.data.curves.new(PREFIX+'Sign text','FONT')
        curve.body=label['text']
        curve.align_x='CENTER'
        curve.align_y='CENTER'
        curve.size=label['height']*.82
        obj=own('Sign / '+label['text'],curve)
        obj.matrix_world=AXIS @ Matrix.Translation(Vector(label['position']))
        curve.materials.append(palette['neon'] if label['text']=='ASTRA' else palette['white'])
    shape=settings.get('shape','sculpture')
    hero_data=make_knot() if shape=='sculpture' else primitive_mesh('sphere' if shape=='sphere' else 'box',PREFIX+'Hero mesh')
    hero=own('Hero material sample',hero_data)
    hero['astra_hero']=True
    if shape=='block':
        scale=1.95*.48
        bevel=hero.modifiers.new('Manufactured edge radius','BEVEL')
        bevel.width=.07
        bevel.segments=4
    else:
        scale=.48*(2.32 if shape=='sphere' else 1)
    rotation=Matrix.Rotation(-.35,4,'Y')
    minimum=min((rotation @ v.co.to_4d()).y for v in hero_data.vertices)*scale
    matrix=Matrix.Translation(Vector((0,.99-minimum,0))) @ rotation @ Matrix.Diagonal((scale,scale,scale,1))
    hero.matrix_world=AXIS @ matrix
    hero.data.materials.append(create_material(settings.get('material','metal'),settings.get('color'),settings.get('roughness'),settings.get('scale',1),settings.get('bump'),settings.get('seed',42)))
    presets={'daylight':((1,.73,.45),3.5,(.42,.57,.68),.5), 'studio':((.8,.9,1),2.2,(.58,.7,.75),.65), 'noir':((.4,.6,1),.8,(.12,.2,.32),.24), 'neon':((.35,.55,.7),.4,(.08,.14,.2),.28)}
    color,power,ambient,strength=presets[lighting]
    world=scene.world
    if world is None or not world.get('astra_rooftop'):
        world=bpy.data.worlds.new(PREFIX+'Sky')
        world['astra_rooftop']=True
        scene.world=world
    world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(*ambient,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=strength
    def light(name,kind,position,target,color,power,size=1):
        block=bpy.data.lights.new(PREFIX+name,kind)
        block.energy=power
        block.color=color
        if kind=='AREA':
            block.shape='DISK'
            block.size=size
        obj=own(name,block)
        obj.location=AXIS @ Vector(position)
        aim(obj,AXIS @ Vector(target))
        return obj
    sun=light('Directional sky light','SUN',[-8,13,6],[0,.7,0],color,power)
    sun.data.angle=.065 if lighting=='daylight' else .25
    light('Workbench task lamp','AREA',[-.53,2.105,-.49],[0,.99,0],(1,.78,.46),35 if lighting in {'noir','neon'} else 8,.45)
    light('Green sign practical','AREA',[2.8,3.9,-10.1],[0,1,0],(.58,1,.36),160 if lighting in {'noir','neon'} else 10,2)
    if haze>0:
        volume=own('Bounded atmospheric haze',primitive_mesh('box',PREFIX+'Atmosphere mesh'))
        volume.location=(0,5,12)
        volume.scale=(100,100,65)
        vm=bpy.data.materials.new(PREFIX+'Atmosphere')
        vm['astra_rooftop']=True
        vm.use_nodes=True
        vt=vm.node_tree
        vt.nodes.clear()
        output=vt.nodes.new('ShaderNodeOutputMaterial')
        scatter=vt.nodes.new('ShaderNodeVolumeScatter')
        scatter.inputs['Density'].default_value=haze*.003
        scatter.inputs['Anisotropy'].default_value=.2
        vt.links.new(scatter.outputs[0],output.inputs['Volume'])
        volume.data.materials.append(vm)
        volume.display_type='WIRE'
    cameras={}
    for name,view in data['cameras'].items():
        block=bpy.data.cameras.new(PREFIX+'Camera / '+name)
        block.sensor_fit='VERTICAL'
        block.sensor_height=24
        block.lens=24/(2*math.tan(math.radians(43)/2))
        block.clip_end=400
        obj=own('Camera / '+name,block)
        obj.location=AXIS @ Vector(view['position'])
        aim(obj,AXIS @ Vector(view['target']))
        block.dof.use_dof=False
        block.show_composition_thirds=True
        cameras[name]=obj
    scene.camera=cameras[settings.get('view','bench')]
    scene.render.resolution_x=1440
    scene.render.resolution_y=1080
    scene.render.resolution_percentage=100
    scene.unit_settings.system='METRIC'
    scene.unit_settings.scale_length=1
    quality(scene,'lookdev')
    scene['astra_world_seed']=42
    scene['astra_world_units']='metres'
    scene['astra_world_object_count']=len(data['objects'])
    scene['astra_world_context']='Fictional Kowloon-inspired rooftop, not a real address reconstruction.'
    scene['astra_world_settings']=json.dumps(settings)
    for m in list(bpy.data.materials):
        if m.get('astra_rooftop') and m.users==0:
            bpy.data.materials.remove(m)
    bpy.context.view_layer.update()
    return scene
