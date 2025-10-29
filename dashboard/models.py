from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model with created timestamp."""

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ('-created_at',)


class SensorReading(TimeStampedModel):
    source = models.CharField(max_length=128)
    payload = models.JSONField()

    def __str__(self):
        return f"{self.source} @ {self.created_at:%Y-%m-%d %H:%M:%S}"


class FinancialMetric(TimeStampedModel):
    symbol = models.CharField(max_length=32)
    payload = models.JSONField()

    def __str__(self):
        return f"{self.symbol} @ {self.created_at:%Y-%m-%d %H:%M:%S}"


class TrafficUpdate(TimeStampedModel):
    region = models.CharField(max_length=128)
    payload = models.JSONField()

    def __str__(self):
        return f"{self.region} @ {self.created_at:%Y-%m-%d %H:%M:%S}"


class WeatherSnapshot(TimeStampedModel):
    location = models.CharField(max_length=128)
    payload = models.JSONField()

    def __str__(self):
        return f"{self.location} @ {self.created_at:%Y-%m-%d %H:%M:%S}"
