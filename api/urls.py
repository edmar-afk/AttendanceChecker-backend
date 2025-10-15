from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
# ssd
urlpatterns = [
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
     
    path('register/', views.RegisterView.as_view(), name='register'),
    path("fingerprints/<int:user_id>/", views.FingerprintGenerateCreateView.as_view(), name="fingerprint-create"),
    
    path('register-face/<int:user_id>/', views.FaceRegisterView.as_view(), name='register-face'),
    path('match-face/', views.FaceMatchView.as_view(), name='match-face'),
    
    path('profile/<int:user_id>/', views.ProfileDetailView.as_view(), name='profile-detail'),
    
    path('attendance/upload/<int:user_id>/', views.AttendanceUploadView.as_view(), name='attendance-upload'),
    path('attendances/', views.AttendanceListView.as_view(), name='attendance-list'),
    

    path('attendance-records/<int:attendance_id>/', views.AttendanceRecordByAttendanceView.as_view(), name='attendance-records-by-attendance'),
    path('attendance-detail/<int:id>/', views.AttendanceDetailView.as_view(), name='attendance-detail'),

    path('attendance/time-in/<int:attendance_id>/<int:user_id>/', views.TimeInAttendanceView.as_view(), name='time-in-attendance'),
    
    
    path('fingerprints/check/<int:user_id>/<str:device_id>/', views.CheckFingerprintView.as_view(), name='check-fingerprint'),
    
    path('attendance/timein/<int:attendance_id>/<int:user_id>/', views.TimeInAttendanceView.as_view(), name='time-in-attendance'),
    path('attendance/timeout/<int:attendance_id>/<int:user_id>/', views.TimeOutAttendanceView.as_view(), name='time-in-attendance'),
    
    
    path('attendance/<int:attendance_id>/records/', views.AttendanceRecordListView.as_view(), name='attendance-records'),
    
    path('facerecognition-timein/<int:attendance_id>/<int:user_id>/', views.UploadTimeInFaceView.as_view(), name='facerecognition-timein'),
    path('facerecognition-timeout/<int:attendance_id>/<int:user_id>/', views.UploadTimeOutFaceView.as_view(), name='facerecognition-timein'),

    path('attendance/status/<int:attendance_id>/', views.AttendanceStatusView.as_view(), name='attendance-status'),

    path('attendance/timein-toggle/<int:attendance_id>/', views.TimeInToggleView.as_view(), name='attendance_time_in'),
    path('attendance/timeout-toggle/<int:attendance_id>/', views.TimeOutToggleView.as_view(), name='attendance_time_out'),
    path('attendance/timein-expire/<int:attendance_id>/', views.TimeInExpireView.as_view(), name='timein-expire'),
    
    path('export-attendance/<int:attendance_id>/', views.ExportAttendanceExcelView.as_view(), name='export_attendance_excel'),



    path('profileUpdate/<int:user_id>/', views.ProfileDetailUpdateView.as_view(), name='profile-detail-update'),

    path('events/', views.EventListCreateView.as_view(), name='events-list-create'),
    path('edit-events/<int:id>/', views.EventDetailView.as_view(), name='event-detail'),
    path('events/delete/<int:eventId>/', views.DeleteEventView.as_view(), name='delete-event'),
    
    path('students/', views.StudentsListView.as_view(), name='students-list'),
    path('students/manage/<int:id>/', views.StudentUpdateView.as_view(), name='student-manage'),
    
    path('attendance-filter/<int:attendance_id>/records/', views.AttendanceFilteredByProfileView.as_view(), name='attendance-filtered-records'),
]
