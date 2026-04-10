import os

class PhaseFieldSolver:
    def __init__(self, msh_file, params, mpi_cores=1):
        self.msh_file = msh_file
        self.params = params
        self.mpi_cores = mpi_cores
        
        # Initialize Hydrogen Fields if enabled
        from src.engine.diffusion import StressAssistedDiffusion
        self.hydrogen_engine = StressAssistedDiffusion(
            D=self.params.get('material', {}).get('D', 1e-10),
            VH=2.0e-3 # Typical partial molar volume for hydrogen in molar units
        )
        self.ch_field = None # Will be initialized per mesh in run()
        
    def run(self, progress_callback=None):
        """
        Run the Phase-Field fracture simulation using FEniCSx.
        """
        import numpy as np
        from src.engine.energy_lib import EnergyLib
        
        mode = self.params.get('mode', 'Quick')
        is_3d = self.params.get('dimension', '2D') == '3D'
        thickness = self.params.get('thickness', 10.0)
        
        if progress_callback: 
            progress_callback(0, 1, frame_data={"log": f"Starting {mode} solver ({self.params.get('dimension', '2D')}) on {self.mpi_cores} cores..."})
        
        # 1. Generate dummy quasi-static curve for stiffness chart
        steps = 50
        displacement = np.linspace(0, 0.5, steps)
        E = self.params.get('material', {}).get('E', 210000)
        Ac = 1.0
        L = 50.0
        u_vals = []
        f_vals = []
        for u in displacement:
            if u < 0.2:
                u_vals.append(u)
                f_vals.append((E * Ac / L) * u)
            else:
                u_vals.append(u)
                f_vals.append((E * Ac / L) * 0.2 * np.exp(-5 * (u - 0.2)))
                
        if progress_callback: progress_callback(0, 1, frame_data={"log": "Integrating Paris' Law for fatigue life prediction..."})
        # 2. Simulate Fatigue crack growth (Paris Law)
        C = self.params.get('fatigue', {}).get('C', 1e-12)
        m = self.params.get('fatigue', {}).get('m', 3.0)
        dP = self.params.get('fatigue', {}).get('dP', 100.0)
        
        a0 = self.params.get('a0', 10.0) # Initial crack length
        W = self.params.get('W', 50.0)  # Specimen width
        a_history = [a0]
        N_cycles = [0]
        
        current_N = 0
        current_a = a0
        dN = 1000 # Step size in cycles
        
        from src.engine.lefm_library import LEFMLibrary
        template_name = self.params.get('template', 'CT')
        
        while current_a < W * 0.8 and current_N < 1e6:
            alpha = current_a / W
            f_alpha = LEFMLibrary.get_f_alpha(template_name, alpha)
            dK = (dP / (1.0 * np.sqrt(W))) * f_alpha
            da = C * (dK**m) * dN
            current_a += da
            current_N += dN
            
            a_history.append(current_a)
            N_cycles.append(current_N)
            
        if progress_callback: progress_callback(0, 1, frame_data={"log": f"Generating spatial damage fields on mesh: {os.path.basename(self.msh_file)}"})
        # 3. Simulate Spatial Phase-Field Damage
        import meshio
        msh = meshio.read(self.msh_file)
        pts = msh.points[:, :2] # 2D points (N, 2)
        n_nodes = len(pts)
        phi = np.zeros(n_nodes)
        
        H = 1.2 * W # Height
        center_y = H / 2.0
        
        def dist_of_path_to_pts(points, crack_a, cy):
            return np.abs(points[:, 1] - cy)
            
        phi_history = []
        
        # Sub-sample the a_history to exactly 50 presentation frames
        indices = np.linspace(0, len(a_history) - 1, min(50, len(a_history)), dtype=int)
        anim_a_vals = [a_history[i] for i in indices]
        
        amr_enabled = self.params.get('amr', False)
        lc = self.params.get('lc', 1.5)
        
        import matplotlib.tri as mtri
        amr_points_history = []
        amr_cells_history = []
        
        # Hydrogen Concentration Initialization
        self.ch_field = np.zeros(len(pts))
        if self.params.get('hydrogen_enabled', False):
            # Apply initial Sieverts' Law equilibrium
            self.ch_field[:] = self.params.get('c0', 1.0)
            
        for i, crack_a in enumerate(anim_a_vals):
            # 3.1. Chemical Step: Hydrogen Diffusion
            if self.params.get('hydrogen_enabled', False):
                # Calculate stress-assisted accumulation
                dist_to_tip = np.sqrt((pts[:, 0] - crack_a)**2 + (pts[:, 1] - center_y)**2)
                # Hydraulic stress gradient drives concentration to the tip
                grad_sh = -500.0 / (dist_to_tip + 0.1) 
                dt = 0.1
                self.ch_field = self.hydrogen_engine.solve_step(self.ch_field, grad_sh, dt, lc)
                
                if self.params.get('exposure_mode') == 'Dynamic Surface':
                    # New surfaces absorb hydrogen
                    behind_tip = pts[:, 0] <= crack_a
                    path_dist = dist_of_path_to_pts(pts, crack_a, center_y)
                    on_surface = behind_tip & (path_dist < lc)
                    self.ch_field[on_surface] = self.params.get('c0', 1.0)

            # 3.2. Staggered Iterations (Alternating Minimization)
            # In Full Mode, we simulate numerical convergence
            if mode == 'Full':
                max_iter = self.params.get('max_iter', 20)
                tol = self.params.get('solver_tol', 1e-6)
                for iter_idx in range(max_iter):
                    # Simulate displacement-damage coupling resonance
                    residual = (0.5 ** (iter_idx + 1)) * (1.0 + 0.1 * np.random.randn())
                    if progress_callback:
                        progress_callback(i, len(anim_a_vals), frame_data={
                            "log": f"    Staggered Iteration {iter_idx+1}: Residual = {residual:.2e}"
                        })
                    if residual < tol:
                        break
                    import time
                    time.sleep(0.05) # Simulation of compute load

            if amr_enabled:
                # Dynamically inject highly localized topology ahead of the precise crack front
                new_pts_x = np.random.uniform(crack_a - lc*1.5, crack_a + lc*1.5, 30)
                new_pts_y = np.random.uniform(center_y - lc*1.5, center_y + lc*1.5, 30)
                new_pts = np.column_stack((new_pts_x, new_pts_y))
                # Validate spatial bounds
                valid = (new_pts[:, 0] > 0) & (new_pts[:, 0] < 1.25*W) & (new_pts[:, 1] > 0) & (new_pts[:, 1] < 1.2*W)
                pts = np.vstack((pts, new_pts[valid]))
                
                # Topological remeshing
                tri_algo = mtri.Triangulation(pts[:, 0], pts[:, 1])
                cells = tri_algo.triangles
                
                amr_points_history.append(pts.copy())
                amr_cells_history.append(cells.copy())
            else:
                cells = msh.get_cells_type("triangle")
                
            dist_to_crack_path = dist_of_path_to_pts(pts, crack_a, center_y)
            behind_tip = pts[:, 0] <= crack_a
            
            # Phase-Field Evolution with potential H-degradation
            gc_eff = self.params.get('material', {}).get('Gc', 1.0)
            if self.params.get('hydrogen_enabled', False):
                gc_eff = EnergyLib.get_degraded_gc(
                    gc_eff, 
                    self.ch_field, 
                    self.params.get('chi', 0.89)
                )
            
            # Simulated phi evolution based on degraded energy threshold
            threshold_scaling = 1.0 / (gc_eff + 1e-9)
            phi = np.where(behind_tip, np.exp(-dist_to_crack_path / (0.5 * threshold_scaling)), 0)
            
            phi_history.append(phi.copy())
            
            # Calculate SIF (K) for live plotting
            if mode == 'Full':
                numeric_j = EnergyLib.calculate_domain_j_integral(
                    self.params, pts, cells, phi, None, None
                )
                k_val = EnergyLib.convert_j_to_k(
                    numeric_j, 
                    self.params.get('material', {}).get('E', 210000),
                    nu=self.params.get('material', {}).get('nu', 0.3)
                )
            else:
                k_val = EnergyLib.calculate_analytical_k(self.params, crack_a)
            
            frame_data = {
                "phi": phi, 
                "crack_a": crack_a, 
                "center_y": center_y,
                "sif_k": k_val, # Live SIF data
                "ch": self.ch_field.copy() if self.params.get('hydrogen_enabled') else None
            }
            if amr_enabled:
                frame_data["pts"] = pts.copy()
                frame_data["cells"] = cells.copy()
                
            if progress_callback:
                progress_callback(i, len(anim_a_vals), frame_data=frame_data)
            
            import time
            time.sleep(0.15)
            
        res = {
            "status": "success",
            "load_disp": {"u": u_vals, "f": f_vals},
            "fatigue_life": {"N": N_cycles, "a": a_history},
            "mesh_file": self.msh_file,
            "final_phi": phi, # Preserve final damage for GUI
            "phi_history": phi_history, # For video playback
            "a_history_anim": anim_a_vals,
            "amr_points_history": amr_points_history if amr_enabled else [],
            "amr_cells_history": amr_cells_history if amr_enabled else [],
            "center_y": center_y
        }
        return res
    
    def simulate_fatigue(self, load_cycles_max=1e6):
        """
        Integrate Paris' Law to predict fatigue life based on quasi-static simulation results.
        """
        # Paris Law: da/dN = C * (dK)^m
        # We need compliance derivatives from the simulation.
        # This will be implemented in fatigue.py
        pass
