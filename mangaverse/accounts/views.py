from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.http import JsonResponse
from django.db.models import Count, Q
from django.urls import reverse

# Importamos modelos necesarios
from catalogo.models import Manga
from .forms import RegisterForm, UserUpdateForm, ProfileUpdateForm
from .models import Profile, Message

# Definimos la variable User para usarla en las consultas
User = get_user_model()

# ------------------------------------
# HELPER DE VISTAS (SOLUCIÓN AL ERROR)
# ------------------------------------

def get_template_base(request):
    """Selecciona la plantilla base (base.html o base_min.html) según el parámetro GET 'mini'."""
    if request.GET.get('mini'):
        return 'base_min.html'
    return 'base.html'

# --------------------------
# VISTAS PRINCIPALES
# --------------------------

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
    Dashboard del usuario: Edición, Estadísticas y Biblioteca.
    """
    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, '¡Tu perfil ha sido actualizado!')
            return redirect('accounts:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    # DATOS PARA EL DASHBOARD
    favoritos = request.user.profile.favorites.all()
    mis_mangas = Manga.objects.filter(owner=request.user).annotate(
        total_likes=Count('favorited_by'),
        total_caps=Count('chapters')
    )
    chart_labels = [m.titulo for m in mis_mangas]
    chart_likes = [m.total_likes for m in mis_mangas]
    chart_caps = [m.total_caps for m in mis_mangas]

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'favoritos': favoritos,
        'mis_mangas': mis_mangas,
        'chart_labels': chart_labels,
        'chart_likes': chart_likes,
        'chart_caps': chart_caps,
    }
    return render(request, "accounts/profile.html", context)

@login_required
@require_POST
def add_favorite(request, manga_slug):
    """
    Vista AJAX para dar like/fav a un manga.
    """
    manga = get_object_or_404(Manga, slug=manga_slug)
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

# --------------------------
# FUNCIONES SOCIALES
# --------------------------

@login_required
@require_POST 
def delete_chat(request, username):
    """
    Elimina todo el historial de mensajes con un usuario específico.
    """
    other_user = get_object_or_404(User, username=username)
    
    Message.objects.filter(
        (Q(sender=request.user) & Q(recipient=other_user)) |
        (Q(sender=other_user) & Q(recipient=request.user))
    ).delete()
    
    messages.success(request, f"Chat con {username} eliminado.")
    
    # Redirigir respetando el modo mini
    next_url = reverse('accounts:inbox')
    if request.GET.get('mini'):
        next_url += '?mini=true'
        
    return redirect(next_url)

def public_profile(request, username):
    """
    Muestra el perfil público de otro usuario.
    """
    target_user = get_object_or_404(User, username=username)
    
    if request.user.is_authenticated and request.user == target_user:
        return redirect('accounts:profile')
        
    mis_mangas = Manga.objects.filter(owner=target_user).annotate(
        total_likes=Count('favorited_by'),
        total_caps=Count('chapters')
    )

    is_following = False
    if request.user.is_authenticated:
        if not hasattr(request.user, 'profile'):
            Profile.objects.create(user=request.user)
        is_following = request.user.profile.following.filter(id=target_user.profile.id).exists()

    context = {
        'target_user': target_user,
        'mis_mangas': mis_mangas,
        'is_following': is_following,
        'followers_count': target_user.profile.followers.count(),
        'following_count': target_user.profile.following.count()
    }
    return render(request, 'accounts/public_profile.html', context)

@login_required
def follow_toggle(request, username):
    """
    Permite seguir o dejar de seguir a un usuario.
    """
    target_user = get_object_or_404(User, username=username)
    
    if request.user == target_user:
        messages.error(request, "No puedes seguirte a ti mismo.")
        return redirect('accounts:profile')

    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user)

    my_profile = request.user.profile
    target_profile = target_user.profile
    
    if my_profile.following.filter(id=target_profile.id).exists():
        my_profile.following.remove(target_profile)
        messages.info(request, f"Dejaste de seguir a {username}.")
    else:
        my_profile.following.add(target_profile)
        messages.success(request, f"Ahora sigues a {username}.")
        
    return redirect('accounts:public_profile', username=username)

@login_required
@xframe_options_sameorigin
def inbox(request):
    """
    Bandeja de entrada: Muestra lista de usuarios con chats activos.
    """
    chat_partners = User.objects.filter(
        Q(received_messages__sender=request.user) | 
        Q(sent_messages__recipient=request.user)
    ).distinct().exclude(id=request.user.id)
    
    return render(request, 'accounts/inbox.html', {
        'users': chat_partners,
        'layout': get_template_base(request)
    })

@login_required
@xframe_options_sameorigin
def chat_detail(request, username):
    """
    Sala de chat privada con un usuario específico.
    """
    other_user = get_object_or_404(User, username=username)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            msg = Message.objects.create(sender=request.user, recipient=other_user, content=content)
            
            # Devolver JSON si es AJAX (para el envío fluido)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'ok',
                    'content': msg.content,
                    'timestamp': msg.timestamp.strftime("%H:%M"),
                    'sender': request.user.username
                })
            
            return redirect('accounts:chat_detail', username=username)
    
    # Historial de mensajes
    messages_list = Message.objects.filter(
        (Q(sender=request.user) & Q(recipient=other_user)) |
        (Q(sender=other_user) & Q(recipient=request.user))
    ).order_by('timestamp')
    
    return render(request, 'accounts/chat.html', {
        'other_user': other_user, 
        'messages_list': messages_list,
        'layout': get_template_base(request)
    })