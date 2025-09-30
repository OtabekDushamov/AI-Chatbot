from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.safestring import mark_safe
import json
import os
from openai import OpenAI
from .modes import get_assistant_prompt, list_modes as modes_catalog, get_assistant_meta


def chat_page(request):
    return render(request, 'chat.html', {})


def modes_page(request):
    return render(request, 'modes.html', {})


@csrf_exempt
@require_POST
def chat_api(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    messages = payload.get('messages')
    if not isinstance(messages, list):
        return HttpResponseBadRequest('messages must be a list')

    # Optional assistant selection
    assistant_id = payload.get('assistant_id')
    base_prompt = get_assistant_prompt(assistant_id) if assistant_id else None
    scope_guard = None
    if assistant_id:
        meta = get_assistant_meta(assistant_id)
        topic_name = meta.get('name') or 'this assistant\'s domain'
        scope_guard = (
            f"You must stay strictly within the topic of '{topic_name}'. "
            "If a user asks something outside of scope, briefly decline and suggest switching to a more suitable assistant."
        )
        system_prompt = (base_prompt + ' ' + scope_guard) if base_prompt else scope_guard
    else:
        system_prompt = None

    # Ensure system prompt is the first message if provided
    if system_prompt:
        if not messages or messages[0].get('role') != 'system':
            messages = [{'role': 'system', 'content': system_prompt}] + messages
        else:
            # Prepend our assistant system prompt before existing system if needed
            messages = [{'role': 'system', 'content': system_prompt}] + messages

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return JsonResponse({'error': 'Server missing OPENAI_API_KEY'}, status=500)

    model = payload.get('model') or os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

    client = OpenAI(api_key=api_key)

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=payload.get('temperature', 0.7),
        )
        content = completion.choices[0].message.content
        return JsonResponse({'reply': content})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def list_modes(request):
    if request.method != 'GET':
        return HttpResponseBadRequest('Only GET allowed')
    return JsonResponse({'modes': modes_catalog()})

# Create your views here.
