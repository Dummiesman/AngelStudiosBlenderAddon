import bpy
from bpy.types import (Operator)

generated_classes = []

class LODUtilityOperatorBase(Operator):
    bl_options = {'REGISTER', 'UNDO'}

    def hide_contains(self, context, name_fragment):
        scene = context.scene
        for ob in scene.objects:
            ob_name_l = ob.name.lower()
            if name_fragment in ob_name_l:
                ob.hide_set(True)

    def show_hide_suffix(self, context, show, suffixes):
        scene = context.scene

        suffix_list = suffixes
        if isinstance(suffixes, str):
            suffix_list = [suffixes]

        for ob in scene.objects:
            ob_name_l = ob.name.lower()
            if any(ob_name_l.endswith(suf) for suf in suffix_list):
                should_swap_state = ob.hide_get() != (not show)
                if should_swap_state:
                    ob.hide_set(not ob.hide_get())

    def show_only_suffix(self, context, suffixes):
        scene = context.scene

        suffix_list = suffixes
        if isinstance(suffixes, str):
            suffix_list = [suffixes]

        for ob in scene.objects:
            ob_name_l = ob.name.lower()
            should_hide = not any(ob_name_l.endswith(suf) for suf in suffix_list)
            ob.hide_set(should_hide)

    def show_object(self, context, show, name):
        scene = context.scene

        name_lower = name.lower()
        for ob in scene.objects:
            ob_name_l = ob.name.lower()
            if ob_name_l == name_lower:
                ob.hide_set(not show)
            
class LODOperatorTemplate(LODUtilityOperatorBase):
    lod_name = ""
    suffixes = ()
    mode = "show"  # could be "show", "hide", "show_only"

    def execute(self, context):
        if self.mode == "show":
            self.show_hide_suffix(context, True, self.suffixes)
            self.show_object(context, True, self.lod_name)
        elif self.mode == "hide":
            self.show_hide_suffix(context, False, self.suffixes)
            self.show_object(context, False, self.lod_name)
        elif self.mode == "show_only":
            self.show_only_suffix(context, self.suffixes)
            self.show_object(context, True, self.lod_name)
        return {'FINISHED'}
    
def create_lod_operator(name, label, lod_name, suffixes, mode):
    created_type = type(
        name,
        (LODOperatorTemplate,),
        {
            "bl_idname": f"angelstudios.{mode}_{lod_name.lower()}_lod",
            "bl_label": label,
            "lod_name": lod_name,
            "suffixes": suffixes,
            "mode": mode
        }
    )
    return created_type

class IsolateLODMenu(bpy.types.Menu):
    bl_label = "Isolate LOD"
    bl_idname = "ANGELSTUDIOS_MT_lod_menu_isolate"

    def draw(self, context):
        layout = self.layout
        for lod_name in ("A","H","M","L","VL"):
            layout.operator(f"angelstudios.show_only_{lod_name.lower()}_lod", text=lod_name)

class ShowLODMenu(bpy.types.Menu):
    bl_label = "Show LOD"
    bl_idname = "ANGELSTUDIOS_MT_lod_menu_show"

    def draw(self, context):
        layout = self.layout
        for lod_name in ("A","H","M","L","VL"):
            layout.operator(f"angelstudios.show_{lod_name.lower()}_lod", text=lod_name)

class HideLODMenu(bpy.types.Menu):
    bl_label = "Hide LOD"
    bl_idname = "ANGELSTUDIOS_MT_lod_menu_hide"

    def draw(self, context):
        layout = self.layout
        for lod_name in ("A","H","M","L","VL"):
            layout.operator(f"angelstudios.hide_{lod_name.lower()}_lod", text=lod_name)
            
class HideDamagedPanels(LODUtilityOperatorBase):
    bl_idname = "angelstudios.hide_dmg_panels"
    bl_label = "Hide Damaged Panels"
    
    def execute(self, context):
        self.hide_contains(context, "_dmg_")
        return {'FINISHED'}
    
class HideUndamagedPanels(LODUtilityOperatorBase):
    bl_idname = "angelstudios.hide_udmg_panels"
    bl_label = "Hide Undamaged Panels"
    
    def execute(self, context):
        self.hide_contains(context, "_udmg_")
        return {'FINISHED'}

def generate_classes():
    for lod_name in ("A", "H", "M", "L", "VL"):
        suffixes = (f"_{lod_name.lower()}", f"_{lod_name.lower()}2")
        show_type = create_lod_operator(f"ShowLod{lod_name}Operator", lod_name, lod_name, suffixes, "show")
        hide_type = create_lod_operator(f"HideLod{lod_name}Operator", lod_name, lod_name, suffixes, "hide")
        show_only_type = create_lod_operator(f"ShowLodOnly{lod_name}Operator", lod_name, lod_name, suffixes, "show_only")
        generated_classes.extend((show_type, hide_type, show_only_type))
   
def register():
    generate_classes()
    for generated_class in generated_classes:
        bpy.utils.register_class(generated_class)
    bpy.utils.register_class(IsolateLODMenu)
    bpy.utils.register_class(ShowLODMenu)
    bpy.utils.register_class(HideLODMenu)
    bpy.utils.register_class(HideDamagedPanels)
    bpy.utils.register_class(HideUndamagedPanels)

def unregister():
    bpy.utils.register_class(HideLODMenu)
    bpy.utils.register_class(ShowLODMenu)
    bpy.utils.register_class(IsolateLODMenu)
    bpy.utils.unregister_class(HideUndamagedPanels)
    bpy.utils.unregister_class(HideDamagedPanels)
    for generated_class in reversed(generated_classes):
        bpy.utils.unregister_class(generated_class)
    
    