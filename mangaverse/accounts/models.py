from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    """
    Modelo que extiende la información del usuario estándar de Django.

    Actúa como una extensión del modelo User (OneToOne), permitiendo almacenar
    información adicional específica para la aplicación, como el avatar,
    una biografía corta y la lista de mangas favoritos.
    """
    # Relación 1 a 1 con el Usuario estándar de Django
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    
    # Campos extra
    avatar = models.ImageField(upload_to='avatars/', default='images/sinfondo.png', blank=True)
    bio = models.TextField(max_length=500, blank=True, help_text="Cuéntanos algo sobre ti")
    
    # Sistema de Favoritos: Relación Muchos-a-Muchos con Manga
    # Usamos 'catalogo.Manga' como string para evitar errores de importación circular
    favorites = models.ManyToManyField('catalogo.Manga', related_name='favorited_by', blank=True)
    # "symmetrical=False" significa que si yo te sigo, tú no me sigues automáticamente (como Instagram/Twitter)
    following = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)

    def __str__(self):
        """Retorna la representación en cadena del perfil, indicando a qué usuario pertenece."""
        return f'Perfil de {self.user.username}'

# --- SEÑALES (SIGNALS) PARA AUTOMATIZACIÓN ---

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta automáticamente después de que se guarda una instancia de User.

    Si el usuario ha sido creado recién (created=True), crea inmediatamente
    una instancia de Profile asociada a dicho usuario. Esto asegura que
    todo usuario registrado tenga un perfil listo para usar.
    """
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal que se ejecuta al guardar una instancia de User.

    Asegura que cualquier cambio que requiera guardar el perfil asociado
    se propague correctamente. Mantiene la consistencia entre User y Profile.
    """
    # Guarda el perfil cuando se guarda el usuario
    instance.profile.save()

# --- NUEVO: MODELO DE MENSAJERÍA ---
class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"De {self.sender} para {self.recipient}"