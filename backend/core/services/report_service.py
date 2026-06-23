"""
Report generation service.

Generates PDF reports from HTML templates using xhtml2pdf,
and manages the verification workflow.
"""

import logging
from datetime import datetime
from io import BytesIO
from django.conf import settings
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from core.models import Batch, Report

logger = logging.getLogger(__name__)


def generate_report(batch_id, user=None):
    """
    Generate a PDF report for a batch.

    Process:
    1. Gather batch data, roll statuses, shade groups, ΔE values
    2. Render HTML template with context
    3. Convert HTML → PDF via xhtml2pdf
    4. Save PDF to media storage
    5. Create Report record

    Returns:
        Report instance

    Raises:
        Batch.DoesNotExist: If batch not found
        RuntimeError: If PDF generation fails
    """
    batch = Batch.objects.get(id=batch_id)
    rolls = list(batch.rolls.all().prefetch_related('scans').order_by('order', 'roll_number'))
    comparison_results = list(batch.comparison_results.all().select_related('roll_1', 'roll_2'))

    # Group rolls by status (in memory)
    accepted_rolls = [r for r in rolls if r.status == 'accepted']
    warning_rolls = [r for r in rolls if r.status == 'warning']
    rejected_rolls = [r for r in rolls if r.status == 'rejected']

    # Group rolls by shade group
    shade_groups = {}
    for roll in rolls:
        if roll.shade_group is not None:
            group = roll.shade_group
            if group not in shade_groups:
                shade_groups[group] = []
            shade_groups[group].append(roll)

    # Compute stats
    scanned_rolls = [r for r in rolls if r.status != 'pending']
    delta_e_values = [r.delta_e for r in scanned_rolls if r.delta_e is not None]

    stats = {}
    if delta_e_values:
        stats = {
            'min_de': round(min(delta_e_values), 4),
            'max_de': round(max(delta_e_values), 4),
            'mean_de': round(sum(delta_e_values) / len(delta_e_values), 4),
            'pass_rate': round(
                (len(accepted_rolls) + len(warning_rolls)) / max(len(scanned_rolls), 1) * 100, 1
            ),
        }

    # Set annotated counts in memory to avoid database queries in template
    batch.annotated_roll_count = len(rolls)
    batch.annotated_accepted_count = len(accepted_rolls)
    batch.annotated_warning_count = len(warning_rolls)
    batch.annotated_rejected_count = len(rejected_rolls)
    batch.annotated_scanned_count = len(scanned_rolls)


    context = {
        'brand_name': settings.BRAND_NAME,
        'batch': batch,
        'rolls': rolls,
        'accepted_rolls': accepted_rolls,
        'warning_rolls': warning_rolls,
        'rejected_rolls': rejected_rolls,
        'shade_groups': dict(sorted(shade_groups.items())),
        'comparison_results': comparison_results,
        'stats': stats,
        'warn_threshold': settings.DELTA_E_WARN_THRESHOLD,
        'reject_threshold': settings.DELTA_E_REJECT_THRESHOLD,
        'generated_at': datetime.now(),
        'generated_by': user,
    }


    # Render HTML
    html_content = render_to_string('reports/batch_report.html', context)

    # Convert to PDF using xhtml2pdf
    from xhtml2pdf import pisa

    result_file = BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=result_file)

    if pisa_status.err:
        error_msg = f"xhtml2pdf reported {pisa_status.err} error(s) generating PDF for batch '{batch.name}'"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    pdf_bytes = result_file.getvalue()

    if not pdf_bytes or len(pdf_bytes) < 100:
        error_msg = f"PDF generation produced empty/invalid output for batch '{batch.name}'"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Create report record
    filename = f"colorpro_report_{batch.name}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
    report = Report.objects.create(
        batch=batch,
        generated_by=user,
        status='draft',
    )
    report.pdf_file.save(filename, ContentFile(pdf_bytes))

    logger.info(f"Report generated: {filename} ({len(pdf_bytes)} bytes)")
    return report


def verify_report(report_id, user, notes, status='verified'):
    """
    QC manager verifies (approves/rejects) a report.

    Args:
        report_id: UUID of the report
        user: Django User instance
        notes: Verification notes
        status: 'verified' or 'draft' (to reject back to draft)

    Returns:
        Updated Report instance
    """
    report = Report.objects.get(id=report_id)
    report.status = status
    report.verification_notes = notes
    report.verified_at = datetime.now()
    report.save(update_fields=['status', 'verification_notes', 'verified_at'])
    return report
