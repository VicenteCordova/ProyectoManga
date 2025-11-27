from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.urls import reverse

class Manga(models.Model):
    # Opciones de Género (Tupla: Valor BD, Valor Legible)
    GENEROS = [
        ('shonen', 'Shonen'),
        ('seinen', 'Seinen'),
        ('shojo', 'Shojo'),
        ('josei', 'Josei'),
        ('isekai', 'Isekai'),
        ('mecha', 'Mecha'),
        ('slice_of_life', 'Slice of Life'),
        ('terror', 'Terror'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='mangas',
        verbose_name="Propietario"
    )
    titulo = models.CharField(max_length=200, verbose_name="Título")
    autor = models.CharField(max_length=100, verbose_name="Autor")
    # NUEVO CAMPO: Género
    genero = models.CharField(max_length=20, choices=GENEROS, default='shonen', verbose_name="Género")
    
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

# --- (El resto de modelos: Arc, Chapter, Panel se quedan IGUAL) ---
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
    arc = models.ForeignKey(Arc, related_name='chapters', on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    chapter_number = models.PositiveIntegerField()
    slug = models.SlugField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True) # Campo que agregamos antes

    class Meta:
        ordering = ['chapter_number']
        unique_together = ('manga', 'chapter_number')

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