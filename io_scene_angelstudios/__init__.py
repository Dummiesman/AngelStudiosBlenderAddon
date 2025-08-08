bl_info = {
    "name": "Angel Studios Formats (ARTS/AGE)",
    "author": "Dummiesman",
    "version": (0, 0, 7),
    "blender": (3, 1, 0),
    "location": "File > Import-Export",
    "description": "Import-Export ARTS/AGE model and animation files",
    "warning": "",
    "doc_url": "https://github.com/Dummiesman/AngelStudiosBlenderAddon/",
    "tracker_url": "https://github.com/Dummiesman/AngelStudiosBlenderAddon/",
    "support": 'COMMUNITY',
    "category": "Import-Export"}

import bpy
import textwrap 

from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        StringProperty,
        CollectionProperty,
        PointerProperty,
        )
from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        )
        
from . import import_tex as import_tex
from . import import_modscene as import_modscene
from . import export_modscene as export_modscene
from . import import_bmsscene as import_bmsscene
from . import export_bmsscene as export_bmsscene
from . import util_ops as util_ops

# ARTS
class ImportDLP(bpy.types.Operator, ImportHelper):
    """Import from ARTS DLP (.DLP)"""
    bl_idname = "import_scene.dlp"
    bl_label = 'Import ARTS DLP'
    bl_options = {'UNDO'}

    filename_ext = ".dlp"
    filter_glob: StringProperty(default="*.dlp", options={'HIDDEN'})

    def execute(self, context):
        from . import import_dlp
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))

        return import_dlp.load(self, context, **keywords)
    
class ImportBMS(bpy.types.Operator, ImportHelper):
    """Import from ARTS BMS (.BMS)"""
    bl_idname = "import_mesh.bms"
    bl_label = 'Import ARTS BMS'
    bl_options = {'UNDO'}

    filename_ext = ".bms"
    filter_glob: StringProperty(default="*.bms", options={'HIDDEN'})

    def execute(self, context):
        from . import import_bms
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))

        return import_bms.load(self, context, **keywords)
        
# AGE
class ImportBND(bpy.types.Operator, ImportHelper):
    """Import from BND file format (.bnd)"""
    bl_idname = "import_scene.bnd"
    bl_label = 'Import Bound'
    bl_options = {'UNDO'}

    filename_ext = ".bnd"
    filter_glob: StringProperty(default="*.bnd", options={'HIDDEN'})

    def execute(self, context):
        from . import import_bnd
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))

        return import_bnd.load(self, context, **keywords)


class ImportBBND(bpy.types.Operator, ImportHelper):
    """Import from BBND file format (.bbnd)"""
    bl_idname = "import_scene.bbnd"
    bl_label = 'Import Binary Bound'
    bl_options = {'UNDO'}

    filename_ext = ".bbnd"
    filter_glob: StringProperty(default="*.bbnd", options={'HIDDEN'})

    bound_repair_debug: BoolProperty(
        name="Make Empty At First Vertex",
        description="Places an empty object at the first vertex, in order to help repair broken bounds.",
        default=False,
        )
        
    def draw(self, context):
        layout = self.layout
        
        wrapp = textwrap.TextWrapper(width=42)
        wList = wrapp.wrap(text=("In the previous versions of this addon, BBND files were exported in a way which could cause quads connected to the first vertex to turn into triangles instead. "
                                 "Use this option to place an empty object at the first vertex, so you can easily locate and fix this issue if it occurred.")) 
        for text in wList: 
            row = layout.row(align = True)
            row.alignment = 'EXPAND'
            row.label(text=text)
            
        sub = layout.row()
        sub.prop(self, "bound_repair_debug")

        
    def execute(self, context):
        from . import import_bbnd
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))

        return import_bbnd.load(self, context, **keywords)


class ExportBND(bpy.types.Operator, ExportHelper):
    """Export to BND file format (.BND)"""
    bl_idname = "export_scene.bnd"
    bl_label = 'Export BND'

    filename_ext = ".bnd"
    filter_glob: StringProperty(
            default="*.bnd",
            options={'HIDDEN'},
            )

    export_binary: BoolProperty(
        name="Export Binary Bound",
        description="Export a binary bound along the ASCII bound",
        default=False,
        )
        
    export_terrain: BoolProperty(
        name="Export Terrain Bound",
        description="Export a terrain bound along the binary bound",
        default=False,
        )

    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply object modifiers in the exported file",
        default=True,
        )
    
    bnd_version : EnumProperty(items = [('1.01','1.01','','',101), 
                                        ('1.10','1.10','','',110)],
                               name = "Version",
                               default = '1.01')
        
    def draw(self, context):
        layout = self.layout
        sub = layout.row()
        sub.prop(self, "apply_modifiers")
        sub = layout.row()
        sub.prop(self, "bnd_version")
        if self.bnd_version == "1.01":
            sub = layout.row()
            sub.prop(self, "export_binary")
            sub = layout.row()
            sub.enabled = self.export_binary
            sub.prop(self, "export_terrain")
        else:
            sub = layout.row()
            sub.prop(self, "export_binary")
        
    def execute(self, context):
        from . import export_bnd
        
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
                                    
        return export_bnd.save(self, context, **keywords)
        
