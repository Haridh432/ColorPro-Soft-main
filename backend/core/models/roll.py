import uuid
from django.db import models


class Roll(models.Model):
    """A single fabric roll within a batch."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scanned', 'Scanned'),
        ('accepted', 'Accepted'),
        ('warning', 'Warning'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        'core.Batch', on_delete=models.CASCADE, related_name='rolls',
        help_text="The batch this roll belongs to"
    )
    roll_number = models.CharField(max_length=100, help_text="Roll identifier (e.g., R-001)")
    order = models.PositiveIntegerField(default=0, help_text="Order position in the batch scan queue")

    # Computed average LAB from scans
    avg_l = models.FloatField(null=True, blank=True, help_text="Average L* value")
    avg_a = models.FloatField(null=True, blank=True, help_text="Average a* value")
    avg_b = models.FloatField(null=True, blank=True, help_text="Average b* value")

    # Quality gate
    delta_e = models.FloatField(null=True, blank=True, help_text="ΔE from batch centroid")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    # ML shade grouping
    shade_group = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="ML-assigned shade group number (1, 2, 3...)"
    )

    # ESP32 hold flag
    is_held = models.BooleanField(default=False, help_text="True if operator pressed Hold Roll on ESP32")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rolls'
        ordering = ['order', 'created_at']
        unique_together = ['batch', 'roll_number']

    def __str__(self):
        return f"{self.roll_number} [{self.get_status_display()}]"

    @property
    def scan_count(self):
        if hasattr(self, '_prefetched_objects_cache') and 'scans' in self._prefetched_objects_cache:
            return len(self.scans.all())
        return self.scans.count()

    @property
    def avg_rgb(self):
        """Return the average RGB from the latest confirmed scan."""
        if hasattr(self, '_prefetched_objects_cache') and 'scans' in self._prefetched_objects_cache:
            scans_list = list(self.scans.all())
            latest = scans_list[0] if scans_list else None
        else:
            latest = self.scans.order_by('-scanned_at').first()
        if latest:
            return [latest.r, latest.g, latest.b]
        return None

