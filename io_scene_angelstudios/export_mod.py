import os, time, struct, math, sys
import os.path as path

from . import utils as utils
import bpy
from bpy_extras import  node_shader_utils

class ModMaterialInfo:
    def __init__(self, material_index):
        self.packets = []
        self.material_index = material_index

class ModPacket:
    def __init__(self):
        self.triangles = []
        self.adjuncts = []
        self.matrices = []
        

class ModAdjunct:
    def __init__(self, vertex_index = -1, normal_index = -1, color_index = -1, 
                 uv0_index = -1, uv1_index = -1, matrix_index = -1):
        self.vertex_index = vertex_index
        self.normal_index = normal_index
        self.color_index = color_index
        self.uv_indices = (uv0_index, uv1_index)
        self.matrix_index = matrix_index

    def __eq__(self, other):
        if not isinstance(other, ModAdjunct):
            return False
        return self.vertex_index == other.vertex_index and\
               self.normal_index == other.normal_index and\
               self.color_index == other.color_index and\
               self.uv_indices[0] == other.uv_indices[0] and\
               self.uv_indices[1] == other.uv_indices[1] and\
               self.matrix_index == other.matrix_index

    def __hash__(self):
        hash_code = 614924594
        hash_code = hash_code * -1521134295 + self.vertex_index
        hash_code = hash_code * -1521134295 + self.normal_index
        hash_code = hash_code * -1521134295 + self.color_index
        hash_code = hash_code * -1521134295 + self.uv_indices[0]
        hash_code = hash_code * -1521134295 + self.uv_indices[1]
        hash_code = hash_code * -1521134295 + self.matrix_index
        return hash_code


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

    uv_layer = me.uv_layers.active.data if me.uv_layers.active is not None else None
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
    
    export_materials = []
    
    mtxv = []
    mtxn = []
    
    vert_remap = {} # coordinate -> file index
    normal_remap = {} # coordinate -> file index
    vert_bone_map = {}
    uv_remap = {} # coordinate -> file index
    color_remap = {} # coordinate -> file index
    loops_to_polygons = {}
    material_loops = [[] for x in range(material_count)]
    
    print("gather bones...")
    bone_count = len(am.bones) if am is not None else 1
    bones = [None for x in range(bone_count)]
    bone_name_to_index = {}
    bone_names = set()

    if am is not None:
        for bone in am.bones:
            bone_names.add(bone.name)
        if len([bone for bone in am.bones if 'bone_id' in bone]) == bone_count:
            print("    ordering bones by their bone_id defined order")
            # use bone_id field to assign bones list
            for bone in am.bones:
                bone_name_to_index[bone.name] = bone['bone_id']
                bones[bone['bone_id']] = bone
        else:
            print("    ordering bones by their armature order")
            # use bone index to assign bones list
            for bone_index, bone in enumerate(am.bones):
                bone_name_to_index[bone.name] = bone_index
                bones[bone_index] = bone
                
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

    # we first need to sort vertices by what bone they're assigned to
    # then export geometry in order of material
    # finally end off with mtxv [bone_adjunct_counts list] mtxn [bone_vert_counts list]
    vert_bone_assignment_map = [[] for x in range(bone_count)]
    for v in me.vertices:
        resident_groups = set()
        for gv in v.groups:
            group_name = ob.vertex_groups[gv.group].name
            if group_name in bone_names and gv.weight > 0.5:
                resident_groups.add(bone_name_to_index[group_name])
        if len(resident_groups) == 0:
            resident_groups.add(0) # add to root bone
        if len(resident_groups) > 1:
            print("UH OH: A vertex is mapped to multiple groups. This is unsupported in the AGE creature library.")
            print("Only one of these bones will provide animation for the vertex")
        
        group_index = resident_groups.pop()
        vert_bone_map[v.index] = group_index
        vert_bone_assignment_map[group_index].append(v.index)
        
    # create squashed vertices/normals lists
    for x in range(bone_count):
        optimized_verts = []
        optimized_vert_map = {}
        optimized_normals = []
        optimized_normals_map = {}

        bone_assignment_map = vert_bone_assignment_map[x]
        for index in bone_assignment_map:
            vert = utils.translate_vector(me.vertices[index].co)
            normal = utils.round_vector(utils.translate_vector(me.vertices[index].normal), 6) 
            
            if not vert in optimized_vert_map:
                vert_remap[vert] = len(optimized_verts) + len(export_vertices)
                optimized_vert_map[vert] = len(optimized_verts)
                optimized_verts.append(vert)
            if not normal in optimized_normals_map:
                normal_remap[normal] = len(optimized_normals) + len(export_normals)
                optimized_normals_map[normal] = len(optimized_normals)
                optimized_normals.append(normal)

        # add to export data
        export_vertices.extend(optimized_verts)
        export_normals.extend(optimized_normals)
        mtxv.append(len(optimized_verts))
        mtxn.append(len(optimized_normals))
            

    # localize vertices if we have an armature
    if am is not None:
        print("localize vertices...")
        localize_offset = 0
        for bone_index, vcount in enumerate(mtxv):
            bone_pos = utils.translate_vector(get_bone_pos(bones[bone_index]))
            for y in range(localize_offset, localize_offset + vcount):
                vertex = export_vertices[y]
                export_vertices[y] = [vertex[0] - bone_pos[0],
                                      vertex[1] - bone_pos[1],
                                      vertex[2] - bone_pos[2]]
            localize_offset += vcount
        
    # make packets    
    print("make packets...")
    
    max_packet_indices = 255
    max_packet_matrices = 8
    
    # make packets for this material
    for slot_index, material_slot in enumerate(ob.material_slots):
        index_offset = 0
        
        packet_loop_indices = material_loops[slot_index]
        mat_info = ModMaterialInfo(slot_index)
        
        # build single packet
        while index_offset < len(packet_loop_indices):
            index_start = index_offset
            index_end = index_start
            
            packet = ModPacket()
            
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
                        matrix_map[matrix_index] = len(packet.matrices)
                        packet.matrices.append(matrix_index)
                
                vert_index = vert_remap[utils.translate_vector(me.vertices[loop.vertex_index].co)]
                normal_index = normal_remap[utils.round_vector(utils.translate_vector(me.vertices[loop.vertex_index].normal), 6)]
                
                uv = (0, 0) if uv_layer is None else utils.translate_uv(uv_layer[loop_index].uv)
                color = (1, 1, 1, 1) if vc_layer is None else tuple(vc_layer.data[loop_index].color)     
                
                uv_index = uv_remap[uv]
                uv2_index = 0
                color_index = color_remap[color]
                
                matrix_index_local = 0 if am is None else matrix_map[matrix_index]
                
                # add adjunct
                adjunct = ModAdjunct(vert_index, normal_index, color_index, uv_index, uv2_index, matrix_index_local)
                if not adjunct in adjunct_map:
                    adjunct_map[adjunct] = len(packet.adjuncts)
                    packet.adjuncts.append(adjunct)
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
                packet.triangles.append(local_tri_indices)
            
            # append paket
            mat_info.packets.append(packet)
    
        # map packet list
        export_materials.append(mat_info)
        
    # final preparation step: clear out materials with no packets
    export_materials = [x for x in export_materials if len(x.packets) > 0]
    
    # count adjuncts and prims
    for export_material in export_materials:
        for packet in export_material.packets:
            adjunct_count += len(packet.adjuncts)
            primitive_count += len(packet.triangles)

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
        file.write(f"materials: {len(export_materials)}\n")
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
        
        for export_material in export_materials:
            material = ob.material_slots[export_material.material_index].material
            mat_wrap = node_shader_utils.PrincipledBSDFWrapper(material) if material else None
            illum = get_illum_type(material)
            
            adjuncts = 0
            triangles = 0
            texture = mat_wrap.base_color_texture
            
            for packet in export_material.packets:
                adjuncts += len(packet.adjuncts)
                triangles += len(packet.triangles)
            
            file.write(f"mtl {material.name} {{\n")
            file.write(f"\tpackets:\t{len(export_material.packets)}\n")
            file.write(f"\tprimitives:\t{triangles}\n")
            file.write("\ttextures:\t%i\n" % (0 if texture is None or texture.image is None else 1))
            file.write(f"\tillum:\t{illum}\n")
            file.write("\tambient:\t0.000000 0.000000 0.000000\n")
            file.write("\tdiffuse:\t%.6f %.6f %.6f\n" % mat_wrap.base_color[:3])
            file.write("\tspecular:\t%.6f %.6f %.6f\n" % (mat_wrap.specular, mat_wrap.specular, mat_wrap.specular))
            if texture is not None and texture.image is not None:
                image_name = utils.get_image_name_from_path(texture.image.filepath)
                file.write(f"\ttexture: 0 \"{image_name}\"\n")
            if version == "1.10":
                # neat little attributes system. the only other valid attribute is 'int draworder'
                file.write("\tattributes: 1\n")
                file.write("\tfloat shininess: %.6f\n" % (1.0 - mat_wrap.roughness))
            file.write("}\n\n")
        
        
        for export_material in export_materials:
            for packet in export_material.packets:
                file.write(f"packet {len(packet.adjuncts)} {len(packet.triangles)} {len(packet.matrices)} {{\n")
                for adjunct in packet.adjuncts:
                    file.write("\tadj\t" + "\t".join([str(x) for x in [adjunct.vertex_index, adjunct.normal_index, adjunct.color_index, adjunct.uv_indices[0], adjunct.uv_indices[1], adjunct.matrix_index]]) + "\n")
                for triangle in packet.triangles:
                    file.write("\ttri\t" + "\t".join([str(x) for x in triangle]) + "\n")
                if len(packet.matrices) > 0:
                    file.write("\tmtx " + " ".join([str(x) for x in packet.matrices]) + "\n")
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