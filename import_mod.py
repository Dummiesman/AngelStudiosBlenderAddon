import bpy, bmesh
import time, os

from . import utils as utils
from .file_parser import FileParser
from .packet_parser import PacketParser
from bpy_extras import node_shader_utils

class ModMaterialInfo:
    def __init__(self):
        self.name = ""
        self.packet_count = 0
        self.adjunct_count = 0
        self.primitive_count = 0
        self.material = None
        
class ModAdjunct:
    def __init__(self, vertex_index = -1, normal_index = -1, color_index = -1, 
                 uv0_index = -1, uv1_index = -1, matrix_index = -1):
        self.vertex_index = vertex_index
        self.normal_index = normal_index
        self.color_index = color_index
        self.uv_indices = (uv0_index, uv1_index)
        self.matrix_index = matrix_index
        

######################################################
# HELPERS
######################################################
def get_bone_name_map():
    """Return a map of [bone_id] = (name, offset) for offsetting imported MOD"""
    am = None
    am_ob = None
    
    for ob in bpy.data.objects:
        if ob.type == 'ARMATURE':
            am = ob.data
            am_ob = ob
            break

    if am is None:
        return None
        
    bone_dict = {}
    for bone in am.bones:
        if not 'bone_id' in bone:
            continue
        bone_dict[bone['bone_id']] = (bone.name, bone.tail_local)
    return bone_dict


