from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.core.mail import send_mail
from django.conf import settings
from .utils import generate_otp
from django.utils import timezone
from .models import EmailOTP
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from pdf_mcq.models import PDFDocument, MCQSession
from test_all.models import UserTestAttempt
from ai_audio.models import AudioGeneration



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

@login_required(login_url='account:login')
def profile_view(request):
    user = request.user
    
    # Fetch Data
    pdf_docs = PDFDocument.objects.filter(user=user).order_by('-uploaded_at')
    
    # Get MCQ sessions with aggregated counts
    mcq_sessions = MCQSession.objects.filter(user=user).order_by('-created_at')
    for session in mcq_sessions:
        answers = session.answers.all()
        session.correct_count = answers.filter(is_correct=True).count()
        session.incorrect_count = answers.filter(is_correct=False).exclude(Q(selected_answer__isnull=True) | Q(selected_answer='')).count()
        session.skipped_count = answers.filter(Q(selected_answer__isnull=True) | Q(selected_answer='')).count()
        # Handle cases where questions might not have answers yet
        total_q = session.questions.count()
        if answers.count() < total_q:
            session.skipped_count += (total_q - answers.count())

    test_attempts = UserTestAttempt.objects.filter(user=user).order_by('-started_at')
    audio_results = AudioGeneration.objects.filter(user=user).order_by('-created_at')
    
    # Calculate exact counts for the dashboard
    stats = {
        'pdf_count': pdf_docs.count(),
        'mcq_count': mcq_sessions.count(),
        'test_count': test_attempts.count(),
        'audio_count': audio_results.count(),
    }
    
    context = {
        'pdf_docs': pdf_docs,
        'mcq_sessions': mcq_sessions,
        'test_attempts': test_attempts,
        'audio_results': audio_results,
        'stats': stats,
    }
    return render(request, 'account/profile.html', context)

@login_required(login_url='account:login')
def update_profile(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        
        user = request.user
        if User.objects.filter(username=username).exclude(id=user.id).exists():
            messages.error(request, "Username already taken.")
        elif User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "Email already taken.")
        else:
            user.username = username
            user.email = email
            user.save()
            messages.success(request, "Profile updated successfully.")
            
    return redirect('account:profile')

@login_required(login_url='account:login')
def change_password(request):
    if request.method == 'POST':
        old_pass = request.POST.get('old_password')
        new_pass = request.POST.get('new_password')
        confirm_pass = request.POST.get('confirm_password')
        
        user = request.user
        if not user.check_password(old_pass):
            messages.error(request, "Incorrect old password.")
        elif new_pass != confirm_pass:
            messages.error(request, "New passwords do not match.")
        else:
            user.set_password(new_pass)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully.")
            
    return redirect('account:profile')