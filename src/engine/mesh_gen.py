import gmsh
import os

class MeshGenerator:
    def __init__(self, output_dir="meshes"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
    def generate_ct_specimen(self, W=50.0, a=22.5, lc=1.5, tip_refine=5.0):
        """
        Generate a realistic Compact Tension (CT) specimen mesh using OCC.
        W: Characteristic width, a: Initial crack length, lc: Element size, tip_refine: factor
        """
        if not gmsh.isInitialized():
            gmsh.initialize(interruptible=False)
        else:
            gmsh.clear()
        
        gmsh.model.add("CT_Specimen")
        
        # We use OpenCascade factory for booleans (holes/notch)
        occ = gmsh.model.occ
        
        # Dimensions based on ASTM E399 (standard proportions)
        h = 1.2 * W  # Total Height
        w_total = 1.25 * W # Total Width
        hole_diam = 0.25 * W
        hole_x = 0.25 * W
        hole_y_offset = 0.275 * W # Distance from centerline to hole center
        
        # 1. Main body
        rect = occ.addRectangle(0, 0, 0, w_total, h)
        
        # 2. Holes
        hole1 = occ.addDisk(hole_x, h/2 + hole_y_offset, 0, hole_diam/2, hole_diam/2)
        hole2 = occ.addDisk(hole_x, h/2 - hole_y_offset, 0, hole_diam/2, hole_diam/2)
        
        # 3. Notch (Simplified as a thin rectangle for now to serve as crack starter)
        notch_w = a
        notch_h = 0.5 # thin slit
        notch = occ.addRectangle(0, h/2 - notch_h/2, 0, notch_w, notch_h)
        
        # Boolean operations: Body - Holes - Notch
        specimen, _ = occ.cut([(2, rect)], [(2, hole1), (2, hole2), (2, notch)])
        
        occ.synchronize()
        
        # Refine mesh near the crack tip
        # We can add a point at (a, h/2) and set a smaller lc there
        p_tip = gmsh.model.geo.addPoint(a, h/2, 0, lc/tip_refine)
        gmsh.model.mesh.setSize([(0, p_tip)], lc/tip_refine)
        
        gmsh.model.mesh.generate(2)
        
        path = os.path.join(self.output_dir, "ct_specimen.msh")
        gmsh.write(path)
        return path

    def generate_senb_specimen(self, L=100.0, H=20.0, a=10.0, lc=0.5, tip_refine=5.0):
        """
        Generate a Single Edge Notch Bending (SENB) specimen mesh.
        """
        if not gmsh.isInitialized():
            gmsh.initialize(interruptible=False)
        else:
            gmsh.clear()
            
        gmsh.model.add("SENB_Specimen")
        
        # Rectangular beam
        p1 = gmsh.model.geo.addPoint(0, 0, 0, lc)
        p2 = gmsh.model.geo.addPoint(L, 0, 0, lc)
        p3 = gmsh.model.geo.addPoint(L, H, 0, lc)
        p4 = gmsh.model.geo.addPoint(0, H, 0, lc)
        
        l1 = gmsh.model.geo.addLine(p1, p2)
        l2 = gmsh.model.geo.addLine(p2, p3)
        l3 = gmsh.model.geo.addLine(p3, p4)
        l4 = gmsh.model.geo.addLine(p4, p1)
        
        loop = gmsh.model.geo.addCurveLoop([l1, l2, l3, l4])
        surf = gmsh.model.geo.addPlaneSurface([loop])
        
        gmsh.model.geo.synchronize()
        gmsh.model.mesh.generate(2)
        
        path = os.path.join(self.output_dir, "senb_specimen.msh")
        gmsh.write(path)
        return path
