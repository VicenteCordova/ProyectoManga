from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    # Relación 1 a 1 con el Usuario estándar de Django
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    
    # Campos extra
    avatar = models.ImageField(upload_to='avatars/', default='images/sinfondo.png', blank=True)
    bio = models.TextField(max_length=500, blank=True, help_text="Cuéntanos algo sobre ti")
    
    # Sistema de Favoritos: Relación Muchos-a-Muchos con Manga
    # Usamos 'catalogo.Manga' como string para evitar errores de importación circular
    favorites = models.ManyToManyField('catalogo.Manga', related_name='favorited_by', blank=True)

    def __str__(self):
        return f'Perfil de {self.user.username}'

# --- SEÑALES MÁGICAS ---
# Esto asegura que si creas un usuario desde el Admin o Registro, 
# se cree su Profile automáticamente.
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    # Guarda el perfil cuando se guarda el usuario
    instance.profile.save()