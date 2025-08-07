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

class ImportBMSSceneOperator(bpy.types.Operator):
    """Bulk import BMS as a scene"""
    bl_idname = "angelstudios.import_bms_scene"
    bl_label = "Import BMS Scene"
    bl_options = {'REGISTER'}

    directory: StringProperty(name="Input Directory")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        from . import import_bms
        
        # import models
        for file in os.listdir(self.directory):
            file_l = file.lower()
            if file_l.endswith(".bms"):
                print("IMPORTING " + file_l)
                file_noext = os.path.splitext(file)[0]
                imported_ob = import_bms.import_bms_object(filepath=os.path.join(self.directory, file))
                imported_ob.name = file_noext
        
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
    bpy.utils.register_class(ImportBMSSceneOperator)

def unregister():
    bpy.utils.unregister_class(ImportBMSSceneOperator)