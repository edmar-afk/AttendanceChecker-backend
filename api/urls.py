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
    
    
]
