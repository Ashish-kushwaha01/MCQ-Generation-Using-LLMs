import pdfplumber
import re
from .models import Question, Test_Upload

def extract_from_pdf(pdf_path, test):
    """
    Extract MCQ questions from PDF and attach them to ONE test
    """

    # ❌ DO NOT delete all questions globally
    # ✅ Delete only this test's questions (optional)
    Question.objects.filter(test=test).delete()

    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    lines = text.split("\n")
    current = {}

    for line in lines:
        line = line.strip()

        # Question start (1. / 2))
        if re.match(r"^\d+[\.\)]", line):
            if current:
                Question.objects.create(
                    test=test,   # 🔥 CRITICAL
                    question=current["q"],
                    option_a=current["A"],
                    option_b=current["B"],
                    option_c=current["C"],
                    option_d=current["D"],
                    correct_option=current["ANS"]
                )

            current = {
                "q": line,
                "A": "",
                "B": "",
                "C": "",
                "D": "",
                "ANS": ""
            }

        elif line.startswith("A)"):
            current["A"] = line[2:].strip()

        elif line.startswith("B)"):
            current["B"] = line[2:].strip()

        elif line.startswith("C)"):
            current["C"] = line[2:].strip()

        elif line.startswith("D)"):
            current["D"] = line[2:].strip()

        elif "Answer" in line:
            current["ANS"] = line.strip()[-1]

    # Save last question
    if current:
        Question.objects.create(
            test=test,   # 🔥 CRITICAL
            question=current["q"],
            option_a=current["A"],
            option_b=current["B"],
            option_c=current["C"],
            option_d=current["D"],
            correct_option=current["ANS"]
        )











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