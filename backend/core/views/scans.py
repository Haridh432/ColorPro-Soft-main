from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.models import Roll, Scan
from core.serializers.scan import ScanSerializer, ScanCreateSerializer, DeviceScanSerializer
from core.utils.color_conversion import rgb_to_lab, lab_to_rgb
from core.services.comparison_service import compute_roll_averages


class ScanViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for scans (creation via dedicated endpoints)."""
    queryset = Scan.objects.all()
    serializer_class = ScanSerializer
    filterset_fields = ['roll']


@api_view(['POST'])
def create_scan(request):
    """
    Upload a manual scan.

    POST /api/scans/
    {"roll_id": "<uuid>", "rgb": [42, 75, 130]}
    """
    serializer = ScanCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    roll_id = serializer.validated_data['roll_id']
    rgb = serializer.validated_data.get('rgb')
    lab = serializer.validated_data.get('lab')

    try:
        roll = Roll.objects.get(id=roll_id)
    except Roll.DoesNotExist:
        return Response(
            {'error': f'Roll {roll_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Convert RGB/LAB based on input
    if lab:
        l_val, a_val, b_val = lab
        r_val, g_val, b_val_rgb = lab_to_rgb(l_val, a_val, b_val)
    else:
        r_val, g_val, b_val_rgb = rgb
        l_val, a_val, b_val = rgb_to_lab(r_val, g_val, b_val_rgb)

    scan = Scan.objects.create(
        roll=roll,
        r=r_val, g=g_val, b=b_val_rgb,
        l_val=l_val, a_val=a_val, b_val=b_val,
    )

    # Update roll averages
    compute_roll_averages(roll)

    return Response(ScanSerializer(scan).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def device_scan(request):
    """
    ESP32 device scan ingest endpoint (no auth required).

    POST /api/scans/device/
    {"batch_id": "<uuid>", "roll_id": "<uuid>", "rgb": [42, 75, 130]}
    """
    serializer = DeviceScanSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    batch_id = serializer.validated_data['batch_id']
    roll_id = serializer.validated_data['roll_id']
    rgb = serializer.validated_data.get('rgb')
    lab = serializer.validated_data.get('lab')

    try:
        roll = Roll.objects.get(id=roll_id, batch_id=batch_id)
    except Roll.DoesNotExist:
        return Response(
            {'error': f'Roll {roll_id} not found in batch {batch_id}'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Convert RGB/LAB based on input
    if lab:
        l_val, a_val, b_val = lab
        r_val, g_val, b_val_rgb = lab_to_rgb(l_val, a_val, b_val)
    else:
        r_val, g_val, b_val_rgb = rgb
        l_val, a_val, b_val = rgb_to_lab(r_val, g_val, b_val_rgb)

    scan = Scan.objects.create(
        roll=roll,
        r=r_val, g=g_val, b=b_val_rgb,
        l_val=l_val, a_val=a_val, b_val=b_val,
    )

    # Update roll averages
    compute_roll_averages(roll)

    return Response({
        'status': 'ok',
        'scan_id': str(scan.id),
        'lab': {'l': l_val, 'a': a_val, 'b': b_val},
        'roll_status': roll.status,
    }, status=status.HTTP_201_CREATED)
