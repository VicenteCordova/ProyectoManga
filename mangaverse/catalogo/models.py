from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse

# --- DEFINICIÓN DE GÉNEROS (IMPORTANTE: Fuera de la clase) ---
GENEROS = [
    ('shonen', 'Shonen'),
    ('seinen', 'Seinen'),
    ('shojo', 'Shojo'),
    ('josei', 'Josei'),
    ('isekai', 'Isekai'),
    ('mecha', 'Mecha'),
    ('slice_of_life', 'Slice of Life'),
    ('terror', 'Terror'),
    ('accion', 'Acción'),
    ('aventura', 'Aventura'),
    ('comedia', 'Comedia'),
    ('drama', 'Drama'),
    ('fantasia', 'Fantasía'),
    ('misterio', 'Misterio'),
    ('psicologico', 'Psicológico'),
    ('romance', 'Romance'),
    ('sci_fi', 'Ciencia Ficción'),
    ('deportes', 'Deportes'),
]

class Manga(models.Model):
    """
    Representa una obra de manga.
    Vinculada a un usuario (owner) para gestión de permisos.
    """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='mangas',
        verbose_name="Propietario"
    )
    titulo = models.CharField(max_length=200, verbose_name="Título")
    autor = models.CharField(max_length=100, verbose_name="Autor")
    
    # Campo de Género usando la lista definida arriba
    genero = models.CharField(
        max_length=50, 
        choices=GENEROS, 
        default='shonen', 
        verbose_name="Género",
        help_text="Categoría principal del manga"
    )
    
    descripcion = models.TextField(blank=True, verbose_name="Sinopsis", help_text="Breve descripción de la trama.")
    portada = models.ImageField(upload_to='portadas/', blank=True, null=True, verbose_name="Portada Oficial")
    slug = models.SlugField(max_length=255, unique=True, blank=True, help_text="Identificador único para URLs.")

    class Meta:
        verbose_name = "Manga"
        verbose_name_plural = "Mangas"
        ordering = ['titulo']

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        """Genera slug automáticamente si no existe."""
        if not self.slug:
            base_slug = slugify(self.titulo)
            unique_slug = base_slug
            num = 1
            while Manga.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('catalogo:manga-detail', kwargs={'manga_slug': self.slug})


class Arc(models.Model):
    """
    Agrupa capítulos en arcos argumentales (Sagas).
    """
    manga = models.ForeignKey(Manga, related_name='arcs', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name="Título del Arco")
    order = models.PositiveIntegerField(default=1, verbose_name="Orden de Lectura")

    class Meta:
        ordering = ['order']
        verbose_name = "Arco"
        verbose_name_plural = "Arcos"

    def __str__(self):
        return f"{self.manga.titulo} - {self.title}"


class Chapter(models.Model):
    """
    Representa un capítulo individual.
    """
    manga = models.ForeignKey(Manga, related_name='chapters', on_delete=models.CASCADE)
    arc = models.ForeignKey(Arc, related_name='chapters', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Arco")
    title = models.CharField(max_length=255, verbose_name="Título del Capítulo")
    chapter_number = models.PositiveIntegerField(verbose_name="Número")
    slug = models.SlugField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['chapter_number']
        unique_together = ('manga', 'chapter_number')

    def __str__(self):
        return f"Cap. {self.chapter_number}: {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"capitulo-{self.chapter_number}")
        super().save(*args, **kwargs)


class Panel(models.Model):
    """
    Imagen individual (página) de un capítulo.
    """
    chapter = models.ForeignKey(Chapter, related_name='panels', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='manga_panels/')
    page_number = models.PositiveIntegerField(verbose_name="Número de Página")

    class Meta:
        ordering = ['page_number']

    def get_upload_path(instance, filename):
        return f'manga_panels/{instance.chapter.manga.slug}/{instance.chapter.slug}/{filename}'
    
    image.upload_to = get_upload_path