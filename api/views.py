from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status, generics
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Profile
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import DestroyAPIView
from django.contrib.auth.models import User
from rest_framework import viewsets, permissions
from rest_framework.generics import ListAPIView
from rest_framework import status as drf_status
from django.contrib.auth import get_user_model

User = get_user_model()
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['id'] = user.id
        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "is_staff": self.user.is_staff,
            "is_superuser": self.user.is_superuser,
        })
        return data



class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


from rest_framework.permissions import AllowAny
import base64, os, json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from webauthn.helpers.structs import (
    PublicKeyCredentialCreationOptions,
    PublicKeyCredentialRequestOptions,
    AttestationConveyancePreference,
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    RegistrationCredential,
    AuthenticationCredential,
)
import webauthn
from .models import Profile

RP_ID = "localhost"   # change to your production domain (e.g. "myapp.com")
FRONTEND_ORIGIN = "http://localhost:3000"  # your React site

# -------------------
# Begin Registration
# -------------------
@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def begin_register(request):
    try:
        data = json.loads(request.body)
        email = data.get("email", "guest@example.com")  # fallback if no email

        challenge = os.urandom(32)
        request.session["registration_challenge"] = base64.urlsafe_b64encode(challenge).decode()

        options = PublicKeyCredentialCreationOptions(
            rp={"id": RP_ID, "name": "My Django App"},
            user={
                # use email as ID (must be bytes)
                "id": email.encode("utf-8"),
                "name": email,
                "displayName": email,
            },
            challenge=challenge,
            pub_key_cred_params=[{"type": "public-key", "alg": -7}],  # ES256
            authenticator_selection=AuthenticatorSelectionCriteria(
                user_verification=UserVerificationRequirement.REQUIRED
            ),
            attestation=AttestationConveyancePreference.DIRECT,
        )

        return JsonResponse(options.model_dump(), safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# -------------------
# Finish Registration
# -------------------
@csrf_exempt
def finish_register(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not logged in"}, status=403)

    credential = RegistrationCredential.parse_raw(request.body)
    expected_challenge = base64.urlsafe_b64decode(request.session["registration_challenge"])

    reg = webauthn.verify_registration_response(
        credential=credential,
        expected_challenge=expected_challenge,
        expected_rp_id=RP_ID,
        expected_origin=FRONTEND_ORIGIN,
        require_user_verification=True,
    )

    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.credential_id = base64.urlsafe_b64encode(reg.credential_id).decode()
    profile.public_key = reg.credential_public_key.decode()
    profile.sign_count = reg.sign_count
    profile.save()

    return JsonResponse({"status": "ok"})


# -------------------
# Begin Login
# -------------------
def begin_login(request):
    username = request.GET.get("username")
    try:
        profile = Profile.objects.get(user__username=username)
    except Profile.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    challenge = os.urandom(32)
    request.session["login_challenge"] = base64.urlsafe_b64encode(challenge).decode()

    options = PublicKeyCredentialRequestOptions(
        challenge=challenge,
        rp_id=RP_ID,
        allow_credentials=[{
            "type": "public-key",
            "id": base64.urlsafe_b64decode(profile.credential_id.encode()),
        }],
        user_verification=UserVerificationRequirement.REQUIRED,
    )

    return JsonResponse(options.model_dump())


# -------------------
# Finish Login
# -------------------
@csrf_exempt
def finish_login(request):
    body = json.loads(request.body)
    username = body.get("username")

    try:
        profile = Profile.objects.get(user__username=username)
    except Profile.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    credential = AuthenticationCredential.parse_raw(request.body)
    expected_challenge = base64.urlsafe_b64decode(request.session["login_challenge"])

    auth = webauthn.verify_authentication_response(
        credential=credential,
        expected_challenge=expected_challenge,
        expected_rp_id=RP_ID,
        expected_origin=FRONTEND_ORIGIN,
        credential_public_key=profile.public_key.encode(),
        credential_current_sign_count=profile.sign_count,
        require_user_verification=True,
    )

    # Update sign count
    profile.sign_count = auth.new_sign_count
    profile.save()

    # Log the user in Django session
    auth_login(request, profile.user)

    return JsonResponse({"status": "authenticated"})
