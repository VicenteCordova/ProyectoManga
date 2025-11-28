from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Count

# --- IMPORTANTE: Importamos el modelo Manga para las estadísticas ---
from catalogo.models import Manga
from .forms import RegisterForm, UserUpdateForm, ProfileUpdateForm
from .models import Profile

def register(request):
    """
    Vista de registro de usuarios.
    """
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "¡Cuenta creada con éxito! Bienvenido.")
            return redirect("accounts:profile")
        messages.error(request, "Revisa los campos: hay errores en el formulario.")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})

@login_required
def profile(request):
    """
    Vista del Perfil de Usuario (Dashboard).
    Maneja la edición de datos y muestra estadísticas + biblioteca.
    """
    # 1. Aseguramos que el usuario tenga un perfil creado en la BD
    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user)

    # 2. Procesamiento del Formulario de Edición (POST)
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, '¡Tu perfil ha sido actualizado!')
            return redirect('accounts:profile')
    else:
        # Carga inicial del formulario (GET)
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    # 3. DATOS PARA EL DASHBOARD (Esto es lo que faltaba para que se vea el gráfico)
    
    # A. Mis Favoritos (Sección "Mi Biblioteca")
    favoritos = request.user.profile.favorites.all()
    
    # B. Mis Creaciones (Mangas subidos por mí)
    # Annotate nos permite contar likes y capítulos para el gráfico
    mis_mangas = Manga.objects.filter(owner=request.user).annotate(
        total_likes=Count('favorited_by'),
        total_caps=Count('chapters')
    )
    
    # C. Preparar listas de datos para Chart.js
    # Convertimos los QuerySets en listas simples de Python
    chart_labels = [m.titulo for m in mis_mangas]
    chart_likes = [m.total_likes for m in mis_mangas]
    chart_caps = [m.total_caps for m in mis_mangas]

    # 4. Enviamos todo al template
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'favoritos': favoritos,       # Para la sección "Mi Biblioteca"
        'mis_mangas': mis_mangas,     # Para contar cuántos subiste
        'chart_labels': chart_labels, # Eje X del gráfico
        'chart_likes': chart_likes,   # Barra Roja del gráfico
        'chart_caps': chart_caps,     # Barra Cian del gráfico
    }
    return render(request, "accounts/profile.html", context)

@login_required
@require_POST
def add_favorite(request, manga_slug):
    """
    Vista AJAX para dar like/fav a un manga.
    """
    manga = get_object_or_404(Manga, slug=manga_slug)
    
    # Verificación de seguridad por si el perfil no existe
    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user)

    profile = request.user.profile
    
    if profile.favorites.filter(id=manga.id).exists():
        profile.favorites.remove(manga)
        liked = False
    else:
        profile.favorites.add(manga)
        liked = True
    
    return JsonResponse({'liked': liked, 'total': profile.favorites.count()})

@require_POST
def logout_confirm(request):
    """
    Cierre de sesión seguro.
    """
    logout(request)
    messages.success(request, "Sesión cerrada correctamente. ¡Hasta pronto!")
    return redirect("catalogo:home")