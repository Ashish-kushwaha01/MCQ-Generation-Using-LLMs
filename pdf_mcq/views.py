from django.shortcuts import render, redirect
import json

from .pdf_logic import (
    get_pdf_text,
    get_text_chunks,
    create_vector_store,
    ask_question
)

def parse_mcqs_from_answer(answer_text):
    """Parse the LLM response into individual MCQs"""
    mcqs = []
    
    if not answer_text:
        return mcqs
    
    lines = answer_text.split('\n')
    current_mcq = None
    in_options = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for question number (e.g., "1.", "2.", etc.)
        question_match = __import__('re').match(r'^(\d+)\.\s*(.+)$', line)
        if question_match:
            # Save previous MCQ
            if current_mcq:
                mcqs.append(current_mcq)
            
            # Start new MCQ
            current_mcq = {
                'number': question_match.group(1),
                'question': question_match.group(2),
                'options': [],
                'correct_answer': '',
                'explanation': ''
            }
            in_options = True
            continue
        
        # Check for options (A), B), C), D))
        option_match = __import__('re').match(r'^([A-D]\))\s*(.+)$', line)
        if option_match and current_mcq and in_options:
            option_text = option_match.group(2)
            is_correct = '(*)' in option_text
            clean_text = option_text.replace('(*)', '').strip()
            
            current_mcq['options'].append({
                'letter': option_match.group(1),
                'text': clean_text,
                'is_correct': is_correct
            })
            
            if is_correct:
                current_mcq['correct_answer'] = f"{option_match.group(1)} {clean_text}"
            continue
        
        # Check for answer/correct answer line
        if 'answer' in line.lower() and current_mcq:
            in_options = False
            if current_mcq['explanation']:
                current_mcq['explanation'] += '\n' + line
            else:
                current_mcq['explanation'] = line
            continue
        
        # Add to explanation if we're past options
        if current_mcq and not in_options:
            if current_mcq['explanation']:
                current_mcq['explanation'] += '\n' + line
            else:
                current_mcq['explanation'] = line
    
    # Add the last MCQ
    if current_mcq:
        mcqs.append(current_mcq)
    
    return mcqs


def pdf_mcq_view(request):
    context = {}
    
    # Initialize session variables if they don't exist
    if 'chat_history' not in request.session:
        request.session['chat_history'] = []
    if 'pdfs_processed' not in request.session:
        request.session['pdfs_processed'] = False
    
    # Get current session data
    chat_history = request.session.get('chat_history', [])
    pdfs_processed = request.session.get('pdfs_processed', False)
    
    if request.method == "POST":
        # PDF Upload
        if request.FILES.getlist("pdf_files"):
            pdf_files = request.FILES.getlist("pdf_files")
            text = get_pdf_text(pdf_files)
            
            if not text or not text.strip():
                context["message"] = "❌ No text found in the uploaded PDF."
                return render(request, "pdf_mcq_generate.html", context)
            
            chunks = get_text_chunks(text)
            if not chunks:
                context["message"] = "❌ Could not create text chunks from the PDF."
                return render(request, "pdf_mcq_generate.html", context)
            
            create_vector_store(chunks)
            request.session['pdfs_processed'] = True
            pdfs_processed = True
            
            # Store uploaded files info
            uploaded_files = []
            for f in pdf_files:
                uploaded_files.append({
                    'name': f.name,
                    'size': f.size
                })
            
            context.update({
                "message": "✅ PDFs processed successfully!",
                "uploaded_files": uploaded_files,
                "pdfs_processed": True
            })
            
            request.session.modified = True
        
        # Ask Question
        elif request.POST.get("question"):
            question = request.POST.get("question")
            mcq_count = request.POST.get("mcq_count", "10")
            
            # Enhance question with count
            enhanced_question = f"Generate {mcq_count} multiple choice questions about: {question}. Format each question with number, options A) B) C) D), mark correct answer with (*), and provide explanation."
            
            try:
                answer = ask_question(enhanced_question)
                
                # Parse MCQs from the answer
                parsed_mcqs = parse_mcqs_from_answer(answer)
                
                # Store in chat history - NO TIMESTAMP
                chat_entry = {
                    "question": question,
                    "mcq_count": mcq_count,
                    "answer": answer,
                    "parsed_mcqs": parsed_mcqs,
                }
                
                # Get existing chat history
                chat_history = request.session.get('chat_history', [])
                chat_history.append(chat_entry)
                request.session['chat_history'] = chat_history
                
                # Update context
                context.update({
                    "question": question,
                    "answer": answer,
                    "last_question": question,
                    "last_count": mcq_count,
                    "pdfs_processed": pdfs_processed
                })
                
            except Exception as e:
                context["error"] = f"❌ Error generating MCQ: {str(e)}"
            
            request.session.modified = True
    
    # Simple context with no datetime
    context['chat_history'] = chat_history
    context['pdfs_processed'] = pdfs_processed
    
    # Simple JSON for JavaScript - NO TIMESTAMP
    chat_history_json = []
    for chat in chat_history:
        chat_history_json.append({
            'question': chat['question'],
            'mcq_count': chat.get('mcq_count', '10'),
        })
    context['chat_history_json'] = json.dumps(chat_history_json)
    
    return render(request, "pdf_mcq_generate.html", context)


def clear_history(request):
    if request.method == "POST":
        request.session['chat_history'] = []
        request.session.modified = True
    # FIXED: Redirect to the correct URL name
    return redirect('pdf_mcq:pdf_mcq')  # Make sure this matches your URL pattern name