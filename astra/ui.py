import bpy
from .textures import MAPS

class ASTRA_PT_main(bpy.types.Panel):
    bl_label='ASTRA / Material Studio'
    bl_idname='ASTRA_PT_main'
    bl_space_type='VIEW_3D'
    bl_region_type='UI'
    bl_category='ASTRA'
    def draw(self,context):
        l=self.layout
        p=context.scene.astra
        l.label(text='Materials')
        l.operator('astra.import_settings',icon='IMPORT')
        l.prop(p,'material')
        l.operator('astra.load_defaults')
        l.prop(p,'color')
        l.prop(p,'roughness')
        l.label(text='Surface detail · bump only')
        for key in ['scale','bump','seed','coordinate','duplicate']:
            l.prop(p,key)
        l.operator('astra.create_material',icon='MATERIAL')
        l.separator()
        l.label(text='Lighting / Camera')
        l.prop(p,'lighting')
        l.operator('astra.create_lighting',icon='LIGHT_AREA')
        l.prop(p,'camera')
        l.operator('astra.create_camera',icon='CAMERA_DATA')
        l.separator()
        l.label(text='Render / Validation')
        l.prop(p,'quality')
        l.operator('astra.apply_quality')
        l.operator('astra.restore_render')
        l.operator('astra.generate_demo',icon='SCENE_DATA')
        l.operator('astra.validate_scene',icon='CHECKMARK')
        for line in p.validation_report.splitlines():
            l.label(text=line[:100])

class ASTRA_PT_textures(bpy.types.Panel):
    bl_label='Texture Import / Review maps'
    bl_idname='ASTRA_PT_textures'
    bl_space_type='VIEW_3D'
    bl_region_type='UI'
    bl_category='ASTRA'
    bl_options={'DEFAULT_CLOSED'}
    def draw(self,context):
        l=self.layout
        p=context.scene.astra
        l.operator('astra.scan_textures',icon='FILE_FOLDER')
        for message in p.scan_report.split(' | '):
            if message:
                l.label(text=message)
        for kind in MAPS:
            row=l.row()
            row.prop(p,'map_'+kind)
            row.prop(p,'channel_'+kind,text='')
        l.prop(p,'directx')
        l.prop(p,'multiply_ao')
        l.label(text='Height uses bump; UVs required.')
        l.operator('astra.import_pbr',icon='MATERIAL')

CLASSES=[ASTRA_PT_main,ASTRA_PT_textures]
