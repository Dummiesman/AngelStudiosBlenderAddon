from . import utils as utils

# This will be removed entirely
# It's only purpose was to keep track of triangle strip index counts
# When I thought a strip was made up of str->str->str->stp, insetad of str/stp being individual strips

class PacketParser:
    def __init__(self):
        pass
    
    def parse_primitive(self, prim_type, indices):
        indices_ints = [int(x) for x in indices]
        triangles = None
        
        if prim_type == "tri":
            # triangles
            triangles = indices_ints
        elif prim_type == "str":
            indices_ints = indices_ints[1:]
            triangles = utils.triangle_strip_to_list(indices_ints, False)
        elif prim_type == "stp":
            indices_ints = indices_ints[1:]
            triangles = utils.triangle_strip_to_list(indices_ints, True)
        else:
            raise Exception(f"Invalid primitive type {prim_type}")
            
        return triangles