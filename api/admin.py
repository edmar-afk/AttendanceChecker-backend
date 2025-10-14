from django.contrib import admin
from .models import Profile, UserFace, Attendance, AttendanceRecord
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff')

class UserFaceAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'face_image')  # assuming you have a user FK and face_image

class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'event_name', 'host', 'date_created', 'is_active')

class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'attendance', 'user', 'time_in', 'time_out')

admin.site.register(Profile)
admin.site.register(UserFace, UserFaceAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(AttendanceRecord, AttendanceRecordAdmin)
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)