import os

class SimulationConfig:
    """
    Singleton class to manage global simulation settings like 
    2D/3D selection and Quick/Full solver modes.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SimulationConfig, cls).__new__(cls)
            cls._instance._init_defaults()
        return cls._instance
    
    def _init_defaults(self):
        self.mode = "Quick"          # "Quick" or "Full"
        self.dimension = "2D"         # "2D" or "3D"
        self.energy_split = "Amor"    # "Isotropic", "Amor", "Miehe"
        self.thickness = 10.0         # Specimen thickness for 3D (mm)
        self.solver_tol = 1e-6        # Variational solver tolerance
        self.max_iter = 100           # Max iterations for staggered solver
        
        # Environmental Fatigue (Hydrogen)
        self.hydrogen_enabled = False
        self.exposure_mode = "Static Boundary"  # "Static Boundary" or "Dynamic Surface"
        self.c0 = 1.0                           # Surface Concentration (mol/m3)
        self.diff_coeff = 1e-10                 # Diffusion Coefficient (m2/s)
        self.chi = 0.89                         # Hydrogen Sensitivity Factor

    def to_dict(self):
        return {
            "mode": self.mode,
            "dimension": self.dimension,
            "energy_split": self.energy_split,
            "thickness": self.thickness,
            "solver_tol": self.solver_tol,
            "max_iter": self.max_iter,
            "hydrogen_enabled": self.hydrogen_enabled,
            "exposure_mode": self.exposure_mode,
            "c0": self.c0,
            "diff_coeff": self.diff_coeff,
            "chi": self.chi
        }

# Global config instance
config = SimulationConfig()
