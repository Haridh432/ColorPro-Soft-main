from rest_framework import serializers
from core.models import Batch


class BatchSerializer(serializers.ModelSerializer):
    roll_count = serializers.SerializerMethodField()
    accepted_count = serializers.SerializerMethodField()
    warning_count = serializers.SerializerMethodField()
    rejected_count = serializers.SerializerMethodField()
    scanned_count = serializers.SerializerMethodField()

    def get_roll_count(self, obj): return obj.roll_count
    def get_accepted_count(self, obj): return obj.accepted_count
    def get_warning_count(self, obj): return obj.warning_count
    def get_rejected_count(self, obj): return obj.rejected_count
    def get_scanned_count(self, obj): return obj.scanned_count



    class Meta:
        model = Batch
        fields = [
            'id', 'name', 'description', 'created_at', 'updated_at',
            'roll_count', 'scanned_count', 'accepted_count',
            'warning_count', 'rejected_count',
            'client_l', 'client_a', 'client_b',
            'client_r', 'client_g', 'client_b_rgb',
            'target_roll'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'target_roll']


class BatchCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = ['name', 'description']
