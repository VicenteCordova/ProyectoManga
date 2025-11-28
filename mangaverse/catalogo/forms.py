from django import forms
from django.forms import inlineformset_factory
from .models import Manga, Chapter, Panel, Arc

class MultipleFileInput(forms.ClearableFileInput):
    """
    Widget personalizado que habilita el atributo 'multiple' en el input HTML de archivos.
    
    Permite al usuario seleccionar varios archivos simultáneamente en el explorador del sistema,
    necesario para la carga masiva de paneles (páginas) de un capítulo.
    """
    allow_multiple_selected = True

class MangaForm(forms.ModelForm):
    """
    Formulario para la creación y edición de la ficha técnica de un Manga.
    
    Gestiona los metadatos principales como título, autor, género, descripción y portada.
    Excluye campos de gestión interna como 'slug' y 'owner'.
    """
    class Meta:
        model = Manga
        exclude = ['slug', 'owner']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            'autor': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
            
            # Selector de género estilizado
            'genero': forms.Select(attrs={
                'class': 'form-select bg-dark text-white border-secondary', 
                'style': 'cursor: pointer;'
            }),
            
            'descripcion': forms.Textarea(attrs={'class': 'form-control bg-dark text-white border-secondary', 'rows': 3}),
            'portada': forms.FileInput(attrs={'class': 'form-control bg-dark text-white border-secondary'}),
        }

class ArcForm(forms.ModelForm):
    """
    Formulario para gestionar los Arcos argumentales (Sagas) de un Manga.
    
    Se utiliza principalmente para crear o editar la estructura narrativa.
    """
    class Meta:
        model = Arc
        fields = ['title', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'placeholder': 'Ej: Saga de East Blue'}),
            'order': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-secondary', 'style': 'width: 80px;'}),
        }

class ChapterForm(forms.ModelForm):
    """
    Formulario para la gestión de Capítulos.
    
    Incluye un campo virtual 'images' para manejar la subida de archivos múltiples
    (imágenes o PDF) que posteriormente se procesan como objetos Panel.
    """
    # Campo especial para subida múltiple; no se guarda directo en el modelo Chapter
    images = forms.FileField(
        required=False,
        label="Imágenes (Selecciona varias con Ctrl)",
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
        """
        Inicializa el formulario y filtra los arcos disponibles.
        
        Asegura que el campo 'arc' solo muestre opciones que pertenecen
        al mismo Manga que el Capítulo que se está editando/creando.
        """
        super().__init__(*args, **kwargs)
        if self.instance and getattr(self.instance, 'manga', None):
             self.fields['arc'].queryset = Arc.objects.filter(manga=self.instance.manga)

# Definición de FormSets para gestión en línea (utilizados en vistas complejas si es necesario)
ArcFormSet = inlineformset_factory(Manga, Arc, form=ArcForm, extra=1, can_delete=True)
ChapterFormSet = inlineformset_factory(Manga, Chapter, form=ChapterForm, extra=1, can_delete=True)