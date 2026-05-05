from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from .models import AudioGeneration
from .audio_logic import generate_audio_from_text, generate_content_for_audio
import uuid

@login_required(login_url='account:login')
def audio_generator_view(request):
    if request.method == 'POST':
        topic = request.POST.get('topic')
        style = request.POST.get('style')
        duration = int(request.POST.get('duration', 1))
        voice = request.POST.get('voice')
        language = request.POST.get('language')

        try:
            # 1. Generate content script using Gemini
            script = generate_content_for_audio(topic, style, duration)
            
            # 2. Convert script to audio using Sarvam AI
            audio_data = generate_audio_from_text(script, language_code=language, speaker=voice)
            
            # 3. Save to database
            generation = AudioGeneration(
                user=request.user,
                topic=topic,
                style=style,
                duration=duration,
                voice=voice,
                language=language,
                script=script
            )
            
            filename = f"audio_{uuid.uuid4().hex}.wav"
            generation.audio_file.save(filename, ContentFile(audio_data))
            generation.save()
            
            messages.success(request, "Audio generated successfully!")
            return redirect('ai_audio:audio_generator')
            
        except Exception as e:
            messages.error(request, f"Error generating audio: {str(e)}")
            return redirect('ai_audio:audio_generator')

    generations = AudioGeneration.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'generations': generations
    }
    return render(request, 'ai_audio/audio_generator.html', context)
