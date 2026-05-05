import os
import re
import json
import warnings
import shutil # New import for deleting directories
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

# -------- FAISS INDEX MANAGEMENT --------
def get_faiss_index_path(user_id):
    """Constructs the path for a user's FAISS index."""
    return f"faiss_index_{user_id}"

def delete_user_faiss_index(user_id):
    """Deletes a user's FAISS index directory if it exists."""
    index_path = get_faiss_index_path(user_id)
    if os.path.exists(index_path):
        try:
            shutil.rmtree(index_path)
            print(f"Successfully deleted FAISS index for user {user_id} at {index_path}")
        except Exception as e:
            print(f"Error deleting FAISS index for user {user_id}: {e}")
            raise
    else:
        print(f"No FAISS index found for user {user_id} at {index_path}")

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
        chunk_size=2000,
        chunk_overlap=400
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
        model="gemini-2.5-flash",  # Confirmed available in 2026 environment
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
1. Respond with ONLY valid JSON.
2. Generate questions, options, correct answers, and explanations IN THE SAME LANGUAGE AS THE PROVIDED CONTEXT.
3. No markdown formatting, no additional text, no explanations outside JSON.
4. Each question must have exactly 4 options (A, B, C, D).
5. Only ONE correct answer per question.
6. Mark the correct answer with its letter (A, B, C, or D).
7. For EVERY question, provide a HIGHLY SPECIFIC topic name based on what the question is testing. This topic MUST NOT be "General" or "Concept Understanding".
8. The topic for EACH question MUST be a concise, specific phrase (e.g., "Photosynthesis Process", "Types of Volcanoes", "Indian History: Mughal Empire").

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
            "topic": "HIGHLY SPECIFIC CONCEPT NAME"
        }}
    ]
}}

Context:
{context}

