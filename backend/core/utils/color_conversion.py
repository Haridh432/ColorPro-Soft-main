"""
RGB to CIELAB color space conversion.

Uses the sRGB → XYZ → CIELAB pipeline with D65 illuminant.
All math follows IEC 61966-2-1 (sRGB) and CIE 15:2004 standards.
"""

import math

# D65 illuminant reference white point
D65_XN = 95.047
D65_YN = 100.000
D65_ZN = 108.883


def _linearize_srgb(c: float) -> float:
    """Convert a single sRGB channel (0-1) to linear RGB."""
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _lab_f(t: float) -> float:
    """CIE LAB nonlinear transform function."""
    delta = 6.0 / 29.0
    if t > delta ** 3:
        return t ** (1.0 / 3.0)
    return t / (3.0 * delta * delta) + 4.0 / 29.0


def _inverse_lab_f(t: float) -> float:
    delta = 6.0 / 29.0
    if t > delta:
        return t ** 3.0
    return 3.0 * delta * delta * (t - 4.0 / 29.0)


def _srgb_gamma(c: float) -> float:
    if c <= 0.0031308:
        return c * 12.92
    return 1.055 * (c ** (1.0 / 2.4)) - 0.055


def rgb_to_lab(r: int, g: int, b: int) -> tuple:
    """
    Convert sRGB (0-255) to CIELAB (L*, a*, b*) using D65 illuminant.

    Args:
        r: Red channel (0-255)
        g: Green channel (0-255)
        b: Blue channel (0-255)

    Returns:
        Tuple of (L*, a*, b*) float values.
        L* ranges from 0 (black) to 100 (white).
        a* and b* are unbounded but typically -128 to +127.
    """
    # Normalize to 0-1
    rn = r / 255.0
    gn = g / 255.0
    bn = b / 255.0

    # Inverse gamma (sRGB → linear)
    rl = _linearize_srgb(rn)
    gl = _linearize_srgb(gn)
    bl = _linearize_srgb(bn)

    # Linear RGB → XYZ (sRGB D65 matrix, scaled to 0-100)
    x = (0.4124564 * rl + 0.3575761 * gl + 0.1804375 * bl) * 100.0
    y = (0.2126729 * rl + 0.7151522 * gl + 0.0721750 * bl) * 100.0
    z = (0.0193339 * rl + 0.1191920 * gl + 0.9503041 * bl) * 100.0

    # XYZ → CIELAB (D65 white point)
    fx = _lab_f(x / D65_XN)
    fy = _lab_f(y / D65_YN)
    fz = _lab_f(z / D65_ZN)

    l_star = 116.0 * fy - 16.0
    a_star = 500.0 * (fx - fy)
    b_star = 200.0 * (fy - fz)

    return (round(l_star, 4), round(a_star, 4), round(b_star, 4))


def lab_to_rgb(l: float, a: float, b: float) -> tuple:
    """
    Convert CIELAB (L*, a*, b*) back to sRGB (0-255) using D65 illuminant.

    Args:
        l: L* value (0-100)
        a: a* value
        b: b* value

    Returns:
        Tuple of (R, G, B) integer values clumped 0-255.
    """
    fy = (l + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0

    x = _inverse_lab_f(fx) * D65_XN / 100.0
    y = _inverse_lab_f(fy) * D65_YN / 100.0
    z = _inverse_lab_f(fz) * D65_ZN / 100.0

    # XYZ → Linear RGB (inverse matrix)
    rl =  3.2404542 * x - 1.5371385 * y - 0.4985314 * z
    gl = -0.9692660 * x + 1.8760108 * y + 0.0415560 * z
    bl =  0.0556434 * x - 0.2040259 * y + 1.0572252 * z

    # Linear RGB → sRGB
    r = round(_srgb_gamma(max(0.0, min(1.0, rl))) * 255)
    g = round(_srgb_gamma(max(0.0, min(1.0, gl))) * 255)
    b_out = round(_srgb_gamma(max(0.0, min(1.0, bl))) * 255)

    return (r, g, b_out)
