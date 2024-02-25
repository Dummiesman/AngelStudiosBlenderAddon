import bpy, bmesh
import time, struct

from . import utils as utils

def make_empty_at_position(name, position):
    # setup object
    ob = bpy.data.objects.new(name, None)

    # set matrix
    ob.location = position
    ob.show_name = True
    
    scn = bpy.context.scene
    scn.collection.objects.link(ob)


######################################################
# IMPORT MAIN FILES
######################################################
def read_bbnd_file(file, bound_repair_debug):
    scn = bpy.context.scene
    # add a mesh and link it to the scene
    me = bpy.data.meshes.new('BoundMesh')
    ob = bpy.data.objects.new('BOUND', me)

    bm = bmesh.new()
    bm.from_mesh(me)
    
    scn.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    
    # read in BBND file!
    bbnd_version = file.read(1)[0]
    if bbnd_version != 1:
        file.close()
        raise Exception('BBND file is wrong version.')
    
    num_verts, num_materials, num_faces = struct.unpack('3L', file.read(12))
    first_vertex = True
    for i in range(num_verts):
        vertex = struct.unpack('<fff', file.read(12))

        if first_vertex:
            if bound_repair_debug:
                make_empty_at_position("FirstVertex", (vertex[0] * -1, vertex[2], vertex[1]))
            first_vertex = False
            
        bm.verts.new((vertex[0] * -1, vertex[2], vertex[1]))
        bm.verts.ensure_lookup_table()
    
    for i in range(num_materials):
        # read name (32 chars), and remove non nulled junk, and skip the rest of the material data
        material_name_bytes = bytearray(file.read(32))
        file.seek(72, 1)
        for b in range(len(material_name_bytes)):
          if material_name_bytes[b] > 126:
            material_name_bytes[b] = 0
        
        # make material
        material_name = material_name_bytes.decode("utf-8").rstrip('\x00')
        ob.data.materials.append(helper.create_material(material_name))
        
    for i in range(num_faces):
        index0, index1, index2, index3, material_index = struct.unpack('<HHHHH', file.read(10))
        if index3 == 0:
          try:
            face = bm.faces.new((bm.verts[index0], bm.verts[index1], bm.verts[index2]))
          except Exception as e:
            print(str(e))
        else:
          try:
            face = bm.faces.new((bm.verts[index0], bm.verts[index1], bm.verts[index2], bm.verts[index3]))
          except Exception as e:
            print(str(e))
        
        # set smooth/material
        if face is not None:
          face.material_index = material_index
          face.smooth = True
          
    # calculate normals
    bm.normal_update()
    
    # free resources
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bm.to_mesh(me)
    bm.free()
      

######################################################
# IMPORT
######################################################
def load_bbnd(filepath,
             context,
             bound_repair_debug):

    print("importing BBND: %r..." % (filepath))

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    time1 = time.perf_counter()
    file = open(filepath, 'rb')

    # start reading our bbnd file
    read_bbnd_file(file, bound_repair_debug)

    print(" done in %.4f sec." % (time.perf_counter() - time1))
    file.close()


def load(operator,
         context,
         filepath="",
         bound_repair_debug = False,
         ):

    load_bbnd(filepath,
             context,
             bound_repair_debug,
             )

    return {'FINISHED'}
