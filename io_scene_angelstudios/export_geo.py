import os, time
import subprocess

import bpy
from . import utils as utils
from bpy_extras import  node_shader_utils

######################################################
# EXPORT MAIN FILES
######################################################
def export_geo(filepath, selection_only=False, apply_modifiers=True):
    with open(filepath, 'w') as file:
        # get objects to export
        export_obs = bpy.context.selected_objects if selection_only else bpy.context.scene.objects
        export_obs = [x for x in export_obs if x.type == 'MESH']
        material_set = set()
        textures_set = set()
        texture_flags = {}

        # get final meshes
        final_meshes = {}
        depsgraph = bpy.context.evaluated_depsgraph_get()
        for ob in export_obs:
            me = None
            if apply_modifiers:
                export_ob = ob.evaluated_get(depsgraph)
                me = export_ob.to_mesh()
            else:
                me = ob.data.copy()
            me.calc_normals_split()
            final_meshes[ob.name] = me

        # gather materials and textures
        for ob in export_obs:
            for material in me.materials:
                material_set.add(material)
        for material in material_set:
            mat_wrap = node_shader_utils.PrincipledBSDFWrapper(material) if material else None
            texture = mat_wrap.base_color_texture
            if texture is not None and texture.image is not None:
                textures_set.add(texture.image)

        # gather total stats
        num_vertices = 0
        num_elements = 0
        num_groups = 4 # start at 4 for H M L VL groups
        num_materials = len(material_set)
        num_textures = len(textures_set)
        for ob in export_obs:
            me = final_meshes[ob.name]
            num_vertices += len(me.vertices)
            num_elements += len(me.polygons)
            num_groups += 1

        # write stats
        file.write(f"## Geo3 {filepath}\n")
        file.write(f"## Vertices        {num_vertices}\n")
        file.write(f"## Elements        {num_elements}\n")
        file.write(f"## Groups          {num_groups}\n")
        file.write(f"## Materials       {num_materials}\n")
        file.write(f"## Textures        {num_textures}\n")
        file.write("\n")

        # write materials
        for material in material_set:
           mat_wrap = node_shader_utils.PrincipledBSDFWrapper(material) if material else None
           file.write(f"material {material.name} {{\n")
           file.write("	diffuse          %.6f          %.6f          %.6f\n" % mat_wrap.base_color[:3])
           file.write("}\n")
           file.write("\n")

        # write textures
        for texture in textures_set:
            # determine flags from materials using this texture
            texture_flags = ["color"]
            for material in material_set:
                mat_wrap = node_shader_utils.PrincipledBSDFWrapper(material) if material else None
                mat_texture = mat_wrap.base_color_texture
                if mat_texture is not None and mat_texture.image == texture and mat_texture.extension == 'REPEAT':
                    texture_flags.append("swrap")
                    texture_flags.append("twrap")

            image_name = utils.get_image_name_from_path_noext(texture.filepath)
            source_file = os.path.realpath(bpy.path.abspath(texture.filepath, library=texture.library))
            file.write(f"texture {image_name} {{\n")
            file.write(f"	source \"{source_file}\"\n")
            file.write(f"	{' '.join(texture_flags)} \n")
            file.write("}\n")
            file.write("\n")
                
        # write vertices
        for ob in export_obs:
            me = final_meshes[ob.name]
            for vert in me.vertices:
               translated_vert = utils.translate_vector(vert.co)
               file.write("vx     %.6f     %.6f    %.6f\n" % translated_vert)
        file.write("\n")

        # write faces
        vert_offset = 1
        for ob in export_obs:
            me = final_meshes[ob.name]
            uv_layer = me.uv_layers.active.data if me.uv_layers.active is not None else None
            vc_layer = me.vertex_colors.active
            for poly in me.polygons:
                material = me.materials[poly.material_index]
                mat_wrap = node_shader_utils.PrincipledBSDFWrapper(material) if material else None
                texture = mat_wrap.base_color_texture
                file.write("facet {\n")
                file.write(f"	res      {poly.loop_total}\n")
                file.write(f"	priority 50\n")
                file.write(f"	map      1 1\n")
                file.write(f"	tile    1.000000 1.000000\n")
                file.write(f"	material {me.materials[poly.material_index].name}\n")
                if texture is not None and texture.image is not None:
                    image_name = utils.get_image_name_from_path_noext(texture.image.filepath)
                    file.write(f"	texture  {image_name}\n")

                poly_flags = ["solid", "shade", "cull", "zread", "zwrite", "antialias"]
                if vc_layer is not None:
                    poly_flags.insert(0, "cpv")
                file.write(f"	flags {{ {' '.join(poly_flags)} }}\n")

                #vx
                file.write("	vx ")
                for loop_index in poly.loop_indices:
                   loop = me.loops[loop_index]
                   file.write(f"{loop.vertex_index + vert_offset} ")
                file.write("\n")

                #cpv
                if vc_layer is not None:
                    file.write("	cpv\n")
                    for loop_index in poly.loop_indices:
                        color = tuple(vc_layer.data[loop_index].color)
                        file.write("		%.6f %.6f %.6f %.6f\n" % color)

                #s/tmap
                if uv_layer is not None:
                    file.write("	smap\n")
                    file.write("		")
                    for loop_index in poly.loop_indices:
                        translated_uv = uv_layer[loop_index].uv
                        file.write("%.6f " % translated_uv[0])
                    file.write("\n")
                    file.write("	tmap\n")
                    file.write("		")
                    for loop_index in poly.loop_indices:
                        translated_uv = uv_layer[loop_index].uv
                        file.write("%.6f " % translated_uv[1])
                    file.write("\n")

                # normals
                file.write(f"	normals {{\n")
                for loop_index in poly.loop_indices:
                   loop = me.loops[loop_index]
                   translated_normal = utils.translate_vector(loop.normal)
                   file.write(f"		%.6f %.6f %.6f\n" % translated_normal)
                file.write("	}\n")
                file.write("}\n\n")

            vert_offset += len(me.vertices)

        # write groups
        index_offset = 1
        for ob in export_obs:
           me = final_meshes[ob.name]
           file.write(f"group {ob.name} {{\n")
           file.write("	patch\n")

           if len(me.polygons) > 0:
            file.write("	    ")
            for i, poly in enumerate(me.polygons):
                # split into groups of 10
                if i > 0 and (i % 10) == 0 and i < (len(me.polygons) - 1):
                    file.write("\n")
                    file.write("	    ")
                file.write(f"{i + index_offset} ")
            file.write("\n")

           file.write("}\n\n")
           index_offset += len(me.polygons)

        # write combined groups for H M L VL
        combined_group_names = ["H", "M", "L", "VL"]
        for group_name in combined_group_names:
            index_offset = 1
            group_patch = []

            for ob in export_obs:
                me = final_meshes[ob.name]
                if ob.name.upper().endswith(f"_{group_name}"):
                    for i, poly in enumerate(me.polygons):
                        group_patch.append(i + index_offset)
                index_offset += len(me.polygons)
            if len(group_patch) > 0:
                file.write(f"group {group_name} {{\n")
                file.write("	patch\n")
                file.write("	    ")
                for i, index in enumerate(group_patch):
                    # split into groups of 10
                    if i > 0 and (i % 10) == 0 and i < (len(group_patch) - 1):
                        file.write("\n")
                        file.write("	    ")
                    file.write(f"{index} ")
                file.write("\n")
                file.write("}\n\n")

        file.write("## EOF\n")
    return

