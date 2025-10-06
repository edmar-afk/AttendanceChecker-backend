from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
# ssd
urlpatterns = [
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
     
    path('register/', views.RegisterView.as_view(), name='register'),
    path("fingerprints/<int:user_id>/", views.FingerprintGenerateCreateView.as_view(), name="fingerprint-create"),
    
    path("upload-face/", views.FaceImageUploadView.as_view(), name="upload-face"),
    path("recognize-face/", views.FaceRecognitionView.as_view(), name="recognize-face"),
]
