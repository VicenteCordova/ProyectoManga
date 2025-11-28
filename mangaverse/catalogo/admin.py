from django import forms
from django.contrib import admin
from .models import Manga, Chapter, Panel, Arc

class AdminMultiFileInput(forms.ClearableFileInput):
    """
    Widget personalizado que permite la selección múltiple de archivos en el panel de administración.
    
    Habilita el atributo HTML 'multiple' en el input de archivos, necesario para
    la funcionalidad de carga masiva de paneles.
    """
    allow_multiple_selected = True

class ChapterAdminForm(forms.ModelForm):
    """
    Formulario personalizado para la administración del modelo Chapter.
    
    Introduce un campo virtual 'imagenes_masivas' que no existe en el modelo,
    permitiendo al administrador subir múltiples imágenes simultáneamente
    para crear los objetos Panel correspondientes automáticamente.
    """
    imagenes_masivas = forms.FileField(
        widget=AdminMultiFileInput(attrs={'multiple': True}), 
        label="Subir Múltiples Paneles",
        required=False,
        help_text="Selecciona todas las imágenes (Ctrl + Clic)."
    )
    
    class Meta:
        model = Chapter
        fields = '__all__'

    def save(self, commit=True):
        """
        Sobrescribe el método save para procesar la carga masiva.
        
        Guarda primero la instancia del Capítulo y luego itera sobre las imágenes
        subidas en 'imagenes_masivas' para crear instancias de Panel vinculadas.
        """
        # Guardamos la instancia del capítulo primero
        chapter = super().save(commit=commit)
        
        # Si se guardó correctamente y hay archivos en el request
        if commit and self.files:
            images = self.files.getlist('imagenes_masivas')
            if images:
                # Calculamos el número de página inicial para no sobrescribir
                inicio = chapter.panels.count() + 1
                
                # Creamos un objeto Panel por cada imagen subida
                for i, img in enumerate(images):
                    Panel.objects.create(chapter=chapter, image=img, page_number=inicio + i)
        
        return chapter

class PanelInline(admin.TabularInline):
    """
    Configuración para la edición en línea (Inline) de Paneles.
    
    Permite visualizar y editar los paneles (páginas) directamente dentro
    de la página de edición de un Capítulo.
    """
    model = Panel
    extra = 0  # No muestra formularios vacíos extra por defecto
    fields = ('image', 'page_number')

class ArcInline(admin.TabularInline):
    """
    Configuración para la edición en línea (Inline) de Arcos.
    
    Permite gestionar los arcos argumentales directamente desde la página
    de edición del Manga principal.
    """
    model = Arc
    extra = 0

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo Chapter.
    
    Integra el formulario de carga masiva y la gestión en línea de paneles.
    """
    form = ChapterAdminForm
    inlines = [PanelInline]
    list_display = ('title', 'manga', 'chapter_number', 'arc')
    list_filter = ('manga',)
    search_fields = ('title', 'manga__titulo')

@admin.register(Manga)
class MangaAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo Manga.
    
    Permite la gestión de Arcos asociados directamente desde esta vista.
    """
    list_display = ('titulo', 'autor', 'owner')
    search_fields = ('titulo', 'autor')
    inlines = [ArcInline]

# Registros simples para acceso directo si fuera necesario
admin.site.register(Panel)
admin.site.register(Arc)