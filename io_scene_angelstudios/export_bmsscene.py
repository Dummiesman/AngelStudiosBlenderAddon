import bpy
import os
from . import utils as utils

from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        StringProperty,
        CollectionProperty,
        IntProperty,
        PointerProperty
        )

class ExportBMSSceneOperator(bpy.types.Operator):
    """Bulk export BMS as a scene"""
    bl_idname = "angelstudios.export_bms_scene"
    bl_label = "Export BMS Scene"
    bl_options = {'REGISTER'}


    directory: StringProperty(name="Output Directory")

    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply object modifiers in the exported file",
        default=True,
        )
    
    export_normals: BoolProperty(
        name="Include Normals",
        default=True,
        )
    
    export_colors: BoolProperty(
        name="Include Vertex Colors",
        default=True,
        )
    
    export_uvs: BoolProperty(
        name="Include UV Mapping",
        default=True,
        )
    
    export_planes: BoolProperty(
        name="Export Planes",
        description="Compute and export a plane for mesh faces, typically desired as these are used in rendering",
        default=True,
        )
    
    selected_only: BoolProperty(name="Selected Only")

    # Filters folders
    filter_folder = BoolProperty(
        default=True,
        options={"HIDDEN"}
        )

    @classmethod
    def poll(cls, context):
        return True
    def execute(self, context):
        obs = [ob for ob in (context.selected_objects if self.selected_only else context.scene.objects) if ob.type == 'MESH']

        if not os.path.isdir(self.directory):
            self.report({"ERROR"}, "Models Path doesn't exist!")
        elif len(obs) == 0:
            self.report({"ERROR"}, "Nothing to export (No selection or empty scene)")
        else:
            from . import export_bms
            
            # export mod/xmod
            for ob in obs:
                filepath = os.path.join(self.directory, f"{ob.name}.BMS")
                export_bms.export_bms_object(filepath, ob, self.apply_modifiers, self.export_normals, self.export_colors, self.export_uvs, self.export_planes)
                    
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def register():
    bpy.utils.register_class(ExportBMSSceneOperator)

def unregister():
    bpy.utils.unregister_class(ExportBMSSceneOperator)