from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from django.http import HttpResponseRedirect, JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Manga, Chapter, Panel, Arc, GENEROS
from .forms import MangaForm, ChapterForm
from django.views.decorators.http import require_POST
import json
from django.contrib.auth import get_user_model


# Importamos la utilidad de procesamiento de archivos
try:
    from .utils import process_chapter_files
except ImportError:
    def process_chapter_files(*args, **kwargs): pass

# --------------------------
# VISTAS PÚBLICAS
# --------------------------

def pagina_inicio(request): 
    """
    Renderiza la página de inicio del sitio.
    
    Esta vista recopila y muestra:
    1. Los 5 mangas más recientes.
    2. Los 5 mangas más populares (basado en likes).
    3. Si el usuario está autenticado, muestra sus últimos 4 favoritos para acceso rápido.
    """
    recent_mangas = Manga.objects.order_by('-id')[:5]
    popular_mangas = Manga.objects.annotate(num_likes=Count('favorited_by')).order_by('-num_likes')[:5]
    contexto = {'recent_mangas': recent_mangas, 'popular_mangas': popular_mangas}
    
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        favorites = request.user.profile.favorites.all().order_by('-id')[:4]
        contexto['favorites'] = favorites

    return render(request, 'catalogo/inicio.html', contexto)

def lista_mangas(request):
    """
    Muestra el catálogo completo de mangas disponibles.
    
    Permite filtrar la lista por género mediante parámetros GET en la URL.
    
    Args:
        request: Objeto HttpRequest. Si contiene 'genero' en GET, filtra los resultados.
    """
    # 1. Obtenemos el parámetro de la URL (si existe)
    genero_filtrado = request.GET.get('genero')
    
    # 2. Empezamos con todos los mangas
    mangas = Manga.objects.all().order_by('titulo')
    
    # 3. Si hay filtro, aplicamos
    if genero_filtrado:
        mangas = mangas.filter(genero=genero_filtrado)
        
    context = {
        'mangas': mangas,
        'generos': GENEROS,       # Pasamos la lista de opciones para el menú
        'filtro_actual': genero_filtrado # Para saber cuál botón pintar de activo
    }
    
    return render(request, 'catalogo/lista_mangas.html', context)

def nosotros(request):
    """
    Renderiza la página estática 'Nosotros' o 'Misión'.
    """
    return render(request, 'catalogo/nosotros.html')

def search(request):
    """
    Realiza una búsqueda de mangas por título, descripción o autor.
    
    MEJORA SOCIAL:
    Si la búsqueda comienza con '@' (ej: @vicente), busca un perfil de usuario
    y redirige directamente a su página pública.
    """
    query = (request.GET.get('q') or '').strip()
    if not query: return redirect('catalogo:lista-mangas')
    
    # --- 1. BÚSQUEDA DE PERFILES DE USUARIO ---
    if query.startswith('@'):
        username = query[1:] # Quitamos el arroba para obtener el nombre limpio
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Si el usuario existe, vamos a su perfil público
        if User.objects.filter(username=username).exists():
            return redirect('accounts:public_profile', username=username)
        else:
            # Si no existe, avisamos y mandamos al home (o podrías dejar que busque mangas con ese nombre)
            messages.error(request, f"El usuario @{username} no fue encontrado.")
            return redirect('catalogo:home')

    # --- 2. BÚSQUEDA DE MANGAS (Lógica original) ---
    chapter_manga_ids = Chapter.objects.filter(Q(title__icontains=query)).values_list('manga_id', flat=True)
    
    mangas_qs = Manga.objects.filter(
        Q(titulo__icontains=query) | 
        Q(descripcion__icontains=query) | 
        Q(autor__icontains=query) | 
        Q(id__in=chapter_manga_ids)
    ).distinct().order_by('titulo')
    
    paginator = Paginator(mangas_qs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'catalogo/search_results.html', {
        'query': query, 
        'page_obj': page_obj, 
        'total': mangas_qs.count()
    })

