from django.db import models
from django.utils import timezone
from datetime import timedelta

class Register(models.Model):
    name=models.CharField(max_length=100)
    email=models.EmailField(max_length=100)
    password=models.CharField(max_length=100)

    def __str__(self):
        return self.name

class EmailOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)
    
    def __str__(self):
        return f'{self.email}'
    