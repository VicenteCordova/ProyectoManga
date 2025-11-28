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
    Vista de registro de nuevos usuarios.
    
    Utiliza el RegisterForm personalizado. Si el registro es exitoso,
    inicia sesión automáticamente y redirige al perfil del usuario.
    En caso de error, muestra mensajes flash informativos.
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
    Vista principal del Perfil de Usuario (Dashboard).
    
    Esta vista cumple múltiples funciones:
    1. Gestión de perfil: Permite editar datos de usuario y perfil (avatar, bio).
    2. Centro de estadísticas: Calcula métricas de las obras subidas por el usuario para Chart.js.
    3. Biblioteca: Muestra la lista de mangas favoritos.
    4. Gestión de obras: Lista los mangas creados por el usuario para edición rápida.
    """
    # 1. Aseguramos que el usuario tenga un perfil creado en la BD
    # Esto previene errores con usuarios antiguos o creados desde admin sin señal
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
        # Carga inicial del formulario (GET) con datos existentes
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    # 3. DATOS PARA EL DASHBOARD (Lógica de Negocio)
    
    # A. Mis Favoritos: Recupera los mangas marcados como favoritos (Biblioteca de lectura)
    favoritos = request.user.profile.favorites.all()
    
    # B. Mis Creaciones: Recupera los mangas donde el usuario es el 'owner'.
    # Usamos .annotate() para agregar campos calculados directamente desde la BD:
    # - total_likes: Cuántos usuarios tienen este manga en favoritos.
    # - total_caps: Cuántos capítulos tiene este manga.
    mis_mangas = Manga.objects.filter(owner=request.user).annotate(
        total_likes=Count('favorited_by'),
        total_caps=Count('chapters')
    )
    
    # C. Preparación de datos para Chart.js
    # Convertimos los QuerySets en listas simples de Python para serializarlos
    # fácilmente en el template como arrays de JavaScript.
    chart_labels = [m.titulo for m in mis_mangas]
    chart_likes = [m.total_likes for m in mis_mangas]
    chart_caps = [m.total_caps for m in mis_mangas]

    # 4. Contexto para el template
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'favoritos': favoritos,       # Para la sección "Mi Biblioteca"
        'mis_mangas': mis_mangas,     # Para la lista de gestión "Mis Creaciones"
        'chart_labels': chart_labels, # Eje X del gráfico (Nombres)
        'chart_likes': chart_likes,   # Dataset 1 (Likes)
        'chart_caps': chart_caps,     # Dataset 2 (Capítulos)
    }
    return render(request, "accounts/profile.html", context)

@login_required
@require_POST
def add_favorite(request, manga_slug):
    """
    Vista API (AJAX) para alternar el estado de favorito de un manga.
    
    Recibe una petición POST asíncrona desde el frontend.
    Retorna:
        JsonResponse: Con el nuevo estado ('liked': boolean) y el total actualizado.
    """
    manga = get_object_or_404(Manga, slug=manga_slug)
    
    # Verificación de seguridad por si el perfil no existe
    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user)

    profile = request.user.profile
    
    # Lógica de Toggle (Si existe lo quita, si no, lo agrega)
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
    Vista de cierre de sesión seguro.
    
    Requiere método POST para evitar CSRF attacks o salidas accidentales por GET.
    """
    logout(request)
    messages.success(request, "Sesión cerrada correctamente. ¡Hasta pronto!")
    return redirect("catalogo:home")