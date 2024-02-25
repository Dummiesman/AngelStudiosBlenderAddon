import struct
from . import binary_ops_arts as binary_ops_arts

class AGIMaterial:
    def __init__(self, file):
        self.name = ""
        self.emission = (0.0, 0.0, 0.0, 0.0)
        self.ambient = (0.0, 0.0, 0.0, 0.0)
        self.diffuse = (0.0, 0.0, 0.0, 0.0)
        self.specular = (0.0, 0.0, 0.0, 0.0)
        self.shininess = 0.0

        if file is not None:
            self.read(file)

    def read(self, file):
        self.name = binary_ops_arts.read_string(file, 32)
        self.emission = struct.unpack('>ffff', file.read(16))
        self.ambient = struct.unpack('>ffff', file.read(16))
        self.diffuse = struct.unpack('>ffff', file.read(16))
        self.specular = struct.unpack('>ffff', file.read(16))
        self.shininess = struct.unpack('>f', file.read(4))[0]
        file.seek(2, 1) # seek past reserved

class AGITexture:
    def __init__(self, file):
        self.name = ""
        self.flags = 0
        
        if file is not None:
            self.read(file)

    def read(self, file):
        self.name =  binary_ops_arts.read_string(file, 32)
        self.flags = struct.unpack('>B', file.read(1))[0]
        file.seek(3, 1) # skip past unks and align

class DLPVertex:
    def __init__(self, file):
        self.index = 0
        self.normal = (0, 0, 0)
        self.s_map = 0.0
        self.t_map = 0.0
        self.color = (0, 0, 0, 0)

        if file is not None:
            self.read(file)

    def read(self, file):
        self.index = struct.unpack('>H', file.read(2))[0]
        self.normal = struct.unpack('>fff', file.read(12))
        self.s_map = struct.unpack('>f', file.read(4))[0]
        self.t_map = struct.unpack('>f', file.read(4))[0]

        color = struct.unpack('>BBBB', file.read(4))
        self.color = (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, color[3] / 255.0)


class DLPGroup:
    def __init__(self, file):
        self.name = ""
        self.vertex_indices = []
        self.patch_indices = []

        if file is not None:
            self.read(file)

    def read(self, file):
        name_len = struct.unpack('>B', file.read(1))[0]
        if name_len > 0:
            self.name = file.read(name_len).decode("utf-8")

        num_vertices, num_patches = struct.unpack('>LL', file.read(8))
        for x in range(num_vertices):
            self.vertex_indices.append(struct.unpack('>H', file.read(2))[0])
        for x in range(num_patches):
            self.patch_indices.append(struct.unpack('>H', file.read(2))[0])

class DLPPatch:
    def __init__(self ,file):
        self.resolution = 0
        self.stride = 0
        self.flags = 0
        self.material_index = 0
        self.texture_index = 0
        self.physics_index = 0
        self.vertices = []
        self.user_data = None

        if file is not None:
            self.read(file)

    def read(self, file):
        self.resolution = struct.unpack(">H", file.read(2))[0]
        self.stride = struct.unpack(">H", file.read(2))[0]
        file.seek(2, 1)
        self.flags = struct.unpack(">H", file.read(2))[0]
        self.material_index = struct.unpack(">H", file.read(2))[0]
        self.texture_index = struct.unpack(">H", file.read(2))[0]
        self.physics_index = struct.unpack(">H", file.read(2))[0]

        num_verts = self.resolution * self.stride
        for x in range(num_verts):
            self.vertices.append(DLPVertex(file))

        user_data_len = struct.unpack(">L", file.read(4))[0]
        if user_data_len > 0:
            self.user_data =  binary_ops_arts.read_string(file, user_data_len)

class DLPFile:
    def __init__(self, file):
        self.vertices = []
        self.groups = []
        self.patches = []
        self.materials = []
        self.physics = []
        self.textures = []

        if file is not None:
            self.read(file)

    def read(self, file):
        print("DLPFile: magic")
        magic = struct.unpack('<L', file.read(4))[0]
        if magic != 0x37504C44:
            raise Exception("Not a DLP7 file!")
        
        print("DLPFile: num_groups, num_patches, num_vertices")
        num_groups, num_patches, num_vertices = struct.unpack('>LLL', file.read(12))
        print(f"{num_groups} {num_patches} {num_vertices}")

        # read groups
        print("DLPFile: groups")
        for x in range(num_groups):
            self.groups.append(DLPGroup(file))

        # read patches
        print("DLPFile: patches")
        for x in range(num_patches):
            self.patches.append(DLPPatch(file))

        # read vertices
        print("DLPFile: vertices")
        for x in range(num_vertices):
            self.vertices.append(struct.unpack('>fff', file.read(12)))

        # read materials
        print("DLPFile: materials")
        num_materials = struct.unpack('>L', file.read(4))[0]
        for x in range(num_materials):
            self.materials.append(AGIMaterial(file))

        # read textures
        print("DLPFile: textures")
        num_textures = struct.unpack('>L', file.read(4))[0]
        for x in range(num_textures):
            self.textures.append(AGITexture(file))

        # read physics (TODO)
        print("DLPFile: physics")
        print("DLPFile: done")