Generate {mcq_count} MCQs. REMEMBER: Each question MUST have a HIGHLY SPECIFIC topic (NOT 'General' or 'Concept Understanding'):
"""
    )

    chain = prompt | get_llm() | StrOutputParser()
    
    for _ in range(2): # Retry mechanism
        try:
            result = chain.invoke({
                "context": context,
                "mcq_count": mcq_count,
                "topic_instruction": topic_instruction
            })
            
            # Directly parse the result, as parse_json_mcqs is now robust
            mcqs = parse_json_mcqs(result)
            if mcqs:
                print(f"Successfully generated {len(mcqs)} MCQs after retry attempt.")
                return result # Return raw result for further processing if needed
            
        except Exception as e:
            print(f"Error generating MCQs (retry attempt): {e}")
            continue # Try again
            
    raise Exception("Failed to generate valid MCQs after multiple attempts.")





def parse_json_mcqs(json_response):
    """Parse JSON response into structured MCQ list, robustly handling LLM output"""
    try:
        # Attempt to find JSON within the response using regex
        match = re.search(r"\{.*\}", json_response, re.DOTALL)
        if not match:
            # If no object found, try to find a list
            match = re.search(r"\[.*\]", json_response, re.DOTALL)
            if not match:
                raise ValueError("No valid JSON object or list found in response.")
        
        json_str = match.group(0)
        data = json.loads(json_str)
        
        # Handle different possible structures (e.g., direct list of MCQs or an object with an 'mcqs' key)
        if 'mcqs' in data:
            mcqs_data = data['mcqs']
        elif isinstance(data, list):
            mcqs_data = data
        else:
            mcqs_data = [data] if data else [] # Wrap single object in a list if it's an MCQ
        
        if not mcqs_data:
            print("No MCQs found in JSON after parsing.")
            return []
        
        mcqs = []
        for idx, item in enumerate(mcqs_data):
            try:
                options = item.get('options', {})
                
                options_list = []
                for letter in ['A', 'B', 'C', 'D']:
                    option_text = options.get(letter, '')
                    if not option_text: # Try lowercase if uppercase not found
                        option_text = options.get(letter.lower(), '')
                    options_list.append({
                        'letter': letter,
                        'text': option_text if option_text else f"Option {letter}",
                        'is_correct': item.get('correct_answer', '').upper() == letter
                    })
                
                correct_letter = item.get('correct_answer', 'A').upper()
                correct_text = ""
                for opt in options_list:
                    if opt['letter'] == correct_letter:
                        correct_text = opt['text']
                        break

                topic = item.get('topic')
                print(f"DEBUG (parse_json_mcqs): Raw topic from LLM: '{topic}' (Type: {type(topic)})")
                if not topic or topic.strip() == "":
                    topic = "Topic Analysis Required"
                print(f"DEBUG (parse_json_mcqs): Processed topic: '{topic}'")
                
                mcq = {
                    'number': item.get('question_number', idx + 1),
                    'question': item.get('question_text', item.get('question', 'Question not available')),
                    'options': options_list,
                    'correct_answer': f"{correct_letter}) {correct_text}",
                    'correct_letter': correct_letter,
                    'explanation': item.get('explanation', 'No explanation provided'),
                    'topic': topic
                }
                mcqs.append(mcq)
                
            except Exception as e:
                print(f"Error processing individual MCQ {idx}: {e}")
                continue
        
        print(f"Parsed MCQs (with topics): {[m['topic'] for m in mcqs]}")
        print(f"Successfully parsed {len(mcqs)} MCQs.")
        return mcqs
        
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Raw response from LLM (for debug): {json_response}")
        return []
    except ValueError as e:
        print(f"Parsing Error: {e}")
        print(f"Raw response from LLM (for debug): {json_response}")
        return []
    except Exception as e:
        print(f"Unexpected error in parse_json_mcqs: {e}")
        print(f"Raw response from LLM (for debug): {json_response}")
        return []


# -------- CONTEXT RETRIEVAL --------
def get_context(query, user_id=None):
    """Retrieve relevant context from user-specific vector store"""
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=GOOGLE_API_KEY
    )

    db = load_vector_store(user_id=user_id)

    docs = db.similarity_search(query, k=4)
    return "\n\n".join(doc.page_content for doc in docs)


def get_weak_context(topics, user_id=None):
    """Retrieve context for weak topics"""
    return get_context(" ".join(topics), user_id=user_id)


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


def generate_detailed_summary(topic, user_id=None):
    """Generate a detailed summary for a given topic from user-specific vector store"""
    try:
        if not GOOGLE_API_KEY:
            raise Exception("GOOGLE_API_KEY not found. Please check your .env file.")

        print(f"Loading vector store for user {user_id} to summarize topic: {topic}...")
        db = load_vector_store(user_id=user_id)

        # Retrieve relevant context for the topic
        print(f"Retrieving context for topic: {topic}")
        docs = db.similarity_search(topic, k=10) # Retrieve more documents for a detailed summary
        context = "\n\n".join(doc.page_content for doc in docs)

        if not context or len(context.strip()) < 200: # Require more context for a detailed summary
            raise Exception("Not enough relevant content in PDFs to generate a detailed summary for this topic. Please upload PDFs with more content related to the topic.")

        print(f"Context length for summary: {len(context)} characters")
        print(f"Generating detailed summary for topic: {topic}...")

        llm = get_llm()
        prompt = PromptTemplate.from_template(
            """
You are an expert summarizer. Your task is to provide a detailed and comprehensive summary of the following content, focusing specifically on the topic: "{topic}".

            Ensure the summary is well-structured, informative, and covers all key aspects related to "{topic}" present in the provided context. The summary should be at least 200 words long if sufficient information is available. The summary MUST be generated in the same language as the provided Context.

            Context:
            {context}

            Detailed Summary of "{topic}":
            """
        )

        chain = prompt | llm | StrOutputParser()
        summary = chain.invoke({"context": context, "topic": topic})

        if not summary or len(summary.strip()) < 50: # Minimum length for a useful summary
            raise Exception("Generated summary is too short or empty. Please try again with more relevant content.")

        print(f"Successfully generated summary for topic: {topic}")
        return summary

    except FileNotFoundError as e:
        raise Exception("Please upload and process PDFs first before generating summaries.")
    except Exception as e:
        print(f"Error in generate_detailed_summary: {e}")
        raise