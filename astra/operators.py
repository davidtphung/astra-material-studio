import json
import re
import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper
from . import materials,scenes,textures,validation

class ASTRA_OT_material(bpy.types.Operator):
    bl_idname='astra.create_material'
    bl_label='Create and apply material'
    bl_options={'REGISTER','UNDO'}
    @classmethod
    def poll(cls,context):
        return context.mode=='OBJECT' and any(o.type=='MESH' for o in context.selected_objects)
    def execute(self,context):
        p=context.scene.astra
        if not re.fullmatch(r'#[0-9a-fA-F]{6}',p.color):
            self.report({'ERROR'},'Use an sRGB color such as #b7bbb5.')
            return {'CANCELLED'}
        m=materials.create_material(p.material,p.color,p.roughness,p.scale,p.bump,p.seed,p.coordinate,p.duplicate)
        count=materials.assign(m,context.selected_objects)
        self.report({'INFO'},f'Applied to {count} selected meshes.')
        return {'FINISHED'}

class ASTRA_OT_defaults(bpy.types.Operator):
    bl_idname='astra.load_defaults'
    bl_label='Load material defaults'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        p=context.scene.astra
        _,p.color,p.roughness,p.bump,_=materials.PRESETS[p.material]
        p.scale=1
        return {'FINISHED'}

class ASTRA_OT_import_settings(bpy.types.Operator,ImportHelper):
    bl_idname='astra.import_settings'
    bl_label='Import browser settings'
    bl_options={'REGISTER','UNDO'}
    filename_ext='.json'
    filter_glob: StringProperty(default='*.json',options={'HIDDEN'})
    def execute(self,context):
        try:
            with open(self.filepath,encoding='utf-8') as f:
                data=json.load(f)
            if data.get('schema')!='astra.look.v1' or data.get('material') not in materials.PRESETS:
                raise ValueError('Unsupported ASTRA settings file.')
            if not re.fullmatch(r'#[0-9a-fA-F]{6}',data.get('color','')):
                raise ValueError('Invalid color.')
            for key,low,high in [('roughness',.04,1),('scale',.3,4),('bump',0,1),('seed',0,10000)]:
                value=data.get(key)
                if isinstance(value,bool) or not isinstance(value,(int,float)) or not low<=value<=high:
                    raise ValueError('Invalid '+key)
            if data.get('lighting') not in scenes.LIGHTS:
                raise ValueError('Invalid lighting preset.')
            p=context.scene.astra
            for key in ['material','color','roughness','scale','bump','seed','lighting']:
                setattr(p,key,int(data[key]) if key=='seed' else data[key])
            self.report({'INFO'},'Settings loaded. Select a mesh and click Create and apply.')
            return {'FINISHED'}
        except (OSError,ValueError,TypeError) as exc:
            self.report({'ERROR'},str(exc))
            return {'CANCELLED'}

class ASTRA_OT_lighting(bpy.types.Operator):
    bl_idname='astra.create_lighting'
    bl_label='Apply editable lighting rig'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        target,size=scenes.bounds(context.selected_objects)
        scenes.lighting(context.scene,context.scene.astra.lighting,target,max(size,.1))
        return {'FINISHED'}

class ASTRA_OT_camera(bpy.types.Operator):
    bl_idname='astra.create_camera'
    bl_label='Create framed camera'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        scenes.camera(context.scene,context.selected_objects,context.scene.astra.camera)
        return {'FINISHED'}

class ASTRA_OT_quality(bpy.types.Operator):
    bl_idname='astra.apply_quality'
    bl_label='Apply render preset (CPU)'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        scenes.quality(context.scene,context.scene.astra.quality)
        return {'FINISHED'}

class ASTRA_OT_restore(bpy.types.Operator):
    bl_idname='astra.restore_render'
    bl_label='Restore previous render settings'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        scenes.restore(context.scene)
        return {'FINISHED'}

class ASTRA_OT_demo(bpy.types.Operator):
    bl_idname='astra.generate_demo'
    bl_label='Generate demonstration scene'
    bl_description='Creates a separate scene; replaces ASTRA demo objects when repeated'
    bl_options={'REGISTER','UNDO'}
    def invoke(self,context,event):
        return context.window_manager.invoke_confirm(self,event)
    def execute(self,context):
        scenes.demo()
        return {'FINISHED'}

class ASTRA_OT_scan(bpy.types.Operator):
    bl_idname='astra.scan_textures'
    bl_label='Scan texture folder'
    bl_options={'REGISTER','UNDO'}
    directory: StringProperty(subtype='DIR_PATH')
    def invoke(self,context,event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    def execute(self,context):
        try:
            mappings,messages=textures.detect(self.directory)
            p=context.scene.astra
            for kind in textures.MAPS:
                setattr(p,'map_'+kind,mappings.get(kind,''))
            p.scan_report=' | '.join(messages) or 'All maps detected. Review paths before applying.'
            self.report({'INFO'},'Review detected paths and channels in Texture Import before applying.')
            return {'FINISHED'}
        except OSError as exc:
            self.report({'ERROR'},str(exc))
            return {'CANCELLED'}

class ASTRA_OT_pbr(bpy.types.Operator):
    bl_idname='astra.import_pbr'
    bl_label='Apply reviewed texture maps'
    bl_options={'REGISTER','UNDO'}
    @classmethod
    def poll(cls,context):
        return context.mode=='OBJECT' and any(o.type=='MESH' for o in context.selected_objects)
    def execute(self,context):
        p=context.scene.astra
        try:
            maps={k:getattr(p,'map_'+k) for k in textures.MAPS if getattr(p,'map_'+k)}
            channels={k:getattr(p,'channel_'+k) for k in textures.MAPS}
            m=textures.import_pbr(maps,channels,p.directx,p.multiply_ao)
            materials.assign(m,context.selected_objects)
            return {'FINISHED'}
        except (OSError,ValueError,RuntimeError) as exc:
            self.report({'ERROR'},str(exc))
            return {'CANCELLED'}

class ASTRA_OT_validate(bpy.types.Operator):
    bl_idname='astra.validate_scene'
    bl_label='Validate scene'
    def execute(self,context):
        result=validation.validate(context.scene)
        context.scene.astra.validation_report='\n'.join(level+': '+text for level,text in result) or 'No supported validation issues detected.'
        self.report({'WARNING'} if result else {'INFO'},context.scene.astra.validation_report[:900])
        return {'FINISHED'}

CLASSES=[ASTRA_OT_material,ASTRA_OT_defaults,ASTRA_OT_import_settings,ASTRA_OT_lighting,ASTRA_OT_camera,ASTRA_OT_quality,ASTRA_OT_restore,ASTRA_OT_demo,ASTRA_OT_scan,ASTRA_OT_pbr,ASTRA_OT_validate]
