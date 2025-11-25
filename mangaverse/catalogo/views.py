# catalogo/views.py
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from django.http import HttpResponseRedirect  
from django.db.models import Q  
from django.http import JsonResponse 
from django.core.paginator import Paginator  
from .models import Manga, Chapter  
from .forms import MangaForm, ChapterFormSet  

# --------------------------
# VISTAS FUNCIONALES EXISTENTES
# -------------------
def pagina_inicio(request): 
    contexto = {}
    return render(request, 'catalogo/inicio.html', contexto)

def lista_mangas(request):
    mangas = Manga.objects.all()
    contexto = {'mangas': mangas}
    return render(request, 'catalogo/lista_mangas.html', contexto)

def manga_detail_view(request, manga_slug):
    # Busca el manga por slug o devuelve error 404 si no existe
    manga = get_object_or_404(Manga, slug=manga_slug)
    # Obtiene los capítulos relacionados con este manga
    chapters = manga.chapters.all()  
    contexto = {
        'manga': manga,
        'chapters': chapters,
    }
    return render(request, 'catalogo/manga_detail.html', contexto)

def chapter_detail_view(request, manga_slug, chapter_slug):
    # Capítulo específico asegurando que pertenece al manga correcto
    chapter = get_object_or_404(Chapter, manga__slug=manga_slug, slug=chapter_slug)
    panels = chapter.panels.all()  
    contexto = {
        'chapter': chapter,
        'panels': panels,
    }
    return render(request, 'catalogo/chapter_detail.html', contexto)

def nosotros(request):
    """Página estática 'Nosotros'."""
    return render(request, 'catalogo/nosotros.html')

# ---------------------------
#  CRUD DE MANGA
# -------------------------

# MANGA CREATE con inline formset de capítulos 
class MangaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Manga
    form_class = MangaForm
    template_name = 'catalogo/manga_form.html'
    permission_required = 'catalogo.add_manga'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
       
        if self.request.method == 'POST':
            context['chapters_formset'] = ChapterFormSet(
                self.request.POST, self.request.FILES, prefix='chapters'
            )
        else:
            context['chapters_formset'] = ChapterFormSet(prefix='chapters')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['chapters_formset']

        if formset.is_valid():
            self.object = form.save()           # guarda Manga
            formset.instance = self.object
            formset.save()                      # guarda capítulos

            # Crear Panels por cada Chapter con las imágenes subidas
            for f in formset.forms:
                if getattr(f, 'cleaned_data', None) and f.cleaned_data.get('DELETE'):
                    continue
                chapter = getattr(f, 'instance', None)
                if not chapter or not chapter.pk:
                    continue

                files = []
                imgs = f.cleaned_data.get('images') if hasattr(f, 'cleaned_data') else None
                if imgs:
                    files = imgs if isinstance(imgs, (list, tuple)) else [imgs]
                if not files:
                    files = self.request.FILES.getlist(f"{f.prefix}-images")

                for img in files:
                    if img:
                        Panel.objects.create(chapter=chapter, image=img)

            messages.success(self.request, 'Manga creado correctamente.')
            return HttpResponseRedirect(self.get_success_url())

        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse('catalogo:manga-detail', kwargs={'manga_slug': self.object.slug})

class MangaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Manga
    form_class = MangaForm
    template_name = 'catalogo/manga_form.html'
    permission_required = 'catalogo.change_manga'
    slug_field = 'slug'
    slug_url_kwarg = 'manga_slug'

    def form_valid(self, form):
        messages.success(self.request, 'Manga actualizado correctamente.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('catalogo:manga-detail', kwargs={'manga_slug': self.object.slug})

class MangaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Manga
    template_name = 'catalogo/manga_confirm_delete.html'
    permission_required = 'catalogo.delete_manga'
    slug_field = 'slug'
    slug_url_kwarg = 'manga_slug'
    success_url = reverse_lazy('catalogo:lista-mangas')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Manga eliminado correctamente.')
        return super().delete(request, *args, **kwargs)
    

def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    if self.request.method == 'POST':
        context['chapters_formset'] = ChapterFormSet(
            self.request.POST, self.request.FILES, prefix='chapters'
        )
    else:
        context['chapters_formset'] = ChapterFormSet(prefix='chapters')
    return context


# ---------------------
# BUSCAR
# ---------------------

def search(request):
    query = (request.GET.get('q') or '').strip()
    if not query:
        messages.info(request, "Ingresa un término para buscar.")
        return redirect('catalogo:lista-mangas')

  
    chapter_manga_ids = Chapter.objects.filter(
        Q(title__icontains=query)
    ).values_list('manga_id', flat=True)

    #  Manga sí tiene 'titulo', 'descripcion', 'autor'
    mangas_qs = (
        Manga.objects.filter(
            Q(titulo__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(autor__icontains=query) |
            Q(id__in=chapter_manga_ids)
        )
        .distinct()
        .order_by('titulo')
    )

    paginator = Paginator(mangas_qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    contexto = {'query': query, 'page_obj': page_obj, 'total': mangas_qs.count()}
    return render(request, 'catalogo/search_results.html', contexto)


def search_suggest(request):
    q = (request.GET.get('q') or '').strip()
    if not q:
        return JsonResponse({'results': []})

    chapter_manga_ids = Chapter.objects.filter(
        Q(title__icontains=q)
    ).values_list('manga_id', flat=True)

    qs = (
        Manga.objects.filter(
            Q(titulo__icontains=q) |
            Q(descripcion__icontains=q) |
            Q(autor__icontains=q) |
            Q(id__in=chapter_manga_ids)
        )
        .distinct()
        .order_by('titulo')[:8]
    )

    results = []
    for m in qs:
        cover_url = m.portada.url if getattr(m, "portada", None) else ""
        results.append({
            "title": m.titulo,                                   # título
            "author": m.autor or "",                              # autor
            "url": reverse("catalogo:manga-detail", args=[m.slug]),
            "cover": cover_url,                                   # imagen (puede venir vacío)
            "snippet": (m.descripcion or "")[:120],
        })
    return JsonResponse({"results": results})