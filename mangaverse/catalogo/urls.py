from django.urls import path
from . import views

app_name = 'catalogo'

urlpatterns = [
    # --- VISTAS PÚBLICAS ---
    path('', views.pagina_inicio, name='home'),
    path('lista/', views.lista_mangas, name='lista-mangas'),
    path('nosotros', views.nosotros, name='nosotros'),
    
    # --- BUSCADOR ---
    path('buscar/', views.search, name='search'),
    path('buscar/sugerencias/', views.search_suggest, name='search-suggest'),

    # --- GESTIÓN DE MANGAS (CRUD) ---
    path('mangas/crear/', views.MangaCreateView.as_view(), name='manga-create'),
    path('mangas/<slug:manga_slug>/editar/', views.MangaUpdateView.as_view(), name='manga-update'),
    path('mangas/<slug:manga_slug>/eliminar/', views.MangaDeleteView.as_view(), name='manga-delete'),

    # --- GESTIÓN DE CAPÍTULOS ---
    path('mangas/<slug:manga_slug>/nuevo-capitulo/', views.chapter_create_upload, name='chapter-create'),
    path('mangas/<slug:manga_slug>/capitulo/<slug:chapter_slug>/eliminar/', 
         views.ChapterDeleteView.as_view(), 
         name='chapter-delete'),

    # --- GESTIÓN DE ARCOS (Nuevas Rutas) ---
    path('mangas/<slug:manga_slug>/nuevo-arco/', views.arc_create_view, name='arc-create'),
    path('arcos/<int:pk>/editar/', views.ArcUpdateView.as_view(), name='arc-update'),
    path('arcos/<int:pk>/eliminar/', views.ArcDeleteView.as_view(), name='arc-delete'),

    # --- DETALLES (Siempre al final para evitar conflictos) ---
    path('mangas/<slug:manga_slug>/', views.manga_detail_view, name='manga-detail'),
    path('mangas/<slug:manga_slug>/<slug:chapter_slug>/', views.chapter_detail_view, name='chapter-detail'),
]