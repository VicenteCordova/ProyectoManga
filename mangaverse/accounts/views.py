from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from .forms import RegisterForm

def register(request):
    """
    Crea un usuario usando RegisterForm (basado en UserCreationForm).
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
    """
    Muestra un perfil básico del usuario autenticado.
    Más adelante puedes enlazar un modelo Profile (OneToOne).
    """
    return render(request, "accounts/profile.html", {"user_obj": request.user})

@require_POST
def logout_confirm(request):
    """
    Cierra sesión solo por POST para evitar disparos accidentales por GET.
    """
    logout(request)
    messages.success(request, "Sesión cerrada correctamente. ¡Hasta pronto!")
    return redirect("catalogo:home")
