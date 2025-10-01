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
