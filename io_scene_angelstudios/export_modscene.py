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

class ExportSceneOperator(bpy.types.Operator):
    """Bulk export MOD/XMOD as a scene"""
    bl_idname = "angelstudios.export_mod_scene"
    bl_label = "Export MOD/XMOD Scene"
    bl_options = {'REGISTER'}

    mod_path: StringProperty(name="Models Path")
    scene_name: StringProperty(name="Scene Name")

    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply object modifiers in the exported file",
        default=True,
        )
    
    selected_only: BoolProperty(name="Selected Only")
    
    mod_version : EnumProperty(items = [('1.09','1.09','','',109), 
                                        ('1.10','1.10','','',110)],
                               name = "File Version",
                               default = '1.09')
                               
    export_extension : EnumProperty(items = [('mod','mod','','',0), 
                                             ('xmod','xmod','','',1)],
                               name = "Extension",
                               default = 'mod')

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        obs = [ob for ob in (context.selected_objects if self.selected_only else context.scene.objects) if ob.type == 'MESH']
        if not os.path.isdir(self.mod_path):
            self.report({"ERROR"}, "Models Path doesn't exist!")
        elif len(obs) == 0:
            self.report({"ERROR"}, "Nothing to export (No selection or empty scene)")
        else:
            from . import export_mod
            scene_prefix = f"{self.scene_name}_"
            matrix_basepath = os.path.join(os.path.abspath(os.path.join(self.mod_path, "..")), "geometry") # Dis-gusting. Temporary.
            for ob in obs:
                full_name = f"{self.scene_name}_{ob.name}"
                ob_basename = utils.object_basename(ob.name)
                
                # export mod
                filepath = os.path.join(self.mod_path, f"{scene_prefix}{ob.name}.{self.export_extension}")
                export_mod.export_mod_object(filepath, ob, self.mod_version, self.apply_modifiers)
                
                # export mtx (TODO: This writes the mtx for each LOD)
                mtx_name = f"{scene_prefix}{ob_basename}"
                utils.write_matrix3x4(mtx_name, matrix_basepath, ob.matrix_world)
                
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


def register():
    bpy.utils.register_class(ExportSceneOperator)

def unregister():
    bpy.utils.unregister_class(ExportSceneOperator)