######################################################
# IMPORT MAIN FILES
######################################################
def import_mod_object(filepath):
    with open(filepath, 'r') as file:
        scn = bpy.context.scene
        # add a mesh and link it to the scene
        me = bpy.data.meshes.new('MODModel')
        ob = bpy.data.objects.new('MODModel', me)

        bm = bmesh.new()
        bm.from_mesh(me)
        
        scn.collection.objects.link(ob)
        bpy.context.view_layer.objects.active = ob
        
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        
        # create layers for this object
        uv_layers = (bm.loops.layers.uv.new(), bm.loops.layers.uv.new())
        vc_layer = bm.loops.layers.color.new()
        
        # start parsing
        lines = file.readlines()
        parser = FileParser(lines)
        
        MOD_TYPE_ADJUNCT = 0
        MOD_TYPE_PACKET = 1
        PRIM_TYPES = ["tri", "stp", "str"]
        
        # get bone map
        bone_map = get_bone_name_map()
        vert_to_bone_map = {}
        vert_bone_assignment_map = None
        have_skeleton = bone_map is not None
        
        # add vertex groups if we have a skeleton
        if have_skeleton:
            vert_bone_assignment_map = [[] for x in range(len(bone_map))]
            for x in range(len(bone_map)):
                bone_name, bone_offset = bone_map[x]
                ob.vertex_groups.new(name=bone_name)
        
        # vert counter
        vert_id = 0
        
        # header info
        material_count = 0
        mod_type = MOD_TYPE_ADJUNCT
        
        # file data
        vertices = []
        normals = []
        colors = []
        tex1s = []
        tex2s = []
        materials = []
        
        adjuncts = []
        
        mtxv = []
        mtxn = []
        
        version = None
        if parser.skip_to("version:"):
            version = parser.read_tokens()[1]
        if version != "1.06" and version != "1.08" and version != "1.09" and version != "1.10":
            raise Exception("Bad MOD file version.")
        
        if have_skeleton and parser.skip_to("matrices:"):
            matrices_count = parser.read_int()
            if matrices_count != len(bone_map):
                raise Exception(f"Model matrices count does not match skeleton bone count.")
        
        # read geometry data
        while parser.skip_to("v", 16):
            vertices.append(utils.translate_vector(parser.read_float_array()))
        while parser.skip_to("n", 16):
            normals.append(utils.translate_vector(parser.read_float_array()))
        while parser.skip_to("c", 16):
            colors.append(parser.read_float_array())
        while parser.skip_to("t1", 16):
            tex1s.append(utils.translate_uv(parser.read_float_array()))
        while parser.skip_to("t2", 16):
            tex2s.append(utils.translate_uv(parser.read_float_array()))
        
        
        # read materials
        while parser.skip_to("mtl", 32):
            material_tokens = parser.read_tokens()
            material_name = material_tokens[1]
            mat_textures = []
            
            print("Material:" + material_name)
            
            mod_material = ModMaterialInfo()
            mod_material.name = material_name
            
            if parser.skip_to("packets:", 16):
                mod_type = MOD_TYPE_PACKET
                mod_material.packet_count = parser.read_int()
            elif parser.skip_to("adjuncts:", 16):
                mod_type = MOD_TYPE_ADJUNCT
                mod_material.adjunct_count = parser.read_int()
                
                if parser.skip_to("primitives:"):
                    mod_material.primitive_count = parser.read_int()
                else:
                    raise Exception(f"Malformed material {material_name}, missing primitive count.")
            elif version == "1.06" and parser.skip_to("primitives:"):
                mod_type = MOD_TYPE_ADJUNCT
                mod_material.primitive_count = parser.read_int()
            else:
                raise Exception(f"Malformed material {material_name}, no geometry specifiers")
            
            # load material info
            parser.skip_to("textures:", 16)
            num_textures = parser.read_int()
            
            parser.skip_to("diffuse:", 16)
            diffuse_color = parser.read_float_array()
            parser.skip_to("specular:", 16)
            specular_color = parser.read_float_array()
            
            for x in range(num_textures):
                parser.skip_to("texture", 16)
                texture_tokens = parser.read_tokens()
                texture_name = texture_tokens[2]
                mat_textures.append(texture_name)
                
            shininess = 0.0
            if version == "1.10":
                # attributes
                parser.skip_to("attributes:", 16)
                num_attributes = parser.read_int()
                for x in range(num_attributes):
                    attribute_tokens = parser.read_tokens()
                    if attribute_tokens[0] == "float" and attribute_tokens[1] == "shininess:":
                        shininess = float(attribute_tokens[2])
            
            # make material
            material = bpy.data.materials.new(mod_material.name)
            mat_wrap =node_shader_utils.PrincipledBSDFWrapper(material, is_readonly=False) 
            material.use_nodes = True
            mod_material.material = material
            
            mat_wrap.base_color = diffuse_color
            mat_wrap.specular = sum(specular_color) / 3.0
            mat_wrap.roughness = (1.0 - shininess)
            
            if len(mat_textures) > 0:
                texture_name = mat_textures[0]
                asset_root_path = os.path.abspath(os.path.join(os.path.dirname(filepath), ".."))
                texture = utils.try_load_texture(texture_name, (os.path.join(asset_root_path, "texture_x"), os.path.join(asset_root_path, "texture")))
                mat_wrap.base_color_texture.image = texture
            
            ob.data.materials.append(mod_material.material)
            materials.append(mod_material)

        # get matrices, then go back to where we were
        before_mtx_offset = parser.tell()
        
        if parser.skip_to("mtxv"):
            mtxv = parser.read_int_array()
        if parser.skip_to("mtxn"):
            mtxn = parser.read_int_array()
            
        parser.seek(before_mtx_offset)
        
        # offset vertices if we have a skeleton
        if have_skeleton:
            index_offset = 0
            for bone_id, vertex_count in enumerate(mtxv):
                bone_name, bone_offset = bone_map[bone_id]
                for x in range(index_offset, index_offset + vertex_count):
                    vertex = vertices[x]
                    vertices[x] = [vertex[0] + bone_offset[0],
                                   vertex[1] + bone_offset[1],
                                   vertex[2] + bone_offset[2]]

                index_offset += vertex_count
                
        # get bone assignments if we have a skeleton
        if have_skeleton:
            index_offset = 0
            for bone_id, vertex_count in enumerate(mtxv):
                for x in range(index_offset, index_offset + vertex_count):
                    vert_to_bone_map[x] = bone_id
                index_offset += vertex_count
                
        # read geometry connection data
        vertex_remap_table = {}
        remapped_verts = []
        
        def get_vert_for_adjunct(adjunct):
            vertex_coord = vertices[adjunct.vertex_index]
            normal_coord = normals[adjunct.normal_index]
            vertex_hash = str(vertex_coord) + "|" + str(normal_coord) + "|" + str(adjunct.matrix_index)
            
            bmvert = None
            if vertex_hash in vertex_remap_table:
                bmvert = remapped_verts[vertex_remap_table[vertex_hash]]
            else:
                bmvert = bm.verts.new(vertex_coord)
                bmvert.normal = normal_coord
                vertex_remap_table[vertex_hash] = len(remapped_verts)
                remapped_verts.append(bmvert)
            return bmvert
                
        def add_tris(tri_indices):
            for y in range(0, len(tri_indices), 3):
                try:
                    face = bm.faces.new([get_vert_for_adjunct(adjuncts[x]) for x in tri_indices[y:y+3]])
                    face.material_index = material_index
                    face.smooth = True
                    for z in reversed(range(3)):
                        loop_adjunct = adjuncts[tri_indices[y+z]]
                        face.loops[z][uv_layers[0]].uv = tex1s[loop_adjunct.uv_indices[0]]
                        face.loops[z][vc_layer] = colors[loop_adjunct.color_index]
                except Exception as e:
                    print(str(e))
                    #raise e
        
        if mod_type == MOD_TYPE_ADJUNCT:
            # parse adjuncts
            while parser.skip_to("adj"):
                adj_data = parser.read_int_array()
                vidx = adj_data[0]
                nidx = adj_data[1]
                cidx = adj_data[2]
                u1idx = adj_data[3]
                u2idx = adj_data[4]
                
                if have_skeleton:
                    vert_bone_assignment_map[vert_to_bone_map[vidx]].append(vert_id)
                    vert_id += 1
                    
                adjuncts.append(ModAdjunct(vidx, nidx, cidx, u1idx, u2idx))
                
            # parse primitives
            for material_index, mod_material in enumerate(materials):
                packet_parser = PacketParser()
                for x in range(mod_material.primitive_count):
                    if parser.skip_to(PRIM_TYPES):
                        tok = parser.read_tokens()
                        tri_indices = packet_parser.parse_primitive(tok[0], tok[1:])
                        add_tris(tri_indices)
                    else:
                        raise Exception(f"Ran out of primitives building geometry for material {mod_material.name}")
        else:
            # parse packets
            for material_index, mod_material in enumerate(materials):
                for x in range(mod_material.packet_count):
                    if parser.skip_to("packet"):
                        # get packet info
                        packet_tok = parser.read_tokens()
                        num_adjuncts = int(packet_tok[1])
                        num_primitives = int(packet_tok[2])
                        
                        # parse adjuncts
                        adjuncts = [] # adjuncts are localized to a packet, so we clear them each packet
                        if num_adjuncts > 0:
                            parser.skip_to("adj")
                            for y in range(num_adjuncts):
                                vidx, nidx, cidx, u1idx, u2idx, mtxidx = parser.read_int_array()
                                if have_skeleton:
                                    vert_bone_assignment_map[vert_to_bone_map[vidx]].append(vert_id)
                                    vert_id += 1
                                
                                adjuncts.append(ModAdjunct(vidx, nidx, cidx, u1idx, u2idx, mtxidx))
                                
                        # parse primitives
                        tot_indices = 0
                        packet_parser = PacketParser()
                        if num_primitives > 0:
                            parser.skip_to(PRIM_TYPES)
                            for y in range(num_primitives):
                                tok = parser.read_tokens()
                                tri_indices = packet_parser.parse_primitive(tok[0], tok[1:])
                                add_tris(tri_indices)
                    else:
                        raise Exception(f"Ran out of packets building geometry for material {mod_material.name}")
        
        # calculate normals
        bm.normal_update()
        
        # free resources
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        bm.to_mesh(me)
        bm.free()

        # add vertex groups
        if have_skeleton:
            for index,vertices in enumerate(vert_bone_assignment_map):
                ob.vertex_groups[index].add(vertices, 1.0, 'REPLACE')
                
        # return the added object
        return ob
    

######################################################
# IMPORT
######################################################
def load(operator,
         context,
         filepath="",
         ):

    print("importing MOD: %r..." % (filepath))
    time1 = time.perf_counter()
    import_mod_object(filepath)
    print(" done in %.4f sec." % (time.perf_counter() - time1))
    
    return {'FINISHED'}
