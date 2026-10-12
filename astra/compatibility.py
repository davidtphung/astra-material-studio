"""Runtime capability checks; verified with Blender 5.2.2."""
import bpy

def devices():
    addon = bpy.context.preferences.addons.get('cycles')
    if not addon:
        return []
    try:
        addon.preferences.refresh_devices()
        return [(d.name, d.type) for d in addon.preferences.devices]
    except Exception:
        return []

def principled_input(node, name):
    socket = node.inputs.get(name)
    if socket is None:
        raise RuntimeError(f'ASTRA: {name} is not supported by Blender {bpy.app.version_string}')
    return socket
