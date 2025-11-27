from django import forms
from django.contrib import admin
from .models import Manga, Chapter, Panel, Arc

class AdminMultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class ChapterAdminForm(forms.ModelForm):
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
        chapter = super().save(commit=commit)
        if commit and self.files:
            images = self.files.getlist('imagenes_masivas')
            if images:
                inicio = chapter.panels.count() + 1
                for i, img in enumerate(images):
                    Panel.objects.create(chapter=chapter, image=img, page_number=inicio + i)
        return chapter

class PanelInline(admin.TabularInline):
    model = Panel
    extra = 0
    fields = ('image', 'page_number')

class ArcInline(admin.TabularInline):
    model = Arc
    extra = 0

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    form = ChapterAdminForm
    inlines = [PanelInline]
    list_display = ('title', 'manga', 'chapter_number', 'arc')
    list_filter = ('manga',)
    search_fields = ('title', 'manga__titulo')

@admin.register(Manga)
class MangaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'owner')
    search_fields = ('titulo', 'autor')
    inlines = [ArcInline]

admin.site.register(Panel)
admin.site.register(Arc)