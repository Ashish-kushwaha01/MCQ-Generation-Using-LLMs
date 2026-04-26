from django.shortcuts import get_object_or_404, render,redirect
from django.contrib import messages
from .models import Test_Upload, UserAnswer, UserTestAttempt
from django.http import HttpResponse 
from .models import Question
from django.conf import settings
from .utils import extract_from_json
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.utils import timezone

from django.views.decorators.http import require_POST

# Create your views here.
@never_cache
def test_page(request):
    tests = Test_Upload.objects.all()
    subject = Test_Upload.objects.values_list('subject',flat=True).distinct()
    if request.method =="GET":
        category = request.GET.get('category')
        
        if category and category!='All Category':
        # Store the category in session
            request.session['category_filter'] = category
            tests = tests.filter(subject__icontains=category)
        else:
            # If no GET parameter, clear the session filter
            if 'category_filter' in request.session:
                del request.session['category_filter']
        
    return render(request, 'tests/test_page.html', {'subject':subject,'tests': tests})


def general_info(request, slug):
    test = get_object_or_404(Test_Upload, test_slug=slug)

    # extract ONLY if questions don't exist and either json_file or json_data is present
    if test.questions.count() == 0 and (test.json_file or test.json_data):
        extract_from_json(test)
        # After extraction, check if questions were actually created
        if test.questions.count() == 0:
            messages.error(request, "No questions could be extracted from the provided JSON. Please ensure the JSON format is correct.")
            return redirect('test_all:test_page') # Redirect back to test list or a suitable page

    return render(request, 'tests/general_info.html', {
        'test': test # Changed 'pdf' to 'test' for consistency
    })
    
    
@never_cache
def start_test(request, slug):
    test = get_object_or_404(Test_Upload, test_slug=slug)
    
    attempt = UserTestAttempt.objects.create(
        user = request.user,
        test  =test,
        total=test.questions.count(),
        started_at=timezone.now()
    )
    
    return redirect('test_all:question_page',slug= slug,attempt_id = attempt.id)

@never_cache
def question_page(request, slug, attempt_id):
    test = get_object_or_404(Test_Upload, test_slug=slug)
    attempt = get_object_or_404(
        UserTestAttempt,
        id=attempt_id,
        user=request.user
    )

    return render(request, 'tests/questions.html', {
        'test': test,
        'attempt_id': attempt.id
    })

        
    
def ajax_question(request, slug, attempt_id):
    test = get_object_or_404(Test_Upload, test_slug=slug)

    attempt = get_object_or_404(
        UserTestAttempt,
        id=attempt_id,
        user=request.user
    )

    questions = test.questions.all()
    total = questions.count()

    q_no = int(request.GET.get('q_no', 1))

    if q_no > total:
        return JsonResponse({'completed': True})

    q = questions[q_no - 1]

    answer_obj = attempt.answers.filter(question=q).first()
    selected = answer_obj.selected_option if answer_obj else None

    return JsonResponse({
        'q_no': q_no,
        'total': total,
        'question': q.question,
        'options': {
            'A': q.option_a,
            'B': q.option_b,
            'C': q.option_c,
            'D': q.option_d,
        },
        'selected': selected
    })

@require_POST
def ajax_save_answer(request, slug, attempt_id):
    attempt = get_object_or_404(
        UserTestAttempt,
        id=attempt_id,
        user=request.user
    )

    q_no = int(request.POST.get('q_no'))
    answer = request.POST.get('answer')

    question = attempt.test.questions.all()[q_no - 1]

    UserAnswer.objects.update_or_create(
        attempt=attempt,
        question=question,
        defaults={'selected_option': answer}
    )

    return JsonResponse({'saved': True})



def test_result(request, slug, attempt_id):
    attempt = get_object_or_404(UserTestAttempt,id=attempt_id,user = request.user)
    test = attempt.test
        
    questions = test.questions.all()
    
    total = questions.count()

    correct = incorrect = skip = 0

    for q in questions:
        ans = attempt.answers.filter(question = q).first()
        
        if not ans or not ans.selected_option:
            skip += 1
            print(q)
        elif ans.selected_option == q.correct_option:
            correct += 1
        else:
            incorrect += 1
            print(q)

    if(total > 0):
        correct_deg = round((correct / total) *360)
        incorrect_deg = round((incorrect / total) *360)
        skip_deg = 360 - (correct_deg + incorrect_deg)
    else:
        correct_deg = incorrect_deg = skip_deg = 0
        
    attempt.total = total
    attempt.correct = correct
    attempt.incorrect = incorrect
    attempt.skipped = skip
    attempt.completed = True
    attempt.completed_at = timezone.now()
    attempt.save()
    
    context = {
    'attempt': attempt,
    'test': test,
    'total': total,
    'correct': correct,
    'incorrect': incorrect,
    'skip': skip,
    'today':timezone.localdate(),
    'correct_deg': correct_deg,
    'incorrect_deg': incorrect_deg,
    'skip_deg': skip_deg,
}
    
    
    return render(request,'tests/test_result.html', context)
    