from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.conf import settings
from .utils import generate_otp
from django.utils import timezone
from .models import EmailOTP
from django.views.decorators.cache import never_cache



def signup(request):
    if request.method =="POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirmPassword')
        
        if password != confirm_password:
            return render(request,'signup.html',{'error':'Passwords do not match'})
        
        if User.objects.filter(email = email).exists():
            return render(request,'signup.html',{'error':'Email already exists'})
        
        otp = generate_otp()
        
        EmailOTP.objects.create(
            email = email,
            otp = otp
        )
        
        send_mail(
            subject="Your OTP",
            message=f'Your OTP is {otp}',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email,]
        )
        
        request.session['signup_email'] = email
        request.session['signup_password'] = password
        
        # login(request,user)

        return redirect('account:verify_otp')
    return render(request,'signup.html')


@never_cache
def verify_otp(request):
    email = request.session.get('signup_email')
    password = request.session.get('signup_password')

    if not email or not password:
        return redirect('account:signup')

    if request.method == 'POST':
        user_otp = request.POST.get('user_otp')

        otp_obj = EmailOTP.objects.filter(
            email=email,
            is_verified=False
        ).last()

        if not otp_obj:
            return redirect('account:signup')

        if otp_obj.is_expired():
            return render(request,'verify_otp.html',{'error':'OTP expired'})

        otp_obj.attempts += 1
        otp_obj.save()

        if otp_obj.attempts > 5:
            otp_obj.is_verified = True
            otp_obj.save()
            return render(request,'verify_otp.html',{'error':'Too many attempts'})

        if otp_obj.otp != user_otp:
            return render(request,'verify_otp.html',{'error':'Invalid OTP'})

        otp_obj.is_verified = True
        otp_obj.save()

        if User.objects.filter(email=email).exists():
            return redirect('account:login')

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        login(request, user)

        request.session.pop('signup_email', None)
        request.session.pop('signup_password', None)

        return redirect('dashboard')

    return render(request,'verify_otp.html')

    

def login_view(request):
    if request.method == "POST":
        email = request.POST.get('username')
        password = request.POST.get('password')
        
        print(f"Username: {email}, Password: {password}")  # Debugging line
        
        user = authenticate(request,username=email,password = password)
        
        if user is not None:
            login(request,user)
            return redirect('dashboard')
        else:
            return render(request,'login.html',{'error':'Invalid email or password'})
    return render(request,'login.html')


def logout_view(request):
    request.session.flush()
    return redirect('dashboard')