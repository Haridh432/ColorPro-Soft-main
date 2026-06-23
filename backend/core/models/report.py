import uuid
from django.db import models
from django.conf import settings


class Report(models.Model):
    """PDF report record for a batch, with QC verification workflow."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('verified', 'Verified'),
        ('sent_to_customer', 'Sent to Customer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        'core.Batch', on_delete=models.CASCADE, related_name='reports'
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='generated_reports',
        help_text="QC manager who generated this report"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    verification_notes = models.TextField(blank=True, default='', help_text="QC manager notes")
    pdf_file = models.FileField(upload_to='reports/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']

    def __str__(self):
        return f"Report: {self.batch.name} [{self.get_status_display()}]"
