from rest_framework import serializers
from core.models import Roll


class RollSerializer(serializers.ModelSerializer):
    scan_count = serializers.SerializerMethodField()
    avg_rgb = serializers.SerializerMethodField()

    def get_scan_count(self, obj): return obj.scan_count
    def get_avg_rgb(self, obj): return obj.avg_rgb

    class Meta:
        model = Roll
        fields = [
            'id', 'batch', 'roll_number', 'order',
            'avg_l', 'avg_a', 'avg_b',
            'delta_e', 'status', 'shade_group', 'is_held',
            'scan_count', 'avg_rgb',
            'created_at',
        ]
        read_only_fields = [
            'id', 'avg_l', 'avg_a', 'avg_b',
            'delta_e', 'status', 'shade_group',
            'created_at',
        ]


class RollCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roll
        fields = ['batch', 'roll_number', 'order']


class RollBulkCreateSerializer(serializers.Serializer):
    """Create multiple rolls at once for a batch."""
    batch_id = serializers.UUIDField()
    roll_numbers = serializers.ListField(
        child=serializers.CharField(max_length=100),
        help_text="List of roll number strings, e.g., ['R-001', 'R-002']"
    )
