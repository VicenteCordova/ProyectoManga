from django import forms
from django.contrib import admin
from .models import Manga, Chapter, Panel, Arc

# --- WIDGET NECESARIO (Para evitar el ValueError en el Admin) ---
class AdminMultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

# 1. Formulario Especial para el ADMIN
class ChapterAdminForm(forms.ModelForm):
    # Campo extra para la interfaz del admin
    imagenes_masivas = forms.FileField(
        # Usamos nuestro widget personalizado aquí
        widget=AdminMultiFileInput(attrs={'multiple': True}),
        label="Subir Múltiples Paneles (Selecciona varios archivos)",
        required=False,
        help_text="Selecciona todas las imágenes del capítulo aquí (Ctrl + Clic). Se guardarán como Paneles automáticamente."
    )

    class Meta:
        model = Chapter
        fields = '__all__'

    def save(self, commit=True):
        # Guardamos el capítulo primero
        chapter = super().save(commit=commit)
        
        # Si se guardó correctamente, procesamos las imágenes
        if commit and self.files:
            # Recuperamos la lista de archivos usando el nombre del campo
            images = self.files.getlist('imagenes_masivas')
            
            # Contamos cuántos paneles hay ya para seguir la numeración
            inicio_paginas = chapter.panels.count() + 1
            
            for i, img in enumerate(images):
                Panel.objects.create(
                    chapter=chapter,
                    image=img,
                    page_number=inicio_paginas + i
                )
        
        return chapter

# 2. Configuración de los Inlines (para ver los paneles subidos)
class PanelInline(admin.TabularInline):
    model = Panel
    extra = 0  # No mostramos filas vacías por defecto
    fields = ('image', 'page_number')
    # readonly_fields = ('image_preview',) # Opcional si agregaste el método en el modelo

class ArcInline(admin.TabularInline):
    model = Arc
    extra = 0

# 3. Registro de Modelos en el Admin
@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    form = ChapterAdminForm  # Conectamos el formulario especial
    inlines = [PanelInline]  # Mostramos los paneles abajo
    list_display = ('title', 'manga', 'chapter_number', 'arc')
    list_filter = ('manga',)
    search_fields = ('title', 'manga__titulo')

@admin.register(Manga)
class MangaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'owner')
    search_fields = ('titulo', 'autor')
    inlines = [ArcInline] # Permite ver/editar arcos dentro del Manga

# Registramos los demás modelos simples
admin.site.register(Panel)
admin.site.register(Arc)