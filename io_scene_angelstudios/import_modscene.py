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

class ImportSceneOperator(bpy.types.Operator):
    """Bulk import MOD/XMOD as a scene"""
    bl_idname = "angelstudios.import_mod_scene"
    bl_label = "Import MOD/XMOD Scene"
    bl_options = {'REGISTER'}

    mod_path: StringProperty(name="Models Path")
    scene_name: StringProperty(name="Scene Name")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if not os.path.isdir(self.mod_path):
            self.report({"ERROR"}, "Models Path doesn't exist!")
        elif len(self.scene_name) == 0:
            self.report({"ERROR"}, "Scene name was empty")
        else:
            from . import import_mod
            
            # import models
            scene_prefix = f"{self.scene_name}_"
            matrix_basepath = os.path.join(os.path.abspath(os.path.join(self.mod_path, "..")), "geometry") # Dis-gusting. Temporary.
            for file in os.listdir(self.mod_path):
                file_l = file.lower()
                if file_l.startswith(scene_prefix) and (file_l.endswith(".mod") or file_l.endswith(".xmod")):
                    print("IMPORTING " + file_l)
                    file_noext = os.path.splitext(file)[0]
                    imported_ob = import_mod.import_mod_object(filepath=os.path.join(self.mod_path, file))
                    imported_ob.name = file_noext[len(scene_prefix):]
                    imported_ob_basename = utils.object_basename(file_noext)
                    if os.path.exists(os.path.join(matrix_basepath, f"{imported_ob_basename}.mtx")):
                        imported_ob.matrix_world = utils.read_matrix3x4(imported_ob_basename, matrix_basepath)
            
            # postprocess: merge down materials
            mats = bpy.data.materials
            for mat in mats:
                (original, _, ext) = mat.name.rpartition(".")
                
                if ext.isnumeric() and mats.find(original) != -1:
                    print("%s -> %s" %(mat.name, original))
                    
                    mat.user_remap(mats[original])
                    mats.remove(mat)

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

def register():
    bpy.utils.register_class(ImportSceneOperator)

def unregister():
    bpy.utils.unregister_class(ImportSceneOperator)