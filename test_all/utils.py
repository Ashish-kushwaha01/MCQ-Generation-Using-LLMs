import json
from .models import Question, Test_Upload

def extract_from_json(test):
    """
    Extract MCQ questions from a JSON source (either FileField or JSONField)
    and attach them to ONE test.
    """
    Question.objects.filter(test=test).delete()
    data = None

    if test.json_data:
        # Load from JSONField
        data = test.json_data
        print(f"Loading questions from JSONField for test: {test.title}")
    elif test.json_file:
        # Load from FileField
        try:
            with open(test.json_file.path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            print(f"Loading questions from JSON file '{test.json_file.name}' for test: {test.title}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from file for test {test.title}: {e}")
            return
        except FileNotFoundError:
            print(f"JSON file not found for test {test.title}: {test.json_file.path}")
            return
    else:
        print(f"No JSON data or file found for test: {test.title}")
        return

    if not data:
        print(f"No valid JSON data to process for test: {test.title}")
        return

    questions_data = data.get('questions', [])
    
    # Update Test_Upload fields from JSON (only if not already set or if you want to override)
    test.title = data.get('title', test.title)
    test.description = data.get('description', test.description)
    test.subject = data.get('subject', test.subject)
    test.duration = data.get('duration', test.duration)
    test.total_questions = len(questions_data) # Recalculate based on actual questions
    test.save()

    for q_data in questions_data:
        Question.objects.create(
            test=test,
            question=q_data.get('question'),
            topic=q_data.get('topic', 'General'), # Use 'General' as default if not provided
            option_a=q_data.get('option_a'),
            option_b=q_data.get('option_b'),
            option_c=q_data.get('option_c'),
            option_d=q_data.get('option_d'),
            correct_option=q_data.get('correct_option')
        )
    print(f"Extracted {len(questions_data)} questions from JSON for test: {test.title}")











# # Change this import:
# # import pdfplumber  ❌ REMOVE

# # Add this import:
# from pypdf import PdfReader  # ✅ ADD
# import re
# from .models import Question, Test_Upload

# def extract_from_pdf(pdf_path, test):
#     """
#     Extract MCQ questions from PDF and attach them to ONE test
#     """

#     # ❌ DO NOT delete all questions globally
#     # ✅ Delete only this test's questions (optional)
#     Question.objects.filter(test=test).delete()

#     text = ""
    
#     # CHANGE THIS PART - replace pdfplumber with pypdf
#     # Before:
#     # with pdfplumber.open(pdf_path) as pdf:
#     #     for page in pdf.pages:
#     #         page_text = page.extract_text()
#     #         if page_text:
#     #             text += page_text + "\n"
    
#     # After:
#     with open(pdf_path, 'rb') as file:
#         reader = PdfReader(file)
#         for page in reader.pages:
#             page_text = page.extract_text()
#             if page_text:
#                 text += page_text + "\n"

#     # REST OF THE CODE STAYS EXACTLY THE SAME
#     lines = text.split("\n")
#     current = {}

#     for line in lines:
#         line = line.strip()

#         # Question start (1. / 2))
#         if re.match(r"^\d+[\.\)]", line):
#             if current:
#                 Question.objects.create(
#                     test=test,   # 🔥 CRITICAL
#                     question=current["q"],
#                     option_a=current["A"],
#                     option_b=current["B"],
#                     option_c=current["C"],
#                     option_d=current["D"],
#                     correct_option=current["ANS"]
#                 )

#             current = {
#                 "q": line,
#                 "A": "",
#                 "B": "",
#                 "C": "",
#                 "D": "",
#                 "ANS": ""
#             }

#         elif line.startswith("A)"):
#             current["A"] = line[2:].strip()

#         elif line.startswith("B)"):
#             current["B"] = line[2:].strip()

#         elif line.startswith("C)"):
#             current["C"] = line[2:].strip()

#         elif line.startswith("D)"):
#             current["D"] = line[2:].strip()

#         elif "Answer" in line:
#             # Extract the answer letter (A, B, C, D)
#             match = re.search(r'[ABCD]', line)
#             if match:
#                 current["ANS"] = match.group()
#             else:
#                 # Fallback to last character
#                 current["ANS"] = line.strip()[-1]

#     # Save last question
#     if current and current.get("q"):
#         Question.objects.create(
#             test=test,   # 🔥 CRITICAL
#             question=current["q"],
#             option_a=current.get("A", ""),
#             option_b=current.get("B", ""),
#             option_c=current.get("C", ""),
#             option_d=current.get("D", ""),
#             correct_option=current.get("ANS", "")
#         )