class ImportMOD(bpy.types.Operator, ImportHelper):
    """Import from MOD file format (.mod)"""
    bl_idname = "import_mesh.mod"
    bl_label = 'Import Model'
    bl_options = {'UNDO'}

    filename_ext = ".mod"
    filter_glob: StringProperty(default="*.mod;*.xmod", options={'HIDDEN'})

    def armature_poll(self, object):
        return object.type == 'ARMATURE'
        
    bind_armature: PointerProperty(name="Bind To Armature", type=bpy.types.Object, poll=armature_poll)
    
    def execute(self, context):
        from . import import_mod
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))

        return import_mod.load(self, context, **keywords)
        
class ImportSKEL(bpy.types.Operator, ImportHelper):
    """Import from SKEL file format (.skel)"""
    bl_idname = "import_mesh.skel"
    bl_label = 'Import Skeleton'
    bl_options = {'UNDO'}

    filename_ext = ".skel"
    filter_glob: StringProperty(default="*.skel", options={'HIDDEN'})

    def execute(self, context):
        from . import import_skel
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))

        return import_skel.load(self, context, **keywords)
        
class ImportANIM(bpy.types.Operator, ImportHelper):
    """Import from ANIM file format (.anim)"""
    bl_idname = "import_mesh.anim"
    bl_label = 'Import Animation'
    bl_options = {'UNDO'}

    filename_ext = ".anim"
    filter_glob: StringProperty(default="*.anim", options={'HIDDEN'})

    def execute(self, context):
        from . import import_anim
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))

        return import_anim.load(self, context, **keywords)

class ExportBMS(bpy.types.Operator, ExportHelper):
    """Export to BMS file format (.bms)"""
    bl_idname = "export_mesh.bms"
    bl_label = 'Export BMS'

    filename_ext = ".bms"
    filter_glob: StringProperty(
            default="*.bms",
            options={'HIDDEN'},
            )
            
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

    def execute(self, context):
        from . import export_bms
        
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
                                    
        return export_bms.save(self, context, **keywords)
    
class ExportGEO(bpy.types.Operator, ExportHelper):
    """Export to GEOD file format (.geo)"""
    bl_idname = "export_mesh.geo"
    bl_label = 'Export GEO'

    filename_ext = ".geo"
    filter_glob: StringProperty(
            default="*.geo",
            options={'HIDDEN'},
            )
            
    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply object modifiers in the exported file",
        default=True,
        )
    
    selection_only: BoolProperty(
        name="Selection Only",
        description="Export only selected objects",
        default=False,
        )
    
    run_translator: BoolProperty(
        name="Run Asset Manager Translation",
        description="If Angel dev tools are found, run asset translation to create runtime files",
        default=False,
        )

    def execute(self, context):
        from . import export_geo
        
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
                                    
        return export_geo.save(self, context, **keywords)
            
class ExportMOD(bpy.types.Operator, ExportHelper):
    """Export to MOD file format (.mod)"""
    bl_idname = "export_mesh.mod"
    bl_label = 'Export MOD'

    filename_ext = ".mod"
    filter_glob: StringProperty(
            default="*.mod;*.xmod",
            options={'HIDDEN'},
            )
            
    mod_version : EnumProperty(items = [('1.09','1.09','','',109), 
                                        ('1.10','1.10','','',110)],
                               name = "Version",
                               default = '1.09')
                               
    def filetype_update(self, context):
        ExportMOD.filename_ext = "." + self.export_extension.lower()
        
    export_extension : EnumProperty(items = [('mod','mod','','',0), 
                                             ('xmod','xmod','','',1)],
                               name = "Extension",
                               default = 'mod', update = filetype_update)
                               
    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply object modifiers in the exported file",
        default=True,
        )

    def execute(self, context):
        from . import export_mod
        
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
                                    
        return export_mod.save(self, context, **keywords)
        
class ExportSKEL(bpy.types.Operator, ExportHelper):
    """Export to SKEL file format (.skel)"""
    bl_idname = "export_mesh.skel"
    bl_label = 'Export SKEL'

    filename_ext = ".skel"
    filter_glob: StringProperty(
            default="*.skel",
            options={'HIDDEN'},
            )
    
    skel_version : EnumProperty(items = [('1.00','1.00','','',100)],
                                name = "Version",
                                default = '1.00')

    def execute(self, context):
        from . import export_skel
        
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
                                    
        return export_skel.save(self, context, **keywords)

