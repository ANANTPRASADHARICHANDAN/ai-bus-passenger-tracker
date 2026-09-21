from django.db import models

class BusTelemetry(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    boarding_count = models.IntegerField(default=0)
    deboarding_count = models.IntegerField(default=0)
    passengers_inside = models.IntegerField(default=0)
    available_seats = models.IntegerField(default=0)
    is_bus_full = models.BooleanField(default=False)

    def __str__(self):
        return f"Bus Log: {self.available_seats} seats available at {self.timestamp}"