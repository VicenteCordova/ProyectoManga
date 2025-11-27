from django import forms
from django.contrib import admin
from .models import Manga, Chapter, Panel, Arc

# --- 1. WIDGET PERSONALIZADO (Evita el error de seguridad de Django) ---
class AdminMultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

# --- 2. FORMULARIO DEL ADMIN ---
class ChapterAdminForm(forms.ModelForm):
    # Campo virtual para subir archivos (no existe en la base de datos)
    imagenes_masivas = forms.FileField(
        widget=AdminMultiFileInput(attrs={'multiple': True}), # Usamos nuestro widget seguro
        label="Subir Múltiples Paneles",
        required=False,
        help_text="Selecciona todas las imágenes del capítulo a la vez (Ctrl + Clic). Se crearán los paneles automáticamente."
    )

    class Meta:
        model = Chapter
        fields = '__all__'

    def save(self, commit=True):
        # Primero guardamos el capítulo (padre)
        chapter = super().save(commit=commit)
        
        # Si la operación fue exitosa (commit=True), procesamos las imágenes
        if commit and self.files:
            # getlist recupera TODAS las imágenes, no solo la última
            images = self.files.getlist('imagenes_masivas')
            
            if images:
                # Calculamos el número de página inicial para no sobreescribir
                inicio = chapter.panels.count() + 1
                
                for i, img in enumerate(images):
                    Panel.objects.create(
                        chapter=chapter,
                        image=img,
                        page_number=inicio + i
                    )
        
        return chapter

# --- 3. CONFIGURACIÓN DE VISTAS (Inlines) ---

class PanelInline(admin.TabularInline):
    model = Panel
    extra = 0  # No muestra filas vacías extra
    fields = ('image', 'page_number')
    ordering = ('page_number',)

class ArcInline(admin.TabularInline):
    model = Arc
    extra = 0

# --- 4. REGISTRO DE MODELOS ---

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    form = ChapterAdminForm  # Conectamos nuestro formulario especial
    inlines = [PanelInline]  # Muestra los paneles existentes abajo
    list_display = ('title', 'manga', 'chapter_number', 'arc')
    list_filter = ('manga',)
    search_fields = ('title', 'manga__titulo')
    autocomplete_fields = ['manga'] # Opcional: mejora la búsqueda si tienes muchos mangas

@admin.register(Manga)
class MangaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'owner')
    search_fields = ('titulo', 'autor')
    inlines = [ArcInline]

# Registro simple para los demás
admin.site.register(Panel)
admin.site.register(Arc)