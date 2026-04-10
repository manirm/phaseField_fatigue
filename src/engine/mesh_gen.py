import gmsh
import os

class MeshGenerator:
    def __init__(self, output_dir="meshes"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
    def _apply_refinement(self, x_min, x_max, y_min, y_max, lc, tip_refine):
        """
        Apply a Box field for localized mesh refinement.
        """
        field_id = gmsh.model.mesh.field.add("Box")
        gmsh.model.mesh.field.setNumber(field_id, "VIn", lc / tip_refine)
        gmsh.model.mesh.field.setNumber(field_id, "VOut", lc)
        gmsh.model.mesh.field.setNumber(field_id, "XMin", x_min)
        gmsh.model.mesh.field.setNumber(field_id, "XMax", x_max)
        gmsh.model.mesh.field.setNumber(field_id, "YMin", y_min)
        gmsh.model.mesh.field.setNumber(field_id, "YMax", y_max)
        gmsh.model.mesh.field.setNumber(field_id, "Thickness", lc * 3) # Transition zone

        gmsh.model.mesh.field.setAsBackgroundMesh(field_id)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

    def generate_ct_specimen(self, W=50.0, a=22.5, lc=1.5, tip_refine=5.0, is_3d=False, thickness=10.0):
        """
        Generate a realistic Compact Tension (CT) specimen mesh with strip refinement.
        """
        if not gmsh.isInitialized():
            gmsh.initialize(interruptible=False)
        else:
            gmsh.clear()
        
        gmsh.model.add("CT_Specimen")
        occ = gmsh.model.occ
        
        h = 1.2 * W
        w_total = 1.25 * W
        hole_diam = 0.25 * W
        hole_x = 0.25 * W
        hole_y_offset = 0.275 * W
        
        rect = occ.addRectangle(0, 0, 0, w_total, h)
        hole1 = occ.addDisk(hole_x, h/2 + hole_y_offset, 0, hole_diam/2, hole_diam/2)
        hole2 = occ.addDisk(hole_x, h/2 - hole_y_offset, 0, hole_diam/2, hole_diam/2)
        
        notch_w = a
        notch_h = 0.5
        notch = occ.addRectangle(0, h/2 - notch_h/2, 0, notch_w, notch_h)
        
        specimen, _ = occ.cut([(2, rect)], [(2, hole1), (2, hole2), (2, notch)])
        
        if is_3d:
            occ.extrude(specimen, 0, 0, thickness)
            
        occ.synchronize()
        
        # Refinement Box: Strip ahead of the notch tip
        self._apply_refinement(
            x_min=a - lc, x_max=w_total,
            y_min=h/2 - lc*2, y_max=h/2 + lc*2,
            lc=lc, tip_refine=tip_refine
        )
        
        gmsh.model.mesh.generate(3 if is_3d else 2)
        path = os.path.join(self.output_dir, "ct_specimen.msh")
        gmsh.write(path)
        return path

    def generate_senb_specimen(self, L=100.0, W=20.0, a=10.0, lc=1.0, tip_refine=5.0, symmetry=False, is_3d=False, thickness=10.0):
        """
        Generate a Single Edge Notch Bending (SENB) specimen mesh with strip refinement.
        """
        if not gmsh.isInitialized():
            gmsh.initialize(interruptible=False)
        else:
            gmsh.clear()
            
        gmsh.model.add("SENB_Specimen")
        occ = gmsh.model.occ
        
        if symmetry:
            rect = occ.addRectangle(L/2, 0, 0, L/2, W)
            notch_w = 0.5
            notch = occ.addRectangle(L/2, 0, 0, notch_w, a)
            specimen, _ = occ.cut([(2, rect)], [(2, notch)])
        else:
            rect = occ.addRectangle(0, 0, 0, L, W)
            notch_w = 0.5
            notch = occ.addRectangle(L/2 - notch_w/2, 0, 0, notch_w, a)
            specimen, _ = occ.cut([(2, rect)], [(2, notch)])
            
        if is_3d:
            occ.extrude(specimen, 0, 0, thickness)
            
        occ.synchronize()
        
        # Refinement Box: Vertical strip ahead of the notch tip
        self._apply_refinement(
            x_min=L/2 - lc*2, x_max=L/2 + lc*2,
            y_min=a - lc, y_max=W,
            lc=lc, tip_refine=tip_refine
        )
        
        gmsh.model.mesh.generate(3 if is_3d else 2)
        path = os.path.join(self.output_dir, "senb_specimen.msh")
        gmsh.write(path)
        return path

    def generate_cct_specimen(self, W=50.0, H=100.0, a=10.0, lc=1.5, tip_refine=5.0, symmetry=False, is_3d=False, thickness=10.0):
        """
        Generate a Center-Cracked Tension (CCT) specimen mesh with strip refinement.
        """
        if not gmsh.isInitialized():
            gmsh.initialize(interruptible=False)
        else:
            gmsh.clear()
            
        gmsh.model.add("CCT_Specimen")
        occ = gmsh.model.occ
        
        if symmetry:
            rect = occ.addRectangle(0, 0, 0, W/2, H/2)
            notch_h = 0.5
            notch = occ.addRectangle(0, 0, 0, a, notch_h)
            specimen, _ = occ.cut([(2, rect)], [(2, notch)])
        else:
            rect = occ.addRectangle(0, 0, 0, W, H)
            notch_h = 0.5
            notch = occ.addRectangle(W/2 - a, H/2 - notch_h/2, 0, 2*a, notch_h)
            specimen, _ = occ.cut([(2, rect)], [(2, notch)])
            
        if is_3d:
            occ.extrude(specimen, 0, 0, thickness)
            
        occ.synchronize()
        
        # Refinement Box: Path ahead of the crack tip(s)
        if symmetry:
            self._apply_refinement(
                x_min=a - lc, x_max=W/2,
                y_min=-lc*2, y_max=lc*2,
                lc=lc, tip_refine=tip_refine
            )
        else:
            self._apply_refinement(
                x_min=0, x_max=W,
                y_min=H/2 - lc*2, y_max=H/2 + lc*2,
                lc=lc, tip_refine=tip_refine
            )
        
        gmsh.model.mesh.generate(3 if is_3d else 2)
        path = os.path.join(self.output_dir, "cct_specimen.msh")
        gmsh.write(path)
        return path
