import os, time, struct, math, sys
import os.path as path

import bpy, bmesh
from bpy_extras import  node_shader_utils
from . import utils as utils
from . import binary_ops_arts as binary_ops_arts

######################################################
# EXPORT HELPERS
######################################################
normals_table = ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0),(0.0, 1.0, 0.0),(-1.0, 0.0, 0.0),(0.0, -1.0, 0.0),(0.0, 0.0, -1.0),(0.2225, 0.0, 0.97490001),
                 (0.4339, 0.0, 0.90100002),(0.62349999, 0.0, 0.78179997),(0.78179997, 0.0, 0.62349999),(0.90100002, 0.0, 0.4339),
                 (0.97490001, 0.0, 0.2225),(0.0, 0.2225, 0.97490001),(0.0, 0.4339, 0.90100002),(0.0, 0.62349999, 0.78179997),
                 (0.0, 0.78179997, 0.62349999),(0.0, 0.90100002, 0.4339),(0.0, 0.97490001, 0.2225),(-0.2225, 0.0, 0.97490001),
                 (-0.4339, 0.0, 0.90100002),(-0.62349999, 0.0, 0.78179997),(-0.78179997, 0.0, 0.62349999),(-0.90100002, 0.0, 0.4339),
                 (-0.97490001, 0.0, 0.2225),(0.0, -0.2225, 0.97490001),(0.0, -0.4339, 0.90100002),(0.0, -0.62349999, 0.78179997),
                 (0.0, -0.78179997, 0.62349999),(0.0, -0.90100002, 0.4339),(0.0, -0.97490001, 0.2225),(0.2225, 0.0, -0.97490001),
                 (0.4339, 0.0, -0.90100002),(0.62349999, 0.0, -0.78179997),(0.78179997, 0.0, -0.62349999),(0.90100002, 0.0, -0.4339),
                 (0.97490001, 0.0, -0.2225),(0.0, 0.2225, -0.97490001),(0.0, 0.4339, -0.90100002),(0.0, 0.62349999, -0.78179997),
                 (0.0, 0.78179997, -0.62349999),(0.0, 0.90100002, -0.4339),(0.0, 0.97490001, -0.2225),(-0.2225, 0.0, -0.97490001),
                 (-0.4339, 0.0, -0.90100002),(-0.62349999, 0.0, -0.78179997),(-0.78179997, 0.0, -0.62349999),(-0.90100002, 0.0, -0.4339),
                 (-0.97490001, 0.0, -0.2225),(0.0, -0.2225, -0.97490001),(0.0, -0.4339, -0.90100002),(0.0, -0.62349999, -0.78179997),
                 (0.0, -0.78179997, -0.62349999),(0.0, -0.90100002, -0.4339),(0.0, -0.97490001, -0.2225),(0.97490001, 0.2225, 0.0),
                 (0.90100002, 0.4339, 0.0),(0.78179997, 0.62349999, 0.0),(0.62349999, 0.78179997, 0.0),(0.4339, 0.90100002, 0.0),
                 (0.2225, 0.97490001, 0.0),(-0.2225, 0.97490001, 0.0),(-0.4339, 0.90100002, 0.0),(-0.62349999, 0.78179997, 0.0),
                 (-0.78179997, 0.62349999, 0.0),(-0.90100002, 0.4339, 0.0),(-0.97490001, 0.2225, 0.0),(-0.97490001, -0.2225, 0.0),
                 (-0.90100002, -0.4339, 0.0),(-0.78179997, -0.62349999, 0.0),(-0.62349999, -0.78179997, 0.0),(-0.4339, -0.90100002, 0.0),
                 (-0.2225, -0.97490001, 0.0),(0.2225, -0.97490001, 0.0),(0.4339, -0.90100002, 0.0),(0.62349999, -0.78179997, 0.0),
                 (0.78179997, -0.62349999, 0.0),(0.90100002, -0.4339, 0.0),(0.97490001, -0.2225, 0.0),(0.2279, 0.2279, 0.94660002),
                 (0.45050001, 0.2361, 0.861),(0.2361, 0.45050001, 0.861),(0.65329999, 0.245, 0.71640003),(0.4691, 0.4691, 0.7482),
                 (0.245, 0.65329999, 0.71640003),(0.8197, 0.2502, 0.51529998),(0.67619997, 0.4815, 0.5575),(0.4815, 0.67619997, 0.5575),
                 (0.2502, 0.8197, 0.51529998),(0.93159997, 0.2448, 0.2685),(0.82880002, 0.47400001, 0.2974),(0.67290002, 0.67290002, 0.30720001),
                 (0.47400001, 0.82880002, 0.2974),(0.2448, 0.93159997, 0.2685),(-0.2279, 0.2279, 0.94660002),(-0.2361, 0.45050001, 0.861),
                 (-0.45050001, 0.2361, 0.861),(-0.245, 0.65329999, 0.71640003),(-0.4691, 0.4691, 0.7482),(-0.65329999, 0.245, 0.71640003),
                 (-0.2502, 0.8197, 0.51529998),(-0.4815, 0.67619997, 0.5575),(-0.67619997, 0.4815, 0.5575),(-0.8197, 0.2502, 0.51529998),
                 (-0.2448, 0.93159997, 0.2685),(-0.47400001, 0.82880002, 0.2974),(-0.67290002, 0.67290002, 0.30720001),
                 (-0.82880002, 0.47400001, 0.2974),(-0.93159997, 0.2448, 0.2685),(-0.2279, -0.2279, 0.94660002),(-0.45050001, -0.2361, 0.861),
                 (-0.2361, -0.45050001, 0.861),(-0.65329999, -0.245, 0.71640003),(-0.4691, -0.4691, 0.7482),(-0.245, -0.65329999, 0.71640003),
                 (-0.8197, -0.2502, 0.51529998),(-0.67619997, -0.4815, 0.5575),(-0.4815, -0.67619997, 0.5575),(-0.2502, -0.8197, 0.51529998),
                 (-0.93159997, -0.2448, 0.2685),(-0.82880002, -0.47400001, 0.2974),(-0.67290002, -0.67290002, 0.30720001),
                 (-0.47400001, -0.82880002, 0.2974),(-0.2448, -0.93159997, 0.2685),(0.2279, -0.2279, 0.94660002),(0.2361, -0.45050001, 0.861),
                 (0.45050001, -0.2361, 0.861),(0.245, -0.65329999, 0.71640003),(0.4691, -0.4691, 0.7482),(0.65329999, -0.245, 0.71640003),
                 (0.2502, -0.8197, 0.51529998),(0.4815, -0.67619997, 0.5575),(0.67619997, -0.4815, 0.5575),(0.8197, -0.2502, 0.51529998),
                 (0.2448, -0.93159997, 0.2685),(0.47400001, -0.82880002, 0.2974),(0.67290002, -0.67290002, 0.30720001),
                 (0.82880002, -0.47400001, 0.2974),(0.93159997, -0.2448, 0.2685),(0.2279, 0.2279, -0.94660002),(0.2361, 0.45050001, -0.861),
                 (0.45050001, 0.2361, -0.861),(0.245, 0.65329999, -0.71640003),(0.4691, 0.4691, -0.7482),(0.65329999, 0.245, -0.71640003),
                 (0.2502, 0.8197, -0.51529998),(0.4815, 0.67619997, -0.5575),(0.67619997, 0.4815, -0.5575),(0.8197, 0.2502, -0.51529998),
                 (0.2448, 0.93159997, -0.2685),(0.47400001, 0.82880002, -0.2974),(0.67290002, 0.67290002, -0.30720001),
                 (0.82880002, 0.47400001, -0.2974),(0.93159997, 0.2448, -0.2685),(-0.2279, 0.2279, -0.94660002),(-0.45050001, 0.2361, -0.861),
                 (-0.2361, 0.45050001, -0.861),(-0.65329999, 0.245, -0.71640003),(-0.4691, 0.4691, -0.7482),(-0.245, 0.65329999, -0.71640003),
                 (-0.8197, 0.2502, -0.51529998),(-0.67619997, 0.4815, -0.5575),(-0.4815, 0.67619997, -0.5575),(-0.2502, 0.8197, -0.51529998),
                 (-0.93159997, 0.2448, -0.2685),(-0.82880002, 0.47400001, -0.2974),(-0.67290002, 0.67290002, -0.30720001),
                 (-0.47400001, 0.82880002, -0.2974),(-0.2448, 0.93159997, -0.2685),(-0.2279, -0.2279, -0.94660002),(-0.2361, -0.45050001, -0.861),
                 (-0.45050001, -0.2361, -0.861),(-0.245, -0.65329999, -0.71640003),(-0.4691, -0.4691, -0.7482),(-0.65329999, -0.245, -0.71640003),
                 (-0.2502, -0.8197, -0.51529998),(-0.4815, -0.67619997, -0.5575),(-0.67619997, -0.4815, -0.5575),(-0.8197, -0.2502, -0.51529998),
                 (-0.2448, -0.93159997, -0.2685),(-0.47400001, -0.82880002, -0.2974),(-0.67290002, -0.67290002, -0.30720001),
                 (-0.82880002, -0.47400001, -0.2974),(-0.93159997, -0.2448, -0.2685),(0.2279, -0.2279, -0.94660002),(0.45050001, -0.2361, -0.861),
                 (0.2361, -0.45050001, -0.861),(0.65329999, -0.245, -0.71640003),(0.4691, -0.4691, -0.7482),(0.245, -0.65329999, -0.71640003),
                 (0.8197, -0.2502, -0.51529998),(0.67619997, -0.4815, -0.5575),(0.4815, -0.67619997, -0.5575),(0.2502, -0.8197, -0.51529998),
                 (0.93159997, -0.2448, -0.2685),(0.82880002, -0.47400001, -0.2974),(0.67290002, -0.67290002, -0.30720001),
                 (0.47400001, -0.82880002, -0.2974),(0.2448, -0.93159997, -0.2685))

