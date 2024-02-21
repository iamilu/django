from django.urls import path, include
from .views import register, login, otp, logout, activate, dashboard, forgotPassword, resetPassword_validation, resetPassword, my_orders, edit_profile, change_password, order_detail

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('otp/', otp, name='otp'),
    path('logout/', logout, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('', dashboard, name='dashboard'),

    path('activate/<uidb64>/<token>', activate, name='activate'),
    path('forgotPassword/', forgotPassword, name='forgotPassword'),
    path('resetPassword_validation/<uidb64>/<token>', resetPassword_validation, name='resetPassword_validation'),
    path('resetPassword/', resetPassword, name='resetPassword'),

    path('my_orders/', my_orders, name='my_orders'),
    path('edit_profile/', edit_profile, name='edit_profile'),
    path('change_password/', change_password, name='change_password'),
    path('order_detail/<int:order_number>', order_detail, name='order_detail'),
]