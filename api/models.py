from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    year_lvl = models.TextField(blank=True, null=True)
    course = models.TextField(blank=True, null=True)
    status = models.TextField(default="Pending")
   
    def __str__(self):
        return f"{self.user.username}'s Profile"


class FingerprintGenerate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fingerprints")
    device_name = models.CharField(max_length=255, blank=True, null=True)
    device_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.device_name or 'Unknown'}"
    

class FaceImage(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="face_image")
    image = models.ImageField(
        upload_to="faces/",
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png"])]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username