from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Profile, FingerprintGenerate, UserFace, Attendance, AttendanceRecord, Events



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_superuser']
        extra_kwargs = {
            'username': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'email': {'required': False},
        }


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ['user', 'year_lvl', 'course', 'schoolId', 'status', 'face_id']

    def update(self, instance, validated_data):
        user_data = self.initial_data.get('user')
        new_password = self.initial_data.get('new_password')

        # 🔹 Update user details
        if user_data:
            user = instance.user
            new_username = user_data.get('username')

            if new_username and new_username != user.username:
                if User.objects.filter(username=new_username).exclude(id=user.id).exists():
                    raise serializers.ValidationError({
                        "user": {"username": "This username is already taken."}
                    })
                user.username = new_username

            if 'first_name' in user_data:
                user.first_name = user_data['first_name']

            # 🔹 Update password if provided
            if new_password and len(new_password) >= 6:
                user.set_password(new_password)
            elif new_password:
                raise serializers.ValidationError({
                    "new_password": "Password must be at least 6 characters long."
                })

            user.save()

        # 🔹 Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

        

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
        


class EventsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = ['id', 'event_name', 'description', 'date_started']
        
        
class ProfileUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=False)
    first_name = serializers.CharField(source='user.first_name', required=False)
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = Profile
        fields = ['username', 'first_name', 'year_lvl', 'course', 'password']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        if 'username' in user_data:
            user.username = user_data['username']
        if 'first_name' in user_data:
            user.first_name = user_data['first_name']

        # Update password if provided
        new_password = validated_data.pop('password', None)
        if new_password:
            user.set_password(new_password)

        user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    
    



class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.CharField(source='user.email')

    class Meta:
        model = Profile
        fields = ['username', 'email', 'year_lvl', 'course', 'schoolId', 'status']


class AttendanceRecordFilteredSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(source='user.profile', read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = ['id', 'user', 'time_in', 'time_out', 'timestamp']