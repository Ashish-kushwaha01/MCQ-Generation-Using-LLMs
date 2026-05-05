from django.db import models
from django.contrib.auth.models import User

class AudioGeneration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.CharField(max_length=255)
    style = models.CharField(max_length=100)
    duration = models.IntegerField()  # in minutes
    voice = models.CharField(max_length=50)
    language = models.CharField(max_length=20)
    script = models.TextField()
    audio_file = models.FileField(upload_to='generated_audio/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.topic} ({self.style}) - {self.user.username}"