# Custom menus
class AngelStudiosMenu(bpy.types.Menu):
    bl_idname = "ANGEL_MT_tools_menu"
    bl_label = "Angel Tools"

    def draw(self, context):
        layout = self.layout

        layout.operator("angelstudios.import_bms_scene")
        layout.operator("angelstudios.export_bms_scene")

        layout.separator()

        layout.operator("angelstudios.import_mod_scene")
        layout.operator("angelstudios.export_mod_scene")
        layout.operator("angelstudios.import_tex")

        layout.separator()
        
        layout.operator("angelstudios.show_h_lod")
        layout.operator("angelstudios.show_m_lod")
        layout.operator("angelstudios.show_l_lod")
        layout.operator("angelstudios.show_vl_lod")

        layout.separator()

        layout.operator("angelstudios.hide_udmg_panels")
        layout.operator("angelstudios.hide_dmg_panels")
        
    def menu_draw(self, context):
        self.layout.menu("ANGEL_MT_tools_menu")
        
# Add to a menu
def menu_func_export(self, context):
    self.layout.separator()
    self.layout.label(text="Angel Studios Formats")
    self.layout.operator(ExportBND.bl_idname, text="Bound (.bnd)")
    self.layout.operator(ExportMOD.bl_idname, text="Model (.mod)")
    self.layout.operator(ExportSKEL.bl_idname, text="Skeleton (.skel)")
    self.layout.operator(ExportBMS.bl_idname, text="ARTS Mesh Set (.bms)")
    self.layout.operator(ExportGEO.bl_idname, text="ARTS Scene (.geo)")
    self.layout.separator()
    
def menu_func_import(self, context):
    self.layout.separator()
    self.layout.label(text="Angel Studios Formats")
    self.layout.operator(ImportBMS.bl_idname, text="ARTS Mesh Set (*.bms)")
    self.layout.operator(ImportDLP.bl_idname, text="ARTS DLP Template (*.dlp)")
    self.layout.operator(ImportBND.bl_idname, text="Bound (.bnd)")
    self.layout.operator(ImportEM.bl_idname, text="Edge Model (.em)")
    self.layout.operator(ImportMOD.bl_idname, text="Model (.mod)")
    self.layout.operator(ImportSKEL.bl_idname, text="Skeleton (.skel)")
    # self.layout.operator(ImportANIM.bl_idname, text="Animation (.anim)")
    self.layout.separator()


# Register factories
def register():
    bpy.utils.register_class(ExportBMS)
    bpy.utils.register_class(ExportGEO)
    bpy.utils.register_class(ImportDLP)
    bpy.utils.register_class(ImportBMS)
    bpy.utils.register_class(ImportBND)
    bpy.utils.register_class(ExportBND)
    bpy.utils.register_class(ImportMOD)
    bpy.utils.register_class(ExportMOD)
    bpy.utils.register_class(ImportSKEL)
    bpy.utils.register_class(ExportSKEL)
    bpy.utils.register_class(ImportANIM)
    bpy.utils.register_class(ImportEM)
    util_ops.register()
    import_tex.register()
    import_modscene.register()
    export_modscene.register()
    import_bmsscene.register()
    export_bmsscene.register()
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.utils.register_class(AngelStudiosMenu)
    bpy.types.TOPBAR_MT_editor_menus.append(AngelStudiosMenu.menu_draw)


def unregister():
    bpy.types.TOPBAR_MT_editor_menus.remove(AngelStudiosMenu.menu_draw)
    bpy.utils.unregister_class(AngelStudiosMenu)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    export_modscene.register()
    import_modscene.register()
    export_bmsscene.register()
    import_bmsscene.register()
    import_tex.unregister()
    util_ops.unregister()
    bpy.utils.unregister_class(ImportEM)
    bpy.utils.unregister_class(ImportANIM)
    bpy.utils.unregister_class(ExportSKEL)
    bpy.utils.unregister_class(ImportSKEL)
    bpy.utils.unregister_class(ExportMOD)
    bpy.utils.unregister_class(ImportMOD)
    bpy.utils.unregister_class(ExportBND)
    bpy.utils.unregister_class(ImportBND)
    bpy.utils.unregister_class(ImportBMS)
    bpy.utils.unregister_class(ImportDLP)
    bpy.utils.unregister_class(ExportGEO)
    bpy.utils.unregister_class(ExportBMS)

if __name__ == "__main__":
    register()
