from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status, generics
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Profile, FingerprintGenerate, FaceImage
from rest_framework.generics import DestroyAPIView
from django.contrib.auth.models import User
from rest_framework import permissions
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, FingerprintGenerateSerializer, FaceImageSerializer
from django.core.files.storage import default_storage
import face_recognition


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
        ip = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "unknown")

        device_id = request.data.get("device_id") or f"{ip}-{user_agent}"

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)

        if FingerprintGenerate.objects.filter(user=user).exists():
            return Response({"detail": "Fingerprint already registered."}, status=400)

        if FingerprintGenerate.objects.filter(device_id=device_id).exists():
            return Response({"detail": "This device is already tied to another account."}, status=400)

        serializer = self.get_serializer(data={"device_id": device_id, **request.data})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)

        return Response(serializer.data, status=201)
    
    
class FaceImageUploadView(APIView):
    def post(self, request):
        serializer = FaceImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FaceRecognitionView(APIView):
    def post(self, request):
        if "image" not in request.FILES:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_image = request.FILES["image"]
        path = default_storage.save("temp_faces/" + uploaded_image.name, uploaded_image)
        uploaded_face = face_recognition.load_image_file(default_storage.path(path))
        uploaded_encodings = face_recognition.face_encodings(uploaded_face)

        if not uploaded_encodings:
            return Response({"error": "No face detected"}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_encoding = uploaded_encodings[0]

        for face in FaceImage.objects.all():
            stored_image = face_recognition.load_image_file(face.image.path)
            stored_encodings = face_recognition.face_encodings(stored_image)
            if stored_encodings:
                match = face_recognition.compare_faces([stored_encodings[0]], uploaded_encoding)
                if match[0]:
                    return Response({"user_id": face.user.id}, status=status.HTTP_200_OK)

        return Response({"message": "No match found"}, status=status.HTTP_404_NOT_FOUND)