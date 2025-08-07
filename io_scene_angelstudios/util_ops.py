import bpy
from bpy.types import (Operator)

class NamedObjectHideOperatorBase(Operator):
    bl_options = {'REGISTER', 'UNDO'}

    def hide_contains(self, context, str):
        scene = context.scene
        for ob in scene.objects:
            ob_name_l = ob.name.lower()
            if str in ob_name_l:
                ob.hide_set(True)

    def hide_suffix(self, context, suffix):
        scene = context.scene
        for ob in scene.objects:
            ob_name_l = ob.name.lower()
            ob.hide_set(not ob_name_l.endswith(suffix))

class ShowLodOnlyHOperator(NamedObjectHideOperatorBase):
    bl_idname = "angelstudios.show_h_lod"
    bl_label = "Isolate H LOD"
    
    def execute(self, context):
        self.hide_suffix(context, "_h")

        scene = context.scene
        for ob in scene.objects:
            if ob.name == "H" or ob.name == "h":
                ob.hide_set(False)

        return {'FINISHED'}
    
class ShowLodOnlyMOperator(NamedObjectHideOperatorBase):
    bl_idname = "angelstudios.show_m_lod"
    bl_label = "Isolate M LOD"

    def execute(self, context):
        self.hide_suffix(context, "_m")

        scene = context.scene
        for ob in scene.objects:
            if ob.name == "M" or ob.name == "m":
                ob.hide_set(False)

        return {'FINISHED'}
    
class ShowLodOnlyLOperator(NamedObjectHideOperatorBase):
    bl_idname = "angelstudios.show_l_lod"
    bl_label = "Isolate L LOD"
    
    def execute(self, context):
        self.hide_suffix(context, "_l")

        scene = context.scene
        for ob in scene.objects:
            if ob.name == "L" or ob.name == "l":
                ob.hide_set(False)

        return {'FINISHED'}
    
class ShowLodOnlyVLOperator(NamedObjectHideOperatorBase):
    bl_idname = "angelstudios.show_vl_lod"
    bl_label = "Isolate VL LOD"
    
    def execute(self, context):
        self.hide_suffix(context, "_vl")

        scene = context.scene
        for ob in scene.objects:
            if ob.name == "VL" or ob.name == "vl":
                ob.hide_set(False)

        return {'FINISHED'}
    
class HideDamagedPanels(NamedObjectHideOperatorBase):
    bl_idname = "angelstudios.hide_dmg_panels"
    bl_label = "Hide Damaged Panels"
    
    def execute(self, context):
        self.hide_contains(context, "_dmg_")
        return {'FINISHED'}
    
class HideUndamagedPanels(NamedObjectHideOperatorBase):
    bl_idname = "angelstudios.hide_udmg_panels"
    bl_label = "Hide Undamaged Panels"
    
    def execute(self, context):
        self.hide_contains(context, "_udmg_")
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(ShowLodOnlyHOperator)
    bpy.utils.register_class(ShowLodOnlyMOperator)
    bpy.utils.register_class(ShowLodOnlyLOperator)
    bpy.utils.register_class(ShowLodOnlyVLOperator)
    bpy.utils.register_class(HideDamagedPanels)
    bpy.utils.register_class(HideUndamagedPanels)

def unregister():
    bpy.utils.unregister_class(HideUndamagedPanels)
    bpy.utils.unregister_class(HideDamagedPanels)
    bpy.utils.unregister_class(ShowLodOnlyVLOperator)
    bpy.utils.unregister_class(ShowLodOnlyLOperator)
    bpy.utils.unregister_class(ShowLodOnlyMOperator)
    bpy.utils.unregister_class(ShowLodOnlyHOperator)
    
    