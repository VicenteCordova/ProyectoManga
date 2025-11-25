# catalogo/urls.py
from django.urls import path
from . import views

app_name = 'catalogo'

urlpatterns = [
    # Home y lista
    path('', views.pagina_inicio, name='home'),
    path('lista/', views.lista_mangas, name='lista-mangas'),

    # Rutas específicas (antes del slug)
    path('mangas/crear/', views.MangaCreateView.as_view(), name='manga-create'),
    path('mangas/<slug:manga_slug>/editar/', views.MangaUpdateView.as_view(), name='manga-update'),
    path('mangas/<slug:manga_slug>/eliminar/', views.MangaDeleteView.as_view(), name='manga-delete'),

    # Buscar
    path('buscar/', views.search, name='search'),
    path('buscar/sugerencias/', views.search_suggest, name='search-suggest'),

    # Detalles
    path('mangas/<slug:manga_slug>/', views.manga_detail_view, name='manga-detail'),
    path('mangas/<slug:manga_slug>/<slug:chapter_slug>/', views.chapter_detail_view, name='chapter-detail'),

    # Página estática
    path('nosotros', views.nosotros, name='nosotros'),
]
