from django.urls import path, include
from .views import register, login, logout, activate, dashboard, forgotPassword, resetPassword_validation, resetPassword

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('', dashboard, name='dashboard'),

    path('activate/<uidb64>/<token>', activate, name='activate'),
    path('forgotPassword/', forgotPassword, name='forgotPassword'),
    path('resetPassword_validation/<uidb64>/<token>', resetPassword_validation, name='resetPassword_validation'),
    path('resetPassword/', resetPassword, name='resetPassword'),
]