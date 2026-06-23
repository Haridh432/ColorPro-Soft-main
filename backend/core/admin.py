from django.contrib import admin
from core.models import Batch, Roll, Scan, ComparisonResult, Report


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'roll_count', 'scanned_count', 'accepted_count', 'rejected_count', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Roll)
class RollAdmin(admin.ModelAdmin):
    list_display = ['roll_number', 'batch', 'status', 'shade_group', 'delta_e', 'is_held', 'created_at']
    list_filter = ['status', 'shade_group', 'is_held', 'batch']
    search_fields = ['roll_number']
    readonly_fields = ['id', 'avg_l', 'avg_a', 'avg_b', 'delta_e', 'created_at']


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = ['roll', 'r', 'g', 'b', 'l_val', 'a_val', 'b_val', 'scanned_at']
    list_filter = ['scanned_at']
    readonly_fields = ['id', 'l_val', 'a_val', 'b_val', 'scanned_at']


@admin.register(ComparisonResult)
class ComparisonResultAdmin(admin.ModelAdmin):
    list_display = ['batch', 'roll_1', 'roll_2', 'delta_e_76', 'delta_e_00', 'created_at']
    list_filter = ['batch', 'created_at']
    readonly_fields = ['id', 'created_at']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['batch', 'status', 'generated_by', 'created_at', 'verified_at']
    list_filter = ['status', 'created_at']
    readonly_fields = ['id', 'created_at', 'verified_at']
