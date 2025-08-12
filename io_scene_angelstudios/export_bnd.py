import os, time, struct, math, sys
import os.path as path

import bpy, bmesh
from . import utils as utils
from .ter_section import TerSection

######################################################
# EXPORT HELPERS
######################################################
def get_bnd_materials(ob):
    export_material_names = []
    for ms in ob.material_slots:
        export_material_names.append(ms.material.name)
    if len(export_material_names) == 0:
        export_material_names.append("default")
    return export_material_names

def write_char_array(file, w_str, length):
    file.write(bytes(w_str, 'utf-8'))
    file.write(bytes('\x00' * (length - len(w_str )), 'utf-8'))

def point_in_polygon(p, vertices):
    n = len(vertices)
    inside =False

    x, y = p
    p1x,p1y = vertices[0]
    for i in range(n+1):
        p2x,p2y = vertices[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/float((p2y-p1y))+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y

    return inside


def point_in_bounds(bmin, bmax, p):
    return p[0] >= bmin[0] and p[1] >= bmin[1] and p[0] <= bmax[0] and p[1] <= bmax[1]

    
def edges_intersect(p1, p2, p3, p4):
    #https://stackoverflow.com/a/24392281
    #returns true if the line from (a,b)->(c,d) intersects with (p,q)->(r,s)
    a = p1[0]
    b = p1[1]
    c = p2[0]
    d = p2[1]
    p = p3[0]
    q = p3[1]
    r = p4[0]
    s = p4[1]
    
    det = (c - a) * (s - q) - (r - p) * (d - b);
    if abs(det) < 0.001:
      return False
    else:
      lmbda = ((s - q) * (r - a) + (p - r) * (s - b)) / det
      gamma = ((b - d) * (r - a) + (c - a) * (s - b)) / det
      return (0 < lmbda and lmbda < 1) and (0 < gamma and gamma < 1)
      
def bounds_intersect(amin, amax, bmin, bmax):
    return amin[0] <= bmax[0] and amax[0] >= bmin[0] and amin[1] <= bmax[1] and amax[1] >= bmin[1]

######################################################
# EXPORT MAIN FILES
######################################################
def export_terrain_bound(filepath, ob, apply_modifiers):
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
    bm.verts.ensure_lookup_table()
    bm.faces.index_update()
    bm.edges.index_update()
    
    with open(filepath, 'wb') as file:
        # header
        file.write(struct.pack('<f', 1.1))
        file.write(struct.pack('<LLB', len(bm.faces), 0, 0))
        
        # boundbox
        bnds = utils.bounds(ob)

        bnds_min = (bnds.x.min, bnds.y.min)
        bnds_max = (bnds.x.max, bnds.y.max)
        
        bnd_width = math.fabs(bnds.x.max - bnds.x.min)
        bnd_height = math.fabs(bnds.z.max - bnds.z.min)
        bnd_depth = math.fabs(bnds.y.max - bnds.y.min)

        file.write(struct.pack('<fff', bnd_width, bnd_height, bnd_depth))
        
        # section data  
        width_sections = max(1, math.ceil(bnd_width / 10))
        depth_sections = max(1, math.ceil(bnd_depth / 10))
        height_sections = 1
        
        total_sections = width_sections * height_sections * depth_sections
        individual_section_width = (1 / width_sections) * bnd_width
        individual_section_depth = (1 / depth_sections) * bnd_depth
        
        file.write(struct.pack('<LLLL', width_sections, height_sections, depth_sections, total_sections))
        
        #calculate intersecting polygons + poly indices
        poly_indices = 0
        ter_sections = []
        
        # create sections structures
        for d in range(depth_sections):
          for w in reversed(range(width_sections)):
            BOUNDS_INFLATION = 0.1
            
            section_bnds_min = ((bnds_min[0] + (w * individual_section_width)) - BOUNDS_INFLATION, (bnds_min[1] + (d * individual_section_depth)) - BOUNDS_INFLATION)
            section_bnds_max = ((bnds_min[0] + ((w + 1) * individual_section_width)) + BOUNDS_INFLATION, (bnds_min[1] + ((d + 1) * individual_section_depth)) + BOUNDS_INFLATION)

            section_edges = (((section_bnds_min[0], section_bnds_min[1]), (section_bnds_max[0], section_bnds_min[1])), ((section_bnds_max[0], section_bnds_min[1]), (section_bnds_max[0], section_bnds_max[1])),
                             ((section_bnds_min[0], section_bnds_max[1]), (section_bnds_max[0], section_bnds_max[1])), ((section_bnds_min[0], section_bnds_min[1]), (section_bnds_min[0], section_bnds_max[1])))
            section_poly = ((section_bnds_min[0], section_bnds_min[1]), (section_bnds_max[0], section_bnds_min[1]), (section_bnds_max[0], section_bnds_max[1]), (section_bnds_min[0], section_bnds_max[1]))
           
            #TerSection(self, bounds_min, bounds_max, edges, polygon):
            ter_section = TerSection(section_bnds_min, section_bnds_max, section_edges, section_poly)
            ter_sections.append(ter_section)
        
        # loop through faces and find faces in each section
        for f in bm.faces:
          # compute bounds
          face_2d = []
          for loop in f.loops:
            face_2d.append((loop.vert.co[0], loop.vert.co[1])) 
          
          face_min = [9999, 9999]
          face_max = [-9999, -9999]
          for pt in face_2d:
            face_min[1] = min(face_min[1], pt[1])
            face_min[0] = min(face_min[0], pt[0])
            face_max[1] = max(face_max[1], pt[1])
            face_max[0] = max(face_max[0], pt[0])
          
          # check each section to see if the face is contained
          for section in ter_sections:
            section_bnds_min = section.bounds[0]
            section_bnds_max = section.bounds[1]
            
            if not bounds_intersect(face_min, face_max, section_bnds_min, section_bnds_max):
              continue
              
            isect = False
            
            # face checks
            # check if this polygon surrounds this section
            section_poly = section.polygon
            for p in section_poly:
              isect |= point_in_polygon(p, face_2d)
              if isect:
                break
                  
            # edge checks
            if not isect:
              for edge in f.edges:
                if isect:
                    break
                    
                v0_3d = edge.verts[0]
                v1_3d = edge.verts[1]
                v0 = (v0_3d.co[0], v0_3d.co[1])
                v1 = (v1_3d.co[0], v1_3d.co[1])
                
                isect |= point_in_bounds(section_bnds_min, section_bnds_max, v0)
                isect |= point_in_bounds(section_bnds_min, section_bnds_max, v1)
                
                # more expensive edge-edge intersect testing (only if edge is not vertical)
                edge_is_vertical = v0[0] == v1[0] and v0[1] == v1[1]
                if not isect and not edge_is_vertical:
                    section_edges = section.edges
                    for se in section_edges:
                        isect |= edges_intersect(se[0], se[1], v0, v1)
                        if isect:
                            break
                
            if isect:
              section.group.append(f.index)
              poly_indices += 1
            
        # continue writing more binary information about boxes and stuff
        file.write(struct.pack('<L', poly_indices))
        
        if bnd_width == 0:
          file.write(struct.pack('<f', float('Inf')))
        else:
          file.write(struct.pack('<f', width_sections / bnd_width))
          
        file.write(struct.pack('<f', 1))
          
        if bnd_depth == 0:
          file.write(struct.pack('<f', float('Inf')))
        else:
          file.write(struct.pack('<f', depth_sections / bnd_depth))
          
        file.write(struct.pack('<ffffff',  -bnds.x.max, bnds.z.min, bnds.y.min, -bnds.x.min, bnds.z.max ,bnds.y.max))
        
        # write index info
        tot_ind = 0
        for i in range(total_sections):
          section_group = ter_sections[i].group
          file.write(struct.pack('H', tot_ind))
          tot_ind += len(section_group)

        for i in range(total_sections):
          section_group = ter_sections[i].group
          file.write(struct.pack('H', len(section_group)))
          
        for i in range(total_sections):
          section_group = ter_sections[i].group
          for j in range(len(section_group)):
              file.write(struct.pack('<H', section_group[j]))
          
        # finish off
        bm.free()
    return
    
def export_binary_bound(filepath, ob, ascii_version="1.01", apply_modifiers=True):
    with open(filepath, 'wb') as file:
        # get mesh data
        me = None
        depsgraph = bpy.context.evaluated_depsgraph_get()
        if apply_modifiers:
            export_ob = ob.evaluated_get(depsgraph)
            me = export_ob.to_mesh()
        else:
            me = ob.data.copy()
        export_material_names = get_bnd_materials(ob)
        
        # get bmesh
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.index_update()
        
        # header
        file.write(struct.pack('<B', 1)) # version. always 1
        file.write(struct.pack('<LLL', len(bm.verts), len(export_material_names), len(bm.faces)))
        
        # vertices
        for v in bm.verts:
            file.write(struct.pack('<fff', *utils.translate_vector(v.co)))

        # materials
        for mat_name in export_material_names:
            write_char_array(file, mat_name, 32)
            file.write(struct.pack('<ff', 0.1, 0.5)) # elasticity and friction
            if ascii_version == "1.01":
                write_char_array(file, 'none', 32)
                write_char_array(file, 'none', 32)
            else:
               file.write(struct.pack("<HH", 0, 0))

        # faces
        for face in bm.faces:
            material_index = max(0, face.material_index)
            if len(face.loops) == 3:
                file.write(struct.pack('<HHHHH', face.loops[0].vert.index, face.loops[1].vert.index, face.loops[2].vert.index, 0, material_index))
            elif len(face.loops) == 4:
                indices = [face.loops[0].vert.index, face.loops[1].vert.index, face.loops[2].vert.index, face.loops[3].vert.index]
                # last index can't be 0 in a quad, so shift this polygon around if that's the case
                if indices[3] == 0:
                    indices = [indices[3], indices[0], indices[1], indices[2]]                
                file.write(struct.pack('<HHHHH', indices[0], indices[1], indices[2], indices[3], material_index))
        
        # finish off
        bm.free()
    return


def export_bound(filepath, ob, version="1.01", apply_modifiers=True):
    with open(filepath, 'w') as file:
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
        bm.verts.index_update()
        bm.edges.index_update()

        export_material_names = get_bnd_materials(ob)
        export_edges = (version == "1.10")

        # header
        file.write(f"version: {version}\n")

        if version == "1.10":
           file.write("type: geometry\n")
           file.write("\n")

        file.write(f"verts: {len(bm.verts)}\n")
        file.write(f"materials: {len(export_material_names)}\n")
        if export_edges:
            file.write(f"edges: {len(bm.edges)}\n")
        else:
           file.write(f"edges: 0\n")
        file.write(f"polys: {len(bm.faces)}\n")
        file.write("\n")

        # vertices
        for v in bm.verts:
            file.write(f"v %.6f %.6f %.6f\n" % utils.translate_vector(v.co))
        file.write("\n")

        # materials
        for mtl_name in export_material_names:
            if version == "1.10":
                file.write("type: BASE\n")
            file.write(f"mtl {mtl_name} {{\n")
            file.write("\telasticity: 0.100000\n")
            file.write("\tfriction: 0.500000\n")
            if version == "1.01":
               file.write("\teffect: none\n")
               file.write("\tsound: none\n")
            file.write("}\n")
        file.write("\n")

        # edges
        if export_edges:
            for edge in bm.edges:
               file.write(f"edge {edge.verts[0].index} {edge.verts[1].index}\n")
            file.write("\n")

        # faces
        for face in bm.faces:
            material_index = max(0, face.material_index)
            if len(face.loops) == 3:
                file.write(f"tri {face.loops[0].vert.index} {face.loops[1].vert.index} {face.loops[2].vert.index} {material_index}")
                if version == "1.10":
                   file.write(f" {face.edges[0].index} {face.edges[1].index} {face.edges[2].index}")
                file.write("\n")
            elif len(face.loops) == 4:
                file.write(f"quad {face.loops[0].vert.index} {face.loops[1].vert.index} {face.loops[2].vert.index} {face.loops[3].vert.index} {material_index}")
                if version == "1.10":
                   file.write(f" {face.edges[0].index} {face.edges[1].index} {face.edges[2].index} {face.edges[3].index}")
                file.write("\n")
                
        # finish off
        bm.free()
    return


######################################################
# EXPORT
######################################################
def save(operator,
         context,
         filepath="",
         export_binary=False,
         export_terrain=False,
         apply_modifiers=False,
         bnd_version="1.01",
         ):
    
    # set object modes
    bound_ob = None
    for ob in context.scene.objects:
      if ob.type == 'MESH' and ob.name.lower() == "bound":
        bound_ob = ob
        break
      elif ob.name.lower() == "bound" and ob.type != 'MESH':
        raise Exception("BOUND has invalid object type, or is not visible in the scene")
    if  bound_ob is None:
       raise Exception("No BOUND object found in scene")
    
    print("exporting BOUND: %r..." % (filepath))
    time1 = time.perf_counter()
    
    # write bnd
    export_bound(filepath, bound_ob, bnd_version, apply_modifiers)
    
    if export_binary:
      # write BBND
      export_binary_bound(filepath[:-3] + "bbnd", bound_ob, bnd_version, apply_modifiers)
    if export_terrain:
      # write TER
      export_terrain_bound(filepath[:-3] + "ter", bound_ob, apply_modifiers)
      
    # bound export complete
    print(" done in %.4f sec." % (time.perf_counter() - time1))

    return {'FINISHED'}
