from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Assistant(models.Model):
    """Stores OpenAI assistant configurations"""
    mode_id = models.CharField(max_length=255, unique=True, default='', help_text="Mode identifier (e.g., teacher_tutor)")
    assistant_id = models.CharField(max_length=255, unique=True, help_text="OpenAI assistant ID")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    system_prompt = models.TextField()
    mode = models.CharField(max_length=50, help_text="Mode category (professional, personal, creative)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['mode', 'name']

    def __str__(self):
        return f"{self.name} ({self.mode})"


class Chat(models.Model):
    """Stores chat sessions with assistants"""
    assistant = models.ForeignKey(Assistant, on_delete=models.CASCADE)
    
    # User association (for authenticated users)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Session association (for anonymous users)
    session_key = models.CharField(max_length=40, null=True, blank=True, help_text="Django session key")
    
    # OpenAI thread ID for this chat
    thread_id = models.CharField(max_length=255, help_text="OpenAI thread ID")
    
    # Chat metadata
    title = models.CharField(max_length=255, blank=True, help_text="Chat title (auto-generated from first message)")
    is_active = models.BooleanField(default=True, help_text="Whether this chat is currently active")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'assistant']),
            models.Index(fields=['session_key', 'assistant']),
            models.Index(fields=['last_activity']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        if self.user:
            return f"Chat: {self.title or 'Untitled'} - {self.assistant.name} ({self.user.username})"
        else:
            return f"Chat: {self.title or 'Untitled'} - {self.assistant.name} (Session {self.session_key[:8]}...)"

    def save(self, *args, **kwargs):
        # Ensure either user or session_key is set, but not both
        if not self.user and not self.session_key:
            raise ValueError("Either user or session_key must be set")
        if self.user and self.session_key:
            raise ValueError("Cannot set both user and session_key")
        
        self.last_activity = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('chat_detail', kwargs={'chat_id': self.id})


class ChatMessage(models.Model):
    """Stores individual messages in a chat"""
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=[('user', 'User'), ('assistant', 'Assistant')])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chat', 'created_at']),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}... ({self.chat})"
