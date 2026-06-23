import uuid
from django.db import models


class ComparisonResult(models.Model):
    """Pairwise Delta E comparison between two rolls in a batch."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        'core.Batch', on_delete=models.CASCADE, related_name='comparison_results'
    )
    roll_1 = models.ForeignKey(
        'core.Roll', on_delete=models.CASCADE, related_name='comparisons_as_roll1'
    )
    roll_2 = models.ForeignKey(
        'core.Roll', on_delete=models.CASCADE, related_name='comparisons_as_roll2'
    )
    delta_e_76 = models.FloatField(help_text="CIE76 Delta E value")
    delta_e_00 = models.FloatField(help_text="CIEDE2000 Delta E value")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comparison_results'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.roll_1.roll_number} ↔ {self.roll_2.roll_number}: ΔE00={self.delta_e_00:.3f}"
