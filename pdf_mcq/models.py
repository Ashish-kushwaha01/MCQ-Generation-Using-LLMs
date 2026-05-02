from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json
from cloudinary_storage.storage import RawMediaCloudinaryStorage

class PDFDocument(models.Model):
    """Store uploaded PDF files"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pdf_documents')
    file = models.FileField(upload_to='user_pdfs/', null=True, blank=True, storage=RawMediaCloudinaryStorage())
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.file_name} - {self.user.username}"


class MCQSession(models.Model):
    """Store each MCQ generation session"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mcq_sessions')
    session_id = models.CharField(max_length=100, unique=True)
    mcq_count = models.IntegerField(default=10)
    created_at = models.DateTimeField(default=timezone.now)
    time_taken = models.IntegerField(null=True, blank=True) # New field to store time taken in seconds
    
    def __str__(self):
        return f"Session {self.session_id} - {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class MCQQuestion(models.Model):
    """Store individual MCQ questions"""
    session = models.ForeignKey(MCQSession, on_delete=models.CASCADE, related_name='questions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mcq_questions')
    question_number = models.IntegerField()
    question_text = models.TextField()
    option_a = models.TextField()
    option_b = models.TextField()
    option_c = models.TextField()
    option_d = models.TextField()
    correct_answer = models.CharField(max_length=1)  # 'A', 'B', 'C', or 'D'
    explanation = models.TextField(blank=True, null=True)
    topic = models.CharField(max_length=255, blank=True, null=True) # New field for MCQ topic
    created_at = models.DateTimeField(default=timezone.now)
    
    def get_options_dict(self):
        """Return options as dictionary"""
        return {
            'A': self.option_a,
            'B': self.option_b,
            'C': self.option_c,
            'D': self.option_d
        }
    
    def get_correct_answer_text(self):
        """Get the full text of correct answer"""
        options = self.get_options_dict()
        return options.get(self.correct_answer, '')
    
    def to_json(self):
        """Convert to JSON format for frontend"""
        options_list = [
            {'letter': 'A', 'text': self.option_a, 'is_correct': self.correct_answer == 'A'},
            {'letter': 'B', 'text': self.option_b, 'is_correct': self.correct_answer == 'B'},
            {'letter': 'C', 'text': self.option_c, 'is_correct': self.correct_answer == 'C'},
            {'letter': 'D', 'text': self.option_d, 'is_correct': self.correct_answer == 'D'},
        ]
        
        correct_text = self.get_correct_answer_text()
        
        return {
            'id': self.id,
            'number': self.question_number,
            'question': self.question_text,
            'options': options_list,
            'correct_answer': f"{self.correct_answer}) {correct_text}",
            'correct_letter': self.correct_answer,
            'explanation': self.explanation or '',
            'topic': self.topic or 'Topic Analysis Required'
        }
    
    def __str__(self):
        return f"Q{self.question_number}: {self.question_text[:50]}..."


class UserAnswer(models.Model):
    """Store user's answers for each question"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_answers')
    question = models.ForeignKey(MCQQuestion, on_delete=models.CASCADE, related_name='user_answers')
    session = models.ForeignKey(MCQSession, on_delete=models.CASCADE, related_name='answers')
    selected_answer = models.CharField(max_length=1, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['user', 'question', 'session']
    
    def __str__(self):
        status = "✓" if self.is_correct else "✗" if self.selected_answer else "○"
        return f"{status} {self.user.username} - Q{self.question.question_number}"


class Feedback(models.Model):
    """Store user feedback on MCQ generation"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback')
    quality_rating = models.IntegerField(choices=[(1, '1 - Very Poor'), (2, '2 - Poor'), (3, '3 - Average'), (4, '4 - Good'), (5, '5 - Excellent')], null=True, blank=True)
    relevance_rating = models.CharField(max_length=3, choices=[('yes', 'Yes'), ('no', 'No')], null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Feedback from {self.user.username} on {self.submitted_at.strftime('%Y-%m-%d')}"