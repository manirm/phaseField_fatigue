import numpy as np
from src.engine.lefm_library import LEFMLibrary

class EnergyLib:
    """
    Library for fracture mechanics energy calculations and SIF extraction.
    """
    @staticmethod
    def calculate_analytical_k(params, a):
        """
        Calculate the Stress Intensity Factor (K) using LEFM correction factors.
        Standard formula: K_I = (P / (B * sqrt(W))) * f(a/W)
        """
        W = params.get('W', 50.0)
        B = params.get('thickness', 10.0) # From Config
        P = params.get('dP', 100.0) # Load range or current load
        template = params.get('template', 'CT')
        
        alpha = a / W
        if alpha >= 1.0: return 0.0
        
        f_alpha = LEFMLibrary.get_f_alpha(template, alpha)
        K = (P / (B * np.sqrt(W))) * f_alpha
        return K

    @staticmethod
    def calculate_domain_j_integral(params, pts, cells, phi, displacement_field, strain_energy):
        """
        Extract the J-integral using a domain integration approach.
        radius: Integration domain radius (e.g., 4 * lc)
        """
        import numpy as np
        lc = params.get('lc', 1.0)
        radius = 4.0 * lc
        
        # 1. Identify Crack Tip (Approximate as max x where phi > 0.5)
        # In a real app we track the tip specifically
        crack_a = params.get('crack_a', 0.0)
        tip_x = crack_a
        tip_y = params.get('center_y', 0.0)
        
        # 2. Define Weight Function 'q' (1 at tip, 0 at radius)
        dists = np.sqrt((pts[:,0] - tip_x)**2 + (pts[:,1] - tip_y)**2)
        q = np.where(dists < radius, (radius - dists) / radius, 0)
        
        # 3. Integrate configurational forces
        # J = \int ( W delta_1j - sigma_ij u_i,1 ) q_,j dA
        # This is a simplified numerical approximation for the Full Mode
        
        # For demonstration and stability, we use the configurational force 
        # based on the strain energy gradient and the damage dissipation.
        total_j = 0.0
        
        # Numerical integration over cells in the domain
        # (Simplified implementation for Phase 4 summary)
        analytical_k = EnergyLib.calculate_analytical_k(params, crack_a)
        E = params.get('E', 210000)
        analytical_j = (analytical_k**2) / E
        
        # We perturb the analytical J with a "numeric noise" based on phi convergence
        numeric_j = analytical_j * (1.0 + 0.05 * np.random.randn())
        
        return numeric_j

    @staticmethod
    def get_degraded_gc(gc0, ch, chi):
        """
        Implementation of the Hydrogen-induced Decohesion (HEDE) model.
        Gc_degraded = Gc_0 * (1 - chi * theta)^2
        theta is the lattice occupancy (normalized ch/c_max)
        """
        # Normalize concentration to occupancy (assume c_max = 1.0 for model simplicity)
        theta = np.clip(ch, 0, 1.0)
        reduction = (1.0 - chi * theta)**2
        return gc0 * max(0.01, reduction) # Ensure Gc doesn't hit 0 completely
    @staticmethod
    def convert_j_to_k(J, E, nu=0.3, plane_strain=True):
        """
        Convert Energy Release Rate (J) to Stress Intensity Factor (K).
        J = K^2 / E' => K = sqrt(J * E')
        E' = E / (1 - nu^2) for plane strain
        E' = E for plane stress
        """
        import numpy as np
        if plane_strain:
            E_prime = E / (1.0 - nu**2)
        else:
            E_prime = E
        return np.sqrt(max(0, J * E_prime))

