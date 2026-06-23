"""
Delta E color difference calculations.

Implements CIE76 (simple Euclidean) and CIEDE2000 (perceptual) formulas.
Both accept CIELAB (L*, a*, b*) tuples and return a float ΔE value.
"""

import math


def delta_e_cie76(lab1: tuple, lab2: tuple) -> float:
    """
    CIE76 Delta E — Euclidean distance in CIELAB space.

    Simple but less accurate for perceptual uniformity.
    Equivalent to: sqrt((L1-L2)² + (a1-a2)² + (b1-b2)²)
    """
    dl = lab1[0] - lab2[0]
    da = lab1[1] - lab2[1]
    db = lab1[2] - lab2[2]
    return math.sqrt(dl * dl + da * da + db * db)


def delta_e_ciede2000(lab1: tuple, lab2: tuple, kL=1.0, kC=1.0, kH=1.0) -> float:
    """
    CIEDE2000 Delta E — perceptually uniform color difference.

    Full implementation of the CIE DE2000 formula with:
    - Lightness weighting (SL)
    - Chroma weighting (SC)
    - Hue weighting (SH)
    - Rotation term (RT) for blue region correction

    Args:
        lab1: (L*, a*, b*) of first color
        lab2: (L*, a*, b*) of second color
        kL, kC, kH: Parametric weighting factors (default 1.0 for standard)

    Returns:
        CIEDE2000 ΔE value (float ≥ 0)
    """
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2

    # Step 1: Calculate C'ab and h'ab
    C1 = math.sqrt(a1 * a1 + b1 * b1)
    C2 = math.sqrt(a2 * a2 + b2 * b2)
    C_avg = (C1 + C2) / 2.0

    C_avg_7 = C_avg ** 7
    G = 0.5 * (1.0 - math.sqrt(C_avg_7 / (C_avg_7 + 25.0 ** 7)))

    a1_prime = a1 * (1.0 + G)
    a2_prime = a2 * (1.0 + G)

    C1_prime = math.sqrt(a1_prime * a1_prime + b1 * b1)
    C2_prime = math.sqrt(a2_prime * a2_prime + b2 * b2)

    h1_prime = math.degrees(math.atan2(b1, a1_prime)) % 360.0
    h2_prime = math.degrees(math.atan2(b2, a2_prime)) % 360.0

    # Step 2: Calculate ΔL', ΔC', ΔH'
    dL_prime = L2 - L1
    dC_prime = C2_prime - C1_prime

    if C1_prime * C2_prime == 0.0:
        dh_prime = 0.0
    elif abs(h2_prime - h1_prime) <= 180.0:
        dh_prime = h2_prime - h1_prime
    elif h2_prime - h1_prime > 180.0:
        dh_prime = h2_prime - h1_prime - 360.0
    else:
        dh_prime = h2_prime - h1_prime + 360.0

    dH_prime = 2.0 * math.sqrt(C1_prime * C2_prime) * math.sin(math.radians(dh_prime / 2.0))

    # Step 3: Calculate weighting functions
    L_avg_prime = (L1 + L2) / 2.0
    C_avg_prime = (C1_prime + C2_prime) / 2.0

    if C1_prime * C2_prime == 0.0:
        h_avg_prime = h1_prime + h2_prime
    elif abs(h1_prime - h2_prime) <= 180.0:
        h_avg_prime = (h1_prime + h2_prime) / 2.0
    elif h1_prime + h2_prime < 360.0:
        h_avg_prime = (h1_prime + h2_prime + 360.0) / 2.0
    else:
        h_avg_prime = (h1_prime + h2_prime - 360.0) / 2.0

    T = (1.0
         - 0.17 * math.cos(math.radians(h_avg_prime - 30.0))
         + 0.24 * math.cos(math.radians(2.0 * h_avg_prime))
         + 0.32 * math.cos(math.radians(3.0 * h_avg_prime + 6.0))
         - 0.20 * math.cos(math.radians(4.0 * h_avg_prime - 63.0)))

    SL = 1.0 + 0.015 * (L_avg_prime - 50.0) ** 2 / math.sqrt(20.0 + (L_avg_prime - 50.0) ** 2)
    SC = 1.0 + 0.045 * C_avg_prime
    SH = 1.0 + 0.015 * C_avg_prime * T

    C_avg_prime_7 = C_avg_prime ** 7
    RT = (-2.0 * math.sqrt(C_avg_prime_7 / (C_avg_prime_7 + 25.0 ** 7))
          * math.sin(math.radians(60.0 * math.exp(-((h_avg_prime - 275.0) / 25.0) ** 2))))

    # Step 4: Calculate CIEDE2000
    term_L = dL_prime / (kL * SL)
    term_C = dC_prime / (kC * SC)
    term_H = dH_prime / (kH * SH)

    dE2000 = math.sqrt(
        term_L ** 2
        + term_C ** 2
        + term_H ** 2
        + RT * term_C * term_H
    )

    return round(dE2000, 4)
