import bpy, mathutils
import os, struct, math
from bpy_extras.io_utils import axis_conversion

MATRIX_TYPE_NONE = 0
MATRIX_TYPE_PIVOT = 1
MATRIX_TYPE_FULL = 1

def bounds(obj):
    """get the bounds of an object"""
    local_coords = obj.bound_box[:]
    coords = [p[:] for p in local_coords]

    rotated = zip(*coords[::-1])

    push_axis = []
    for (axis, _list) in zip('xyz', rotated):
        info = lambda: None
        info.max = max(_list)
        info.min = min(_list)
        info.distance = info.max - info.min
        push_axis.append(info)

    import collections

    originals = dict(zip(['x', 'y', 'z'], push_axis))

    o_details = collections.namedtuple('object_details', 'x y z')
    return o_details(**originals)
    
def object_basename(ob_name):
    ob_name_l = ob_name.lower()
    if ob_name_l.endswith("_h") or ob_name_l.endswith("_m") or ob_name_l.endswith("_l"):
        return ob_name[:-2]
    elif ob_name_l.endswith("_vl"):
        return ob_name[:-3]
    return ob_name

def get_unique_object_names(obs):
    """ return a list of unique object names. e.g. [body_h, body_m, hlight_l] -> [body, hlight] """
    names = set()
    for ob in obs:
        ob_name_l = ob.name.lower()
        names.add(object_basename(ob_name_l))
    return list(names)
         
def det_object_mtx_type_old(ob):
   """ determine the mtx type for an object (old AGE games)"""
   basename = object_basename(ob.name)
   basename_l = basename.lower()
   
   full_mtx_obs = {'arm0', 'arm1', 'arm2', 'arm3', 'shock0', 'shock1', 'shock2', 'shock3', 
                   'axle0', 'axle1', 'splash0', 'splash1', 'shaft2', 'shaft3', 'engine'}
   if basename_l in full_mtx_obs:
    return MATRIX_TYPE_FULL
   elif abs(ob.location[0]) > 0.001 or abs(ob.location[1]) > 0.001 or abs(ob.location[2]) > 0.001:
    return MATRIX_TYPE_PIVOT
   else:
    return MATRIX_TYPE_NONE
    
def det_object_mtx_type(ob):
    """ determine the mtx type for an object (new AGE games)"""
    if (abs(ob.location[0]) > 0.001 or abs(ob.location[1]) > 0.001 or abs(ob.location[2]) > 0.001
    or abs(ob.rotation_euler[0]) > 0.001 or abs(ob.rotation_euler[1]) > 0.001 or abs(ob.rotation_euler[2]) > 0.001):
     return MATRIX_TYPE_FULL
    else:
     return MATRIX_TYPE_NONE
   
    
def read_matrix3x4(name, directory):
    """search for *.mtx and load if found"""
    matrix_path = os.path.join(directory, f"{name}.mtx")
    if os.path.exists(matrix_path):
        with open(matrix_path, 'rb') as mtxfile:
            row1r = list(struct.unpack('<fff', mtxfile.read(12)))
            row2r = list(struct.unpack('<fff', mtxfile.read(12)))
            row3r = list(struct.unpack('<fff', mtxfile.read(12)))
            translation = struct.unpack('<fff', mtxfile.read(12))
            
            col1 = [row1r[0], row2r[0], row3r[0], translation[0]]
            col2 = [row1r[1], row2r[1], row3r[1], translation[1]]
            col3 = [row1r[2], row2r[2], row3r[2], translation[2]]
            
            mtx = mathutils.Matrix((col1, col2, col3)).to_4x4()
            
            mtx_convert = axis_conversion(from_forward='-Z', 
                from_up='Y',
                to_forward='-Y',
                to_up='Z').to_4x4()
                
            mtx = mtx_convert @ mtx
            
            mat_rot = mathutils.Matrix.Rotation(math.radians(90), 4, 'X') @ mathutils.Matrix.Rotation(math.radians(180), 4, 'Y')
            mtx @= mat_rot 
            
            return mtx.to_4x4()
    return None
    
def write_matrix3x4(name, directory, matrix):  
    # passed by ref, don't mess that up
    matrix = matrix.copy() 
    
    # convert coordinate space   
    mat_rot = mathutils.Matrix.Rotation(math.radians(-180.0), 4, 'Y') @ mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'X')
    matrix @= mat_rot
    
    mtx_convert = axis_conversion(from_forward='-Y', 
        from_up='Z',
        to_forward='-Z',
        to_up='Y').to_4x4()
    matrix = mtx_convert @ matrix
    
    #write 3x3
    matrix_path = os.path.join(directory, f"{name}.mtx")
    with open(matrix_path, 'wb') as file:
        file.write(struct.pack('<fff', matrix[0][0], matrix[1][0], matrix[2][0]))
        file.write(struct.pack('<fff', matrix[0][1], matrix[1][1], matrix[2][1]))
        file.write(struct.pack('<fff', matrix[0][2], matrix[1][2], matrix[2][2]))
        file.write(struct.pack('<fff', matrix[0][3], matrix[1][3], matrix[2][3]))
    
