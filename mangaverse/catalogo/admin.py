from django.contrib import admin
from .models import Manga, Chapter, Panel

# Inline para mostrar y añadir Paneles dentro de Chapter
class PanelInline(admin.TabularInline):
    model = Panel
    extra = 1 

# Configuración Admin para Chapter
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'manga', 'chapter_number')
    list_filter = ('manga',)
    search_fields = ('title',)
    inlines = [PanelInline] # Añade los paneles aquí
    prepopulated_fields = {'slug': ('title',)} # Ayuda a generar el slug

# Configuración Admin para Manga
class MangaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor')
    search_fields = ('titulo', 'autor')
    prepopulated_fields = {'slug': ('titulo',)} # Ayuda a generar el slug

admin.site.register(Manga, MangaAdmin)
admin.site.register(Chapter, ChapterAdmin)
