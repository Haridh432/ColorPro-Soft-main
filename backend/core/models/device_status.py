from django.db import models
from django.utils import timezone

class DeviceStatus(models.Model):
    name = models.CharField(max_length=100, default="ESP32 Color Sensor")
    last_ping = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'device_status'

    @classmethod
    def ping(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        obj.last_ping = timezone.now()
        obj.save(update_fields=['last_ping'])
        return obj

    @property
    def is_online(self):
        # Consider online if pinged within the last 30 seconds
        return (timezone.now() - self.last_ping).total_seconds() <= 30
