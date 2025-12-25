from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("police", "Police"),
        ("hospital", "Hospital"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class UserLocation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

class Alert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.TextField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert #{self.id} - {self.address}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    address = models.TextField(blank=True)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    
    public_alert = models.ForeignKey(
        "PolicePublicAlert",
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class PoliceStation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    station_name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.station_name


class Hospital(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    hospital_name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.hospital_name

class AlertAssignment(models.Model):
    STATUS_CHOICES = [
        ("assigned", "Assigned"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
    ]

    alert = models.ForeignKey(Alert, on_delete=models.CASCADE)
    police = models.ForeignKey(
        PoliceStation, on_delete=models.SET_NULL, null=True, blank=True
    )
    hospital = models.ForeignKey(
        Hospital, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="assigned"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assignment #{self.id} - {self.status}"

class PolicePublicAlert(models.Model):
    police = models.ForeignKey(PoliceStation, on_delete=models.CASCADE)
    message = models.TextField()
    address = models.TextField()
    photo = models.ImageField(upload_to="missing_persons/", null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Police Alert - {self.address}"
