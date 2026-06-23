from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from core.models import Batch, ComparisonResult
from core.serializers.result import ComparisonResultSerializer, ComparisonRequestSerializer
from core.serializers.roll import RollSerializer
from core.services.comparison_service import compare_batch, run_quality_gate
from core.services.clustering_service import cluster_shade_groups, cluster_shade_groups_advanced


@api_view(['POST'])
def run_comparison(request):
    """
    Run pairwise Delta E comparison for a batch.

    POST /api/compare/
    {"batch_id": "<uuid>", "method": "CIEDE2000"}
    """
    serializer = ComparisonRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    batch_id = serializer.validated_data['batch_id']
    method = serializer.validated_data['method']

    try:
        results = compare_batch(batch_id, method)
        return Response(
            ComparisonResultSerializer(results, many=True).data,
            status=status.HTTP_200_OK
        )
    except Batch.DoesNotExist:
        return Response(
            {'error': f'Batch {batch_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def get_comparison_results(request, batch_id):
    """
    Get existing comparison results for a batch.

    GET /api/compare/<batch_id>/
    """
    results = ComparisonResult.objects.filter(batch_id=batch_id).select_related('roll_1', 'roll_2')

    return Response(ComparisonResultSerializer(results, many=True).data)


@api_view(['POST'])
def run_gate(request, batch_id):
    """
    Run quality gate on a batch (accept/warn/reject).

    POST /api/compare/<batch_id>/gate/
    """
    try:
        result = run_quality_gate(batch_id)
        return Response({
            'batch_id': str(batch_id),
            'centroid': result.get('centroid'),
            'accepted': RollSerializer(result['accepted'], many=True).data,
            'warning': RollSerializer(result['warning'], many=True).data,
            'rejected': RollSerializer(result['rejected'], many=True).data,
            'summary': {
                'accepted': len(result['accepted']),
                'warning': len(result['warning']),
                'rejected': len(result['rejected']),
            }
        })
    except Batch.DoesNotExist:
        return Response(
            {'error': f'Batch {batch_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def run_clustering(request, batch_id):
    """
    Run ML shade grouping on accepted rolls.

    POST /api/compare/<batch_id>/cluster/
    """
    try:
        groups = cluster_shade_groups(batch_id)
        response_data = {}
        for group_num, rolls in groups.items():
            response_data[str(group_num)] = RollSerializer(rolls, many=True).data

        return Response({
            'batch_id': str(batch_id),
            'num_groups': len(groups),
            'groups': response_data,
        })
    except Batch.DoesNotExist:
        return Response(
            {'error': f'Batch {batch_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def get_shade_groups(request, batch_id):
    """
    Get current shade group assignments for a batch.

    GET /api/compare/<batch_id>/groups/
    """
    try:
        batch = Batch.objects.get(id=batch_id)
    except Batch.DoesNotExist:
        return Response(
            {'error': f'Batch {batch_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    rolls = batch.rolls.filter(shade_group__isnull=False).order_by('shade_group')
    groups = {}
    for roll in rolls:
        key = str(roll.shade_group)
        if key not in groups:
            groups[key] = []
        groups[key].append(RollSerializer(roll).data)

    return Response({
        'batch_id': str(batch_id),
        'num_groups': len(groups),
        'groups': groups,
    })

@api_view(['POST'])
def run_advanced_clustering(request, batch_id):
    """
    Run ML shade grouping on accepted rolls with advanced parameters.

    POST /api/compare/<batch_id>/cluster/advanced/
    {"method": "kmeans", "n_clusters": 3, "eps": 0.3}
    """
    method = request.data.get('method', 'auto')
    n_clusters = request.data.get('n_clusters')
    eps = request.data.get('eps', 0.3)
    
    try:
        groups = cluster_shade_groups_advanced(
            batch_id, 
            method=method, 
            n_clusters=int(n_clusters) if n_clusters else None,
            eps=float(eps)
        )
        response_data = {}
        for group_num, rolls in groups.items():
            response_data[str(group_num)] = RollSerializer(rolls, many=True).data

        return Response({
            'batch_id': str(batch_id),
            'num_groups': len(groups),
            'groups': response_data,
        })
    except Batch.DoesNotExist:
        return Response(
            {'error': f'Batch {batch_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )

