"""Six deterministic procedural approximations, using object-space metres."""
import hashlib
import json
import bpy
from .compatibility import principled_input

PRESETS = {
    'metal': ('Brushed metal', '#b7bbb5', .32, .30, 1),
    'paint': ('Painted metal', '#a74c34', .42, .25, 0),
    'concrete': ('Concrete', '#aaa695', .86, .55, 0),
    'wood': ('Wood', '#885331', .48, .35, 0),
    'glass': ('Glass', '#c4dfcb', .12, .06, 0),
    'plastic': ('Plastic', '#ccc079', .36, .18, 0),
}

def linear_color(value):
    if isinstance(value, str):
        values = [int(value[i:i+2], 16)/255 for i in (1, 3, 5)]
    else:
        values = list(value)[:3]
    return tuple(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in values) + (1,)

def node(tree, kind, name, x, y):
    n = tree.nodes.new(kind)
    n.name = n.label = name
    n.location = (x, y)
    return n

def field_group():
    name = 'ASTRA / Surface field v1'
    existing = bpy.data.node_groups.get(name)
    if existing and existing.get('astra'):
        return existing
    g = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    g['astra'] = True
    for socket_name, kind, default in [('Vector','NodeSocketVector',None),('Scale','NodeSocketFloat',1.0),('Seed','NodeSocketFloat',42.0)]:
        s = g.interface.new_socket(name=socket_name, in_out='INPUT', socket_type=kind)
        if default is not None:
            s.default_value = default
            s.min_value = 0
            s.max_value = 10000
    for name in ['Macro', 'Structure', 'Micro']:
        g.interface.new_socket(name=name, in_out='OUTPUT', socket_type='NodeSocketFloat')
    inp = node(g,'NodeGroupInput','Artist controls',-600,0)
    out = node(g,'NodeGroupOutput','Correlated surface fields',400,0)
    for i, (name, frequency) in enumerate([('Macro',3),('Structure',35),('Micro',420)]):
        mul = node(g,'ShaderNodeMath',name+' frequency',-380,-i*240)
        mul.operation = 'MULTIPLY'
        mul.inputs[1].default_value = frequency
        g.links.new(inp.outputs['Scale'],mul.inputs[0])
        noise = node(g,'ShaderNodeTexNoise',name+' field',-120,-i*240)
        noise.noise_dimensions = '4D'
        noise.inputs['Detail'].default_value = 3
        g.links.new(inp.outputs['Vector'],noise.inputs['Vector'])
        g.links.new(mul.outputs[0],noise.inputs['Scale'])
        g.links.new(inp.outputs['Seed'],noise.inputs['W'])
        g.links.new(noise.outputs['Fac'],out.inputs[name])
    return g

