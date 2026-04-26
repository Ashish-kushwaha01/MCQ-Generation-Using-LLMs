from django.db import models
# from autoslug import AutoSlugField
from django.contrib.auth.models import User

# Create your models here.

class Test_Upload(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    subject = models.CharField(max_length=200,null=True,blank=True)
    json_file = models.FileField(upload_to='tests/json_data/',null=True,blank=True)
    json_data = models.JSONField(null=True, blank=True, help_text="Paste JSON content directly here, or upload a JSON file above.")
    duration = models.IntegerField()  # duration in minutes
    total_questions = models.IntegerField()
    test_slug = models.SlugField(unique=True, blank=True, null=True)

    def __str__(self):
        return self.title
    
class Question(models.Model):
    test = models.ForeignKey(Test_Upload, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    topic = models.CharField(max_length=255, blank=True, null=True) # New field for question topic
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_option = models.CharField(max_length=1,choices=[
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D')
        ])  # 'A', 'B', 'C', or 'D'

    def __str__(self):
        return self.question[:50]  # Return the first 50 characters of the question for display purposes
    
    
class UserTestAttempt(models.Model):
    user = models.ForeignKey(User , on_delete=models.CASCADE)
    test = models.ForeignKey("Test_Upload", on_delete=models.CASCADE)
    
    total = models.IntegerField(default=0)
    correct= models.IntegerField(default=0)
    incorrect = models.IntegerField(default=0)
    skipped  = models.IntegerField(default=0)
    
    
    completed = models.BooleanField(default=False)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
 
    def __str__(self):
        return f"{self.user.username} - {self.test.title} ({self.started_at})"
    
    
class UserAnswer(models.Model):
    attempt = models.ForeignKey(UserTestAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1,blank=True,null=True)  # 'A', 'B', 'C', or 'D'
    
    class Meta:
        unique_together = ('attempt', 'question')  # Ensure a user can only answer a question once
        
    def __str__(self):
        return f"{self.attempt.user}.Q{self.question.id}: {self.question.id}"