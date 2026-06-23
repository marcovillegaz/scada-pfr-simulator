"""Function to compute overall yield
"""

from scipy.integrate import quad


def overall_yield_pfr(phi, Ca_0, Ca_f):
    """
    Computes the overall yield of a PFR reactor.

    Parameters:
        phi (function): Function representing the reaction rate fraction φ(Ca).
        Ca_0 (float): Initial concentration of A.
        Ca_f (float): Final concentration of A.

    Returns:
        float: Overall yield (Phi_p).
    """
    # Numerically integrate phi over the range [Ca_f, Ca_0]
    integral, _ = quad(phi, Ca_0, Ca_f)
    return (1 / (Ca_f - Ca_0)) * integral


def overall_yield_mfr(phi, Ca_f):
    """
    Computes the overall yield of a PFR reactor.

    Parameters:
        phi (function): Function representing the reaction rate fraction φ(Ca).
        Ca_f (float): Final concentration of A.

    Returns:
        float: Overall yield (Phi_m).
    """
    return phi(Ca_f)
