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

class ImportMODSceneOperator(bpy.types.Operator):
    """Bulk import MOD/XMOD as a scene"""
    bl_idname = "angelstudios.import_mod_scene"
    bl_label = "Import MOD/XMOD Scene"
    bl_options = {'REGISTER'}

    directory: StringProperty(name="Input Directory")
    scene_name: StringProperty(name="Scene Name")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if len(self.scene_name) == 0:
            self.report({"ERROR"}, "Scene name was empty")
        else:
            from . import import_mod
            
            # import models
            scene_prefix = f"{self.scene_name}_"

            matrix_basepath = self.directory
            search_path = self.directory
            for _ in range(4):
                search_path = os.path.dirname(search_path)
                geometry_path = os.path.join(search_path, "geometry")
                if os.path.exists(geometry_path):
                    matrix_basepath = geometry_path
                    break

            textures_basepath = self.directory
            search_path = self.directory
            for _ in range(4):
                search_path = os.path.dirname(search_path)
                for entry in os.listdir(search_path):
                    entry_path = os.path.join(search_path, entry)
                    if os.path.isdir(entry_path) and entry.lower().startswith("texture"):
                        textures_basepath = entry_path
                        break

            print("Textures path: " + textures_basepath)

            for file in os.listdir(self.directory):
                file_l = file.lower()
                if file_l.startswith(scene_prefix) and (file_l.endswith(".mod") or file_l.endswith(".xmod")):
                    print("IMPORTING " + file_l)
                    file_noext = os.path.splitext(file)[0]
                    imported_ob = import_mod.import_mod_object(filepath=os.path.join(self.directory, file), textures_basepath = textures_basepath)
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
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(ImportMODSceneOperator)

def unregister():
    bpy.utils.unregister_class(ImportMODSceneOperator)