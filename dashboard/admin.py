from django.contrib import admin

from . import models


@admin.register(models.SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ('source', 'created_at')
    search_fields = ('source',)
    ordering = ('-created_at',)


@admin.register(models.FinancialMetric)
class FinancialMetricAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'created_at')
    search_fields = ('symbol',)
    ordering = ('-created_at',)


@admin.register(models.TrafficUpdate)
class TrafficUpdateAdmin(admin.ModelAdmin):
    list_display = ('region', 'created_at')
    search_fields = ('region',)
    ordering = ('-created_at',)


@admin.register(models.WeatherSnapshot)
class WeatherSnapshotAdmin(admin.ModelAdmin):
    list_display = ('location', 'created_at')
    search_fields = ('location',)
    ordering = ('-created_at',)
