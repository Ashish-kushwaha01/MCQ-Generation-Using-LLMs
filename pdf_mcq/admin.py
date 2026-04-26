from django.contrib import admin
from .models import PDFDocument, MCQSession, MCQQuestion, UserAnswer, Feedback

class PDFDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'file_name', 'file_size', 'uploaded_at')
    list_filter = ('user', 'uploaded_at')
    search_fields = ('file_name', 'user__username')
    readonly_fields = ('uploaded_at',)

class MCQSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'session_id', 'user', 'mcq_count', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('session_id', 'user__username')
    readonly_fields = ('created_at',)

class MCQQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question_number', 'question_text_short', 'session', 'user', 'correct_answer', 'topic', 'created_at')
    list_filter = ('user', 'session', 'topic', 'created_at')
    search_fields = ('question_text', 'topic')
    readonly_fields = ('created_at',)
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question'

class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'question', 'session', 'selected_answer', 'is_correct', 'answered_at')
    list_filter = ('user', 'is_correct', 'answered_at')
    search_fields = ('user__username', 'question__question_text')
    readonly_fields = ('answered_at',)

class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'quality_rating', 'relevance_rating', 'submitted_at')
    list_filter = ('user', 'quality_rating', 'relevance_rating', 'submitted_at')
    search_fields = ('user__username', 'description')
    readonly_fields = ('submitted_at',)

# Register all models
admin.site.register(PDFDocument, PDFDocumentAdmin)
admin.site.register(MCQSession, MCQSessionAdmin)
admin.site.register(MCQQuestion, MCQQuestionAdmin)
admin.site.register(UserAnswer, UserAnswerAdmin)
admin.site.register(Feedback, FeedbackAdmin)