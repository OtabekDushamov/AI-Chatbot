from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.safestring import mark_safe
import json
import os
from openai import OpenAI


def chat_page(request):
    return render(request, 'chat.html', {})


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

# Create your views here.
