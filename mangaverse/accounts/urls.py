from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import LoginForm  # <--- Importamos el nuevo formulario
from django.conf import settings             # <--- Importar settings
from django.conf.urls.static import static   # <--- Importar static

app_name = "accounts"

urlpatterns = [
    # Agregamos authentication_form=LoginForm aquí:
    path("login/",  auth_views.LoginView.as_view(
        template_name="accounts/login.html",
        authentication_form=LoginForm 
    ), name="login"),
    
    path("logout/", views.logout_confirm, name="logout"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    path("favoritos/<slug:manga_slug>/", views.add_favorite, name="add_favorite"),
]

# --- BLOQUE MÁGICO PARA SERVIR IMÁGENES EN DESARROLLO ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)