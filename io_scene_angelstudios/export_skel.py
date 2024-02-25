import time
import os.path as path

from . import utils as utils
import bpy

#####################################################
# EXPORT MAIN FILES
######################################################
def write_bone(file, indentation_level, bone):
    indentation = "\t" * indentation_level
    parent_tail_pos = (0,0,0) if bone.parent is None else bone.parent.tail_local
    tail_pos = bone.tail_local
    
    tail_pos = (tail_pos[0] - parent_tail_pos[0], tail_pos[1] - parent_tail_pos[1], tail_pos[2] - parent_tail_pos[2])
    tail_pos = utils.translate_vector(tail_pos)
    
    file.write(indentation + "bone " + bone.name + " {\n")
    file.write(f"{indentation}\toffset {tail_pos[0]:.6f} {tail_pos[1]:.6f} {tail_pos[2]:.6f}\n")
    
    for child in bone.children:
        write_bone(file, indentation_level + 1, child)
    
    file.write(indentation + "}\n")

def export_skel(filepath, ob, version="1.00"):
    with open(filepath, 'w') as file:
        am = ob.data
        num_bones = len(am.bones)

        file.write(f"NumBones {num_bones}\n")
        for bone in am.bones:
            if bone.parent is None:
                write_bone(file, 0, bone)
    
######################################################
# EXPORT
######################################################
def save(operator,
         context,
         filepath="",
         skel_version="1.00",
         ):
    
    print("exporting SKEL: %r..." % (filepath))

    ob = bpy.context.active_object
    if ob is None:
        raise Exception("No object selected to export")

    if ob.type != 'ARMATURE':
        raise Exception("Selected object is not an armature")
        
    time1 = time.perf_counter()

    # write skel
    export_skel(filepath, ob, skel_version)
    
    #export complete
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}