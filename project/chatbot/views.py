from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services.chatbot import get_chat_response, reset_chat_session
from .services.gemini_config import SUBTOPIC_INSTRUCTIONS, DEFAULT_INSTRUCTION
# from .services.genchatbot import get_chat_response as get_gen_chat_response


def chat(request):
    """
    Renders the chatbot page and sets up session-based system instruction.
    """
    subtopic = request.GET.get('subtopic', None)
    instruction = SUBTOPIC_INSTRUCTIONS.get(subtopic, DEFAULT_INSTRUCTION)

    # Store selected instruction and reset chat state for this session
    request.session['system_instruction'] = instruction
    request.session['custom_history'] = []  # Optional: for your own use
    request.session.modified = True

    # Reset the global chatbot session (optional)
    reset_chat_session(instruction)

    return render(request, 'chatbot/chatbot.html', {"subtopic": subtopic or "General"})


@csrf_exempt
def chat_endpoint(request):
    if request.method == 'POST':
        try:
            user_message = request.POST.get('message', '').strip()
            if not user_message:
                return JsonResponse({'error': 'No message provided'}, status=400)

            # You can access session data if needed
            # system_instruction = request.session.get('system_instruction', DEFAULT_INSTRUCTION)

            # Use existing chatbot logic
            response = get_chat_response(user_message)
            return JsonResponse({'response': response})

        except Exception as e:
            import traceback
            print("Chat Error:", traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)



def general_chat(request):
    """
    Renders the general chatbot page.
    """
    # return render(request, 'chatbot/genchatbot.html')
    return JsonResponse({"error": "disabled"})


@csrf_exempt
def general_chat_endpoint(request):
    if request.method == 'POST':
        try:
            user_message = request.POST.get('message', '').strip()
            if not user_message:
                return JsonResponse({'error': 'No message provided'}, status=400)

            response = get_gen_chat_response(user_message)
            return JsonResponse({'response': response})

        except Exception as e:
            import traceback
            print("General Chat Error:", traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)
