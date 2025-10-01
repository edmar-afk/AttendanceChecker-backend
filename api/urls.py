from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
# ssd
urlpatterns = [
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path("fingerprint/begin-register/", views.begin_register, name="begin_register"),
    path("fingerprint/finish-register/", views.finish_register, name="finish_register"),
    path("fingerprint/begin-login/", views.begin_login, name="begin_login"),
    path("fingerprint/finish-login/", views.finish_login, name="finish_login"),
   
]
