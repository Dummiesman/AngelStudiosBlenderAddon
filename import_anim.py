import bpy, bmesh, mathutils
import struct, time, os

from . import utils as utils

######################################################
# IMPORT MAIN FILES
######################################################
def read_anim_file(file, filepath):
    # parse animation file
    is_old_animation = True
    num_frames = struct.unpack("<L", file.read(4))[0]
    if num_frames == 0:
        num_frames = struct.unpack("<L", file.read(4))[0]
        is_old_animation = False
        
    num_channels = struct.unpack("<L", file.read(4))[0]
    if is_old_animation:
        num_channels = (3 * num_channels) + 3
    
    file.seek(5, 1) # unknown stuff
    
    anim_frames = []
    for x in range(num_frames):
        frame_data = struct.unpack(f"<{num_channels}f", file.read(4 * num_channels))
        anim_frames.append(frame_data)
        
    feof = file.tell()
    file.seek(0, 2)
    eof = file.tell()
    print(f"at {feof} of {eof}")
    
    # import it onto the selected armature
    ob = bpy.context.active_object
    if ob.type != 'ARMATURE':
        print("NO ARMATURE SELECTED")
        return
    
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    edit_bones = ob.data.edit_bones
    am = ob.data
    
    num_bones = (num_channels // 3) - 1
    if num_bones != len(am.bones):
        print(f"BONE COUNT MISMATCH {num_bones} vs {len(am.bones)}")
        return
        
    # create action
    action_name = os.path.splitext(os.path.basename(filepath))[0]
    action = bpy.data.actions.new(action_name)
    
    # create curves
    curves = {}
    root_curves = [action.fcurves.new(data_path='pose.bones["root"].location', index=x) for x in range(3)]
            
    bone_id_map = {}
    bone_name_map = {}
    for bone in am.bones:
        bone_id_map[bone["bone_id"]] = bone.name
        bone_name_map[bone.name] = bone["bone_id"]
        

    for bone_num in range(num_bones):
        bone = am.bones[bone_id_map[bone_num]]
        data_path = f'pose.bones["{bone.name}"].rotation_euler'
        curves[bone.name] = [action.fcurves.new(data_path=data_path, index=x) for x in range(3)]

    # fill curves
    for frame_num in range(num_frames):
        frame = anim_frames[frame_num]
        
        x,y,z = frame[0], frame[1], frame[2]
        root_curves[0].keyframe_points.insert(frame_num, x)
        root_curves[1].keyframe_points.insert(frame_num, y)
        root_curves[2].keyframe_points.insert(frame_num, z)
        
        for bone_num in range(num_bones):
            data_index = (bone_num + 1) * 3
            
            r,p,h = frame[data_index], frame[data_index + 1], frame[data_index + 2]
            
            bone_name = bone_id_map[bone_num]
            bone = ob.pose.bones[bone_name]
            
            rot_mtx = mathutils.Euler((h, r, p), 'XYZ').to_quaternion().to_matrix().to_4x4()
            if bone.parent is not None:
                bone.matrix_basis = bone.bone.matrix_local @ bone.parent.matrix_basis @ rot_mtx
            else:                                         
                bone.matrix_basis = bone.bone.matrix_local @ rot_mtx
            
            # cool, now get a euler back
            rpheul = bone.rotation_euler
            
            bone_curves = curves[bone_name]
            bone_curves[0].keyframe_points.insert(frame_num, rpheul[0])
            bone_curves[1].keyframe_points.insert(frame_num, rpheul[1])
            bone_curves[2].keyframe_points.insert(frame_num, rpheul[2])
    
    for curve in bone_curves:
        curve.update()
    for curve in root_curves:
        curve.update()
    # clean up
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        
   
######################################################
# IMPORT
######################################################
def load_anim(filepath,
             context):

    print("importing ANIM: %r..." % (filepath))

    time1 = time.perf_counter()
    file = open(filepath, 'rb')

    # start reading our bnd file
    read_anim_file(file, filepath)

    print(" done in %.4f sec." % (time.perf_counter() - time1))
    file.close()


def load(operator,
         context,
         filepath="",
         ):

    load_anim(filepath,
             context,
             )

    return {'FINISHED'}
