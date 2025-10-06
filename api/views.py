from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status, generics
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Profile, FingerprintGenerate, UserFace
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import DestroyAPIView
from django.contrib.auth.models import User
from rest_framework import viewsets, permissions
from rest_framework.generics import ListAPIView
from rest_framework import status as drf_status
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer,FingerprintGenerateSerializer
User = get_user_model()
from .serializers import RegisterSerializer, FingerprintGenerateSerializer, UserFaceSerializer
from django.core.files.storage import default_storage
from .utils import extract_face_embedding
from django.core.files.storage import default_storage
import numpy as np


class FaceRegisterView(generics.CreateAPIView):
    serializer_class = UserFaceSerializer

    def create(self, request, *args, **kwargs):
        user_id = self.kwargs.get("user_id")
        uploaded_file = request.FILES.get("face_image")

        if not uploaded_file:
            return Response({"message": "No face image provided"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data={"face_image": uploaded_file, "name": f"User {user_id}"})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        embedding = extract_face_embedding(instance.face_image.path)
        if embedding is not None:
            instance.embedding = embedding.tobytes()
            instance.save()

        return Response({"id": instance.id, "name": instance.name})

class FaceMatchView(generics.CreateAPIView):
    serializer_class = UserFaceSerializer

    def create(self, request, *args, **kwargs):
        uploaded_file = request.FILES['face_image']
        temp_path = default_storage.save('temp.jpg', uploaded_file)
        embedding = extract_face_embedding(default_storage.path(temp_path))

        if embedding is None:
            return Response({"message": "No face detected"}, status=status.HTTP_400_BAD_REQUEST)

        users = UserFace.objects.all()
        best_score = 0
        best_user = None

        for user in users:
            stored_emb = np.frombuffer(user.embedding, dtype=np.float32)
            score = np.dot(embedding, stored_emb) / (np.linalg.norm(embedding) * np.linalg.norm(stored_emb))
            if score > best_score:
                best_score = score
                best_user = user

        if best_score > 0.75:
            return Response({
                "match": True,
                "user_id": best_user.id,
                "name": best_user.name,
                "score": float(best_score)
            })

        return Response({"match": False, "message": "No match found"})



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


class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User registered successfully!",
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "username": user.username,
                    "profile": {
                        "year_lvl": user.profile.year_lvl,
                        "course": user.profile.course,
                        "status": user.profile.status,
                    }
                }
            }, status=status.HTTP_201_CREATED)
        print(serializer.errors)  # 👈 Add this
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class FingerprintGenerateCreateView(generics.CreateAPIView):
    serializer_class = FingerprintGenerateSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        user_id = self.kwargs.get("user_id")
        device_id = request.data.get("device_id")

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if this user already has a fingerprint registered
        if FingerprintGenerate.objects.filter(user=user).exists():
            return Response(
                {"detail": "Fingerprint already registered for this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Optionally enforce 1 device = 1 account rule
        if FingerprintGenerate.objects.filter(device_id=device_id).exists():
            return Response(
                {"detail": "This device is already tied to another account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)