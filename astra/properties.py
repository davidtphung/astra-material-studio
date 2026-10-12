import bpy
from bpy.props import StringProperty,FloatProperty,EnumProperty,IntProperty,BoolProperty
from .materials import PRESETS
from .textures import MAPS

class ASTRA_Settings(bpy.types.PropertyGroup):
    material: EnumProperty(name='Material',items=[(k,v[0],'Procedural approximation') for k,v in PRESETS.items()])
    color: StringProperty(name='sRGB hex',default='#b7bbb5')
    roughness: FloatProperty(name='Roughness',min=.04,max=1,default=.32)
    scale: FloatProperty(name='Master scale',min=.01,max=1000,default=1)
    bump: FloatProperty(name='Bump strength',min=0,max=1,default=.3)
    seed: IntProperty(name='Seed',min=0,max=10000,default=42)
    coordinate: EnumProperty(name='Coordinates',items=[('OBJECT','Object','One Blender unit = one metre; preserve object transforms'),('UV','UV','Requires unwrapped UVs')])
    duplicate: BoolProperty(name='Create separate material',default=False,description='Keep existing assigned ASTRA materials unchanged')
    lighting: EnumProperty(name='Lighting',items=[(k,k.title(),'Editable area lights') for k in ['studio','daylight','noir','neon']])
    camera: EnumProperty(name='Framing',items=[(k,k.title(),'Bounds-based framing') for k in ['close','hero','medium','wide']])
    quality: EnumProperty(name='Quality',items=[('draft','Draft — 16 samples','Cycles CPU, denoised'),('lookdev','Look development — 64','Cycles CPU, denoised'),('final','Final — 256','Cycles CPU, denoised')])
    directx: BoolProperty(name='DirectX normals (invert green)',default=False)
    multiply_ao: BoolProperty(name='Multiply AO into color (artistic)',default=False)
    scan_report: StringProperty()
    validation_report: StringProperty()

for key in MAPS:
    ASTRA_Settings.__annotations__['map_'+key]=StringProperty(name=key.replace('_',' ').title(),subtype='FILE_PATH')
    ASTRA_Settings.__annotations__['channel_'+key]=EnumProperty(name='Channel',items=[(v,v,'Explicit map channel') for v in ['RGB','R','G','B','A']])
