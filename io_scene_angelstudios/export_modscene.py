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
    
    export_matrices: BoolProperty(
        name="Export Matrices",
        description="Export a MTX file for each object in the scene",
        default=True,
        )
    
    export_bounding_boxes: BoolProperty(
        name="Export Bounding Boxes",
        description="Export a box BND file for each object in the scene",
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

    def write_matrix(self, name, directory, ob):
        utils.write_matrix3x4(name, directory, ob.matrix_world)

    def write_bounding_box(self, name, directory, ob):
        bounds = utils.bounds(ob)
        bound_size = (bounds.x.max - bounds.x.min, bounds.y.max - bounds.y.min, bounds.z.max - bounds.z.min)
        bound_center = ((bounds.x.min + bounds.x.max) / 2.0, (bounds.y.min + bounds.y.max) / 2.0, (bounds.z.min + bounds.z.max) / 2.0)
        bound_centroid = (bound_center[0] - ob.location[0], bound_center[1] - ob.location[1], bound_center[2] - ob.location[2])

        path = os.path.join(directory, f"{name}.bnd")
        with open(path, 'w') as file:
            file.write("version: 1.10\n")
            file.write("type: box\n\n")
            file.write("size: %.6f %.6f %.6f\n" % utils.translate_size(bound_size))
            file.write("centroid: %.6f %.6f %.6f\n\n" % utils.translate_vector(bound_centroid))
            file.write("materials: 1 \n")
            file.write("type: BASE\n")
            file.write("mtl default {\n")
            file.write("	elasticity: 0.100000 \n")
            file.write("	friction: 0.500000 \n")
            file.write("}\n\n")

    def execute(self, context):
        obs = [ob for ob in (context.selected_objects if self.selected_only else context.scene.objects) if ob.type == 'MESH']
        ob_map = {ob.name.lower(): ob for ob in obs}
        unique_obs = utils.get_unique_object_names(obs)

        if not os.path.isdir(self.mod_path):
            self.report({"ERROR"}, "Models Path doesn't exist!")
        elif len(obs) == 0:
            self.report({"ERROR"}, "Nothing to export (No selection or empty scene)")
        else:
            from . import export_mod
            scene_prefix = f"{self.scene_name}_"
            basepath = os.path.abspath(os.path.join(self.mod_path, ".."))
            matrix_basepath = os.path.join(basepath, "geometry") 
            bound_basepath = os.path.join(basepath, "bound")

            # export mod/xmod
            for ob in obs:
                filepath = os.path.join(self.mod_path, f"{scene_prefix}{ob.name}.{self.export_extension}")
                export_mod.export_mod_object(filepath, ob, self.mod_version, self.apply_modifiers)
            
            # export matrices/bounds for the highest LOD
            lod_suffixes = ["", "_h", "_m", "_l", "_vl"]
            for ob_prefix in unique_obs:
                for suffix in lod_suffixes:
                    ob_name = f"{ob_prefix}{suffix}"
                    if ob_name in ob_map:
                        ob = ob_map[ob_name]

                        # export mtx
                        if os.path.isdir(matrix_basepath) and self.export_matrices:
                            mtx_name = f"{scene_prefix}{ob_prefix}"
                            self.write_matrix(mtx_name, matrix_basepath, ob)

                        # export bnd
                        if os.path.isdir(bound_basepath) and self.export_bounding_boxes:
                            bnd_name = f"{scene_prefix}{ob_prefix}"
                            self.write_bounding_box(bnd_name, bound_basepath, ob)

                        break
                    
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


def register():
    bpy.utils.register_class(ExportSceneOperator)

def unregister():
    bpy.utils.unregister_class(ExportSceneOperator)