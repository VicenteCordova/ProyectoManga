# catalogo/models.py
from django.db import models
from django.utils.text import slugify # Para generar slugs automáticamente

class Manga(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, help_text="Sinopsis")
    portada = models.ImageField(upload_to='portadas/', blank=True, null=True)
    # NUEVO CAMPO SLUG:
    slug = models.SlugField(max_length=255, unique=True, blank=True, help_text="URL amigable (se genera automáticamente si se deja vacío)")

    def __str__(self):
        return self.titulo

    # Sobreescribimos save para generar el slug automáticamente si está vacío
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

# NUEVO MODELO CHAPTER
class Chapter(models.Model):
    manga = models.ForeignKey(Manga, related_name='chapters', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    chapter_number = models.PositiveIntegerField()
    slug = models.SlugField(max_length=255, blank=True, help_text="URL amigable (ej: capitulo-1)")

    class Meta:
        ordering = ['chapter_number'] # Ordena capítulos por número
        unique_together = ('manga', 'slug') # El slug debe ser único para cada manga

    def __str__(self):
        return f"{self.manga.titulo} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"capitulo-{self.chapter_number}")
        super().save(*args, **kwargs)

# NUEVO MODELO PANEL
class Panel(models.Model):
    chapter = models.ForeignKey(Chapter, related_name='panels', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='manga_panels/') # Sube a media/manga_panels/
    page_number = models.PositiveIntegerField()

    class Meta:
        ordering = ['page_number'] # Ordena los paneles/páginas

    def __str__(self):
        return f"Panel {self.page_number} de {self.chapter}"

    # Ajustamos upload_to dinámicamente (Opcional pero recomendado)
    def get_upload_path(instance, filename):
        return f'manga_panels/{instance.chapter.manga.slug}/{instance.chapter.slug}/{filename}'

    image.upload_to = get_upload_path