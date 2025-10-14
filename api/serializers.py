from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Profile, FingerprintGenerate, UserFace, Attendance, AttendanceRecord


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = '__all__'

class RegisterSerializer(serializers.ModelSerializer):
    # profile fields
    year_lvl = serializers.CharField(write_only=True, required=False)
    course = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'username', 'password', 'year_lvl', 'course']
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'required': True},  # School ID
        }

    def create(self, validated_data):
        year_lvl = validated_data.pop('year_lvl', None)
        course = validated_data.pop('course', None)

        # create user
        user = User.objects.create_user(
            username=validated_data['username'],  # school ID
            first_name=validated_data.get('first_name', ''),
            password=validated_data['password']
        )

        # create profile
        Profile.objects.create(
            user=user,
            year_lvl=year_lvl,
            course=course,
        )

        return user


class FingerprintGenerateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FingerprintGenerate
        fields = ["id", "device_name", "device_id", "created_at"]
        read_only_fields = ["id", "created_at"]


class UserFaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFace
        fields = ['id', 'user', 'name', 'face_image', 'embedding']

    def validate_face_image(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Image size should be less than 5MB")
        return value
    
    
    
class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ['host', 'time_limit']


class AttendanceRecordSerializer(serializers.ModelSerializer):
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = ['id', 'attendance', 'user', 'user_first_name', 'timestamp', 'time_in', 'time_out']