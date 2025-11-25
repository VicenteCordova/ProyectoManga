from django.db import models
from django.utils.text import slugify
from django.conf import settings  # Importar settings para usar el usuario

class Manga(models.Model):
    # Nuevo campo: Dueño del manga
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='mangas',
        null=True, blank=True  # Permitimos null temporalmente para la migración
    )
    
    titulo = models.CharField(max_length=200)
    autor = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, help_text="Sinopsis")
    portada = models.ImageField(upload_to='portadas/', blank=True, null=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

# NUEVO MODELO: ARCO
class Arc(models.Model):
    manga = models.ForeignKey(Manga, related_name='arcs', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name="Título del Arco")
    order = models.PositiveIntegerField(default=1, verbose_name="Orden")

    class Meta:
        ordering = ['order']
        unique_together = ('manga', 'title')

    def __str__(self):
        return f"{self.manga.titulo} - {self.title}"

class Chapter(models.Model):
    manga = models.ForeignKey(Manga, related_name='chapters', on_delete=models.CASCADE)
    # Nuevo campo opcional: Arco
    arc = models.ForeignKey(Arc, related_name='chapters', on_delete=models.SET_NULL, null=True, blank=True)
    
    title = models.CharField(max_length=255)
    chapter_number = models.PositiveIntegerField()
    slug = models.SlugField(max_length=255, blank=True)

    class Meta:
        ordering = ['chapter_number']
        unique_together = ('manga', 'slug')

    def __str__(self):
        return f"{self.manga.titulo} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"capitulo-{self.chapter_number}")
        super().save(*args, **kwargs)

class Panel(models.Model):
    chapter = models.ForeignKey(Chapter, related_name='panels', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='manga_panels/')
    page_number = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['page_number']

    def get_upload_path(instance, filename):
        return f'manga_panels/{instance.chapter.manga.slug}/{instance.chapter.slug}/{filename}'
    image.upload_to = get_upload_path