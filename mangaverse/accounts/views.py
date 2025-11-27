from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from catalogo.models import Manga
from .forms import RegisterForm, UserUpdateForm, ProfileUpdateForm

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "¡Cuenta creada con éxito! Bienvenido.")
            return redirect("accounts:profile")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})

@login_required
def profile(request):
    if not hasattr(request.user, 'profile'):
        from .models import Profile; Profile.objects.create(user=request.user)
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save(); p_form.save()
            messages.success(request, '¡Perfil actualizado!')
            return redirect('accounts:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    favorites = request.user.profile.favorites.all()
    return render(request, "accounts/profile.html", {'u_form': u_form, 'p_form': p_form, 'favoritos': favorites})

@login_required
@require_POST
def add_favorite(request, manga_slug):
    manga = get_object_or_404(Manga, slug=manga_slug)
    if not hasattr(request.user, 'profile'):
        from .models import Profile; Profile.objects.create(user=request.user)
    profile = request.user.profile
    if profile.favorites.filter(id=manga.id).exists():
        profile.favorites.remove(manga); liked = False
    else:
        profile.favorites.add(manga); liked = True
    return JsonResponse({'liked': liked, 'total': profile.favorites.count()})

@require_POST
def logout_confirm(request):
    logout(request)
    messages.success(request, "Sesión cerrada.")
    return redirect("catalogo:home")