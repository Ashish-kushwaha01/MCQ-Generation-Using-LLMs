from django.contrib import admin
from .models import Register,EmailOTP


class RegisterAdmin(admin.ModelAdmin):
    list_display=('name', 'email')
    
class EmailOTPAdmin(admin.ModelAdmin):
    list_display=('email','otp','created_at','is_verified','attempts')


admin.site.register(Register,RegisterAdmin)

admin.site.register(EmailOTP,EmailOTPAdmin)
# Register your models here.
