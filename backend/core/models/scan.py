import uuid
from django.db import models


class Scan(models.Model):
    """A single color scan reading from a fabric roll."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    roll = models.ForeignKey(
        'core.Roll', on_delete=models.CASCADE, related_name='scans',
        help_text="The roll this scan belongs to"
    )

    # Raw RGB from device
    r = models.PositiveIntegerField(help_text="Red channel (0-255)")
    g = models.PositiveIntegerField(help_text="Green channel (0-255)")
    b = models.PositiveIntegerField(help_text="Blue channel (0-255)")

    # Computed LAB values
    l_val = models.FloatField(help_text="CIELAB L* value")
    a_val = models.FloatField(help_text="CIELAB a* value")
    b_val = models.FloatField(help_text="CIELAB b* value")

    scanned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'scans'
        ordering = ['-scanned_at']

    def __str__(self):
        return f"Scan({self.roll.roll_number}) RGB({self.r},{self.g},{self.b})"
