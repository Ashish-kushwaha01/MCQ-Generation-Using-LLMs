import os
from dotenv import load_dotenv

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI
)

from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

import google.generativeai as genai

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)


# -------- PDF TEXT EXTRACTION --------
from pypdf import PdfReader

def get_pdf_text(pdf_files):

    text = ""

    for pdf in pdf_files:

        reader = PdfReader(pdf)

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text


# -------- TEXT CHUNKING --------
def get_text_chunks(text):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    return splitter.split_text(text)


# -------- VECTOR STORE --------
def create_vector_store(chunks):

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )

    db = FAISS.from_texts(chunks, embeddings)

    db.save_local("faiss_index")


# -------- LOAD VECTOR STORE --------
def load_vector_store():

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )

    db = FAISS.load_local(
        "faiss_index",
        embeddings,
        allow_dangerous_deserialization=True
    )

    return db


# -------- LLM --------
def get_llm():

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3
    )


# -------- MCQ GENERATION --------
def generate_mcq(context, question):

    prompt = PromptTemplate.from_template(
        """
you are a helpful assistant for creating a mcqs from the provided context.
        You are a helpful assistant for creating MCQs from the provided context.

        Provide 4 options for the question and mark the correct answer using (*).

Context:
{context}

Question:
{question}

Answer:
"""
    )

    chain = prompt | get_llm() | StrOutputParser()

    return chain.invoke({
        "context": context,
        "question": question
    })


# -------- QUERY FUNCTION --------
def ask_question(question):

    db = load_vector_store()

    docs = db.similarity_search(question, k=4)

    print("DOCS FOUND:", len(docs))

    context = "\n\n".join(doc.page_content for doc in docs)

    print("CONTEXT LENGTH:", len(context))

    answer = generate_mcq(context, question)

    print("LLM ANSWER:", answer)

    return answer




# import os
# from dotenv import load_dotenv

# from pypdf import PdfReader
# from langchain_text_splitters import RecursiveCharacterTextSplitter

# from langchain_google_genai import (
#     GoogleGenerativeAIEmbeddings,
#     ChatGoogleGenerativeAI
# )

# from langchain_community.vectorstores import FAISS
# from langchain_core.prompts import PromptTemplate
# from langchain_core.output_parsers import StrOutputParser

# # -------- LOAD ENV --------
# load_dotenv()
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# # -------- PDF TEXT EXTRACTION --------
# def get_pdf_text(pdf_files):
#     text = ""

#     for pdf in pdf_files:
#         reader = PdfReader(pdf)

#         for page in reader.pages:
#             page_text = page.extract_text()

#             if page_text:
#                 text += page_text + "\n"

#     return text


# # -------- TEXT CHUNKING --------
# def get_text_chunks(text):
#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=1000,
#         chunk_overlap=200
#     )

#     return splitter.split_text(text)


# # -------- VECTOR STORE --------
# def create_vector_store(chunks):

#     embeddings = GoogleGenerativeAIEmbeddings(
#         model="models/embedding-001"   # ✅ FIXED MODEL NAME
#     )

#     db = FAISS.from_texts(chunks, embeddings)
#     db.save_local("faiss_index")


# # -------- LOAD VECTOR STORE --------
# def load_vector_store():

#     embeddings = GoogleGenerativeAIEmbeddings(
#         model="models/embedding-001"
#     )

#     db = FAISS.load_local(
#         "faiss_index",
#         embeddings,
#         allow_dangerous_deserialization=True
#     )

#     return db


# # -------- LLM --------
# def get_llm():
#     return ChatGoogleGenerativeAI(
#         model="gemini-1.5-flash",   # ✅ stable model
#         temperature=0.3
#     )


# # -------- MCQ GENERATION --------
# def generate_mcq(context, question):

#     prompt = PromptTemplate.from_template(
#         """
# You are a helpful assistant for creating MCQs.

# Create:
# - 4 options
# - Mark correct answer with (*)

# Only use given context.
# If not enough info → say "more information is needed".

# Context:
# {context}

# Question:
# {question}

# Answer:
# """
#     )

#     chain = prompt | get_llm() | StrOutputParser()

#     return chain.invoke({
#         "context": context,
#         "question": question
#     })


# # -------- QUERY FUNCTION --------
# def ask_question(question):

#     db = load_vector_store()

#     docs = db.similarity_search(question, k=4)

#     context = "\n\n".join(doc.page_content for doc in docs)

#     answer = generate_mcq(context, question)

#     return answer







# import os
# import requests
# import json
# from dotenv import load_dotenv
# from pypdf import PdfReader

# load_dotenv()

# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# # -------- PDF TEXT EXTRACTION --------
# def get_pdf_text(pdf_files):
#     """Extract text from PDF files"""
#     text = ""
#     for pdf in pdf_files:
#         reader = PdfReader(pdf)
#         for page in reader.pages:
#             page_text = page.extract_text()
#             if page_text:
#                 text += page_text + "\n"
#     return text


# # -------- TEXT CHUNKING --------
# def get_text_chunks(text):
#     """Split text into chunks (simple version without LangChain)"""
#     # Simple chunking: split by paragraphs, then combine up to ~1000 chars
#     paragraphs = text.split('\n\n')
#     chunks = []
#     current_chunk = ""
    
#     for para in paragraphs:
#         if len(current_chunk) + len(para) < 1000:
#             current_chunk += para + "\n\n"
#         else:
#             if current_chunk:
#                 chunks.append(current_chunk.strip())
#             current_chunk = para + "\n\n"
    
#     if current_chunk:
#         chunks.append(current_chunk.strip())
    
#     # If no chunks created (text too small), use the whole text
#     if not chunks and text.strip():
#         chunks = [text.strip()]
    
#     return chunks


# # -------- CREATE VECTOR STORE (Simplified - just returns chunks) --------
# def create_vector_store(chunks):
#     """Store chunks for later retrieval (simplified version)"""
#     # In a simple version, we just save chunks to session
#     # For now, this just returns the chunks
#     return chunks


# # -------- ASK QUESTION USING GEMINI API --------
# def ask_question(question):
#     """Generate MCQs using Gemini API directly"""
    
#     prompt = f"""Generate multiple choice questions based on general knowledge.
    
# Topic: {question}

# Please generate 5-10 multiple choice questions with the following format:
# 1. Question text here?
# A) First option
# B) Second option
# C) Third option
# D) Fourth option (*)

# Mark the correct answer with (*). Include an explanation after each question.

# Questions:
# """
    
#     url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GOOGLE_API_KEY}"
    
#     payload = {
#         "contents": [{
#             "parts": [{"text": prompt}]
#         }]
#     }
    
#     headers = {
#         "Content-Type": "application/json"
#     }
    
#     try:
#         response = requests.post(url, json=payload, headers=headers)
        
#         if response.status_code == 200:
#             data = response.json()
#             if 'candidates' in data and len(data['candidates']) > 0:
#                 return data['candidates'][0]['content']['parts'][0]['text']
#             else:
#                 return "Error: No response from API"
#         else:
#             return f"Error: API returned {response.status_code}"
#     except Exception as e:
#         return f"Error: {str(e)}"