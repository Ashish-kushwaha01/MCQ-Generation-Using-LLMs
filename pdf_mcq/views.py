import os
import json
import uuid
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

from .pdf_logic import (
    get_pdf_text,
    get_text_chunks,
    create_vector_store,
    ask_question_json
)
from .models import PDFDocument, MCQSession, MCQQuestion, UserAnswer


@login_required(login_url='account:login')
def pdf_mcq_view(request):
    context = {}
    user = request.user
    
    # Get user-specific data
    pdf_documents = PDFDocument.objects.filter(user=user).order_by('-uploaded_at')
    mcq_sessions = MCQSession.objects.filter(user=user).order_by('-created_at')
    
    # Check if PDFs are processed for this user
    vector_store_path = f"faiss_index_{user.id}"
    vector_store_exists = os.path.exists(vector_store_path)
    
    # IMPORTANT: Set pdfs_processed for template
    context['pdfs_processed'] = vector_store_exists
    
    if request.method == "POST":
        # PDF Upload
        if request.FILES.getlist("pdf_files"):
            pdf_files = request.FILES.getlist("pdf_files")
            text = get_pdf_text(pdf_files)
            
            if not text or not text.strip():
                messages.error(request, "❌ No text found in the uploaded PDF.")
                return render(request, "pdf_mcq_generate.html", context)
            
            chunks = get_text_chunks(text)
            if not chunks:
                messages.error(request, "❌ Could not create text chunks from the PDF.")
                return render(request, "pdf_mcq_generate.html", context)
            
            # Create user-specific vector store
            create_vector_store(chunks, user_id=user.id)
            
            # Save PDF documents to database
            for pdf_file in pdf_files:
                PDFDocument.objects.create(
                    user=user,
                    file_name=pdf_file.name,
                    file_size=pdf_file.size
                )
            
            # Update the vector store exists flag
            vector_store_exists = True
            context['pdfs_processed'] = True
            
            messages.success(request, f"✅ {len(pdf_files)} PDF(s) processed successfully!")
            
            context.update({
                "message": f"✅ {len(pdf_files)} PDF(s) processed successfully!",
                "pdfs_processed": True
            })
        
        # Generate MCQs (only number of questions)
        elif request.POST.get("mcq_count"):
            mcq_count = int(request.POST.get("mcq_count", "10"))
            
            # Validate count
            if mcq_count < 1 or mcq_count > 100:
                messages.error(request, "Please enter a number between 1 and 100")
                return redirect('pdf_mcq:pdf_mcq')
            
            try:
                # Generate MCQs from PDF
                result = ask_question_json("Generate comprehensive MCQs from this document", mcq_count, user_id=user.id)
                
                # Create session
                session_id = str(uuid.uuid4())[:8]
                mcq_session = MCQSession.objects.create(
                    user=user,
                    session_id=session_id,
                    mcq_count=result['mcq_count']
                )
                
                # Save questions to database
                saved_questions = []
                for mcq in result['mcqs']:
                    options = {opt['letter']: opt['text'] for opt in mcq['options']}
                    
                    question = MCQQuestion.objects.create(
                        session=mcq_session,
                        user=user,
                        question_number=mcq['number'],
                        question_text=mcq['question'],
                        option_a=options.get('A', ''),
                        option_b=options.get('B', ''),
                        option_c=options.get('C', ''),
                        option_d=options.get('D', ''),
                        correct_answer=mcq.get('correct_letter', 'A'),
                        explanation=mcq.get('explanation', '')
                    )
                    saved_questions.append(question)
                
                messages.success(request, f"✅ Generated {result['mcq_count']} MCQs successfully!")
                
                # Prepare context for display
                context.update({
                    "current_session": mcq_session,
                    "current_mcqs": [q.to_json() for q in saved_questions],
                    "mcq_count": result['mcq_count'],
                    "pdfs_processed": True,
                    "show_test": True
                })
                
            except Exception as e:
                messages.error(request, f"❌ Error generating MCQ: {str(e)}")
        
        # Load specific session from history
        elif request.POST.get("load_session"):
            session_id = request.POST.get("load_session")
            try:
                mcq_session = MCQSession.objects.get(session_id=session_id, user=user)
                questions = MCQQuestion.objects.filter(session=mcq_session, user=user).order_by('question_number')
                
                # Get user's answers for this session
                user_answers = UserAnswer.objects.filter(
                    user=user, 
                    session=mcq_session
                ).values_list('question_id', 'selected_answer')
                user_answers_dict = {str(ua[0]): ua[1] for ua in user_answers}
                
                context.update({
                    "current_session": mcq_session,
                    "current_mcqs": [q.to_json() for q in questions],
                    "mcq_count": questions.count(),
                    "pdfs_processed": True,
                    "show_test": True,
                    "user_answers": user_answers_dict
                })
            except MCQSession.DoesNotExist:
                messages.error(request, "Session not found")
    
    # Get all sessions for chat history
    all_sessions = MCQSession.objects.filter(user=user).order_by('-created_at')
    
    # Prepare chat history for sidebar - FIX THE DATETIME SERIALIZATION
    chat_history = []
    for session in all_sessions:
        question_count = MCQQuestion.objects.filter(session=session).count()
        chat_history.append({
            'session_id': session.session_id,
            'mcq_count': question_count,
            'created_at': session.created_at.isoformat() if session.created_at else None,  # Convert datetime to string
            'display_date': session.created_at.strftime('%b %d, %Y') if session.created_at else 'Unknown'
        })
    
    # Get current session data (most recent if exists)
    current_session_data = None
    if all_sessions.exists() and not context.get('current_session'):
        latest_session = all_sessions.first()
        questions = MCQQuestion.objects.filter(session=latest_session, user=user).order_by('question_number')
        if questions.exists():
            current_session_data = {
                'session': latest_session,
                'mcqs': [q.to_json() for q in questions],
                'mcq_count': questions.count()
            }
    
    # Convert chat history to JSON with proper datetime handling
    context.update({
        'chat_history': chat_history,
        'chat_history_json': json.dumps(chat_history, cls=DjangoJSONEncoder),  # Use DjangoJSONEncoder
        'pdfs_processed': vector_store_exists,
        'current_session_data': current_session_data
    })
    
    return render(request, "pdf_mcq_generate.html", context)


