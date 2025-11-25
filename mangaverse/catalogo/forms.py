from django import forms
from django.forms import inlineformset_factory
from django.forms.widgets import ClearableFileInput   
from .models import Manga, Chapter

#  Widget que sí acepta múltiples archivos
class MultiFileInput(ClearableFileInput):
    allow_multiple_selected = True

class MangaForm(forms.ModelForm):
    class Meta:
        model = Manga
        exclude = ['slug']

# Campo extra  para subir varias imágenes por capítulo
class ChapterForm(forms.ModelForm):
    images = forms.FileField(
        widget=MultiFileInput(attrs={'multiple': True}),
        required=False,
        label="Páginas / Imágenes"
    )

    class Meta:
        model = Chapter
        fields = ['title', 'chapter_number']  # ajusta a tus campos reales

ChapterFormSet = inlineformset_factory(
    Manga, Chapter,
    form=ChapterForm,
    extra=0,          # 0 o 1 una fila inicial
    can_delete=True
)
