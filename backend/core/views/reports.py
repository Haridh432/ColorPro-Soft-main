import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse

from core.models import Report, Batch
from core.serializers.result import ReportSerializer, ReportVerifySerializer
from core.services.report_service import generate_report, verify_report

logger = logging.getLogger(__name__)


@api_view(['POST'])
def generate_batch_report(request, batch_id):
    """
    Generate a PDF report for a batch.

    POST /api/reports/generate/<batch_id>/
    """
    try:
        report = generate_report(batch_id, user=request.user if request.user.is_authenticated else None)
        return Response(
            ReportSerializer(report, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    except Batch.DoesNotExist:
        return Response(
            {'error': f'Batch {batch_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except RuntimeError as e:
        logger.error(f"Report generation failed for batch {batch_id}: {e}")
        return Response(
            {'error': f'PDF generation failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.exception(f"Unexpected error generating report for batch {batch_id}")
        return Response(
            {'error': f'Report generation failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_report(request, report_id):
    """
    Get report metadata.

    GET /api/reports/<report_id>/
    """
    try:
        report = Report.objects.get(id=report_id)
        return Response(ReportSerializer(report, context={'request': request}).data)
    except Report.DoesNotExist:
        return Response(
            {'error': 'Report not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def download_report_pdf(request, report_id):
    """
    Download the PDF file for a report.

    GET /api/reports/<report_id>/pdf/
    """
    try:
        report = Report.objects.get(id=report_id)
        if not report.pdf_file:
            return Response(
                {'error': 'PDF not yet generated'},
                status=status.HTTP_404_NOT_FOUND
            )
        return FileResponse(
            report.pdf_file.open('rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=f"colorpro_{report.batch.name}.pdf"
        )
    except Report.DoesNotExist:
        return Response(
            {'error': 'Report not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['PATCH'])
def verify_batch_report(request, report_id):
    """
    QC manager verifies a report.

    PATCH /api/reports/<report_id>/verify/
    {"status": "verified", "verification_notes": "All rolls within tolerance"}
    """
    serializer = ReportVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        report = verify_report(
            report_id,
            user=request.user if request.user.is_authenticated else None,
            notes=serializer.validated_data.get('verification_notes', ''),
            status=serializer.validated_data['status'],
        )
        return Response(ReportSerializer(report, context={'request': request}).data)
    except Report.DoesNotExist:
        return Response(
            {'error': 'Report not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def list_reports(request):
    """
    List reports, optionally filtered by batch_id.

    GET /api/reports/?batch_id=<uuid>
    """
    batch_id = request.query_params.get('batch_id')
    queryset = Report.objects.all()
    if batch_id:
        queryset = queryset.filter(batch_id=batch_id)
    return Response(ReportSerializer(queryset, many=True, context={'request': request}).data)
