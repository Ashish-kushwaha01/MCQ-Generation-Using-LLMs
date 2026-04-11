import os
import re
import json
import warnings
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

# Configure genai
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    print(f"Google API configured successfully")
else:
    print("WARNING: GOOGLE_API_KEY not found in environment variables")

# -------- PDF TEXT EXTRACTION --------
def get_pdf_text(pdf_files):
    text = ""
    for pdf in pdf_files:
        try:
            reader = PdfReader(pdf)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            print(f"Error reading PDF {pdf.name}: {e}")
            continue
    return text


# -------- TEXT CHUNKING --------
def get_text_chunks(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    return splitter.split_text(text)


# -------- VECTOR STORE --------
def create_vector_store(chunks, user_id=None):
    """Create user-specific vector store using Gemini embeddings"""
    try:
        # Use the correct embedding model from your API
        embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",  # This is available in your API
            google_api_key=GOOGLE_API_KEY
        )
        
        db = FAISS.from_texts(chunks, embeddings)
        
        # Save user-specific index
        index_name = f"faiss_index_{user_id}" if user_id else "faiss_index"
        db.save_local(index_name)
        print(f"Vector store created successfully: {index_name}")
        return db
        
    except Exception as e:
        print(f"Error creating vector store: {e}")
        raise Exception(f"Failed to create vector store: {str(e)}")


def load_vector_store(user_id=None):
    """Load user-specific vector store"""
    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",  # Use the same model
            google_api_key=GOOGLE_API_KEY
        )
        
        index_name = f"faiss_index_{user_id}" if user_id else "faiss_index"
        
        if not os.path.exists(index_name):
            raise FileNotFoundError(f"Vector store {index_name} not found. Please upload PDFs first.")
        
        db = FAISS.load_local(
            index_name,
            embeddings,
            allow_dangerous_deserialization=True
        )
        print(f"Vector store loaded successfully: {index_name}")
        return db
        
    except Exception as e:
        print(f"Error loading vector store: {e}")
        raise Exception(f"Failed to load vector store: {str(e)}")


# -------- LLM (Gemini 2.5 Flash) --------
def get_llm():
    """Get the Gemini LLM - using Gemini 2.5 Flash"""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",  # You have this model available
        temperature=0.3,
        google_api_key=GOOGLE_API_KEY
    )


# -------- MCQ GENERATION WITH JSON OUTPUT --------
def generate_mcq_json(context, mcq_count, specific_topic=None):
    """Generate MCQs in JSON format from the provided context"""
    
    topic_instruction = ""
    if specific_topic:
        topic_instruction = f"""
IMPORTANT: Generate all questions specifically about the topic: "{specific_topic}"
The topic for EACH question MUST be "{specific_topic}".
"""
    
    prompt = PromptTemplate.from_template(
        """
You are an expert at creating high-quality multiple-choice questions (MCQs) from given content.

Generate EXACTLY {mcq_count} multiple-choice questions.

{topic_instruction}

IMPORTANT RULES:
1. Respond with ONLY valid JSON
2. No markdown formatting, no additional text, no explanations outside JSON
3. Each question must have exactly 4 options (A, B, C, D)
4. Only ONE correct answer per question
5. Mark the correct answer with its letter (A, B, C, or D)
6. For EVERY question, provide a SPECIFIC topic name based on what the question is testing
7. NEVER use "General" as a topic - this is FORBIDDEN

The JSON structure MUST be exactly like this:
{{
    "mcqs": [
        {{
            "question_number": 1,
            "question_text": "What is the main topic discussed?",
            "options": {{
                "A": "First option",
                "B": "Second option", 
                "C": "Third option",
                "D": "Fourth option"
            }},
            "correct_answer": "B",
            "explanation": "Brief explanation why B is correct",
            "topic": "SPECIFIC CONCEPT NAME"
        }}
    ]
}}

Context:
{context}

Generate {mcq_count} MCQs. REMEMBER: Each question MUST have a SPECIFIC topic (NOT 'General'):
"""
    )

    chain = prompt | get_llm() | StrOutputParser()
    
    try:
        result = chain.invoke({
            "context": context,
            "mcq_count": mcq_count,
            "topic_instruction": topic_instruction
        })
        
        print(f"Raw LLM response length: {len(result)}")
        
        # Clean the response
        result = clean_json_response(result)
        return result
        
    except Exception as e:
        print(f"Error generating MCQs: {e}")
        raise Exception(f"Failed to generate MCQs: {str(e)}")


