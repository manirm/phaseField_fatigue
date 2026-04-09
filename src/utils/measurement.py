import numpy as np
try:
    from skimage.morphology import skeletonize
except ImportError:
    skeletonize = None

class CrackMeasurer:
    def __init__(self, threshold=0.5):
        """
        threshold: The phase-field value above which material is considered 'cracked' (phi > threshold)
        """
        self.threshold = threshold
        
    def measure_crack_length(self, phi_field, mesh_spacing=0.1):
        """
        Measure crack length from the phase-field variable phi.
        phi_field: 2D numpy array of the phase-field values.
        mesh_spacing: physical size of a pixel in the field.
        """
        if skeletonize is None:
            raise ImportError("scikit-image is required for crack skeletonization.")
            
        # Binary mask of the crack
        mask = (phi_field > self.threshold).astype(np.uint8)
        
        # Skeletonize to get a single-pixel wide crack path
        skeleton = skeletonize(mask)
        
        # Count pixels in the skeleton
        crack_pixels = np.sum(skeleton)
        
        # Approximate length (simplified; for better accuracy, consider pixel connectivity/diagonal distance)
        crack_length = crack_pixels * mesh_spacing
        
        # Correction: phase-field tends to overestimate at the crack tip.
        # The docs mention a length scale (l) dependent correction.
        return crack_length

    @staticmethod
    def calculate_compliance(u_load, P):
        """
        Calculate compliance C = u / P
        u_load: average displacement at the load point
        P: applied force
        """
        if P == 0:
            return 0
        return u_load / P
