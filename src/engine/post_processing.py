import numpy as np
from skimage.morphology import skeletonize

class CrackTracker:
    """
    Post-processing tools for extracting crack metrics from phase-field data.
    """
    @staticmethod
    def extract_crack_tip(pts, phi, threshold=0.95):
        """
        Find the furthest coordinates of the crack tip where damage exceeds threshold.
        """
        mask = phi > threshold
        if not np.any(mask):
            return None
        
        damaged_pts = pts[mask]
        
        # We assume the crack grows in a dominant direction (e.g. +X or +Y)
        # Find the point with maximum coordinate in the direction of growth
        # For CT/CCT growth is in X. For SENB growth is in Y.
        
        # Let's find the centroid of the "tip region" (top 5% of damaged points)
        # in the growth direction.
        
        # Strategy: find the point furthest from the notch root.
        root_x = np.min(pts[:, 0])
        root_y = np.mean(pts[:, 1]) # Rough approximation
        
        dists = np.sqrt((damaged_pts[:, 0] - root_x)**2 + (damaged_pts[:, 1] - root_y)**2)
        tip_idx = np.argmax(dists)
        return damaged_pts[tip_idx]

    @staticmethod
    def calculate_crack_length(pts, phi, a0, template="CT"):
        """
        Calculate the crack length 'a' based on the spatial damage field.
        """
        tip = CrackTracker.extract_crack_tip(pts, phi)
        if tip is None:
            return a0
        
        if "SENB" in template:
            # Vertical growth
            return tip[1]
        else:
            # Horizontal growth (CT/CCT)
            # tip[0] is the absolute X-coordinate. 
            # In our CCT it's centered, in CT it starts at 0.
            return tip[0]
