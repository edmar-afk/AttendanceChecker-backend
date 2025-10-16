from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status, generics
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Profile, FingerprintGenerate, UserFace, Attendance, AttendanceRecord, Events
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework import permissions
from django.contrib.auth import get_user_model
User = get_user_model()
from .serializers import AttendanceRecordFilteredSerializer, ProfileUpdateSerializer, EventsSerializer, AttendanceRecordSerializer, AttendanceSerializer, RegisterSerializer, FingerprintGenerateSerializer, UserFaceSerializer, ProfileSerializer
from django.core.files.storage import default_storage
from .utils import extract_face_embedding
from django.core.files.storage import default_storage
import numpy as np
import uuid
from openpyxl import Workbook
from django.http import HttpResponse
# Assuming UserFace, User, UserFaceSerializer, and extract_face_embedding are defined elsewhere
# from .models import UserFace, User
# from .serializers import UserFaceSerializer
# from .utils import extract_face_embedding
from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import NotFound
from django.http import Http404

# --- FaceRegisterView (No changes needed, but included for completeness) ---

class FaceRegisterView(generics.CreateAPIView):
    serializer_class = UserFaceSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        user_id = self.kwargs.get("user_id")
        uploaded_file = request.FILES.get("face_image")

        if not uploaded_file:
            return Response({"message": "No face image provided"}, status=400)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=404)

        serializer = self.get_serializer(data={
            "face_image": uploaded_file,
            "name": user.id,
            "user": user.id
        })
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Make sure the file is fully saved
        instance.face_image.open()
        instance.face_image.close()

        # Extract embedding
        embedding = extract_face_embedding(instance.face_image.path)
        if embedding is not None:
            instance.embedding = embedding.tobytes()
            instance.save()
        else:
            return Response({"message": "Face could not be detected"}, status=400)

        return Response({"id": instance.id, "name": instance.name})

# --- FaceMatchView (Fix applied here) ---

