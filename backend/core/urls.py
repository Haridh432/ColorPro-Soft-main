from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.views.batches import BatchViewSet
from core.views.rolls import RollViewSet, bulk_create_rolls
from core.views.scans import ScanViewSet, create_scan, device_scan
from core.views.comparison import (
    run_comparison, get_comparison_results,
    run_gate, run_clustering, get_shade_groups,
    run_advanced_clustering
)
from core.views.reports import (
    generate_batch_report, get_report,
    download_report_pdf, verify_batch_report, list_reports,
)
from core.views.device import (
    device_roll_queue, device_hold_roll,
    device_ping, get_device_status, simulate_batch_scans
)

router = DefaultRouter()
router.register(r'batches', BatchViewSet, basename='batch')
router.register(r'rolls', RollViewSet, basename='roll')
router.register(r'scans', ScanViewSet, basename='scan')


@api_view(['GET'])
def me(request):
    """Get current authenticated user info."""
    if request.user.is_authenticated:
        return Response({
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'is_staff': request.user.is_staff,
        })
    return Response({'detail': 'Not authenticated'}, status=401)


urlpatterns = [
    # Custom endpoints
    path('rolls/bulk/', bulk_create_rolls, name='roll-bulk-create'),
    path('scans/upload/', create_scan, name='scan-create'),
    path('scans/device/', device_scan, name='scan-device'),

    # Comparison & quality gate
    path('compare/', run_comparison, name='compare-run'),
    path('compare/<uuid:batch_id>/', get_comparison_results, name='compare-results'),
    path('compare/<uuid:batch_id>/gate/', run_gate, name='compare-gate'),
    path('compare/<uuid:batch_id>/cluster/', run_clustering, name='compare-cluster'),
    path('compare/<uuid:batch_id>/cluster/advanced/', run_advanced_clustering, name='compare-cluster-advanced'),
    path('compare/<uuid:batch_id>/groups/', get_shade_groups, name='compare-groups'),

    # Reports
    path('reports/', list_reports, name='report-list'),
    path('reports/generate/<uuid:batch_id>/', generate_batch_report, name='report-generate'),
    path('reports/<uuid:report_id>/', get_report, name='report-detail'),
    path('reports/<uuid:report_id>/pdf/', download_report_pdf, name='report-pdf'),
    path('reports/<uuid:report_id>/verify/', verify_batch_report, name='report-verify'),

    # Device endpoints
    path('device/batch/<uuid:batch_id>/rolls/', device_roll_queue, name='device-roll-queue'),
    path('device/roll/<uuid:roll_id>/hold/', device_hold_roll, name='device-hold-roll'),
    path('device/ping/', device_ping, name='device-ping'),
    path('device/status/', get_device_status, name='device-status'),
    path('device/simulate/<uuid:batch_id>/', simulate_batch_scans, name='device-simulate'),

    # Auth
    path('me/', me, name='me'),

    # Router-based endpoints (MUST be last to prevent catching custom routes like rolls/bulk/)
    path('', include(router.urls)),
]
