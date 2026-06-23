from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from core.models import Batch, Roll
from core.serializers.roll import RollSerializer, RollCreateSerializer, RollBulkCreateSerializer


class RollViewSet(viewsets.ModelViewSet):
    """CRUD endpoints for rolls."""
    queryset = Roll.objects.prefetch_related('scans')
    serializer_class = RollSerializer
    filterset_fields = ['batch', 'status', 'shade_group', 'is_held']

    def get_serializer_class(self):
        if self.action == 'create':
            return RollCreateSerializer
        return RollSerializer


@api_view(['POST'])
def bulk_create_rolls(request):
    """
    Create multiple rolls for a batch at once.

    POST /api/rolls/bulk/
    {
        "batch_id": "<uuid>",
        "roll_numbers": ["R-001", "R-002", "R-003"]
    }
    """
    serializer = RollBulkCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    batch_id = serializer.validated_data['batch_id']
    roll_numbers = serializer.validated_data['roll_numbers']

    try:
        batch = Batch.objects.get(id=batch_id)
    except Batch.DoesNotExist:
        return Response(
            {'error': f'Batch {batch_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    import uuid
    # Fetch existing rolls of this batch matching target roll numbers
    existing_rolls = {
        r.roll_number: r for r in Roll.objects.filter(batch=batch, roll_number__in=roll_numbers)
    }

    rolls_to_create = []
    for idx, roll_num in enumerate(roll_numbers):
        if roll_num not in existing_rolls:
            new_roll = Roll(
                id=uuid.uuid4(),
                batch=batch,
                roll_number=roll_num,
                order=idx
            )
            rolls_to_create.append(new_roll)

    if rolls_to_create:
        Roll.objects.bulk_create(rolls_to_create)

    # Fetch all rolls with prefetched scans and return them in the requested order
    db_rolls = {
        r.roll_number: r for r in Roll.objects.filter(batch=batch, roll_number__in=roll_numbers).prefetch_related('scans')
    }
    ordered_rolls = [db_rolls[roll_num] for roll_num in roll_numbers if roll_num in db_rolls]

    return Response(
        RollSerializer(ordered_rolls, many=True).data,
        status=status.HTTP_201_CREATED
    )