######################################################
# TOOLCHAIN
######################################################
def run_translator_process(operator, filepath, review=False):
    """Run the asset manager and convert to runtime files (blocking)"""
    if not os.path.exists("c:\\toolroot.ini"):
        operator.report({'WARNING'}, "Translation failed, cannot find toolroot.ini")
        return
    
    # get the path from toolroot
    tools_path = None
    with open('c:\\toolroot.ini', 'r') as file:
        tools_path = file.read().strip()
    if not os.path.exists(tools_path):
        operator.report({'WARNING'}, f"Translation failed, toolroot.ini points to nonexistant path {tools_path}")
        return
    
    # check if am.exe exists
    am_path = os.path.join(tools_path, "am.exe")
    if not os.path.exists(am_path):
        operator.report({'WARNING'}, "Translation failed, cannot fnd am.exe")
        return
    
    # determine the shop path, the exported geo should be in shop\geo\*
    shop_path = os.path.abspath(os.path.join(tools_path, "..", "shop"))
    if not filepath.lower().startswith(shop_path.lower()):
        operator.report({'ERROR'}, "Exported file is not in the correct shop directory")
        return
    
    # we are now ready to run the translation
    geo_input_path = filepath[len(shop_path)+1:]
    am_args = ["-translate", geo_input_path]
    if review: 
        am_args.insert(0, "-review")
        am_args.insert(0, "-bw")
    p = subprocess.Popen([am_path, *am_args], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=tools_path)

    processing_errors = []
    process_success = True
    for line in p.stdout.readlines():
        print(line.strip())
        if "errors in processing." in line:
            process_success = False
        if line.startswith("ERROR:"):
            processing_errors.append(line.strip())
    
    if not process_success:
        operator.report({'WARNING'}, "Translation had errors:\n" + "\n".join(processing_errors))   
    else:
        operator.report({'INFO'}, "Translation finished succesfully")   

######################################################
# EXPORT
######################################################
def save(operator,
         context,
         filepath="",
         apply_modifiers=False,
         selection_only=False,
         run_translator=False,
         ):
    
    print("exporting GEO: %r..." % (filepath))
    time1 = time.perf_counter()
    
    # write geo
    export_geo(filepath, selection_only, apply_modifiers)

    # run asset manager
    if run_translator:
        run_translator_process(operator, filepath, review=True)
      
    # export complete
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}
