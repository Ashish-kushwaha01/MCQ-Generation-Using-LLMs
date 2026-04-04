from django.db import models

# class MCQTest(models.Model):
#     mcq_count = models.IntegerField()
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     def __str__(self):
#         return f"({self.mcq_count})"
    
    
# class MCQQuestion(models.Model):
#     test= models.ForeignKey(MCQTest,on_delete=models.CASCADE,related_name='questions')
    
#     question_text = models.TextField()
#     option_a = models.TextField()
#     option_b = models.TextField()
#     option_c = models.TextField()
#     option_d = models.TextField()
    
#     correct_answer = models.CharField(max_length=1)
#     explanation= models.TextChoices()
    
#     def __str__(self):
#         return self.question_text[:50]