import uuid
from django.db import models


class Batch(models.Model):
    """A production batch containing multiple fabric rolls."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Batch identifier or name")
    description = models.TextField(blank=True, help_text="Optional batch details")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Client Master Shade (Mathematical target)
    client_l = models.FloatField(null=True, blank=True, help_text="Target L*")
    client_a = models.FloatField(null=True, blank=True, help_text="Target a*")
    client_b = models.FloatField(null=True, blank=True, help_text="Target b*")
    client_r = models.PositiveIntegerField(null=True, blank=True, help_text="Render Target R")
    client_g = models.PositiveIntegerField(null=True, blank=True, help_text="Render Target G")
    client_b_rgb = models.PositiveIntegerField(null=True, blank=True, help_text="Render Target B")

    # Target Roll Shade (Internal standard)
    target_roll = models.ForeignKey(
        'core.Roll', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='targeted_in_batches', help_text="The internal reference roll"
    )

    class Meta:
        db_table = 'batches'
        ordering = ['-created_at']
        verbose_name_plural = 'batches'

    def __str__(self):
        return f"{self.name} ({self.created_at:%Y-%m-%d})"

    @property
    def roll_count(self):
        if hasattr(self, 'annotated_roll_count'):
            return self.annotated_roll_count
        return self.rolls.count()

    @property
    def accepted_count(self):
        if hasattr(self, 'annotated_accepted_count'):
            return self.annotated_accepted_count
        return self.rolls.filter(status='accepted').count()

    @property
    def warning_count(self):
        if hasattr(self, 'annotated_warning_count'):
            return self.annotated_warning_count
        return self.rolls.filter(status='warning').count()

    @property
    def rejected_count(self):
        if hasattr(self, 'annotated_rejected_count'):
            return self.annotated_rejected_count
        return self.rolls.filter(status='rejected').count()

    @property
    def scanned_count(self):
        if hasattr(self, 'annotated_scanned_count'):
            return self.annotated_scanned_count
        return self.rolls.exclude(status='pending').count()

