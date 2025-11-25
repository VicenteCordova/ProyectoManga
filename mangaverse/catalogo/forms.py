from django import forms
from django.forms import inlineformset_factory
from .models import Manga, Chapter, Panel, Arc

# Widget para permitir selección múltiple en el navegador
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MangaForm(forms.ModelForm):
    class Meta:
        model = Manga
        exclude = ['slug', 'owner']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'autor': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control bg-dark text-white border-secondary', 'rows': 3}),
            'portada': forms.FileInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
        }

class ArcForm(forms.ModelForm):
    class Meta:
        model = Arc
        fields = ['title', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'placeholder': 'Ej: Saga de East Blue'}),
            'order': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'style': 'width: 80px;'}),
        }

class ChapterForm(forms.ModelForm):
    # Campo simple, delegamos el guardado a la vista
    images = forms.FileField(
        required=False,
        label="Páginas / Imágenes (Selecciona todas juntas)",
        widget=MultipleFileInput(attrs={
            'class': 'form-control bg-dark text-white border-secondary', 
            'multiple': True 
        })
    )

    class Meta:
        model = Chapter
        fields = ['title', 'chapter_number', 'arc']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'chapter_number': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'arc': forms.Select(attrs={'class': 'form-select bg-dark text-white border-secondary'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and getattr(self.instance, 'manga', None):
             self.fields['arc'].queryset = Arc.objects.filter(manga=self.instance.manga)

# Formsets
ArcFormSet = inlineformset_factory(
    Manga, Arc,
    form=ArcForm,
    extra=1,
    can_delete=True
)

ChapterFormSet = inlineformset_factory(
    Manga, Chapter,
    form=ChapterForm,
    extra=1,
    can_delete=True
)