def search_suggest(request):
    """
    API Endpoint para sugerencias de búsqueda en tiempo real (AJAX).
    
    Retorna:
        JsonResponse: Una lista de diccionarios con título, autor, URL y portada de los mangas coincidentes.
    """
    q = (request.GET.get('q') or '').strip()
    if not q: return JsonResponse({'results': []})
    
    chapter_manga_ids = Chapter.objects.filter(Q(title__icontains=q)).values_list('manga_id', flat=True)
    qs = Manga.objects.filter(
        Q(titulo__icontains=q) | Q(descripcion__icontains=q) | Q(autor__icontains=q) | Q(id__in=chapter_manga_ids)
    ).distinct().order_by('titulo')[:8]
    
    results = [{'title': m.titulo, 'author': m.autor or "", 'url': reverse("catalogo:manga-detail", args=[m.slug]), 'cover': m.portada.url if m.portada else ""} for m in qs]
    return JsonResponse({"results": results})

def manga_detail_view(request, manga_slug):
    """
    Muestra la ficha detallada de un manga específico.
    
    Incluye la lista de capítulos ordenados y la estructura de arcos narrativos.
    """
    manga = get_object_or_404(Manga, slug=manga_slug)
    chapters = manga.chapters.all().order_by('chapter_number')
    arcs = manga.arcs.all().order_by('order')
    return render(request, 'catalogo/manga_detail.html', {'manga': manga, 'chapters': chapters, 'arcs': arcs})

def chapter_detail_view(request, manga_slug, chapter_slug):
    """
    Visor de lectura de un capítulo.
    
    Carga todas las imágenes (Paneles) asociadas al capítulo, ordenadas por número de página.
    """
    chapter = get_object_or_404(Chapter, manga__slug=manga_slug, slug=chapter_slug)
    panels = chapter.panels.all().order_by('page_number')
    return render(request, 'catalogo/chapter_detail.html', {'chapter': chapter, 'panels': panels})

# --------------------------
# GESTIÓN Y PERMISOS (CRUD)
# --------------------------

class OwnerOrAdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin de control de acceso personalizado.
    
    Permite el acceso a una vista solo si el usuario actual es:
    1. El propietario (owner) del objeto (Manga) o del objeto padre (Manga del Capítulo/Arco).
    2. Un superusuario (Administrador).
    """
    def test_func(self):
        obj = self.get_object()
        if isinstance(obj, Chapter):
            return self.request.user == obj.manga.owner or self.request.user.is_superuser
        if isinstance(obj, Arc):
            return self.request.user == obj.manga.owner or self.request.user.is_superuser
        return self.request.user == obj.owner or self.request.user.is_superuser

# --- MANGA CRUD ---

class MangaCreateView(LoginRequiredMixin, CreateView):
    """
    Vista para crear un nuevo Manga.
    
    Cualquier usuario registrado puede crear un manga.
    Automáticamente asigna al usuario actual como el 'owner' del manga.
    """
    model = Manga
    form_class = MangaForm
    template_name = 'catalogo/manga_form.html'
    # ELIMINAMOS LA LÍNEA: permission_required = 'catalogo.add_manga'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "¡Manga creado! Ahora puedes agregar capítulos y arcos.")
        return response

    def get_success_url(self):
        return reverse('catalogo:manga-detail', kwargs={'manga_slug': self.object.slug})

class MangaUpdateView(LoginRequiredMixin, OwnerOrAdminRequiredMixin, UpdateView):
    """
    Vista para editar la información de un Manga existente.
    
    Protegida por OwnerOrAdminRequiredMixin.
    """
    model = Manga
    form_class = MangaForm
    template_name = 'catalogo/manga_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'manga_slug'

    def form_valid(self, form):
        messages.success(self.request, 'Manga actualizado correctamente.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('catalogo:manga-detail', kwargs={'manga_slug': self.object.slug})

class MangaDeleteView(LoginRequiredMixin, OwnerOrAdminRequiredMixin, DeleteView):
    """
    Vista para eliminar un Manga.
    
    Protegida por OwnerOrAdminRequiredMixin.
    """
    model = Manga
    template_name = 'catalogo/manga_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'manga_slug'
    success_url = reverse_lazy('catalogo:lista-mangas')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Manga eliminado correctamente.')
        return super().delete(request, *args, **kwargs)

# --- CAPÍTULO DELETE ---

class ChapterDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Vista para eliminar un Capítulo específico.
    
    Verifica que el usuario sea dueño del Manga padre o admin.
    """
    model = Chapter
    template_name = 'catalogo/chapter_confirm_delete.html'
    
    def get_object(self, queryset=None):
        return get_object_or_404(Chapter, manga__slug=self.kwargs['manga_slug'], slug=self.kwargs['chapter_slug'])

    def test_func(self):
        chapter = self.get_object()
        return self.request.user == chapter.manga.owner or self.request.user.is_superuser

    def get_success_url(self):
        messages.success(self.request, 'Capítulo eliminado.')
        return reverse('catalogo:manga-detail', kwargs={'manga_slug': self.object.manga.slug})