def calculate_plane(p1, p2, p3):
    u = (p3[0] - p2[0], p3[1] - p2[1], p3[2] - p2[2])
    v = (p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2])

    # cross
    nx = u[1] * v[2] - u[2] * v[1]
    ny = u[2] * v[0] - u[0] * v[2]
    nz = u[0] * v[1] - u[1] * v[0]

    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length != 0.0:
        nx /= length
        ny /= length
        nz /= length

    # distance term
    w = -(nx * p2[0] + ny * p2[1] + nz * p2[2])

    return (nx, ny, nz, w)

def calculate_plane_for_face(face):
    p1 = utils.translate_vector(face.loops[0].vert.co)
    p2 = utils.translate_vector(face.loops[1].vert.co)
    p3 = utils.translate_vector(face.loops[2].vert.co)
    return calculate_plane(p1, p2, p3)

def pack_normal(normal):
    # quick checks
    if normal[1] > 0.99:
        return 2
    if normal[0] > 0.99:
        return 1
    if normal[2] > 0.99:
        return 0

    closest_index = 0
    best_dist = float('inf')

    for i, check_normal in enumerate(normals_table):
        dot = (normal[0] * check_normal[0] +
               normal[1] * check_normal[1] +
               normal[2] * check_normal[2])
        
        if dot < 0:
            continue  # opposite direction, skip

        dx = normal[0] - check_normal[0]
        dy = normal[1] - check_normal[1]
        dz = normal[2] - check_normal[2]
        dist = dx * dx + dy * dy + dz * dz

        if dist < best_dist:
            best_dist = dist
            closest_index = i

    return closest_index

