import numpy as np

class FatigueIntegrator:
    def __init__(self, c_paris, m_paris, e_modulus):
        self.c_paris = c_paris
        self.m_paris = m_paris
        self.e_modulus = e_modulus
        
    def integrate_paris_law(self, crack_lengths, compliance_values, delta_p, load_ratio=0.1):
        """
        Integrate Paris' Law to compute Cycles N.
        crack_lengths (a): array of crack lengths.
        compliance_values (C): array of corresponding compliances.
        delta_p (dP): load range (P_max - P_min).
        """
        # Calculate dC/da (central difference)
        dc_da = np.gradient(compliance_values, crack_lengths)
        
        # Energy release rate G = 0.5 * P^2 * dC/da
        # Here we use Delta G as an approximation for Delta K
        # dG = 0.5 * (P_max^2 - P_min^2) * dC/da 
        # (This is a simplification; different formulations exist)
        
        # Approximate Delta K from Delta G
        # G = K^2 / E' -> Delta K = sqrt(Delta G * E')
        # dG = 0.5 * (delta_p^2) * dc_da (very simplified)
        
        delta_g = 0.5 * (delta_p**2) * dc_da
        delta_k = np.sqrt(np.maximum(delta_g * self.e_modulus, 0))
        
        # da/dN = C_paris * (delta_k)^m
        # dN/da = 1 / (C_paris * (delta_k)^m)
        
        dn_da = 1.0 / (self.c_paris * (delta_k**self.m_paris))
        
        # Numerical integration for N(a)
        # N = cumulative_sum(dn_da * delta_a)
        da = np.diff(crack_lengths, prepend=crack_lengths[0])
        n_cycles = np.cumsum(dn_da * da)
        
        return n_cycles
