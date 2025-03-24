from django.urls import path

from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    LogoutView,
)

urlpatterns = [
    # re_path(r'^o/(?P<provider>\S+)/$', CustomProviderAuthView.as_view(), name='provider-auth'),
    path('jwt/create/', CustomTokenObtainPairView.as_view(), name='jwt_create'),
    path('jwt/refresh/', CustomTokenRefreshView.as_view(), name='jwt_refresh'),
    path('jwt/verify/', CustomTokenVerifyView.as_view(), name='jwt_verify'),
    path('logout/', LogoutView.as_view()),
]
