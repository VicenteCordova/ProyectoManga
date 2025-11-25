from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/",  auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", views.logout_confirm, name="logout"),  # <-- POST-only
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
]