######################################################
# EXPORT MAIN FILES
######################################################
def export_bms_object(filepath, ob, apply_modifiers=True, export_normals=True, export_colors=True, export_uvs=True, export_planes=True, apply_transform=False):
    # get mesh data
    me = None
    depsgraph = bpy.context.evaluated_depsgraph_get()
    if apply_modifiers:
        export_ob = ob.evaluated_get(depsgraph)
        me = export_ob.to_mesh()
    else:
        me = ob.data.copy()
        
    # get bmesh
    bm = bmesh.new()
    bm.from_mesh(me)

    if apply_transform:
        bm.transform(ob.matrix_world)

    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.active
    vc_layer = bm.loops.layers.color.active

    # disable export flags where not possible
    if uv_layer is None:
        export_uvs = False
    if vc_layer is None:
        export_colors = False

    # mesh info
    offset = (0.0, 0.0, 0.0) if apply_transform else tuple(ob.location)
    bounds = utils.bounds(ob)
    num_points = len(bm.verts)
    num_adjuncts = 0
    num_surfaces = 0
    cache_size = 0
    mesh_radius = 0.0
    box_radius = 0.0
    num_indices = 0
    num_textures = len(ob.material_slots)

    # calc bounding info
    for vert in bm.verts:
        dist = math.sqrt(vert.co[0] * vert.co[0] + vert.co[1] * vert.co[1] + vert.co[2] * vert.co[2])
        mesh_radius = max(dist, mesh_radius)

    bbox_corners = []
    bbox_corners.append((bounds.x.min, bounds.y.min, bounds.z.min))  # 0
    bbox_corners.append((bounds.x.max, bounds.y.min, bounds.z.min))  # 1
    bbox_corners.append((bounds.x.max, bounds.y.min, bounds.z.max))  # 2
    bbox_corners.append((bounds.x.min, bounds.y.min, bounds.z.max))  # 3
    bbox_corners.append((bounds.x.min, bounds.y.max, bounds.z.min))  # 4
    bbox_corners.append((bounds.x.max, bounds.y.max, bounds.z.min))  # 5
    bbox_corners.append((bounds.x.max, bounds.y.max, bounds.z.max))  # 6
    bbox_corners.append((bounds.x.min, bounds.y.max, bounds.z.max))  # 7
    for vert in bbox_corners:
        dist = math.sqrt(vert[0] * vert[0] + vert[1] * vert[1] + vert[2] * vert[2])
        box_radius = max(box_radius, dist)

    # create adjuncts
    loop_hash_map = {}
    loop_index_map = {}

    adjuncts_indices = []
    adjuncts_uvs = []
    adjuncts_normals = []
    adjuncts_colors = []
    
    for face in bm.faces:
        for loop in face.loops:
            if not loop.index in loop_index_map:
                # prepare our hash entry
                pos_hash = str(loop.vert.co)
                uv_hash = "NOUV"
                col_hash = "NOCOL"
                nrm_hash = "NONRM"
                if export_normals:
                    nrm_hash = str(loop.vert.normal)
                if uv_layer is not None and export_uvs:
                    uv_hash = str(loop[uv_layer].uv)
                if vc_layer is not None and export_colors:
                    col_hash = str(loop[vc_layer])
                
                index_hash = pos_hash + "|" + uv_hash + "|" + col_hash + "|" + nrm_hash
                if index_hash in loop_hash_map:
                    loop_index_map[loop.index] = loop_hash_map[index_hash]
                else:
                    loop_hash_map[index_hash] = num_adjuncts
                    loop_index_map[loop.index] = num_adjuncts
                    num_adjuncts += 1

                    adjuncts_indices.append(loop.vert.index)
                    if export_normals:
                        adjuncts_normals.append(loop.vert.normal)
                    if uv_layer is not None and export_uvs:
                        adjuncts_uvs.append(loop[uv_layer].uv)
                    if vc_layer is not None and export_colors:
                        adjuncts_colors.append(loop[vc_layer])


    # create surfaces
    surfaces = []
    for face in bm.faces:
        num_loops = len(face.loops)
        if num_loops == 3 or num_loops == 4:
            surfaces.append(face)
            num_surfaces += 1

    # create surface indices
    surface_indices = []
    for face in surfaces:
        num_loops = len(face.loops)
        if num_loops == 3:
            indices = [loop_index_map[face.loops[0].index], loop_index_map[face.loops[1].index],
                       loop_index_map[face.loops[2].index], 0]
            surface_indices.extend(indices)
        elif num_loops == 4:
            indices = [loop_index_map[face.loops[0].index], loop_index_map[face.loops[1].index],
                       loop_index_map[face.loops[2].index], loop_index_map[face.loops[3].index]]
            # last index can't be 0 in a quad, so shift this polygon around if that's the case
            if indices[3] == 0:
                indices = [indices[3], indices[0], indices[1], indices[2]]                
            surface_indices.extend(indices)
        num_indices += 4

    # create flags
    flags = 0
    if export_uvs:
        flags |= 0x1 # MESH_SET_UV
    if export_normals:
        flags |= 0x2 # MESH_SET_NORMAL
    if export_colors:
        flags |= 0x4 #MESH_SET_CPV

    obj_offcenter = abs(offset[0]) > 0.001 or abs(offset[1]) > 0.001 or abs(offset[2]) > 0.001
    if obj_offcenter:
        flags |= 0x8 # MESH_SET_OFFSET

    if export_planes:
        flags |= 0x10 # MESH_SET_PLANES

    # compute cache size
    cache_size = 12 * num_points
    if num_points >= 16:
        cache_size += 12 * 8
    if export_normals:
        cache_size += 12 * num_adjuncts
    if export_uvs:
        cache_size += 8 * num_adjuncts
    if export_colors:
        cache_size += 4 * num_adjuncts
    if export_planes:
        cache_size += 16 * num_surfaces

    cache_size += 2 * num_adjuncts # indices
    cache_size += 1 * num_surfaces # texture indices
    cache_size += 2 * num_indices # surface indices

    # compute planes
    planes = []
    if export_planes:
        for face in surfaces:
            planes.append(calculate_plane_for_face(face))

    with open(filepath, 'wb') as file:
        # header
        file.write(struct.pack('<L', 0x4D534833)) # 3HSM
        file.write(struct.pack('<fff', *utils.translate_vector(offset))) # offset
        file.write(struct.pack('<LLLL', num_points, num_adjuncts, num_surfaces, num_indices))

        file.write(struct.pack('<ff', mesh_radius, mesh_radius * mesh_radius))
        file.write(struct.pack('<f', box_radius))

        file.write(struct.pack('<B', num_textures))
        file.write(struct.pack('<B', flags))

        file.write(struct.pack('<H', 0)) # padding
        file.write(struct.pack('<L', cache_size))

        # write textures
        for material_slot in ob.material_slots:
            material = material_slot.material
            mat_wrap = node_shader_utils.PrincipledBSDFWrapper(material)
            
            texture = mat_wrap.base_color_texture

            texture_name = "" if material is None else material.name
            texture_flags = 0x00
            texture_props = 0x00
            field_28 = 2.0

            if mat_wrap.emission_strength == 1.0:
                texture_props |= 0x40 # notLit
            if texture is not None and texture.image is not None:
                texture_name = utils.get_image_name_from_path(texture.image.filepath)
                if texture.extension == "REPEAT":
                    texture_flags |= 0x6 # wrap U/V
                else:
                    texture_props |= 0x400 # Clamp both
            if material is not None and material.blend_method != 'OPAQUE':
                texture_flags |= 0x1 # alpha
                texture_props |= 0x10 # transparent

            if material is not None and "Snowable" in material:
                field_28 = 4.0
                texture_props |= 0x1 # snowable

            binary_ops_arts.write_string(file, texture_name, 32)
            file.write(struct.pack('<BBBB', texture_flags, 0, 0, 0)) # flags, lod/maxlod?, pad
            file.write(struct.pack('<L', texture_props))
            file.write(struct.pack('<f', field_28))

            color = mat_wrap.base_color
            alpha = mat_wrap.alpha

            cr = int(max(0, min(255, color[2] * 255.0)))
            cg = int(max(0, min(255, color[1] * 255.0)))
            cb = int(max(0, min(255, color[0] * 255.0)))
            ca = int(max(0, min(255, alpha * 255.0)))
            file.write(struct.pack('<BBBB', cr, cg, cb, ca))
            
        # write verts
        for vert in bm.verts:
            file.write(struct.pack('<fff', *utils.translate_vector(vert.co)))

        # write bbox
        if num_points >= 16:
            for vert in bbox_corners:
                file.write(struct.pack('<fff', *utils.translate_vector(vert)))

        # write normals
        if export_normals:
            for normal in adjuncts_normals:
                translated = utils.translate_vector(normal)
                index = pack_normal(translated)
                file.write(struct.pack('<B', index))
        
        # write texture coordinates
        if export_uvs:
            for uv in adjuncts_uvs:
                file.write(struct.pack('<ff', *utils.translate_uv(uv)))

        # write colors
        if export_colors:
            for color in adjuncts_colors:
                cr = int(max(0, min(255, color[2] * 255.0)))
                cg = int(max(0, min(255, color[1] * 255.0)))
                cb = int(max(0, min(255, color[0] * 255.0)))
                ca = int(max(0, min(255, color[3] * 255.0)))
                file.write(struct.pack('<BBBB', cr, cg, cb, ca))

        # write indices
        if num_adjuncts > 0:
            file.write(struct.pack(f"<{num_adjuncts}H", *adjuncts_indices))

        # write planes
        if export_planes:
            for plane in planes:
                #print(f"Plane {plane[0]:.4f} {plane[1]:.4f} {plane[2]:.4f} {plane[3]:.4f}")
                file.write(struct.pack('<ffff', *plane))

        # texture and surface indices
        for face in surfaces:
            file.write(struct.pack("<B", face.material_index + 1)) # 0 = none, 1 = first
        file.write(struct.pack(f"<{num_indices}H", *surface_indices))

    # finish off
    bm.free()
    return

######################################################
# EXPORT
######################################################
def save(operator,
         context,
         filepath="",
         apply_modifiers=True,
         export_normals=True,
         export_colors=True,
         export_uvs=True,
         export_planes=True,
         ):
    
    print("exporting BMS: %r..." % (filepath))
    ob = bpy.context.active_object
    if ob is None:
        raise Exception("No object selected to export")
    
    time1 = time.perf_counter()
    # save BMS
    export_bms_object(filepath, ob, apply_modifiers, export_normals, export_colors, export_uvs, export_planes)
    
    #export complete
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}