import bpy, bmesh
import time
from .file_parser import FileParser
from . import utils as utils

######################################################
# HELPER FUNCTIONS
######################################################
def get_material_color(name):
  material_colors = {
                      'grass': (0, 0.507, 0.005, 1.0),
                      'cobblestone': (0.040, 0.040, 0.040, 1.0),
                      'default': (1, 1, 1, 1.0),
                      'wood': (0.545, 0.27, 0.074, 1.0),
                      'dirt': (0.545, 0.35, 0.168, 1.0),
                      'mud': (0.345, 0.25, 0.068, 1.0),
                      'sand': (1, 0.78, 0.427, 1.0),
                      'water': (0.20, 0.458, 0.509, 1.0),
                      'deepwater': (0.15, 0.408, 0.459, 1.0),
                    }
  
  name_l = name.lower()
  for key in material_colors:
     if key in name_l:
        return material_colors[key]
  return material_colors["default"]


def create_material(name):
  name_l = name.lower()
  
  # get color
  material_color = get_material_color(name_l)
    
  # setup material
  mtl = bpy.data.materials.new(name=name_l)
  mtl.diffuse_color = material_color
  mtl.specular_intensity = 0
  
  mtl.use_nodes = True
  mtl.use_backface_culling = True
  
  # get output node
  output_node = None
  for node in mtl.node_tree.nodes:
      if node.type == "OUTPUT_MATERIAL":
          output_node = node
          break
  
  # clear principled, put diffuse in it's place
  bsdf = mtl.node_tree.nodes["Principled BSDF"]
  mtl.node_tree.nodes.remove(bsdf)
  
  bsdf = mtl.node_tree.nodes.new(type='ShaderNodeBsdfDiffuse')
  mtl.node_tree.links.new( bsdf.outputs['BSDF'], output_node.inputs['Surface'] )
  
  # setup bsdf
  bsdf.inputs["Color"].default_value = material_color
  
  return mtl
  
######################################################
# IMPORT MAIN FILES
######################################################
def read_bnd_file(file):
    scn = bpy.context.scene

    # read in BND file!
    lines = file.readlines()
    parser = FileParser(lines)
    
    version = None
    type = "geometry"
    if parser.skip_to("version:"):
        version = parser.read_tokens()[1]
    if version != "1.01" and version != "1.10":
        raise Exception("Bad BND file version.")
        
    if version == "1.10":
        parser.skip_to("type:")
        type = parser.read_tokens()[1]
        
    if type == 'geometry':
        # load and create geometry!
        PRIM_TYPES = ["tri", "quad"]
        
        me = bpy.data.meshes.new('BoundMesh')
        ob = bpy.data.objects.new('BOUND', me)

        bm = bmesh.new()
        bm.from_mesh(me)
        
        scn.collection.objects.link(ob)
        bpy.context.view_layer.objects.active = ob
        
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        
        while parser.skip_to("v", 16):
            bm.verts.new((utils.translate_vector(parser.read_float_array())))
            bm.verts.ensure_lookup_table()
            
        while parser.skip_to("mtl", 32):
            # material
            mtl_name = parser.read_tokens()[1]
            ob.data.materials.append(create_material(mtl_name))
            
        while parser.skip_to("edge", 16):
            parser.seek(1, 1) # skip
            
        while parser.skip_to(PRIM_TYPES):
            tokens = parser.read_tokens()
            num_indices = 4 if tokens[0] == "quad" else 3
            
            # create face
            if num_indices == 4:
              try:
                face = bm.faces.new((bm.verts[int(tokens[1])], bm.verts[int(tokens[2])], bm.verts[int(tokens[3])], bm.verts[int(tokens[4])]))
              except Exception as e:
                print(str(e))
            if num_indices == 3:
              try:
                face = bm.faces.new((bm.verts[int(tokens[1])], bm.verts[int(tokens[2])], bm.verts[int(tokens[3])]))
              except Exception as e:
                print(str(e))
            
            # set smooth/material
            if face is not None:
              face.material_index = int(tokens[num_indices+1])
              face.smooth = True
              
        # calculate normals
        bm.normal_update()
        
        # free resources
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        bm.to_mesh(me)
        bm.free()
    #elif type == "sphere":
    #    ob = bpy.data.objects.new( "BOUND", None )
    #    scn.collection.objects.link(ob)
    #    bpy.context.view_layer.objects.active = ob
    #    
    #    radius = 1.0
    #    if parser.skip_to("radius:", 16):
    #        radius = parser.read_float()
    #    
    #    ob.empty_display_size = radius
    #    ob.empty_display_type = 'SPHERE'   
    else:
        raise NotImplementedError(f"No bound loader for type: {type}")
      

######################################################
# IMPORT
######################################################
def load_bnd(filepath,
             context):

    print("importing BND: %r..." % (filepath))

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    time1 = time.perf_counter()
    file = open(filepath, 'r')

    # start reading our bnd file
    read_bnd_file(file)

    print(" done in %.4f sec." % (time.perf_counter() - time1))
    file.close()


def load(operator,
         context,
         filepath="",
         ):

    load_bnd(filepath,
             context,
             )

    return {'FINISHED'}
