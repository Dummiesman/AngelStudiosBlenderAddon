import bpy, bmesh
from .dlp_classes import *
from . import utils as utils
import time

######################################################
# HELPERS
######################################################
def create_material(material, texture=None):
  # setup material
  material_name = material.name
  if texture is not None:
      material_name += f"_{texture.name}"

  mtl = bpy.data.materials.new(name=material_name)
  mtl.diffuse_color = material.diffuse
  mtl.specular_intensity = 0
  
  mtl.use_nodes = True
  mtl.use_backface_culling = True

  bsdf = mtl.node_tree.nodes.get("Principled BSDF") 
  bsdf.inputs['Base Color'].default_value = material.diffuse

  return mtl

def vert_key(vert):
    return str(vert.index) + "|" + str(vert.normal)

######################################################
# IMPORT
######################################################
def import_dlp(filepath):
    scn = bpy.context.scene
    obs = []

    with open(filepath, 'rb') as file:
        dlp_file = DLPFile(file)
        all_materials = []
        textured_materials = {}

        # create materials
        for material in dlp_file.materials:
            all_materials.append(create_material(material))

        # create objects
        for group in dlp_file.groups:
            me = bpy.data.meshes.new(group.name + 'Mesh')
            ob = bpy.data.objects.new(group.name, me)
            scn.collection.objects.link(ob)
            obs.append(ob)

            bm = bmesh.new()
            bm.from_mesh(me)
            uv_layer = bm.loops.layers.uv.new()
            vc_layer = bm.loops.layers.color.new()

            # create local maps
            vertex_map = {}
            vertices = []
            material_map = {}

            # construct local maps
            for patch_index in group.patch_indices:
                patch = dlp_file.patches[patch_index]
                if patch.material_index > 0 and not patch.material_index in material_map:
                    material_map[patch.material_index] = len(ob.data.materials)
                    ob.data.materials.append(all_materials[patch.material_index-1])

                for patch_vert in patch.vertices:
                    key = vert_key(patch_vert)
                    if not key in vertex_map:
                        vertex_map[key] = len(vertices)
                        vertex = utils.translate_vector(dlp_file.vertices[patch_vert.index])
                        vertices.append(bm.verts.new(vertex))


            # construct geometry
            for patch_index in group.patch_indices:
                patch = dlp_file.patches[patch_index]
                if patch.stride != 1 or patch.resolution < 3:
                    continue

                bmverts = []
                for patch_vert in patch.vertices:
                    key = vert_key(patch_vert)
                    bmverts.append(vertices[vertex_map[key]])

                try:
                    face = bm.faces.new(bmverts)
                    for x, patch_vert in reversed(enumerate(patch.vertices)):
                        face.loops[x][uv_layer].uv = utils.translate_uv((patch_vert.s_map, patch_vert.t_map))
                        face.loops[x][vc_layer] = patch_vert.color

                    face.material_index = material_map[patch.material_index] if patch.material_index > 0 else 0
                    face.smooth = True
                except Exception as e:
                    print(str(e))


            # calculate normals
            bm.normal_update()
        
            # free resources
            bm.to_mesh(me)
            bm.free()

    return obs

######################################################
# IMPORT
######################################################
def load(operator,
         context,
         filepath="",
         ):

    print("importing ARTS DLP: %r..." % (filepath))
    time1 = time.perf_counter()
    import_dlp(filepath)
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}
