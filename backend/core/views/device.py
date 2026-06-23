from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from core.models import Batch, Roll, DeviceStatus
from core.serializers.roll import RollSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def device_roll_queue(request, batch_id):
    """
    Get the roll queue for ESP32 device.
    Returns ordered list of rolls (pending + held) for scanning.

    GET /api/device/batch/<batch_id>/rolls/
    """
    # Track device activity implicitly when it asks for its queue
    DeviceStatus.ping()

    try:
        batch = Batch.objects.get(id=batch_id)
    except Batch.DoesNotExist:
        return Response(
            {'error': f'Batch {batch_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Return all rolls ordered by position, with status info
    rolls = batch.rolls.all().prefetch_related('scans').order_by('order', 'created_at')


    roll_data = []
    for roll in rolls:
        roll_data.append({
            'id': str(roll.id),
            'roll_number': roll.roll_number,
            'order': roll.order,
            'status': roll.status,
            'is_held': roll.is_held,
            'scan_count': roll.scan_count,
        })

    return Response({
        'batch_id': str(batch_id),
        'batch_name': batch.name,
        'total_rolls': len(roll_data),
        'rolls': roll_data,
    })


@api_view(['PATCH'])
@permission_classes([AllowAny])
def device_hold_roll(request, roll_id):
    """
    Mark a roll as held (ESP32 Hold Roll button).

    PATCH /api/device/roll/<roll_id>/hold/
    """
    try:
        roll = Roll.objects.get(id=roll_id)
        roll.is_held = True
        roll.save(update_fields=['is_held'])
        return Response({
            'status': 'ok',
            'roll_id': str(roll.id),
            'roll_number': roll.roll_number,
            'is_held': True,
        })
    except Roll.DoesNotExist:
        return Response(
            {'error': f'Roll {roll_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def device_ping(request):
    """
    Heartbeat ping from ESP32 to track connection status.
    
    POST /api/device/ping/
    """
    obj = DeviceStatus.ping()
    return Response({'status': 'ok', 'last_seen': obj.last_ping})


@api_view(['GET'])
@permission_classes([AllowAny])
def get_device_status(request):
    """
    Check if the ESP32 is currently online.
    
    GET /api/device/status/
    """
    obj, _ = DeviceStatus.objects.get_or_create(id=1)
    return Response({
        'name': obj.name,
        'online': obj.is_online,
        'last_seen': obj.last_ping
    })

import random
from core.models import Scan
from core.services.comparison_service import compute_roll_averages

@api_view(['POST'])
def simulate_batch_scans(request, batch_id):
    """
    Simulate device scans for all pending rolls in a batch.
    
    POST /api/device/simulate/<batch_id>/
    """
    try:
        batch = Batch.objects.get(id=batch_id)
    except Batch.DoesNotExist:
        return Response({'error': 'Batch not found'}, status=status.HTTP_404_NOT_FOUND)
        
    rolls = batch.rolls.filter(status='pending')
    
    if not rolls.exists():
        return Response({'status': 'no pending rolls'})
        
    # Determine base shade
    base_l = batch.client_l if batch.client_l is not None else 50.0
    base_a = batch.client_a if batch.client_a is not None else 0.0
    base_b = batch.client_b if batch.client_b is not None else 0.0
    
    from core.utils.color_conversion import lab_to_rgb
    
    simulated_count = 0
    for roll in rolls:
        # Add realistic jitter (standard deviation ~0.4)
        l_val = base_l + random.gauss(0, 0.4)
        a_val = base_a + random.gauss(0, 0.4)
        b_val = base_b + random.gauss(0, 0.4)
        
        r_val, g_val, b_val_rgb = lab_to_rgb(l_val, a_val, b_val)
        
        Scan.objects.create(
            roll=roll,
            r=r_val, g=g_val, b=b_val_rgb,
            l_val=l_val, a_val=a_val, b_val=b_val,
        )
        compute_roll_averages(roll)
        simulated_count += 1
        
    return Response({
        'status': 'ok',
        'simulated_count': simulated_count
    })
