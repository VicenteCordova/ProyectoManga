from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'has_avatar', 'id')
    search_fields = ('user__username', 'user__email')
    list_filter = ('user__is_active',)

    def has_avatar(self, obj):
        return bool(obj.avatar)
    has_avatar.boolean = True
    has_avatar.short_description = "¿Tiene Avatar?"