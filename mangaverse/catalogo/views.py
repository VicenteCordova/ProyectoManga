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

# Importamos la utilidad de procesamiento de archivos
try:
    from .utils import process_chapter_files
except ImportError:
    def process_chapter_files(*args, **kwargs): pass



@login_required
def profile(request):
    # Aseguramos perfil
    if not hasattr(request.user, 'profile'):
        from .models import Profile
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
    # 1. Mis Favoritos (Lo que leo)
    favoritos = request.user.profile.favorites.all()
    
    # 2. Mis Creaciones (Lo que subí) - Para el gráfico
    mis_mangas = Manga.objects.filter(owner=request.user).annotate(
        total_likes=Count('favorited_by'),
        total_caps=Count('chapters')
    )
    
    # Preparamos listas para Chart.js
    chart_labels = [m.titulo for m in mis_mangas]
    chart_likes = [m.total_likes for m in mis_mangas]
    chart_caps = [m.total_caps for m in mis_mangas]

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'favoritos': favoritos,
        'mis_mangas': mis_mangas, # Enviamos también los objetos
        'chart_labels': chart_labels,
        'chart_likes': chart_likes,
        'chart_caps': chart_caps,
    }
    return render(request, "accounts/profile.html", context)
# --------------------------
# VISTAS PÚBLICAS
# --------------------------

def pagina_inicio(request): 
    recent_mangas = Manga.objects.order_by('-id')[:5]
    popular_mangas = Manga.objects.annotate(num_likes=Count('favorited_by')).order_by('-num_likes')[:5]
    contexto = {'recent_mangas': recent_mangas, 'popular_mangas': popular_mangas}
    
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        favorites = request.user.profile.favorites.all().order_by('-id')[:4]
        contexto['favorites'] = favorites

    return render(request, 'catalogo/inicio.html', contexto)

def lista_mangas(request):
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
    return render(request, 'catalogo/nosotros.html')

def search(request):
    query = (request.GET.get('q') or '').strip()
    if not query: return redirect('catalogo:lista-mangas')
    
    chapter_manga_ids = Chapter.objects.filter(Q(title__icontains=query)).values_list('manga_id', flat=True)
    mangas_qs = Manga.objects.filter(
        Q(titulo__icontains=query) | 
        Q(descripcion__icontains=query) | 
        Q(autor__icontains=query) | 
        Q(id__in=chapter_manga_ids)
    ).distinct().order_by('titulo')
    
    paginator = Paginator(mangas_qs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'catalogo/search_results.html', {'query': query, 'page_obj': page_obj, 'total': mangas_qs.count()})

def search_suggest(request):
    q = (request.GET.get('q') or '').strip()
    if not q: return JsonResponse({'results': []})
    
    chapter_manga_ids = Chapter.objects.filter(Q(title__icontains=q)).values_list('manga_id', flat=True)
    qs = Manga.objects.filter(
        Q(titulo__icontains=q) | Q(descripcion__icontains=q) | Q(autor__icontains=q) | Q(id__in=chapter_manga_ids)
    ).distinct().order_by('titulo')[:8]
    
    results = [{'title': m.titulo, 'author': m.autor or "", 'url': reverse("catalogo:manga-detail", args=[m.slug]), 'cover': m.portada.url if m.portada else ""} for m in qs]
    return JsonResponse({"results": results})

def manga_detail_view(request, manga_slug):
    manga = get_object_or_404(Manga, slug=manga_slug)
    chapters = manga.chapters.all().order_by('chapter_number')
    arcs = manga.arcs.all().order_by('order')
    return render(request, 'catalogo/manga_detail.html', {'manga': manga, 'chapters': chapters, 'arcs': arcs})

def chapter_detail_view(request, manga_slug, chapter_slug):
    chapter = get_object_or_404(Chapter, manga__slug=manga_slug, slug=chapter_slug)
    panels = chapter.panels.all().order_by('page_number')
    return render(request, 'catalogo/chapter_detail.html', {'chapter': chapter, 'panels': panels})

# --------------------------
# GESTIÓN Y PERMISOS (CRUD)
# --------------------------

class OwnerOrAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        if isinstance(obj, Chapter):
            return self.request.user == obj.manga.owner or self.request.user.is_superuser
        if isinstance(obj, Arc):
            return self.request.user == obj.manga.owner or self.request.user.is_superuser
        return self.request.user == obj.owner or self.request.user.is_superuser

# --- MANGA CRUD ---

# En catalogo/views.py

# Quitamos PermissionRequiredMixin de la lista de herencia
class MangaCreateView(LoginRequiredMixin, CreateView):
    """
    Crea solo el objeto Manga. Cualquier usuario registrado puede hacerlo.
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
    Permite editar los datos de un capítulo y agregarle más páginas.
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