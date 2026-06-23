"""
Comparison and quality gate service.

Handles pairwise Delta E computation and accept/warn/reject classification.
"""

import numpy as np
from django.conf import settings
from core.models import Batch, Roll, ComparisonResult
from core.utils.delta_e import delta_e_cie76, delta_e_ciede2000


def compute_roll_averages(roll):
    """Update roll shade values, strictly adopting the latest scan instead of mathematically averaging history."""
    latest_scan = roll.scans.order_by('-scanned_at').first()
    if not latest_scan:
        return

    # User explicitly requested no averaging so that re-scans can instantly override typos
    roll.avg_l = round(latest_scan.l_val, 4)
    roll.avg_a = round(latest_scan.a_val, 4)
    roll.avg_b = round(latest_scan.b_val, 4)

    if roll.status == 'pending':
        roll.status = 'scanned'

    roll.save(update_fields=['avg_l', 'avg_a', 'avg_b', 'status'])


def compare_batch(batch_id, method='CIEDE2000'):
    """
    Compute all pairwise Delta E comparisons for a batch.

    Args:
        batch_id: UUID of the batch
        method: 'CIE76' or 'CIEDE2000'

    Returns:
        List of ComparisonResult instances
    """
    import uuid
    batch = Batch.objects.get(id=batch_id)
    rolls = list(batch.rolls.exclude(status='pending').filter(
        avg_l__isnull=False
    ))

    if len(rolls) < 2:
        return []

    # Clear old results
    ComparisonResult.objects.filter(batch=batch).delete()

    comparison_objects = []
    for i in range(len(rolls)):
        for j in range(i + 1, len(rolls)):
            lab1 = (rolls[i].avg_l, rolls[i].avg_a, rolls[i].avg_b)
            lab2 = (rolls[j].avg_l, rolls[j].avg_a, rolls[j].avg_b)

            de76 = delta_e_cie76(lab1, lab2)
            de00 = delta_e_ciede2000(lab1, lab2)

            result = ComparisonResult(
                id=uuid.uuid4(),
                batch=batch,
                roll_1=rolls[i],
                roll_2=rolls[j],
                delta_e_76=de76,
                delta_e_00=de00,
            )
            comparison_objects.append(result)

    if comparison_objects:
        ComparisonResult.objects.bulk_create(comparison_objects)

    return comparison_objects


def run_quality_gate(batch_id):
    """
    Run quality gate on all scanned rolls in a batch.

    Process:
    1. Compute batch centroid (mean LAB of all scanned rolls)
    2. Compute CIEDE2000 from centroid to each roll
    3. Classify: ΔE ≤ 0.6 → accepted, 0.6 < ΔE ≤ 0.8 → warning, > 0.8 → rejected

    Returns:
        Dict with 'accepted', 'warning', 'rejected' roll lists
    """
    batch = Batch.objects.get(id=batch_id)
    rolls = list(batch.rolls.exclude(status='pending').filter(
        avg_l__isnull=False
    ))

    if not rolls:
        return {'accepted': [], 'warning': [], 'rejected': []}

    warn_threshold = settings.DELTA_E_WARN_THRESHOLD
    reject_threshold = settings.DELTA_E_REJECT_THRESHOLD

    # Compute target centroid structure
    if batch.client_l is not None:
        centroid = (batch.client_l, batch.client_a, batch.client_b)
    else:
        # Fallback to computing batch centroid average
        l_vals = [r.avg_l for r in rolls]
        a_vals = [r.avg_a for r in rolls]
        b_vals = [r.avg_b for r in rolls]
        centroid = (np.mean(l_vals), np.mean(a_vals), np.mean(b_vals))

    accepted = []
    warning = []
    rejected = []

    for roll in rolls:
        lab = (roll.avg_l, roll.avg_a, roll.avg_b)
        de = delta_e_ciede2000(lab, centroid)

        roll.delta_e = de

        if de <= warn_threshold:
            roll.status = 'accepted'
            accepted.append(roll)
        elif de <= reject_threshold:
            roll.status = 'warning'
            warning.append(roll)
        else:
            roll.status = 'rejected'
            rejected.append(roll)

    if rolls:
        Roll.objects.bulk_update(rolls, ['delta_e', 'status'])

    return {
        'accepted': accepted,
        'warning': warning,
        'rejected': rejected,
        'centroid': {'l': centroid[0], 'a': centroid[1], 'b': centroid[2]},
    }

