from rest_framework import serializers
from core.models import Scan


class ScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scan
        fields = [
            'id', 'roll', 'r', 'g', 'b',
            'l_val', 'a_val', 'b_val',
            'scanned_at',
        ]
        read_only_fields = ['id', 'l_val', 'a_val', 'b_val', 'scanned_at']


class ScanCreateSerializer(serializers.Serializer):
    """Manual scan upload — provide roll_id and RGB or LAB."""
    roll_id = serializers.UUIDField()
    rgb = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=255),
        min_length=3,
        max_length=3,
        required=False,
        help_text="RGB values as [R, G, B]"
    )
    lab = serializers.ListField(
        child=serializers.FloatField(),
        min_length=3,
        max_length=3,
        required=False,
        help_text="LAB values as [L, a, b]"
    )

    def validate(self, data):
        if 'rgb' not in data and 'lab' not in data:
            raise serializers.ValidationError("Must provide either 'rgb' or 'lab' payload.")
        return data


class DeviceScanSerializer(serializers.Serializer):
    """ESP32 device scan format."""
    batch_id = serializers.UUIDField()
    roll_id = serializers.UUIDField()
    rgb = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=255),
        min_length=3,
        max_length=3,
        required=False,
        help_text="RGB values from color sensor as [R, G, B]"
    )
    lab = serializers.ListField(
        child=serializers.FloatField(),
        min_length=3,
        max_length=3,
        required=False,
        help_text="LAB values as [L, a, b]"
    )

    def validate(self, data):
        if 'rgb' not in data and 'lab' not in data:
            raise serializers.ValidationError("Must provide either 'rgb' or 'lab' payload.")
        return data