def read_matrix(name, directory):
    """search for *.mtx and load if found"""
    matrix_path = os.path.join(directory, f"{name}.mtx")
    if os.path.exists(matrix_path):
        with open(matrix_path, 'rb') as mtxfile:
            mtx_info = struct.unpack('ffffffffffff', mtxfile.read(48))
            
            mtx_min = ((-mtx_info[0], mtx_info[2], mtx_info[1]))
            mtx_max = ((-mtx_info[3], mtx_info[5], mtx_info[4]))
            pivot =   ((-mtx_info[6], mtx_info[8], mtx_info[7]))
            origin =  ((-mtx_info[9], mtx_info[11],mtx_info[10]))
       
            return (mtx_min, mtx_max, pivot, origin)
    return None
    
def write_matrix(name, directory, ob):
    bnds = bounds(object)
    matrix_path = os.path.join(directory, f"{name}.mtx")
    with open(matrix_path, 'wb') as file:
        file.write(struct.pack('fff', (bnds.x.max * -1, bnds.z.min, bnds.y.min)))
        file.write(struct.pack('fff', (bnds.x.min * -1, bnds.z.max, bnds.y.max)))
        file.write(struct.pack('fff', (-object.location[0], object.location[2], object.location[1]))) # pivot
        file.write(struct.pack('fff', (-object.location[0], object.location[2], object.location[1]))) # location
    
def get_image_name_from_path(image_path):
    # strip off Blenders relative slashes, basename doesnt't like these
    if image_path.startswith("//"):
        image_path = image_path[2:]
    return os.path.splitext(os.path.basename(image_path))[0]


def _load_texture_from_path(file_path):
    from .tex_file import TEXFile
    
    # extract the filename for manual image format names
    image_name= os.path.splitext(os.path.basename(file_path))[0]   
    if file_path.lower().endswith(".tex"):
        tf = TEXFile(file_path)
        if tf.is_valid():
            if tf.is_compressed_format():
                tf.decompress()
            tf_img = tf.to_blender_image(image_name)
            tf_img.filepath_raw = file_path # set filepath manually for TEX stuff, since it didn't come from an actual file import
            return tf_img
        else:
            print("Invalid TEX file: " + file_path)
    else:
        img = bpy.data.images.load(file_path)
        return img
        
    return None 

def _image_load_placeholder(name, path):
    image = bpy.data.images.new(name, 128, 128)
    image.filepath_raw = path
    return image
        
def try_load_texture(tex_name, search_paths):
    existing_image = bpy.data.images.get(tex_name)
    if existing_image is not None:
        return existing_image
    
    bl_img = None
    for search_path in search_paths:
        if os.path.isdir(search_path):
            check_file = os.path.join(search_path, tex_name + ".tex")
            if os.path.exists(check_file):
                bl_img = _load_texture_from_path(check_file)

            if bl_img is None:
                standard_extensions = (".tga", ".bmp", ".png")
                for ext in standard_extensions:
                    check_file = os.path.join(search_path, tex_name + ext)
                    if os.path.exists(check_file):
                        bl_img = _load_texture_from_path(check_file)
                        if bl_img is not None:
                            break

            if bl_img is not None:
                break

    if bl_img is None:
        bl_img = _image_load_placeholder(tex_name, os.path.join(search_path, tex_name))
    return bl_img
    
def translate_uv(uv):
    """ translate uv coordinate from/to blender<->AGE """
    return (uv[0], 1 - uv[1])
    
def translate_vector(vector):
    """ translate vector coordinate from/to blender<->AGE """
    return (-vector[0], vector[2], vector[1])

def translate_size(vector):
    """ translate size from/to blender<->AGE """
    return (vector[0], vector[2], vector[1])

def round_vector(vec, places):
    return (round(vec[0], places), round(vec[1], places), round(vec[2], places))

def triangle_strip_to_list(strip, clockwise):
    """convert a strip of triangles into a list of triangles"""
    triangle_list = []
    for v in range(len(strip) - 2):
        if clockwise:
            triangle_list.extend([strip[v+1], strip[v], strip[v+2]])
        else:
            triangle_list.extend([strip[v], strip[v+1], strip[v+2]])
        clockwise = not clockwise

    return triangle_list