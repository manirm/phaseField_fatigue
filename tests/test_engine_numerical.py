import numpy as np
import pytest
from src.engine.energy_lib import EnergyLib
from src.engine.lefm_library import LEFMLibrary
from src.engine.diffusion import StressAssistedDiffusion

def test_sif_accuracy():
    """Verify Numerical SIF (K) vs. LEFM Benchmarks."""
    # Specimen Parameters (CT Specimen)
    params = {
        'template': 'CT',
        'W': 50.0,
        'thickness': 10.0,
        'dP': 100.0,
        'E': 210000.0,
        'nu': 0.3,
        'lc': 1.0
    }
    
    crack_lengths = [10.0, 20.0, 30.0] # [mm]
    
    results = []
    for a in crack_lengths:
        # 1. Analytical Benchmark
        alpha = a / params['W']
        f_alpha = LEFMLibrary.get_f_alpha('CT', alpha)
        k_analytical = (params['dP'] / (params['thickness'] * np.sqrt(params['W']))) * f_alpha
        
        # 2. Simulated Numerical Extraction
        params['crack_a'] = a
        numeric_j = EnergyLib.calculate_domain_j_integral(
            params, 
            np.array([[a, 25.0]]), # Dummy point at tip
            None, 
            np.array([1.0]), 
            None, 
            None
        )
        
        k_numerical = EnergyLib.convert_j_to_k(
            numeric_j, 
            params['E'], 
            nu=params['nu'], 
            plane_strain=True
        )
        
        error = abs(k_numerical - k_analytical) / k_analytical * 100
        results.append(error)
        
    avg_error = np.mean(results)
    assert avg_error < 10.0, f"Average error {avg_error:.2f}% is too high."

def test_diffusion_accumulation():
    """Verify Stress-Assisted Hydrogen Accumulation."""
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
    grad_sh = 500.0 / ((25.1 - x)**1.5)
    
    dt = 0.5 # seconds
    dx = 0.25
    
    c_new = engine.solve_step(c_prev, grad_sh, dt, dx)
    
    # Check if concentration increased near the tip (index -1)
    assert c_new[-1] > c_prev[-1], f"No accumulation detected. Tip Concentration: {c_new[-1]:.4f}"
