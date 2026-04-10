import numpy as np

class LEFMLibrary:
    """
    Collection of geometric correction factors f(alpha) for Stress Intensity Factor (K) calculation.
    General form: K = (P / (B * sqrt(W))) * f(alpha)
    where alpha = a/W.
    """
    
    @staticmethod
    def get_f_alpha(template_name, alpha):
        """
        Returns the geometric factor f(alpha) for a given specimen template.
        """
        if "Compact Tension" in template_name or "CT" in template_name:
            return LEFMLibrary.f_ct(alpha)
        elif "Single Edge Notch Bending" in template_name or "SENB" in template_name:
            return LEFMLibrary.f_senb(alpha)
        elif "Center-Cracked Tension" in template_name or "CCT" in template_name:
            return LEFMLibrary.f_cct(alpha)
        else:
            # Fallback to a generic flat plate factor or 1.0
            return 1.0

    @staticmethod
    def f_ct(alpha):
        """
        ASTM E399 Formula for Compact Tension (CT) Specimen.
        Valid for 0.45 <= alpha <= 0.55 (strictly), but usable for wider range in fatigue.
        """
        num = (2 + alpha)
        den = (1 - alpha)**1.5
        poly = (0.886 + 4.64*alpha - 13.32*alpha**2 + 14.72*alpha**3 - 5.6*alpha**4)
        return (num / den) * poly

    @staticmethod
    def f_senb(alpha, s_w=4.0):
        """
        ASTM E399 Formula for Single Edge Notch Bending (SENB) Specimen.
        s_w: Support span to width ratio (default is 4.0).
        """
        num = 1.5 * s_w * np.sqrt(alpha)
        den = (1 + 2 * alpha) * (1 - alpha)**1.5
        poly = (1.99 - alpha * (1 - alpha) * (2.15 - 3.93 * alpha + 2.7 * alpha**2))
        return (num / den) * poly

    @staticmethod
    def f_cct(alpha):
        """
        Tada Factor for Center-Cracked Tension (CCT) Specimen.
        K = sigma * sqrt(pi * a) * f_cct_correction
        Converted to f(alpha) format where alpha = 2a/W.
        """
        # alpha = 2a/W
        correction = np.sqrt(1.0 / np.cos(np.pi * alpha / 2.0))
        return np.sqrt(np.pi * alpha / 2.0) * correction
