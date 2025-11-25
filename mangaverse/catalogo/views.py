from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from django.http import HttpResponseRedirect, JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Manga, Chapter, Panel, Arc
from .forms import MangaForm, ChapterFormSet, ArcFormSet

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
    return render(request, 'catalogo/lista_mangas.html', {'mangas': Manga.objects.all()})

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
    return render(request, 'catalogo/manga_detail.html', {'manga': manga, 'chapters': chapters})

def chapter_detail_view(request, manga_slug, chapter_slug):
    chapter = get_object_or_404(Chapter, manga__slug=manga_slug, slug=chapter_slug)
    panels = chapter.panels.all().order_by('page_number')
    return render(request, 'catalogo/chapter_detail.html', {'chapter': chapter, 'panels': panels})

# --------------------------
# GESTIÓN (CRUD)
# --------------------------

class OwnerOrAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        return self.request.user == obj.owner or self.request.user.is_superuser

class MangaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Manga
    form_class = MangaForm
    template_name = 'catalogo/manga_form.html'
    permission_required = 'catalogo.add_manga'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['arcs_formset'] = ArcFormSet(self.request.POST, prefix='arcs')
            # Pasamos FILES al formset de capítulos
            context['chapters_formset'] = ChapterFormSet(self.request.POST, self.request.FILES, prefix='chapters')
        else:
            context['arcs_formset'] = ArcFormSet(prefix='arcs')
            context['chapters_formset'] = ChapterFormSet(prefix='chapters')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        arcs_formset = context['arcs_formset']
        chapters_formset = context['chapters_formset']

        if form.is_valid() and arcs_formset.is_valid() and chapters_formset.is_valid():
            # 1. Guardar Manga
            self.object = form.save(commit=False)
            self.object.owner = self.request.user
            self.object.save()
            
            # 2. Guardar Arcos
            arcs_formset.instance = self.object
            arcs_formset.save()

            # 3. Guardar Capítulos y PROCESAR IMÁGENES MANUALMENTE
            # Guardamos los objetos capítulo pero sin commitear a DB aún si fuera necesario, 
            # pero aquí usaremos el save del formset y luego iteraremos.
            
            # Guardamos los formularios para tener las instancias de Chapter creadas
            instances = chapters_formset.save(commit=False)
            for obj in instances:
                obj.manga = self.object
                obj.save()
            
            # Manejo de borrados
            for obj in chapters_formset.deleted_objects:
                obj.delete()

            # AHORA LA MAGIA: Iteramos sobre los formularios para sacar las imágenes crudas
            for i, chapter_form in enumerate(chapters_formset.forms):
                if chapter_form.cleaned_data and not chapter_form.cleaned_data.get('DELETE'):
                    # La instancia ya debería tener ID gracias al save() anterior
                    chapter_instance = chapter_form.instance
                    
                    # Buscamos en request.FILES usando el prefijo del formset
                    # El nombre del campo en HTML es: chapters-0-images, chapters-1-images, etc.
                    files_key = f"{chapters_formset.prefix}-{i}-images"
                    
                    images_list = self.request.FILES.getlist(files_key)
                    
                    if images_list:
                        start_page = chapter_instance.panels.count() + 1
                        for idx, img in enumerate(images_list):
                            Panel.objects.create(
                                chapter=chapter_instance,
                                image=img,
                                page_number=start_page + idx
                            )

            messages.success(self.request, '¡Manga creado exitosamente!')
            return HttpResponseRedirect(self.get_success_url())

        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse('catalogo:manga-detail', kwargs={'manga_slug': self.object.slug})

class MangaUpdateView(LoginRequiredMixin, OwnerOrAdminRequiredMixin, UpdateView):
    model = Manga
    form_class = MangaForm
    template_name = 'catalogo/manga_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'manga_slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['arcs_formset'] = ArcFormSet(self.request.POST, instance=self.object, prefix='arcs')
            context['chapters_formset'] = ChapterFormSet(self.request.POST, self.request.FILES, instance=self.object, prefix='chapters')
        else:
            context['arcs_formset'] = ArcFormSet(instance=self.object, prefix='arcs')
            context['chapters_formset'] = ChapterFormSet(instance=self.object, prefix='chapters')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        arcs_formset = context['arcs_formset']
        chapters_formset = context['chapters_formset']

        if form.is_valid() and arcs_formset.is_valid() and chapters_formset.is_valid():
            self.object = form.save()
            arcs_formset.save()
            
            # Misma lógica manual para Update
            instances = chapters_formset.save(commit=False)
            for obj in instances:
                obj.manga = self.object
                obj.save()
            for obj in chapters_formset.deleted_objects:
                obj.delete()

            for i, chapter_form in enumerate(chapters_formset.forms):
                if chapter_form.cleaned_data and not chapter_form.cleaned_data.get('DELETE'):
                    chapter_instance = chapter_form.instance
                    files_key = f"{chapters_formset.prefix}-{i}-images"
                    images_list = self.request.FILES.getlist(files_key)
                    
                    if images_list:
                        start_page = chapter_instance.panels.count() + 1
                        for idx, img in enumerate(images_list):
                            Panel.objects.create(
                                chapter=chapter_instance,
                                image=img,
                                page_number=start_page + idx
                            )

            messages.success(self.request, 'Manga actualizado correctamente.')
            return HttpResponseRedirect(self.get_success_url())
        
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse('catalogo:manga-detail', kwargs={'manga_slug': self.object.slug})

class MangaDeleteView(LoginRequiredMixin, OwnerOrAdminRequiredMixin, DeleteView):
    model = Manga
    template_name = 'catalogo/manga_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'manga_slug'
    success_url = reverse_lazy('catalogo:lista-mangas')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Manga eliminado.')
        return super().delete(request, *args, **kwargs)