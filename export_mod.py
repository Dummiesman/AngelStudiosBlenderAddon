import os, time, struct, math, sys
import os.path as path

from . import utils as utils
import bpy, bmesh, mathutils
from bpy_extras import io_utils, node_shader_utils

######################################################
# HELPERS
######################################################
def get_armature(ob):
    for modifier in ob.modifiers:
        if modifier.type == 'ARMATURE':
            return modifier.object.data
    return None
    
def get_illum_type(mat):
    if not mat.use_nodes:
        return "diffuse"
    
    illum = "diffuse"
    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            illum = "emit"
    return illum
    
def get_verts_in_group(me, group_index):
    verts = []
    for v in me.vertices:
        for g in v.groups:
            if g.group == group_index and g.weight > 0.5:
                verts.append(v)
    return verts
    
def get_bone_pos(bone):
    return bone.tail_local

            
#####################################################
# EXPORT MAIN FILES
######################################################
def export_mod_object(filepath, ob, version, apply_modifiers=True):
    if version == "1.09" or  version == "1.10":
        export_mod(filepath, ob, version, apply_modifiers)
    elif version == "1.06":
        export_mod_old(filepath, ob, version, apply_modifiers)
    elif version == "2.00" or version == "2.12":
        export_mod_bin(filepath, ob, version, apply_modifiers)
    else:
        raise Exception(f"export_mod_object: Unrecognized version {version}")

def export_mod_old(filepath, ob, version, apply_modifiers=True):
    """Export an older, adjunct based mod file"""
    raise NotImplementedError ("export_mod_old - not implemented")

def export_mod_bin(filepath, ob, version, apply_modifiers=True):
    """ Export a binary .mod file from newer AGE"""
    raise NotImplementedError ("export_mod_bin - not implemented")

