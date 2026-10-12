"""User supplied texture paths, explicit packed channels and normal convention."""
from pathlib import Path
import re
import bpy
from .materials import node

MAPS = {'base_color':('basecolor','base_color','albedo','diffuse'), 'roughness':('roughness','rough'), 'metallic':('metallic','metalness','metal'), 'normal':('normal','nor','normalgl','normaldx'), 'height':('height','displacement','disp'), 'ao':('ao','ambientocclusion','occlusion'), 'alpha':('opacity','alpha'), 'emission':('emission','emissive')}

def detect(directory):
    paths = [p for p in Path(directory).iterdir() if p.is_file() and p.suffix.lower() in {'.png','.jpg','.jpeg','.tif','.tiff','.exr','.webp'}]
    found = {}
    messages=[]
    for kind, aliases in MAPS.items():
        candidates = [p for p in paths if any(re.search(r'(?:^|[_. -])'+re.escape(a)+r'(?:$|[_. -])',p.stem.lower()) for a in aliases)]
        if len(candidates)==1:
            found[kind]=str(candidates[0])
        elif len(candidates)>1:
            messages.append(f'{kind}: ambiguous ({len(candidates)} files); choose a path/resolution manually.')
        else:
            messages.append(f'{kind}: not detected.')
    return found,messages

def import_pbr(mappings, channels=None, directx=False, multiply_ao=False):
    channels=channels or {}
    # Validate before creating any nodes or images.
    for kind,path in mappings.items():
        if kind not in MAPS:
            raise ValueError('Unknown map '+kind)
        if not Path(bpy.path.abspath(path)).is_file():
            raise ValueError('Missing '+kind+' image: '+path)
    if not mappings:
        raise ValueError('No image maps selected. Scan a folder or enter paths first.')
    mat=bpy.data.materials.new('ASTRA / Imported PBR')
    mat['astra']=True
    mat['astra_coordinate']='UV'
    mat.use_nodes=True
    tree=mat.node_tree
    bsdf=tree.nodes.get('Principled BSDF')
    outputs={}
    for i,(kind,path) in enumerate(mappings.items()):
        texture=node(tree,'ShaderNodeTexImage',kind.replace('_',' ').title(),-800,-i*290)
        # Separate datablocks preserve another material's color-space interpretation.
        image=bpy.data.images.load(bpy.path.abspath(path),check_existing=False)
        image.colorspace_settings.name='sRGB' if kind in {'base_color','emission'} else 'Non-Color'
        texture.image=image
        channel=channels.get(kind,'RGB')
        out=texture.outputs['Color']
        if channel=='A':
            out=texture.outputs['Alpha']
        elif channel in {'R','G','B'}:
            sep=node(tree,'ShaderNodeSeparateColor',kind+' packed channel',-530,-i*290)
            tree.links.new(out,sep.inputs['Color'])
            out=sep.outputs[{'R':'Red','G':'Green','B':'Blue'}[channel]]
        outputs[kind]=out
    direct={'base_color':'Base Color','roughness':'Roughness','metallic':'Metallic','alpha':'Alpha','emission':'Emission Color'}
    for kind,name in direct.items():
        if kind in outputs:
            tree.links.new(outputs[kind],bsdf.inputs[name])
    if 'emission' in outputs:
        bsdf.inputs['Emission Strength'].default_value=1
    normal=None
    if 'normal' in outputs:
        src=outputs['normal']
        if directx:
            sep=node(tree,'ShaderNodeSeparateColor','DirectX normal channels',-250,-700)
            tree.links.new(src,sep.inputs['Color'])
            invert=node(tree,'ShaderNodeMath','Invert green only',-30,-850)
            invert.operation='SUBTRACT'
            invert.inputs[0].default_value=1
            tree.links.new(sep.outputs['Green'],invert.inputs[1])
            combine=node(tree,'ShaderNodeCombineColor','OpenGL normal convention',200,-700)
            tree.links.new(sep.outputs['Red'],combine.inputs['Red'])
            tree.links.new(invert.outputs[0],combine.inputs['Green'])
            tree.links.new(sep.outputs['Blue'],combine.inputs['Blue'])
            src=combine.outputs[0]
        n=node(tree,'ShaderNodeNormalMap','Tangent-space normal (UV required)',440,-600)
        tree.links.new(src,n.inputs['Color'])
        normal=n.outputs['Normal']
    if 'height' in outputs:
        b=node(tree,'ShaderNodeBump','Height as safe bump — not displacement',660,-450)
        b.inputs['Distance'].default_value=.001
        tree.links.new(outputs['height'],b.inputs['Height'])
        if normal:
            tree.links.new(normal,b.inputs['Normal'])
        normal=b.outputs['Normal']
    if normal:
        tree.links.new(normal,bsdf.inputs['Normal'])
    if multiply_ao and 'ao' in outputs and 'base_color' in outputs:
        mix=node(tree,'ShaderNodeMixRGB','AO multiplication — artistic override',200,400)
        mix.blend_type='MULTIPLY'
        mix.inputs[0].default_value=1
        tree.links.new(outputs['base_color'],mix.inputs[1])
        tree.links.new(outputs['ao'],mix.inputs[2])
        tree.links.new(mix.outputs[0],bsdf.inputs['Base Color'])
    return mat
