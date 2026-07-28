import numpy as np

from app.core.adversarial_engine import apply_adversarial_protection


def apply_phase_protection(y: np.ndarray, sr: int) -> np.ndarray:
    """Protect audio against voice cloning using adversarial perturbation.

    Delegates to the adversarial engine, which uses PGD to find a small,
    inaudible perturbation that maximally confuses speaker encoder models.

    The function signature is unchanged so the API endpoint (router.py)
    continues to work without modification.
    """
    return apply_adversarial_protection(y, sr)
