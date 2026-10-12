bl_info = {'name':'ASTRA Material Studio','author':'DANCO WORLDS','version':(0,1,0),'blender':(5,2,0),'location':'View3D > Sidebar > ASTRA','description':'Procedural materials, PBR import, editable lights and demonstration scenes','category':'Material'}
import bpy
from . import properties,operators,ui
CLASSES=[properties.ASTRA_Settings]+operators.CLASSES+ui.CLASSES

def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.astra=bpy.props.PointerProperty(type=properties.ASTRA_Settings)

def unregister():
    if hasattr(bpy.types.Scene,'astra'):
        del bpy.types.Scene.astra
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)

if __name__=='__main__':
    register()
