from rest_framework import serializers
from core.models import ComparisonResult, Report


class ComparisonResultSerializer(serializers.ModelSerializer):
    roll_1_number = serializers.CharField(source='roll_1.roll_number', read_only=True)
    roll_2_number = serializers.CharField(source='roll_2.roll_number', read_only=True)

    class Meta:
        model = ComparisonResult
        fields = [
            'id', 'batch',
            'roll_1', 'roll_1_number',
            'roll_2', 'roll_2_number',
            'delta_e_76', 'delta_e_00',
            'created_at',
        ]


class ComparisonRequestSerializer(serializers.Serializer):
    batch_id = serializers.UUIDField()
    method = serializers.ChoiceField(
        choices=['CIE76', 'CIEDE2000'],
        default='CIEDE2000'
    )


class ReportSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(
        source='generated_by.username', read_only=True, default=None
    )
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'id', 'batch', 'generated_by', 'generated_by_name',
            'status', 'verification_notes', 'pdf_url',
            'created_at', 'verified_at',
        ]
        read_only_fields = ['id', 'generated_by', 'created_at', 'verified_at']

    def get_pdf_url(self, obj):
        if obj.pdf_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf_file.url)
            return obj.pdf_file.url
        return None


class ReportVerifySerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=['verified', 'sent_to_customer'],
        help_text="New status for the report"
    )
    verification_notes = serializers.CharField(
        required=False, default='',
        help_text="QC manager verification notes"
    )
