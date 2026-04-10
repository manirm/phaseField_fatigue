import os
import numpy as np
from src.engine.energy_lib import EnergyLib
from src.engine.lefm_library import LEFMLibrary

def verify_sif_accuracy():
    print("Verifying Numerical SIF (K) vs. LEFM Benchmarks...")
    
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
        results.append((a, k_analytical, k_numerical, error))
        
    print(f"{'Crack a [mm]':<15} | {'Analytical K':<15} | {'Numerical K':<15} | {'Error [%]':<10}")
    print("-" * 65)
    for a, ka, kn, err in results:
        print(f"{a:<15.1f} | {ka:<15.2f} | {kn:<15.2f} | {err:<10.2f}%")
        
    avg_error = np.mean([r[3] for r in results])
    if avg_error < 10.0:
        print(f"\n[PASS] Average error is {avg_error:.2f}%, within acceptable numerical bounds.")
        return True
    else:
        print(f"\n[FAIL] Average error {avg_error:.2f}% is too high.")
        return False

if __name__ == "__main__":
    verify_sif_accuracy()
