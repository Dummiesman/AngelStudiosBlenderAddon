import bpy, bmesh
import time

from . import utils as utils
from .file_parser import FileParser

######################################################
# IMPORT MAIN FILES
######################################################
def read_skel_file(file):
    scn = bpy.context.scene
    # add a mesh and link it to the scene
    am = bpy.data.armatures.new('MODArmature')
    ob = bpy.data.objects.new('MODArmature', am)

    scn.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    edit_bones = ob.data.edit_bones
    
    # start parsing
    lines = file.readlines()
    parser = FileParser(lines)
    
    parser.seek(0, 2)
    parser_eof = parser.tell()
    parser.seek(0, 0)
    
    # file data
    cur_bone_level = 0
    max_heir_depth = 0
    
    bones = []
    bone_heir = {} # {level: bone_id}
    
    while parser.tell() != parser_eof:
        tok = parser.read_tokens()
        if len(tok) == 0:
            continue
            
        if tok[0] == "bone":
            bone_name = tok[1]
            bone_id = len(bones)
            print("bone " + bone_name + " id " + str(bone_id))
            
            parser.skip_to("offset")
            bone_offset = parser.read_float_array()
            bone_offset = utils.translate_vector(bone_offset)
            
            parent_bone_index = -1 if cur_bone_level == 0 else bone_heir[cur_bone_level - 1]
            
            bones.append([parent_bone_index, bone_id, bone_name, bone_offset, cur_bone_level])
            bone_heir[cur_bone_level] = bone_id
            
            cur_bone_level += 1
            max_heir_depth = max(max_heir_depth, cur_bone_level)
        elif tok[0] == "}":
            cur_bone_level -= 1
    
    # move bones to global sace
    for x in range(1, max_heir_depth):
        for bone in bones:
            bone_parent_index, bone_id, bone_name, bone_offset, bone_heir_level = bone
            if bone_heir_level != x:
                continue
            
            # offset bone by all lower bones in the heirarchy
            parent_bone_offset = bones[bone_parent_index][3]
            bone[3] = [bone_offset[0] + parent_bone_offset[0],
                       bone_offset[1] + parent_bone_offset[1],
                       bone_offset[2] + parent_bone_offset[2]]
    
    # blender has some auto merging fudgery, but we need the overlapping bones
    armature_merge_set = set()
    for bone in bones:
        bone_parent_index, bone_id, bone_name, bone_offset, bone_heir_level = bone
        offset_tup = tuple(bone_offset)
        if offset_tup in armature_merge_set:
            bone_offset[2] += 0.01
        else:
            armature_merge_set.add(offset_tup)
    
    # build armatures
    built_bones = []
    for bone in bones:
        bone_parent_index, bone_id, bone_name, bone_offset, bone_heir_level = bone
        
        e_bone = edit_bones.new(bone_name)
        e_bone['bone_id'] = bone_id
        
        e_bone.tail = bone_offset
        
        if bone_parent_index != -1:
            e_bone.parent = built_bones[bone_parent_index]
        
        e_bone.use_connect = (bone_heir_level > 0)   
        e_bone.use_inherit_rotation = False        
        built_bones.append(e_bone)
    
    # clean up
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    
    # set pose bone rotation mode
    # the animation format uses eulers instead of quaternions
    for pb in ob.pose.bones:
        pb.rotation_mode = 'XYZ'
    
   

######################################################
# IMPORT
######################################################
def load_skel(filepath,
             context):

    print("importing SKEL: %r..." % (filepath))

    time1 = time.perf_counter()
    file = open(filepath, 'r')

    # start reading our bnd file
    read_skel_file(file)

    print(" done in %.4f sec." % (time.perf_counter() - time1))
    file.close()


def load(operator,
         context,
         filepath="",
         ):

    load_skel(filepath,
             context,
             )

    return {'FINISHED'}