def export_mod(filepath, ob, version, apply_modifiers=True):
    """Export a newer, packet  based mod file"""
    
    # get armature
    # if none is found, the object center is taken to be the "root bone"
    am = get_armature(ob)
    bone_count = len(am.bones) if am is not None else 1
    
    # get mesh data
    export_ob = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()) if apply_modifiers else ob.data
    me = export_ob.to_mesh()

    uv_layer = me.uv_layers.active.data
    vc_layer = me.vertex_colors.active
    
    me.calc_loop_triangles()
    triangle_loops = me.loop_triangles
    triangle_indices = []
    
    for loop in triangle_loops:
        for vertex_index in loop.loops:
            triangle_indices.append(vertex_index)
    material_count = len(ob.material_slots)
    
    if material_count >= 256:
        raise Exception("Cannot export model with more than 256 materials")
    
    # export data
    adjunct_count = 0
    primitive_count = 0
    
    export_vertices = []
    export_normals = []
    export_uvs = []
    export_colors = []
    
    packet_lists = {}
    
    mtxv = []
    mtxn = []
    
    vert_remap = {}
    normal_remap = {}
    vert_bone_map = {}
    uv_remap = {}
    color_remap = {}
    loops_to_polygons = {}
    material_loops = [[] for x in range(material_count)]
    
    # we first need to sort vertices by what bone they're assigned to
    # then export geometry in order of material
    # finally end off with mtxv [bone_adjunct_counts list] mtxn [bone_vert_counts list]
    if am is not None:
        print("make bonemap...")
        bone_id_map = {} # index: name
        for bone in am.bones:
            if 'bone_id' in bone:
                bone_id_map[bone['bone_id']] = bone.name
        print(f"bonemap size is {len(bone_id_map)}")
        
        
        print("map verts...")
        
        unmapped_verts = []
        for v in me.vertices:
            num_groups = 0
            for g in v.groups:
                if g.weight > 0.5:
                    num_groups += 1
                    
            if num_groups == 0:
                print("WARNING: Found a vertex without any group assignments. It will be selected and mapped to the first bone (typically root).")
                v.select = True
                unmapped_verts.append(v)
                
                        
        for bone_idx in range(len(bone_id_map)):
            grp_name = bone_id_map[bone_idx]
            if not grp_name in ob.vertex_groups:
                print(f"\tskipping group {grp_name}: no vertex group")
                mtxn.append(0)
                mtxv.append(0)
                continue
            
            grp_index = ob.vertex_groups[grp_name].index
            grp_vert_count = 0
            grp_normal_count = 0
            
            print(f"\tgroup {grp_name}:{grp_index}")
            
            grp_verts = get_verts_in_group(me, grp_index)
            if bone_idx == 0:
                grp_verts += unmapped_verts
            
            for v in grp_verts:
                if v.index in vert_remap:
                    existing_bone_name = am.bones[vert_bone_map[v.index]].name
                    print(f"WARNING: Skipping vertex group mapping, a vert from {grp_name} is already mapped to {existing_bone_name}")
                else:
                    vert_bone_map[v.index] = bone_idx
                    vert_remap[v.index] = len(export_vertices)
                    normal_remap[v.index] = len(export_normals)
                    
                    export_vertices.append(utils.translate_vertex(v.co))
                    export_normals.append(utils.translate_vertex(v.normal))
                    
                    grp_vert_count += 1
                    grp_normal_count += 1
                            
            
            print(f"\t\t{grp_vert_count} verts, {grp_normal_count} normals")
            mtxn.append(grp_normal_count)
            mtxv.append(grp_vert_count)
    else:
        for v in me.vertices:
            vert_remap[v.index] = len(export_vertices)
            normal_remap[v.index] = len(export_normals)
            export_vertices.append(utils.translate_vertex(v.co))
            export_normals.append(utils.translate_vertex(v.normal))
        mtxn.append(len(export_normals))
        mtxv.append(len(export_vertices))
        
    
    # localize vertices if we have an armature
    if am is not None:
        print("localize vertices...")
        
        localize_offset = 0
        for x in range(len(bone_id_map)):
            bone_name = bone_id_map[x]
            bone = am.bones[bone_name]
            vertex_count = mtxv[x]
            
            bone_pos = get_bone_pos(bone)
            
            for y in range(localize_offset, localize_offset + vertex_count):
                vertex = export_vertices[y]
                export_vertices[y] = [vertex[0] - bone_pos[0],
                                      vertex[1] - bone_pos[1],
                                      vertex[2] - bone_pos[2]]
            localize_offset += vertex_count
        
    # do texture coordinates, colors, and map loops
    print("map loops...")
    for polygon in me.polygons:
        for loop_index in polygon.loop_indices:
            loops_to_polygons[loop_index] = polygon.index
            
    for local_loop_index, loop_index in enumerate(triangle_indices):
        polygon = me.polygons[loops_to_polygons[loop_index]]
        material_loops[polygon.material_index].append(loop_index)
    
        uv = (0, 0) if uv_layer is None else utils.translate_uv(uv_layer[loop_index].uv)
        if not uv in uv_remap:
            uv_remap[uv] = len(export_uvs)
            export_uvs.append(uv)
        
        color = (1, 1, 1, 1) if vc_layer is None else tuple(vc_layer.data[loop_index].color)     
        if not color in color_remap:
            color_remap[color] = len(export_colors)
            export_colors.append(color)
    
    # make packets    
    print("make packets...")
    
    max_packet_indices = 255
    max_packet_matrices = 8
    
    # make packets for this material
    for slot_index, material_slot in enumerate(ob.material_slots):
        index_offset = 0
        
        packet_loop_indices = material_loops[slot_index]
        mat_packet_list = []
        
        # build single packet
        while index_offset < len(packet_loop_indices):
            index_start = index_offset
            index_end = index_start
            
            adjuncts = []
            triangles = []
            matrices = []
            
            matrix_map = {}
            adjunct_map = {}
            loop_to_adjunct_map = {}
            
            for loop_index in packet_loop_indices[index_start:]:
                # convert this loop to indices
                loop = me.loops[loop_index]
                
                matrix_index = 0 if am is None else vert_bone_map[loop.vertex_index]
                if not matrix_index in matrix_map:
                    if len(matrix_map) >= max_packet_matrices:
                        break
                    else:
                        matrix_map[matrix_index] = len(matrices)
                        matrices.append(matrix_index)
                
                vert_index = vert_remap[loop.vertex_index]
                normal_index = normal_remap[loop.vertex_index]
                
                uv = (0, 0) if uv_layer is None else utils.translate_uv(uv_layer[loop_index].uv)
                color = (1, 1, 1, 1) if vc_layer is None else tuple(vc_layer.data[loop_index].color)     
                
                uv_index = uv_remap[uv]
                uv2_index = 0
                color_index = color_remap[color]
                
                matrix_index_local = 0 if am is None else matrix_map[matrix_index]
                
                # add adjunct
                adjunct = (vert_index, normal_index, color_index, uv_index, uv2_index, matrix_index_local)
                if not adjunct in adjunct_map:
                    adjunct_map[adjunct] = len(adjuncts)
                    adjuncts.append(adjunct)
                loop_to_adjunct_map[loop_index] = adjunct_map[adjunct]
                
                # set index_end
                index_offset += 1
                
                # at our limit for indices
                if len(loop_to_adjunct_map) >= max_packet_indices:
                    break
            
            index_end = (index_offset // 3) * 3 # round down to the nearest 3
            index_offset = index_end
            for local_loop_index in range(index_start, index_end, 3):
                tri_loop_indices = packet_loop_indices[local_loop_index:local_loop_index + 3]
                local_tri_indices = [loop_to_adjunct_map[l] for l in tri_loop_indices]
                triangles.append(local_tri_indices)
            
            # append paket
            mat_packet_list.append([adjuncts, triangles, matrices])
    
        # map packet list
        packet_lists[slot_index] = mat_packet_list
        
    # count adjuncts and prims
    for packet_list in packet_lists.values():
        for packet in packet_list:
            adjuncts, triangles, matrices = packet
            adjunct_count += len(adjuncts)
            primitive_count += len(triangles)
    
    # write mod file
    with open(filepath, 'w') as file:
        # write header
        file.write(f"version: {version}\n")
        file.write(f"verts: {len(export_vertices)}\n")
        file.write(f"normals: {len(export_normals)}\n")
        file.write(f"colors: {len(export_colors)}\n")
        file.write(f"tex1s: {len(export_uvs)}\n") 
        file.write(f"tex2s: {0}\n") # todo version 1.10
        file.write(f"tangents: {0}\n") # never used in AGE?
        file.write(f"materials: {material_count}\n")
        file.write(f"adjuncts: {adjunct_count}\n")
        file.write(f"primitives: {primitive_count}\n")
        file.write(f"matrices: {bone_count}\n")
        if version == "1.10":
            file.write("reskins: 1\n")
        file.write("\n")
        
        # write geomdata
        if len(export_vertices) > 0:
            for vert in export_vertices:
                file.write(f"v\t{vert[0]:.6f}\t{vert[1]:.6f}\t{vert[2]:.6f}\n")
            file.write("\n")

        if len(export_normals) > 0:
            for normal in export_normals:
                file.write(f"n\t{normal[0]:.6f}\t{normal[1]:.6f}\t{normal[2]:.6f}\n")
            file.write("\n")    
        
        if len(export_colors) > 0:
            for color in export_colors:
                file.write(f"c\t{color[0]:.6f}\t{color[1]:.6f}\t{color[2]:.6f}\t{color[3]:.6f}\n")
            file.write("\n") 
        
        if len(export_uvs) > 0:
            for uv in export_uvs:
                file.write(f"t1\t{uv[0]:.6f}\t{uv[1]:.6f}\n")
            file.write("\n") 
        
        for material_index, material_slot in enumerate(ob.material_slots):
            material = material_slot.material
            mat_wrap = node_shader_utils.PrincipledBSDFWrapper(material) if material else None
            illum = get_illum_type(material)
            
            adjuncts = 0
            triangles = 0
            texture = mat_wrap.base_color_texture
            
            mat_packet_list = packet_lists[material_index]
            for packet in mat_packet_list:
                adjuncts += len(packet[0])
                triangles += len(packet[1])
            
            file.write(f"mtl {material.name} {{\n")
            file.write(f"\tpackets:\t{len(mat_packet_list)}\n")
            file.write(f"\tprimitives:\t{triangles}\n")
            file.write("\ttextures:\t%i\n" % (0 if texture is None or texture.image is None else 1))
            file.write(f"\tillum:\t{illum}\n")
            file.write("\tambient:\t0.000000 0.000000 0.000000\n")
            file.write("\tdiffuse:\t%.6f %.6f %.6f\n" % mat_wrap.base_color[:3])
            file.write("\tspecular:\t%.6f %.6f %.6f\n" % (mat_wrap.specular, mat_wrap.specular, mat_wrap.specular))
            if texture is not None and texture.image is not None:
                image_name = os.path.splitext(os.path.basename(texture.image.filepath))[0]
                file.write(f"\ttexture: 0 \"{image_name}\"\n")
            if version == "1.10":
                # neat little attributes system. the only other valid attribute is 'int draworder'
                file.write("\tattributes: 1\n")
                file.write("\tfloat shininess: %.6f\n" % (1.0 - mat_wrap.roughness))
            file.write("}\n\n")
        
        
        for material_index in range(material_count):
            mat_packet_list = packet_lists[material_index]
            for adjuncts, triangles, matrices in mat_packet_list:
                file.write(f"packet {len(adjuncts)} {len(triangles)} {len(matrices)} {{\n")
                for adjunct in adjuncts:
                    file.write("\tadj\t" + "\t".join([str(x) for x in adjunct]) + "\n")
                for triangle in triangles:
                    file.write("\ttri\t" + "\t".join([str(x) for x in triangle]) + "\n")
                if len(matrices) > 0:
                    file.write("\tmtx " + " ".join([str(x) for x in matrices]) + "\n")
                file.write("}\n\n")
        
        file.write("mtxv " + " ".join([str(x) for x in mtxv]) + "\n")
        file.write("mtxn " + " ".join([str(x) for x in mtxn]))

    # heccin done
    print("done")
    
######################################################
# EXPORT
######################################################
def save(operator,
         context,
         filepath="",
         mod_version="1.09",
         apply_modifiers=True,
         ):
         
    print("exporting MOD: %r..." % (filepath))
    ob = bpy.context.active_object
    if ob is None:
        raise Exception("No object selected to export")
    
    time1 = time.perf_counter()
    # save MOD
    export_mod_object(filepath, ob, mod_version, apply_modifiers)
    
    #export complete
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}