class FaceMatchView(generics.CreateAPIView):
    serializer_class = UserFaceSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        uploaded_file = request.FILES['face_image']
        temp_path = default_storage.save('temp.jpg', uploaded_file)
        # Assuming extract_face_embedding is defined
        embedding = extract_face_embedding(default_storage.path(temp_path))

        if embedding is None:
            return Response({"message": "No face detected"}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve all user faces
        users = UserFace.objects.all()
        best_score = 0
        best_user = None

        for user in users:
            # 💡 THE FIX: Check if the user has an embedding stored before trying to use it.
            if user.embedding is None:
                continue  # Skip users with missing or failed embeddings

            # Convert the stored bytes back to a NumPy array
            stored_emb = np.frombuffer(user.embedding, dtype=np.float32)

            # Perform similarity calculation (assuming dot product similarity/cosine similarity)
            score = np.dot(embedding, stored_emb) / (np.linalg.norm(embedding) * np.linalg.norm(stored_emb))

            if score > best_score:
                best_score = score
                best_user = user

        # Clean up temporary file (optional, but good practice)
        default_storage.delete(temp_path)

        if best_score > 0.75:
            # Assuming a threshold of 0.75 for a successful match
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




import uuid
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import FingerprintGenerate
from .serializers import FingerprintGenerateSerializer

class FingerprintGenerateCreateView(generics.CreateAPIView):
    serializer_class = FingerprintGenerateSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        user_id = self.kwargs.get("user_id")

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if FingerprintGenerate.objects.filter(user=user).exists():
            return Response(
                {"detail": "Fingerprint already registered for this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ Use the device_id and device_name sent by frontend
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)



class ProfileDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, user_id):
        profile = get_object_or_404(Profile, user__id=user_id)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AttendanceUploadView(generics.CreateAPIView):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user_id = self.kwargs.get("user_id")
        minutes = int(self.request.data.get("time_limit", 0))
        current_time = timezone.now()
        time_limit = current_time + timedelta(minutes=minutes)

        serializer.save(
            host_id=user_id,
            time_limit=time_limit,
            is_active=True,
            is_time_in=True,
            is_time_out=False,
        )

    def create(self, request, *args, **kwargs):
        # Remove the auto-deactivate logic entirely
        mutable_data = request.data.copy()
        mutable_data.pop("host", None)
        mutable_data.pop("time_limit", None)

        serializer = self.get_serializer(data=mutable_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



class AttendanceListView(generics.ListAPIView):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        current_time = timezone.now()

        # Auto-expire logic
        Attendance.objects.filter(
            time_limit__lte=current_time,
            is_active=True
        ).update(is_active=False, is_time_in=False, is_time_out=False)

        return Attendance.objects.all().order_by('-id')







class AttendanceRecordByAttendanceView(generics.ListAPIView):
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        attendance_id = self.kwargs['attendance_id']
        return AttendanceRecord.objects.filter(attendance_id=attendance_id)


class AttendanceDetailView(generics.RetrieveAPIView):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'  # Use 'id' as the URL parameter



class TimeInAttendanceView(APIView):
    def post(self, request, attendance_id, user_id):
        attendance = get_object_or_404(Attendance, id=attendance_id)
        user = get_object_or_404(User, id=user_id)

        record, created = AttendanceRecord.objects.get_or_create(
            attendance=attendance,
            user=user
        )

        if record.time_in:
            return Response({"detail": "User already timed in."}, status=status.HTTP_400_BAD_REQUEST)

        record.time_in = timezone.now().isoformat()
        record.save()

        serializer = AttendanceRecordSerializer(record)
        return Response(serializer.data, status=status.HTTP_200_OK)




class CheckFingerprintView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, user_id, device_id):
        fingerprint_exists = FingerprintGenerate.objects.filter(
            user_id=user_id, device_id=device_id
        ).exists()
        return Response({"valid": fingerprint_exists})



class TimeInAttendanceView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, attendance_id, user_id):
        device_id = request.data.get("device_id")
        if not device_id:
            return Response({"error": "Device ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        fingerprint_exists = FingerprintGenerate.objects.filter(
            user_id=user_id, device_id=device_id
        ).exists()

        if not fingerprint_exists:
            return Response({"error": "Unauthorized device or fingerprint not found."}, status=status.HTTP_403_FORBIDDEN)

        attendance = get_object_or_404(Attendance, id=attendance_id)

        # Format the current date/time (local time)
        current_time = timezone.localtime(timezone.now()).strftime("%I:%M %p")

        record, created = AttendanceRecord.objects.get_or_create(
            attendance=attendance,
            user_id=user_id,
            defaults={"time_in": current_time},
        )

        if not created:
            return Response({"message": "User already timed in."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AttendanceRecordSerializer(record)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class TimeOutAttendanceView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, attendance_id, user_id):
        # Capture and send request data to frontend for debugging
        raw_data = request.data
        print("Raw data:", raw_data)

        device_id = raw_data.get("device_id")

        if not device_id:
            return Response({
                "error": "Device ID is required.",
                "debug_raw_data": raw_data,  # 👈 Send raw data to frontend
            }, status=status.HTTP_400_BAD_REQUEST)

        fingerprint_exists = FingerprintGenerate.objects.filter(
            user_id=user_id, device_id=device_id
        ).exists()

        if not fingerprint_exists:
            return Response({
                "error": "Unauthorized device or fingerprint not found.",
                "debug_raw_data": raw_data,  # 👈 Send raw data
            }, status=status.HTTP_403_FORBIDDEN)

        attendance = get_object_or_404(Attendance, id=attendance_id)
        current_time = timezone.localtime(timezone.now()).strftime("%I:%M %p")

        record, created = AttendanceRecord.objects.get_or_create(
            attendance=attendance,
            user_id=user_id,
            defaults={"time_out": current_time},
        )

        if not created:
            record.time_out = current_time
            record.save()
            return Response({
                "message": "Time out updated successfully.",
                "debug_raw_data": raw_data,
            }, status=status.HTTP_200_OK)

        serializer = AttendanceRecordSerializer(record)
        return Response({
            "success": True,
            "data": serializer.data,
            "debug_raw_data": raw_data,  # 👈 Send raw data to frontend
        }, status=status.HTTP_201_CREATED)





class AttendanceRecordListView(generics.ListAPIView):
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        attendance_id = self.kwargs.get('attendance_id')
        try:
            attendance = Attendance.objects.get(id=attendance_id)
        except Attendance.DoesNotExist:
            raise NotFound('Attendance not found.')
        return AttendanceRecord.objects.filter(attendance=attendance)










class UploadTimeInFaceView(generics.CreateAPIView):
    serializer_class = AttendanceRecordSerializer
    permission_classes = [AllowAny]

    def post(self, request, attendance_id, user_id, *args, **kwargs):
        try:
            attendance = Attendance.objects.get(id=attendance_id)
            user = User.objects.get(id=user_id)
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance not found."}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        print("Time-in POST triggered:", attendance_id, user_id)


        record, created = AttendanceRecord.objects.get_or_create(
            attendance=attendance,
            user=user,
            defaults={"time_in": timezone.localtime(timezone.now()).strftime("%I:%M %p")}
        )

        if not created:
            record.time_in = timezone.localtime(timezone.now()).strftime("%I:%M %p")
            record.save()

        serializer = self.get_serializer(record)
        return Response(serializer.data, status=status.HTTP_200_OK)



class UploadTimeOutFaceView(generics.CreateAPIView):
    serializer_class = AttendanceRecordSerializer
    permission_classes = [AllowAny]

    def post(self, request, attendance_id, user_id, *args, **kwargs):
        try:
            attendance = Attendance.objects.get(id=attendance_id)
            user = User.objects.get(id=user_id)
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance not found."}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        print("Time-out POST triggered:", attendance_id, user_id)


        record, created = AttendanceRecord.objects.get_or_create(
            attendance=attendance,
            user=user,
            defaults={"time_out": timezone.localtime(timezone.now()).strftime("%I:%M %p")}
        )

        if not created:
            record.time_out = timezone.localtime(timezone.now()).strftime("%I:%M %p")
            record.save()

        serializer = self.get_serializer(record)
        return Response(serializer.data, status=status.HTTP_200_OK)






class TimeInToggleView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, attendance_id):
        try:
            attendance = Attendance.objects.get(id=attendance_id)
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance not found."}, status=status.HTTP_404_NOT_FOUND)

        # Auto-expire logic (same as list view)
        current_time = timezone.now()
        Attendance.objects.filter(
            time_limit__lte=current_time,
            is_active=True
        ).update(is_active=False, is_time_in=False, is_time_out=False)

        time_limit_minutes = request.data.get("time_limit_minutes")
        if not time_limit_minutes:
            return Response({"error": "time_limit_minutes is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            time_limit_minutes = int(time_limit_minutes)
        except ValueError:
            return Response({"error": "time_limit_minutes must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        # Set new active attendance
        attendance.is_active = True
        attendance.is_time_in = True
        attendance.is_time_out = False
        attendance.time_limit = current_time + timedelta(minutes=time_limit_minutes)
        attendance.save()

        serializer = AttendanceSerializer(attendance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TimeOutToggleView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, attendance_id):
        try:
            attendance = Attendance.objects.get(id=attendance_id)
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance not found."}, status=status.HTTP_404_NOT_FOUND)

        current_time = timezone.now()

        # Auto-expire logic
        Attendance.objects.filter(
            time_limit__lte=current_time,
            is_active=True
        ).update(is_active=False, is_time_in=False, is_time_out=False)

        # Get time limit from request
        time_limit_minutes = request.data.get("time_limit_minutes")
        if not time_limit_minutes:
            return Response({"error": "time_limit_minutes is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            time_limit_minutes = int(time_limit_minutes)
        except ValueError:
            return Response({"error": "time_limit_minutes must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Set new time limit and update status
        attendance.is_time_out = True
        attendance.is_time_in = False
        attendance.is_active = False
        attendance.time_limit = current_time + timedelta(minutes=time_limit_minutes)
        attendance.save()

        serializer = AttendanceSerializer(attendance)
        return Response(serializer.data, status=status.HTTP_200_OK)




class AttendanceStatusView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, attendance_id):
        try:
            attendance = Attendance.objects.get(id=attendance_id)
            data = {
                "is_time_in": attendance.is_time_in,
                "is_time_out": attendance.is_time_out
            }
            return Response(data, status=status.HTTP_200_OK)
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance not found"}, status=status.HTTP_404_NOT_FOUND)



class TimeInExpireView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, attendance_id):
        try:
            attendance = Attendance.objects.get(id=attendance_id)
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance not found."}, status=status.HTTP_404_NOT_FOUND)

        attendance.is_time_in = False
        attendance.is_time_out = False
        attendance.save()

        return Response({"message": "Time expired. Both is_time_in and is_time_out set to false."}, status=status.HTTP_200_OK)




class ExportAttendanceExcelView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, attendance_id):
        try:
            attendance = Attendance.objects.get(id=attendance_id)
        except Attendance.DoesNotExist:
            return HttpResponse("Attendance not found.", status=404)

        records = AttendanceRecord.objects.filter(attendance=attendance).select_related('user')

        wb = Workbook()
        ws = wb.active
        ws.title = "Attendance Records"

        ws.append(["School ID", "First Name", "Course", "Year Level", "Time In", "Time Out"])

        for record in records:
            profile = Profile.objects.filter(user=record.user).first()

            time_in = record.time_in if record.time_in else None
            time_out = record.time_out if record.time_out else None

           

            ws.append([
                record.user.username,
                record.user.first_name,
                profile.course if profile and profile.course else "N/A",
                profile.year_lvl if profile and profile.year_lvl else "N/A",
                time_in or "25",
                time_out or "25",
               
            ])

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f"{attendance.event_name}_attendance.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response


class ProfileDetailUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    lookup_url_kwarg = 'user_id'
    permission_classes = [AllowAny]

    def get_object(self):
        user_id = self.kwargs.get(self.lookup_url_kwarg)
        print("🔍 [DEBUG] Getting profile for user_id:", user_id)
        try:
            profile = Profile.objects.get(user__id=user_id)
            print("✅ [DEBUG] Found profile:", profile)
            return profile
        except Profile.DoesNotExist:
            print("❌ [DEBUG] Profile not found for user_id:", user_id)
            raise Http404

    def update(self, request, *args, **kwargs):
        print("🟢 [DEBUG] Update method triggered")
        print("📦 [DEBUG] Request method:", request.method)
        print("📥 [DEBUG] Request data:", request.data)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            print("❌ [DEBUG] Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)
        print("📤 [DEBUG] Update response data:", serializer.data)
        return Response(serializer.data)




class EventListCreateView(generics.ListCreateAPIView):
    queryset = Events.objects.all().order_by('date_started')
    serializer_class = EventsSerializer
    permission_classes = [AllowAny]
    
class EventDetailView(generics.RetrieveUpdateAPIView):
    queryset = Events.objects.all()
    serializer_class = EventsSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'
    

class DeleteEventView(APIView):
    permission_classes = [AllowAny]
    
    def delete(self, request, eventId):
        try:
            event = Events.objects.get(id=eventId)
            event.delete()
            return Response({"message": "Event deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Events.DoesNotExist:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
        

class StudentsListView(generics.ListAPIView):
    queryset = Profile.objects.select_related('user').filter(user__is_superuser=False)
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]

    
class StudentUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileUpdateSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user_id = self.kwargs['id']
        return Profile.objects.get(user__id=user_id)
    
    
    
class AttendanceFilteredByProfileView(generics.ListAPIView):
    serializer_class = AttendanceRecordFilteredSerializer
    permission_classes = [AllowAny]
     
    def get_queryset(self):
        attendance_id = self.kwargs.get('attendance_id')
        year_lvl = self.request.query_params.get('year_lvl')
        course = self.request.query_params.get('course')

        queryset = AttendanceRecord.objects.filter(attendance_id=attendance_id)

        if year_lvl:
            queryset = queryset.filter(user__profile__year_lvl=year_lvl)
        if course:
            queryset = queryset.filter(user__profile__course=course)

        return queryset

    def list(self, request, *args, **kwargs):
        attendance_id = kwargs.get('attendance_id')
        try:
            Attendance.objects.get(id=attendance_id)
        except Attendance.DoesNotExist:
            return Response({"detail": "Attendance not found."}, status=status.HTTP_404_NOT_FOUND)

        return super().list(request, *args, **kwargs)