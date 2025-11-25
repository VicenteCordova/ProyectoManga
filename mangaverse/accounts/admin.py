from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # Mostramos el usuario y si tiene biografía
    list_display = ('user', 'has_avatar', 'id')
    # Buscador por nombre de usuario o email
    search_fields = ('user__username', 'user__email')
    # Filtro lateral (opcional)
    list_filter = ('user__is_active',)

    # Método helper para ver rápido si tiene foto en la lista
    def has_avatar(self, obj):
        return bool(obj.avatar)
    has_avatar.boolean = True
    has_avatar.short_description = "¿Tiene Avatar?"