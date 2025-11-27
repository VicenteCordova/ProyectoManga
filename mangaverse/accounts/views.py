from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse

# --- CORRECCIÓN IMPORTANTE ---
# Importamos Manga desde 'catalogo.models', NO desde '.models'
from catalogo.models import Manga

# Importamos los formularios de la app actual (accounts)
from .forms import RegisterForm, UserUpdateForm, ProfileUpdateForm

def register(request):
    """
    Crea un usuario usando RegisterForm.
    Si es válido, inicia sesión y redirige a 'Mi perfil'.
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
    # Aseguramos que el usuario tenga perfil (por si es un usuario antiguo)
    if not hasattr(request.user, 'profile'):
        from .models import Profile
        Profile.objects.create(user=request.user)

    if request.method == 'POST':
        # Instanciamos los formularios con los datos POST
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, '¡Tu perfil ha sido actualizado!')
            return redirect('accounts:profile')
    else:
        # Formularios vacíos (con datos actuales) para GET
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    # Obtenemos los favoritos para mostrarlos
    favoritos = request.user.profile.favorites.all()

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'favoritos': favoritos
    }
    return render(request, "accounts/profile.html", context)

@login_required
@require_POST
def add_favorite(request, manga_slug):
    """Vista que recibe una petición AJAX para agregar/quitar favorito"""
    manga = get_object_or_404(Manga, slug=manga_slug)
    
    # Verificación de seguridad por si el perfil no existe
    if not hasattr(request.user, 'profile'):
        from .models import Profile
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
    Cierra sesión solo por POST para evitar disparos accidentales por GET.
    """
    logout(request)
    messages.success(request, "Sesión cerrada correctamente. ¡Hasta pronto!")
    return redirect("catalogo:home")