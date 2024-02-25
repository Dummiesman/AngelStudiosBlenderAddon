import bpy

from bpy.props import (
        StringProperty,
        )
from bpy_extras.io_utils import (
        ImportHelper,
        )

class ImportTEX(bpy.types.Operator, ImportHelper):
    """Import image from Angel Studios TEX file format"""
    bl_idname = "angelstudios.import_tex"
    bl_label = 'Import TEX Image'
    bl_options = {'UNDO'}

    filename_ext = ".tex"
    filter_glob: StringProperty(default="*.tex", options={'HIDDEN'})

    def execute(self, context):
        from .tex_file import TEXFile

        filepath = self.properties.filepath
        image_name = bpy.path.display_name_from_filepath(self.properties.filepath)
        
        tex = TEXFile(filepath)
        if tex.is_compressed_format():
            tex.decompress()
            
        tf_img = tex.to_blender_image(image_name)
        tf_img.filepath_raw = filepath # set filepath manually for TEX stuff, since it didn't come from an actual file import
        
        return {'FINISHED'}

def register():
    bpy.utils.register_class(ImportTEX)

def unregister():
    bpy.utils.unregister_class(ImportTEX)