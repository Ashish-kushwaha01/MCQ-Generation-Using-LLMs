from django.shortcuts import render
from .summarize import extract_transcript, generate_summary


def summarize_video(request):

    context = {}

    if request.method == "POST":

        video_url = request.POST.get("video_url")

        transcript = extract_transcript(video_url)

        if "Error" not in transcript:

            summary = generate_summary(transcript)

            video_id = video_url.split("v=")[-1].split("&")[0]

            context = {

                "video_url": video_url,
                "video_id": video_id,
                "transcript": transcript,
                "summary": summary

            }

        else:

            context["error"] = transcript

    return render(
        request,
        "summarizer/youtube_video.html",
        context
    )