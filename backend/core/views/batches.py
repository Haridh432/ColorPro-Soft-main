from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import Batch
from core.serializers.batch import BatchSerializer, BatchCreateSerializer
from core.serializers.roll import RollSerializer


class BatchViewSet(viewsets.ModelViewSet):
    """CRUD endpoints for batches."""
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer

    def get_queryset(self):
        from django.db.models import Count, Q
        return Batch.objects.annotate(
            annotated_roll_count=Count('rolls'),
            annotated_accepted_count=Count('rolls', filter=Q(rolls__status='accepted')),
            annotated_warning_count=Count('rolls', filter=Q(rolls__status='warning')),
            annotated_rejected_count=Count('rolls', filter=Q(rolls__status='rejected')),
            annotated_scanned_count=Count('rolls', filter=~Q(rolls__status='pending')),
        ).order_by('-created_at')


    def get_serializer_class(self):
        if self.action == 'create':
            return BatchCreateSerializer
        return BatchSerializer

    def create(self, request, *args, **kwargs):
        serializer = BatchCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        batch = serializer.save()
        
        # Annotate the newly created batch instance to prevent queries when serializing it
        batch.annotated_roll_count = 0
        batch.annotated_accepted_count = 0
        batch.annotated_warning_count = 0
        batch.annotated_rejected_count = 0
        batch.annotated_scanned_count = 0
        
        return Response(
            BatchSerializer(batch).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def rolls(self, request, pk=None):
        """Get all rolls for a batch."""
        batch = self.get_object()
        rolls = batch.rolls.all().prefetch_related('scans')
        return Response(RollSerializer(rolls, many=True).data)


    @action(detail=True, methods=['patch'], url_path='client-shade')
    def set_client_shade(self, request, pk=None):
        """Set the absolute geometric target (Client Master Shade)"""
        batch = self.get_object()
        rgb = request.data.get('rgb')
        lab = request.data.get('lab')
        
        # Clear shade if neither provided
        if not rgb and not lab:
            batch.client_l = batch.client_a = batch.client_b = None
            batch.client_r = batch.client_g = batch.client_b_rgb = None
            batch.save()
            return Response({'status': 'Client shade cleared'})
            
        from core.utils.color_conversion import rgb_to_lab, lab_to_rgb
        if lab:
            l, a, b = lab
            r, g, b_rgb = lab_to_rgb(l, a, b)
        else:
            r, g, b_rgb = rgb
            l, a, b = rgb_to_lab(r, g, b_rgb)
            
        batch.client_l = l
        batch.client_a = a
        batch.client_b = b
        batch.client_r = r
        batch.client_g = g
        batch.client_b_rgb = b_rgb
        batch.save()
        return Response({'status': 'Client master shade updated'})

    @action(detail=True, methods=['patch'], url_path='target-roll')
    def set_target_roll(self, request, pk=None):
        """Set the internal benchmark Target Roll Shade"""
        batch = self.get_object()
        roll_id = request.data.get('roll_id')
        
        if not roll_id:
            batch.target_roll = None
        else:
            try:
                from core.models import Roll
                roll = Roll.objects.get(id=roll_id, batch=batch)
                batch.target_roll = roll
            except Roll.DoesNotExist:
                return Response({'error': 'Roll not found in batch'}, status=status.HTTP_404_NOT_FOUND)
                
        batch.save()
        return Response({'status': 'Target roll updated'})