def clean_json_response(response):
    """Clean LLM response to extract valid JSON"""
    # Remove markdown code blocks
    response = re.sub(r'```json\s*', '', response)
    response = re.sub(r'```\s*', '', response)
    response = re.sub(r'`json\s*', '', response)
    
    # Remove any leading/trailing whitespace
    response = response.strip()
    
    # Find JSON content - look for object
    json_match = re.search(r'(\{.*\})', response, re.DOTALL)
    if json_match:
        response = json_match.group(1)
    
    # Try to fix common JSON issues
    response = re.sub(r',\s*}', '}', response)
    response = re.sub(r',\s*]', ']', response)
    
    return response


def parse_json_mcqs(json_response):
    """Parse JSON response into structured MCQ list"""
    try:
        # Try to parse JSON
        data = json.loads(json_response)
        
        # Handle different possible structures
        if 'mcqs' in data:
            mcqs_data = data['mcqs']
        elif isinstance(data, list):
            mcqs_data = data
        else:
            mcqs_data = [data] if data else []
        
        if not mcqs_data:
            print("No MCQs found in JSON")
            return []
        
        mcqs = []
        for idx, item in enumerate(mcqs_data):
            try:
                options = item.get('options', {})
                
                # Ensure all options exist
                options_list = []
                for letter in ['A', 'B', 'C', 'D']:
                    option_text = options.get(letter, '')
                    if not option_text:
                        option_text = options.get(letter.lower(), '')
                    options_list.append({
                        'letter': letter,
                        'text': option_text if option_text else f"Option {letter}",
                        'is_correct': item.get('correct_answer', '').upper() == letter
                    })
                
                correct_letter = item.get('correct_answer', 'A').upper()
                # Find correct option text
                correct_text = ""
                for opt in options_list:
                    if opt['letter'] == correct_letter:
                        correct_text = opt['text']
                        break

                topic = item.get('topic', 'Concept Understanding') # Fixed: Provide a default string if 'topic' is not found
                
                mcq = {
                    'number': item.get('question_number', idx + 1),
                    'question': item.get('question_text', item.get('question', 'Question not available')),
                    'options': options_list,
                    'correct_answer': f"{correct_letter}) {correct_text}",
                    'correct_letter': correct_letter,
                    'explanation': item.get('explanation', 'No explanation provided'),
                    'topic': topic if topic and topic.lower() != 'general' else "Concept Understanding"
                }
                mcqs.append(mcq)
                
            except Exception as e:
                print(f"Error parsing MCQ {idx}: {e}")
                continue
        
        print(f"Successfully parsed {len(mcqs)} MCQs")
        return mcqs
        
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print(f"Raw response from LLM: {json_response}") # Print full raw response
        return []


# -------- QUERY FUNCTION --------
def ask_question_json(question, mcq_count, user_id=None, specific_topic=None):
    """Generate MCQs in JSON format with user-specific vector store"""
    try:
        # First check if API key is configured
        if not GOOGLE_API_KEY:
            raise Exception("GOOGLE_API_KEY not found. Please check your .env file.")
        
        print(f"Loading vector store for user {user_id}...")
        db = load_vector_store(user_id=user_id)
        
        # Search for relevant content
        search_query = specific_topic if specific_topic else question
        print(f"Searching for content related to: {search_query}")
        docs = db.similarity_search(search_query, k=6)
        context = "\n\n".join(doc.page_content for doc in docs)
        
        if not context or len(context.strip()) < 100:
            raise Exception("Not enough content in PDFs to generate questions. Please upload PDFs with more content.")
        
        print(f"Context length: {len(context)} characters")
        print(f"Generating {mcq_count} MCQs...")
        
        json_response = generate_mcq_json(context, mcq_count, specific_topic)
        mcqs = parse_json_mcqs(json_response)
        
        if not mcqs:
            raise Exception("Failed to parse MCQs from LLM response. Please try again.")
        
        # Ensure all MCQs have proper topics
        for mcq in mcqs:
            if not mcq['topic'] or mcq['topic'].lower() == 'general':
                mcq['topic'] = extract_topic_from_question(mcq['question'])
        
        print(f"Successfully generated {len(mcqs)} MCQs")
        
        return {
            'raw_response': json_response,
            'mcqs': mcqs,
            'mcq_count': len(mcqs)
        }
        
    except FileNotFoundError as e:
        raise Exception("Please upload and process PDFs first before generating MCQs.")
    except Exception as e:
        print(f"Error in ask_question_json: {e}")
        raise