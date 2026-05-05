from django.contrib import admin
from .models import AudioGeneration

@admin.register(AudioGeneration)
class AudioGenerationAdmin(admin.ModelAdmin):
    list_display = ('topic', 'user', 'style', 'voice', 'language', 'created_at')
    list_filter = ('style', 'language', 'voice', 'created_at')
    search_fields = ('topic', 'script', 'user__username')
    readonly_fields = ('created_at',)
