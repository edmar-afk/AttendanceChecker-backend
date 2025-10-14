from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    year_lvl = models.TextField(blank=True, null=True)
    course = models.TextField(blank=True, null=True)
    schoolId = models.TextField(blank=True, null=True)
    status = models.TextField(default="Pending")
    face_id = models.ImageField(
        upload_to='face_recognition/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png'])]
    )

    # WebAuthn fields
    credential_id = models.TextField(blank=True, null=True)   # base64 urlsafe
    public_key = models.TextField(blank=True, null=True)      # PEM or JWK
    sign_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class FingerprintGenerate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fingerprints")
    device_name = models.CharField(max_length=255, blank=True, null=True)
    device_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.device_name or 'Unknown'}"
        


class UserFace(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='faces')
    name = models.CharField(max_length=100)
    face_image = models.ImageField(
        upload_to='faces/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    embedding = models.BinaryField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    
    
class Attendance(models.Model):
    event_name = models.CharField(max_length=255)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_attendances')
    date_created = models.DateTimeField(auto_now_add=True)
    time_limit = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    is_time_in = models.BooleanField(default=True)
    is_time_out = models.BooleanField(default=False)
    location = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.event_name
    
    
class AttendanceRecord(models.Model):
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='records')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    timestamp = models.DateTimeField(auto_now_add=True)
    time_in = models.TextField(blank=True, null=True)
    time_out = models.TextField(blank=True, null=True)