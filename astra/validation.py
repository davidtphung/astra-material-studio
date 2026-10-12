from pathlib import Path
import bpy
from .compatibility import devices

def validate(scene):
    messages=[]
    if not scene.camera:
        messages.append(('WARNING','No active camera.'))
    for obj in scene.objects:
        if obj.type != 'MESH':
            continue
        if any(abs(v-1)>.001 for v in obj.scale):
            messages.append(('WARNING',obj.name+': non-unit scale may stretch procedural detail.'))
        for slot in obj.material_slots:
            mat=slot.material
            if not mat or not mat.node_tree:
                continue
            if mat.get('astra_coordinate')=='UV' and not obj.data.uv_layers:
                messages.append(('WARNING',obj.name+': material requires UV coordinates.'))
            for node in mat.node_tree.nodes:
                if node.type=='TEX_IMAGE' and node.image:
                    img=node.image
                    if img.source=='FILE' and not img.packed_file and not Path(bpy.path.abspath(img.filepath)).is_file():
                        messages.append(('ERROR',img.name+': missing image file.'))
                if node.type=='OUTPUT_MATERIAL' and node.inputs['Displacement'].is_linked:
                    messages.append(('WARNING',mat.name+': true displacement needs compatible renderer, material mode and sufficient geometry.'))
    if scene.render.engine=='CYCLES' and scene.cycles.device=='GPU' and not any(kind!='CPU' for _,kind in devices()):
        messages.append(('ERROR','GPU rendering requested but no supported GPU detected.'))
    return list(dict.fromkeys(messages))
