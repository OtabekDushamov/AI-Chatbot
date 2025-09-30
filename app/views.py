from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.safestring import mark_safe
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
import json
import os
from openai import OpenAI
from .modes import get_assistant_prompt, list_modes as modes_catalog, get_assistant_meta
from .models import Assistant, Chat, ChatMessage


def modes_page(request):
    return render(request, 'modes.html', {})


def create_chat(request):
    """Create a new chat with the selected assistant or reuse existing one"""
    assistant_id = request.GET.get('assistant_id')
    if not assistant_id:
        return redirect('modes_page')
    
    try:
        assistant = Assistant.objects.get(mode_id=assistant_id)
    except Assistant.DoesNotExist:
        return redirect('modes_page')
    
    user = request.user if request.user.is_authenticated else None
    session_key = request.session.session_key
    
    # Ensure session exists
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    
    # Check if user/session already has a thread with this assistant
    existing_thread_id = None
    try:
        if user:
            existing_chat = Chat.objects.filter(user=user, assistant=assistant).order_by('-created_at').first()
        else:
            existing_chat = Chat.objects.filter(session_key=session_key, assistant=assistant).order_by('-created_at').first()
        
        if existing_chat:
            existing_thread_id = existing_chat.thread_id
        
    except Chat.DoesNotExist:
        pass
    
    # Create new chat (always create new chat record)
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    if existing_thread_id:
        # Reuse existing thread
        openai_thread_id = existing_thread_id
    else:
        # Create new thread
        openai_thread = client.beta.threads.create()
        openai_thread_id = openai_thread.id
    
    # Create new chat in database
    chat = Chat.objects.create(
        assistant=assistant,
        user=user,
        session_key=session_key if not user else None,
        thread_id=openai_thread_id,
        title="New Chat"
    )
    
    return redirect('chat_detail', chat_id=chat.id)


def chat_detail(request, chat_id):
    """Display a specific chat with its history"""
    chat = get_object_or_404(Chat, id=chat_id)
    
    # Check if user has access to this chat
    user = request.user if request.user.is_authenticated else None
    session_key = request.session.session_key
    
    if user and chat.user != user:
        return redirect('modes_page')
    elif not user and chat.session_key != session_key:
        return redirect('modes_page')
    
    # Get chat messages
    messages = chat.messages.all()
    
    context = {
        'chat': chat,
        'messages': messages,
        'assistant': chat.assistant,
    }
    
    return render(request, 'chat.html', context)


@csrf_exempt
@require_POST
def chat_api(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    message = payload.get('message')
    if not message or not isinstance(message, str):
        return HttpResponseBadRequest('message must be a non-empty string')

    chat_id = payload.get('chat_id')
    if not chat_id:
        return HttpResponseBadRequest('chat_id is required')

    # Get chat
    try:
        chat = Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        return JsonResponse({'error': f'Chat {chat_id} not found'}, status=404)

    # Check if user has access to this chat
    user = request.user if request.user.is_authenticated else None
    session_key = request.session.session_key
    
    if user and chat.user != user:
        return JsonResponse({'error': 'Access denied'}, status=403)
    elif not user and chat.session_key != session_key:
        return JsonResponse({'error': 'Access denied'}, status=403)

    api_key = settings.OPENAI_API_KEY
    if not api_key:
        return JsonResponse({'error': 'Server missing OPENAI_API_KEY'}, status=500)

    client = OpenAI(api_key=api_key)

    try:
        # Store user message in database
        user_message = ChatMessage.objects.create(
            chat=chat,
            role='user',
            content=message
        )
        
        # Update chat title if it's the first message
        if chat.title == "New Chat" and not chat.messages.filter(role='assistant').exists():
            chat.title = message[:50] + "..." if len(message) > 50 else message
            chat.save()
        
        # Add user message to OpenAI thread
        client.beta.threads.messages.create(
            thread_id=chat.thread_id,
            role="user",
            content=message
        )
        
        # Run the assistant
        run = client.beta.threads.runs.create_and_poll(
            thread_id=chat.thread_id,
            assistant_id=chat.assistant.assistant_id
        )
        
        if run.status == 'completed':
            # Get the latest assistant message
            messages = client.beta.threads.messages.list(
                thread_id=chat.thread_id,
                order="desc",
                limit=1
            )
            
            if messages.data:
                content = messages.data[0].content[0].text.value
                
                # Store assistant message in database
                assistant_message = ChatMessage.objects.create(
                    chat=chat,
                    role='assistant',
                    content=content
                )
                
                return JsonResponse({'reply': content})
            else:
                return JsonResponse({'error': 'No response from assistant'}, status=500)
        else:
            return JsonResponse({'error': f'Assistant run failed with status: {run.status}'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def list_modes(request):
    if request.method != 'GET':
        return HttpResponseBadRequest('Only GET allowed')
    return JsonResponse({'modes': modes_catalog()})

# Create your views here.
