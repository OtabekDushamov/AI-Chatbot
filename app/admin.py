from django.contrib import admin
from .models import Assistant, Chat, ChatMessage


@admin.register(Assistant)
class AssistantAdmin(admin.ModelAdmin):
    list_display = ['name', 'mode_id', 'assistant_id', 'mode', 'created_at']
    list_filter = ['mode', 'created_at']
    search_fields = ['name', 'mode_id', 'assistant_id', 'description']
    readonly_fields = ['assistant_id', 'created_at', 'updated_at']


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'assistant', 'user', 'session_key', 'is_active', 'last_activity']
    list_filter = ['assistant__mode', 'is_active', 'created_at', 'last_activity']
    search_fields = ['title', 'thread_id', 'user__username', 'session_key']
    readonly_fields = ['thread_id', 'created_at', 'updated_at', 'last_activity']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assistant', 'user')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'chat', 'role', 'created_at']
    list_filter = ['role', 'created_at', 'chat__assistant__mode']
    search_fields = ['content', 'chat__title', 'chat__user__username']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('chat', 'chat__assistant', 'chat__user')
