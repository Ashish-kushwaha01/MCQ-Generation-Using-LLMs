from django.contrib import admin
from django.core.exceptions import ValidationError # Import ValidationError
from .models import Test_Upload,UserTestAttempt,UserAnswer
from .models import Question
from .forms import TestUploadForm # Import the custom form

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0

# Register your models here.

class TestUploadAdmin(admin.ModelAdmin):
    form = TestUploadForm # Use the custom form
    list_display = (
        'title',
        'subject', # Added subject to list display
        'duration',
        'total_questions',
        'test_slug',
        'json_file', # Display the JSON file
        'json_data', # Display the JSON data field
    )
    fields = ('json_file', 'json_data', 'test_slug') # Only show these fields for input
    inlines = [QuestionInline] 

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'test', 'topic', 'correct_option') # Added topic
    list_filter = ('test', 'topic',) # Added topic

    
    
class UserTestAttemptAdmin(admin.ModelAdmin):
    list_display = ('user','test','total','correct','incorrect','skipped','completed','started_at','completed_at')
    
    list_filter = ('completed','test')
    
    search_fields = ('user__username','test__title')
    
    readonly_fields = ('user','test','total','started_at','completed_at')
    
    ordering = ('-completed_at',)
    
    
class UserAnswerAdmin(admin.ModelAdmin):
    list_display=('attempt','question','selected_option')
    list_filter = ('attempt__test',)
    search_fields = ('question__question',)
    
    
    
admin.site.register(Test_Upload, TestUploadAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(UserTestAttempt,UserTestAttemptAdmin)
admin.site.register(UserAnswer,UserAnswerAdmin)