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
    # --- NUEVAS RUTAS SOCIALES ---
    # Ver perfil público de otro usuario (ej: /accounts/u/vicente/)
    path("u/<str:username>/", views.public_profile, name="public_profile"),
    
    # Seguir/Dejar de seguir
    path("u/<str:username>/follow/", views.follow_toggle, name="follow_toggle"),
    
    # Mensajería
    path("mensajes/", views.inbox, name="inbox"),
    path("mensajes/<str:username>/", views.chat_detail, name="chat_detail"),
    
    path("favoritos/<slug:manga_slug>/", views.add_favorite, name="add_favorite"),
    path("mensajes/<str:username>/eliminar/", views.delete_chat, name="delete_chat"),
]

# --- BLOQUE MÁGICO PARA SERVIR IMÁGENES EN DESARROLLO ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)