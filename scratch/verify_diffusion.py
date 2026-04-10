import numpy as np
from src.engine.diffusion import StressAssistedDiffusion

def verify_diffusion_accumulation():
    print("Verifying Stress-Assisted Hydrogen Accumulation...")
    
    # Material Constants for High-Strength Steel
    D = 1e-10        # m2/s
    VH = 2.0e-6      # m3/mol (Approximate)
    R = 8.314        # J/(mol*K)
    T = 298.0        # K
    
    engine = StressAssistedDiffusion(D, VH, R, T)
    
    # 1D line of points toward a crack tip at x=25
    x = np.linspace(0, 25, 100)
    c_prev = np.ones_like(x) * 1.0 # Initial uniform concentration 1.0 mol/m3
    
    # High negative gradient (driving atoms to x=25)
    # sigma_h = 1000 / sqrt(25.1 - x)
    # grad_sh = d(sigma_h)/dx
    grad_sh = 500.0 / ((25.1 - x)**1.5)
    
    dt = 0.5 # seconds
    dx = 0.25
    
    c_new = engine.solve_step(c_prev, grad_sh, dt, dx)
    
    # Check if concentration increased near the tip (index -1)
    if c_new[-1] > c_prev[-1]:
        print(f"[PASS] Hydrogen accumulated at tip. Tip Concentration: {c_new[-1]:.4f}")
        return True
    else:
        print(f"[FAIL] No accumulation detected. Tip Concentration: {c_new[-1]:.4f}")
        return False

if __name__ == "__main__":
    verify_diffusion_accumulation()