def create_material(kind='metal', color=None, roughness=None, scale=1, bump=None, seed=42, coordinate='OBJECT', duplicate=False):
    if kind not in PRESETS:
        raise ValueError('Unknown ASTRA material: '+str(kind))
    label, default_color, default_roughness, default_bump, metallic = PRESETS[kind]
    signature = json.dumps([kind,color,roughness,scale,bump,seed,coordinate],sort_keys=True)
    name = 'ASTRA / '+label+' / '+hashlib.sha256(signature.encode()).hexdigest()[:8]
    material = bpy.data.materials.get(name)
    if duplicate or (material and not material.get('astra')):
        material = None
    if material is not None and material.get('astra'):
        return material
    if material is None:
        material = bpy.data.materials.new(name)
    material['astra'] = True
    material['astra_kind'] = kind
    material['astra_coordinate'] = coordinate
    material['astra_seed'] = seed
    material.use_nodes = True
    t = material.node_tree
    t.nodes.clear()
    output = node(t,'ShaderNodeOutputMaterial','Surface output',1050,160)
    bsdf = node(t,'ShaderNodeBsdfPrincipled','Physically based surface',740,160)
    t.links.new(bsdf.outputs['BSDF'],output.inputs['Surface'])
    principled_input(bsdf,'Metallic').default_value = metallic
    principled_input(bsdf,'Roughness').default_value = default_roughness if roughness is None else roughness
    base_color = linear_color(color or default_color)
    tex = node(t,'ShaderNodeTexCoord','Coordinates (1 Blender unit = 1 metre)',-1050,160)
    mapping = node(t,'ShaderNodeMapping','Direction (editable rotation)',-820,160)
    mapping.inputs['Scale'].default_value = (1,40,1) if kind == 'metal' else (3,3,.12) if kind == 'wood' else (1,1,1)
    t.links.new(tex.outputs['UV' if coordinate == 'UV' else 'Object'],mapping.inputs['Vector'])
    field = node(t,'ShaderNodeGroup','Surface controls',-570,160)
    field.node_tree = field_group()
    field.inputs['Scale'].default_value = scale
    field.inputs['Seed'].default_value = seed
    t.links.new(mapping.outputs['Vector'],field.inputs['Vector'])
    ramp = node(t,'ShaderNodeValToRGB','Restrained tonal variation',-240,280)
    low, high = ramp.color_ramp.elements
    low.position = .15
    high.position = .85
    low.color = tuple(v*.75 for v in base_color[:3]) + (1,)
    high.color = base_color
    t.links.new(field.outputs['Structure' if kind == 'wood' else 'Macro'],ramp.inputs['Fac'])
    t.links.new(ramp.outputs['Color'],bsdf.inputs['Base Color'])
    rough = node(t,'ShaderNodeMapRange','Roughness variation',-200,-50)
    nominal = default_roughness if roughness is None else roughness
    rough.inputs['To Min'].default_value = max(.02,nominal-.06)
    rough.inputs['To Max'].default_value = min(1,nominal+.06)
    t.links.new(field.outputs['Micro'],rough.inputs['Value'])
    t.links.new(rough.outputs['Result'],bsdf.inputs['Roughness'])
    relief = node(t,'ShaderNodeBump','Fine relief — bump only',400,-130)
    relief.inputs['Strength'].default_value = default_bump if bump is None else bump
    relief.inputs['Distance'].default_value = .0015 if kind == 'concrete' else .00025
    t.links.new(field.outputs['Structure' if kind in {'wood','concrete'} else 'Micro'],relief.inputs['Height'])
    t.links.new(relief.outputs['Normal'],bsdf.inputs['Normal'])
    if kind == 'metal':
        principled_input(bsdf,'Anisotropic').default_value = .5
        tangent = node(t,'ShaderNodeTangent','Object-axis brushing tangent',380,-400)
        tangent.direction_type = 'RADIAL'
        tangent.axis = 'Z'
        t.links.new(tangent.outputs['Tangent'],bsdf.inputs['Tangent'])
    if kind == 'paint':
        chip = node(t,'ShaderNodeMath','Chip threshold (procedural approximation)',-150,-400)
        chip.operation = 'GREATER_THAN'
        chip.inputs[1].default_value = .73
        t.links.new(field.outputs['Structure'],chip.inputs[0])
        t.links.new(chip.outputs[0],bsdf.inputs['Metallic'])
        mix = node(t,'ShaderNodeMixRGB','Paint versus exposed substrate',400,280)
        mix.inputs[2].default_value = (.24,.27,.29,1)
        t.links.new(chip.outputs[0],mix.inputs[0])
        t.links.new(ramp.outputs['Color'],mix.inputs[1])
        t.links.new(mix.outputs[0],bsdf.inputs['Base Color'])
        t.links.new(chip.outputs[0],relief.inputs['Height'])
    if kind == 'glass':
        principled_input(bsdf,'Transmission Weight').default_value = 1
        principled_input(bsdf,'IOR').default_value = 1.46
        absorption = node(t,'ShaderNodeVolumeAbsorption','Tint through thickness',740,-400)
        absorption.inputs['Color'].default_value = base_color
        absorption.inputs['Density'].default_value = .1
        t.links.new(absorption.outputs['Volume'],output.inputs['Volume'])
    if kind == 'plastic':
        principled_input(bsdf,'Coat Weight').default_value = .15
    material.diffuse_color = base_color
    return material

def assign(material, objects):
    meshes = [o for o in objects if o.type == 'MESH' and o.data.library is None]
    if not meshes:
        raise ValueError('Select at least one editable mesh object.')
    for obj in meshes:
        # Preserve other objects sharing this mesh before changing its material slot.
        if obj.data.users > 1:
            obj.data = obj.data.copy()
        if obj.data.materials:
            obj.data.materials[obj.active_material_index] = material
        else:
            obj.data.materials.append(material)
    return len(meshes)
