from django.urls import path

from .views import RegisterView, UserProfileView, ChangePasswordView, RefreshKeyView, ActivateKeyView, DecoratedTokenObtainPairView, DecoratedTokenRefreshView, DecoratedTokenBlacklistView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', DecoratedTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', DecoratedTokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('refresh-key/', RefreshKeyView.as_view(), name='refresh-key'),
    path('logout/', DecoratedTokenBlacklistView.as_view(), name='token_blacklist'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('activate-key/', ActivateKeyView.as_view(), name='activate-key'),
]