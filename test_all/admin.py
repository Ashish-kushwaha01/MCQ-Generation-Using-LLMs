from django.contrib import admin
from .models import Test_Upload,UserTestAttempt,UserAnswer
from .models import Question

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0

# Register your models here.

class TestUploadAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'duration',
        'total_questions',
        'test_slug'
    )
    prepopulated_fields = {'test_slug': ('title',)}
    inlines = [QuestionInline] 


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'test', 'correct_option')
    list_filter = ('test',)
    
    
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