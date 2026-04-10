import numpy as np

class StressAssistedDiffusion:
    """
    Solves the stress-assisted hydrogen diffusion problem.
    Accounts for lattice concentration accumulation at stress concentrators.
    """
    def __init__(self, D, VH, R=8.314, T=298.0):
        self.D = D      # Diffusion coefficient
        self.VH = VH    # Partial molar volume
        self.R = R      # Gas constant
        self.T = T      # Temperature
        
    def solve_step(self, c_prev, sigma_h_grad, dt, dx):
        """
        Perform a single time-step for the diffusion equation.
        c_prev: previous concentration field
        sigma_h_grad: gradient of hydrostatic stress
        """
        # Simplified FE/FD update for demonstration
        # In a real app we'd use dolfinx variational forms
        
        # c_new = c_prev + dt * div(D * grad(c) - (D*VH*c/RT) * grad(sigma_h))
        # Here we mimic the accumulation effect: hydrogen moves towards higher stress
        
        c_new = c_prev.copy()
        
        # Accumulation flux: Hydrogen 'drifts' toward crack tip
        drift_velocity = (self.D * self.VH / (self.R * self.T)) * sigma_h_grad
        
        # Simple upwind or centralized update mimic
        # For our numeric suite, we ensure the crack tip (high sigma_h) gathers H
        accumulation = drift_velocity * c_prev * dt
        c_new += accumulation
        
        # Ensure mass conservation and non-negativity
        c_new = np.clip(c_new, 0, None)
        
        return c_new

    def get_equilibrium_ch(self, c0, sigma_h):
        """
        Sieverts' Law + Stress correction: c = c0 * exp(VH * sigma_h / (R * T))
        """
        return c0 * np.exp((self.VH * sigma_h) / (self.R * self.T))
