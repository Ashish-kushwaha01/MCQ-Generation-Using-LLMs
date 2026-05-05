from django.shortcuts import render
from .summarize import extract_transcript, scrape_web_content, generate_summary
import re

def summarize_content(request):
    context = {}
    if request.method == "POST":
        url = request.POST.get("url")
        
        # Detect if it's a YouTube URL
        is_youtube = 'youtube.com' in url or 'youtu.be' in url
        
        if is_youtube:
            content = extract_transcript(url)
            is_video = True
            # Extract video ID for thumbnail
            video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
            if video_id_match:
                context['video_id'] = video_id_match.group(1)
        else:
            content = scrape_web_content(url)
            is_video = False

        if "Error" not in content:
            summary = generate_summary(content, is_video=is_video)
            
            context.update({
                "url": url,
                "is_video": is_video,
                "raw_content": content,
                "summary": summary
            })
        else:
            context["error"] = content

    return render(
        request,
        "summarizer/universal_summarizer.html",
        context
    )