@login_required(login_url='account:login')
def clear_history(request):
    if request.method == "POST":
        # Delete all MCQ sessions and related data for the user
        MCQSession.objects.filter(user=request.user).delete()
        messages.success(request, "Chat history cleared successfully!")
    
    return redirect('pdf_mcq:pdf_mcq')


@login_required(login_url='account:login')
def submit_answers(request):
    """API endpoint to submit user answers"""
    if request.method == "POST":
        try:
            user = request.user
            data = json.loads(request.body)
            
            session_id = data.get('session_id')
            answers = data.get('answers', {})
            
            print(f"Received answers for session {session_id}: {answers}")  # Debug
            
            if not session_id:
                return JsonResponse({'status': 'error', 'message': 'Session ID required'}, status=400)
            
            try:
                session = MCQSession.objects.get(session_id=session_id, user=user)
                
                saved_count = 0
                for question_id_str, selected_answer in answers.items():
                    question_id = int(question_id_str)
                    try:
                        question = MCQQuestion.objects.get(id=question_id, user=user, session=session)
                        
                        # Compare answers (case insensitive)
                        is_correct = False
                        if selected_answer:
                            is_correct = selected_answer.upper() == question.correct_answer.upper()
                        
                        # Update or create user answer
                        user_answer, created = UserAnswer.objects.update_or_create(
                            user=user,
                            question=question,
                            session=session,
                            defaults={
                                'selected_answer': selected_answer.upper() if selected_answer else None,
                                'is_correct': is_correct
                            }
                        )
                        saved_count += 1
                        print(f"Saved answer for question {question_id}: {selected_answer} -> Correct: {is_correct}")
                        
                    except MCQQuestion.DoesNotExist:
                        print(f"Question {question_id} not found")
                        continue
                
                print(f"Saved {saved_count} answers for session {session_id}")
                return JsonResponse({
                    'status': 'success', 
                    'message': f'{saved_count} answers saved successfully'
                })
                
            except MCQSession.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Session not found'}, status=404)
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
        except Exception as e:
            print(f"Error saving answers: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)



@login_required(login_url='account:login')
def get_session_results(request, session_id):
    """Get results for a specific session"""
    user = request.user
    
    try:
        session = MCQSession.objects.get(session_id=session_id, user=user)
        questions = MCQQuestion.objects.filter(session=session, user=user)
        
        results = []
        correct_count = 0
        
        for question in questions:
            try:
                user_answer = UserAnswer.objects.get(user=user, question=question, session=session)
                is_correct = user_answer.is_correct
                if is_correct:
                    correct_count += 1
            except UserAnswer.DoesNotExist:
                user_answer = None
                is_correct = False
            
            results.append({
                'question_id': question.id,
                'question_number': question.question_number,
                'question_text': question.question_text,
                'user_answer': user_answer.selected_answer if user_answer else None,
                'correct_answer': question.correct_answer,
                'is_correct': is_correct
            })
        
        return JsonResponse({
            'status': 'success',
            'total': questions.count(),
            'correct': correct_count,
            'percentage': (correct_count / questions.count() * 100) if questions.count() > 0 else 0,
            'results': results
        })
        
    except MCQSession.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Session not found'}, status=404)