@login_required
def chapter_edit_upload(request, manga_slug, chapter_slug):
    """
    Vista híbrida para editar un capítulo existente.
    
    Funcionalidad dual:
    1. POST (Dropzone): Permite agregar nuevas páginas (imágenes/PDF) al final del capítulo existente.
    2. POST (Formulario): Permite editar los metadatos del capítulo (título, número, arco).
    """
    manga = get_object_or_404(Manga, slug=manga_slug)
    chapter = get_object_or_404(Chapter, manga=manga, slug=chapter_slug)

    # Seguridad
    if request.user != manga.owner and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para editar este capítulo.")
        return redirect('catalogo:manga-detail', manga_slug=manga.slug)

    if request.method == 'POST':
        # CASO A: Dropzone (Agregar páginas extra)
        if 'file' in request.FILES:
            try:
                # Usamos la misma utilidad. Las nuevas imágenes se agregan al final.
                process_chapter_files(chapter, [request.FILES['file']])
                return JsonResponse({'status': 'success'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

        # CASO B: Formulario Normal (Editar Título/Arco/Número)
        form = ChapterForm(request.POST, instance=chapter)
        form.fields['arc'].queryset = Arc.objects.filter(manga=manga)

        if form.is_valid():
            chapter = form.save()
            messages.success(request, "Capítulo actualizado correctamente.")
            return redirect('catalogo:chapter-detail', manga_slug=manga.slug, chapter_slug=chapter.slug)
    
    else:
        form = ChapterForm(instance=chapter)
        form.fields['arc'].queryset = Arc.objects.filter(manga=manga)

    return render(request, 'catalogo/chapter_edit.html', {
        'form': form,
        'manga': manga,
        'chapter': chapter
    })

# --- ARCO CRUD ---

class ArcUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Vista para editar un Arco narrativo.
    """
    model = Arc
    fields = ['title', 'order']
    template_name = 'catalogo/arc_form_modal.html'

    def test_func(self):
        arc = self.get_object()
        return self.request.user == arc.manga.owner or self.request.user.is_superuser

    def get_success_url(self):
        messages.success(self.request, 'Arco actualizado.')
        return reverse('catalogo:manga-detail', kwargs={'manga_slug': self.object.manga.slug})

class ArcDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Vista para eliminar un Arco narrativo.
    """
    model = Arc
    template_name = 'catalogo/arc_confirm_delete.html'

    def test_func(self):
        arc = self.get_object()
        return self.request.user == arc.manga.owner or self.request.user.is_superuser

    def get_success_url(self):
        messages.success(self.request, 'Arco eliminado.')
        return reverse('catalogo:manga-detail', kwargs={'manga_slug': self.object.manga.slug})

# --------------------------
# VISTAS DE GESTIÓN (Funciones)
# --------------------------

@login_required
def chapter_create_upload(request, manga_slug):
    """
    Vista híbrida para crear un nuevo capítulo.
    
    Maneja dos tipos de solicitudes POST:
    1. AJAX (Dropzone): Recibe archivos (imágenes o PDF) y los procesa en segundo plano.
    2. Standard Form: Crea la instancia del Capítulo con sus metadatos.
    """
    manga = get_object_or_404(Manga, slug=manga_slug)
    
    if request.user != manga.owner and not request.user.is_superuser:
        messages.error(request, "No tienes permiso.")
        return redirect('catalogo:manga-detail', manga_slug=manga.slug)

    if request.method == 'POST':
        # CASO A: Dropzone
        if 'file' in request.FILES:
            chapter_id = request.POST.get('chapter_id')
            if not chapter_id: return JsonResponse({'error': 'Falta ID'}, status=400)
            chapter = get_object_or_404(Chapter, id=chapter_id, manga=manga)
            try:
                process_chapter_files(chapter, [request.FILES['file']])
                return JsonResponse({'status': 'success'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

        # CASO B: Formulario
        form = ChapterForm(request.POST)
        form.fields['arc'].queryset = Arc.objects.filter(manga=manga)
        
        if form.is_valid():
            chapter = form.save(commit=False)
            chapter.manga = manga
            chapter.save()
            return JsonResponse({
                'status': 'created', 
                'chapter_id': chapter.id, 
                'redirect_url': reverse('catalogo:chapter-detail', args=[manga.slug, chapter.slug])
            })
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    
    else:
        form = ChapterForm()
        form.fields['arc'].queryset = Arc.objects.filter(manga=manga)

    return render(request, 'catalogo/chapter_create.html', {'form': form, 'manga': manga})

@login_required
def arc_create_view(request, manga_slug):
    """
    Vista rápida para crear Arcos desde un Modal.
    
    Redirige siempre a la página de referencia (HTTP_REFERER) para mantener el flujo.
    """
    manga = get_object_or_404(Manga, slug=manga_slug)
    if request.user != manga.owner and not request.user.is_superuser:
        return redirect('catalogo:manga-detail', manga_slug=manga.slug)

    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            last_order = Arc.objects.filter(manga=manga).count()
            Arc.objects.create(manga=manga, title=title, order=last_order + 1)
            messages.success(request, f"Arco '{title}' creado.")
    
    return redirect(request.META.get('HTTP_REFERER') or reverse('catalogo:manga-detail', args=[manga.slug]))

# En catalogo/views.py

@login_required
@require_POST
def panel_delete(request, panel_id):
    """
    Elimina una página (panel) individual de un capítulo.
    """
    panel = get_object_or_404(Panel, id=panel_id)
    chapter = panel.chapter
    
    # Seguridad: Solo el dueño del manga o admin puede borrar
    if request.user != chapter.manga.owner and not request.user.is_superuser:
        messages.error(request, "No tienes permiso.")
        return redirect('catalogo:chapter-detail', manga_slug=chapter.manga.slug, chapter_slug=chapter.slug)

    # Borramos el panel
    panel.delete()
    
    # Opcional: Reordenar las páginas restantes (Script simple)
    # Esto evita huecos en la numeración (1, 3, 4...)
    for index, p in enumerate(chapter.panels.all().order_by('page_number'), start=1):
        p.page_number = index
        p.save()

    messages.success(request, "Página eliminada y numeración reordenada.")
    
    # Volvemos a la misma página de edición
    return redirect('catalogo:chapter-edit', manga_slug=chapter.manga.slug, chapter_slug=chapter.slug)

@login_required
@require_POST
def reorder_panels(request):
    """
    Recibe una lista de IDs de paneles en el nuevo orden y actualiza sus page_number.
    """
    try:
        data = json.loads(request.body)
        panel_ids = data.get('panel_ids', [])
        
        if not panel_ids:
            return JsonResponse({'status': 'error', 'message': 'Lista vacía'}, status=400)

        # Verificación de seguridad rápida (tomamos el primer panel para chequear dueño)
        first_panel = Panel.objects.get(id=panel_ids[0])
        if request.user != first_panel.chapter.manga.owner and not request.user.is_superuser:
            return JsonResponse({'status': 'error', 'message': 'Sin permisos'}, status=403)

        # Actualización masiva del orden
        # Iteramos la lista que nos mandó el frontend (que ya viene ordenada)
        for index, panel_id in enumerate(panel_ids, start=1):
            Panel.objects.filter(id=panel_id).update(page_number=index)
            
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)