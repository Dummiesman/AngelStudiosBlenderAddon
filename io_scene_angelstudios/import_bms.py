import bpy, bmesh
from . import binary_ops_arts as binary_ops_arts
from . import utils as utils
import time, struct, os

######################################################
# GLOBAL CONTEXT
######################################################
import_context = None  # Global import context

######################################################
# HELPERS
######################################################
def create_material(name):
  
  global import_context    
  if import_context is None:
    raise RuntimeError("Import context is not set. Ensure import_bms_object is called first.")

  # setup material
  mtl = bpy.data.materials.new(name=name)
  mtl.specular_intensity = 0
  
  mtl.use_nodes = True
  mtl.use_backface_culling = True

  # clear existing nodes
  nodes = mtl.node_tree.nodes
  nodes.clear()
    
  # create new material nodes
  material_output = nodes.new(type='ShaderNodeOutputMaterial')
  material_output.location = (200, 0)
    
  principled_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
  principled_bsdf.location = (-200, 0)
    
  texture_node = nodes.new(type='ShaderNodeTexImage')
  texture_node.location = (-600, 0)

  imagepath = os.path.join(import_context, name + '.DDS')

  # fetch and assign image
  if imagepath:
    if os.path.exists(imagepath):
        try:
            texture_image = bpy.data.images.load(imagepath)
            texture_node.image = texture_image
        except Exception as e:
            print(f"Failed to load image {imagepath}: {e}")
    else:
        print(f"Texture file not found: {imagepath}")
  else:
    print("Invalid image path.")
    
  # connect nodes
  mtl.node_tree.links.new(principled_bsdf.inputs['Base Color'], texture_node.outputs['Color'])
  mtl.node_tree.links.new(material_output.inputs['Surface'], principled_bsdf.outputs['BSDF'])
    
  return mtl

def vert_key(position, normal=None):
    if normal is not None:
        return str(position) + "|" + str(normal)
    else:
        return str(position)

######################################################
# IMPORT
######################################################
def import_bms_object(filepath):

    global import_context
    import_context = os.path.dirname(filepath)

    scn = bpy.context.scene

    points = []
    textures = []
    normal_indices = []
    texture_coords = []
    colors = []
    vertex_indices = []
    texture_indices = []

    # read data
    with open(filepath, 'rb') as file:
        magic = struct.unpack('<L', file.read(4))[0]
        if magic != 0x4D534833:
            raise Exception("Not a BMS file!")
        
        offset = struct.unpack('<fff', file.read(12))
        num_points, num_adjuncts, num_surfaces, num_indices = struct.unpack('<LLLL', file.read(16))

        file.seek(12, 1) # seek past radius

        num_textures = struct.unpack('<B', file.read(1))[0]
        flags = struct.unpack('<B', file.read(1))[0]

        file.seek(6, 1) # seek past padding+cache size

        # read textures
        for x in range(num_textures):
            texture_name = binary_ops_arts.read_string(file, 32)
            file.seek(16, 1) # seek past the rest of the texture info
            textures.append(texture_name)

        # read points
        for x in range(num_points):
            points.append(struct.unpack('<fff', file.read(12)))

        # seek past bounding box if it exists
        if num_points >= 16:
            file.seek(12 * 8, 1) # 8 x vec3

        # normals
        if (flags & 2) != 0:
            for x in range(num_adjuncts):
                normal_indices.append(struct.unpack('<B', file.read(1))[0])

        # tex coords
        if (flags & 1) != 0:
            for x in range(num_adjuncts):
                texture_coords.append(struct.unpack('<ff', file.read(8)))

        # colors
        if (flags & 4) != 0:
            for x in range(num_adjuncts):
                color = struct.unpack('<BBBB', file.read(4))
                colors.append((color[2] / 255.0, color[1] / 255.0, color[0] / 255.0, color[3] / 255.0))

        vertex_indices = struct.unpack(f"{num_adjuncts}H", file.read(num_adjuncts * 2))

        if (flags & 16) != 0:
            # planes
            file.seek(16 * num_surfaces, 1) # num_surfaces x vec4

        # texture and surface indices
        texture_indices = struct.unpack(f"<{num_surfaces}B", file.read(num_surfaces))
        surface_indices = struct.unpack(f"{num_indices}H", file.read(num_indices * 2))
        
        # build object&mesh
        name = "BMSMesh"
        me = bpy.data.meshes.new(name + 'Mesh')
        ob = bpy.data.objects.new(name, me)
        ob.location = utils.translate_vector(offset)
        scn.collection.objects.link(ob)

        bm = bmesh.new()
        bm.from_mesh(me)
        uv_layer = bm.loops.layers.uv.new()
        vc_layer = bm.loops.layers.color.new()

        for x in range(num_textures):
            ob.data.materials.append(create_material(textures[x]))

        # compile vertex_map
        vertex_map = {}
        vertices = []
        for x in range(num_adjuncts):
            pos = points[vertex_indices[x]]
            normal = None if (flags & 2) == 0 else normal_indices[x]
            key = vert_key(pos, normal)

            if not key in vertex_map:
                vertex_map[key] = len(vertices)
                vertex = utils.translate_vector(pos)
                vertices.append(bm.verts.new(vertex))

        # create surface geometry
        for x in range(num_surfaces):
            index_base = x * 4
            side_count = 4 if surface_indices[index_base + 3] > 0 else 3
            indices = surface_indices[index_base:index_base+side_count]
            
            bmverts = []
            for adj_index in indices:
                pos = points[vertex_indices[adj_index]]
                normal = None if (flags & 2) == 0 else normal_indices[adj_index]
                key = vert_key(pos, normal)
                bmverts.append(vertices[vertex_map[key]])
            
            try:
                face = bm.faces.new(bmverts)
                for xx in reversed(range(side_count)):
                    if flags & 1 != 0:
                        face.loops[xx][uv_layer].uv = utils.translate_uv(texture_coords[indices[xx]])   
                    if flags & 4 != 0:
                        face.loops[xx][vc_layer] = colors[indices[xx]]

                face.material_index = 0 if texture_indices[x] == 0 else texture_indices[x] - 1
                face.smooth = True
            except Exception as e:
                print(str(e))

        # calculate normals
        bm.normal_update()

        # free resources
        bm.to_mesh(me)
        bm.free()

        import_context = None

        return ob


######################################################
# IMPORT
######################################################
def load(operator,
         context,
         filepath="",
         ):

    print("importing ARTS BMS: %r..." % (filepath))
    time1 = time.perf_counter()
    ob = import_bms_object(filepath)
    ob.name = os.path.splitext(os.path.basename(filepath))[0]
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}
