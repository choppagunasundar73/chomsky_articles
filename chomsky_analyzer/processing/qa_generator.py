import requests
import json
from typing import List, Dict
import re
import hashlib
import random
import time
from collections import defaultdict

# API key for Groq
API_KEY = ''  # Replace with your actual Groq API key

def create_qa_pairs(paragraphs: List[Dict]) -> List[Dict]:
    """Create question-answer pairs from article paragraphs with diverse themes"""
    qa_pairs = []
    
    # Group paragraphs by article
    articles = {}
    for para in paragraphs:
        article_id = f"{para['article_title']} ({para['article_date']})"
        if article_id not in articles:
            articles[article_id] = {
                'title': para['article_title'],
                'date': para['article_date'],
                'url': para['article_url'],
                'content': []
            }
        articles[article_id]['content'].append(para)
    
    # Process each article
    for article_id, article in articles.items():
        print(f"\nProcessing article: {article['title']}")
        
        # Group content by speaker
        speaker_content = defaultdict(list)
        
        for para in article['content']:
            speaker = para['speaker']
            content = para['content'].strip()
            if content:
                speaker_content[speaker].append(content)
        
        # Process each speaker's content
        for speaker, content_list in speaker_content.items():
            # Combine all content for this speaker
            full_text = "\n\n".join(content_list)
            
            print(f"Processing content for {speaker}, {len(full_text.split())} words")
            
            # Divide content into thematic segments for diverse questions
            segments = segment_article(full_text)
            print(f"Divided into {len(segments)} thematic segments")
            
            # Track used questions to avoid duplicates
            used_questions = set()
            used_answers = []
            
            # Generate Q&A pairs using multiple approaches
            article_qa_pairs = []
            
            # 1. Try direct generation first
            direct_pairs = generate_qa_pairs_direct(
                full_text[:4000],  # Use beginning of article
                speaker,
                article['title'],
                article['date'],
                article['url'],
                num_pairs=5
            )
            
            # Add non-duplicate pairs
            for pair in direct_pairs:
                if len(article_qa_pairs) >= 10:
                    break
                    
                # Skip if too similar to existing questions
                if any(calculate_similarity(pair['question'], q['question']) > 0.4 for q in article_qa_pairs):
                    continue
                
                article_qa_pairs.append(pair)
                used_questions.add(pair['question'])
                used_answers.append(pair['answer'])
            
            print(f"Generated {len(article_qa_pairs)} Q&A pairs from direct approach")
            
            # 2. Try themed questions if we need more
            if len(article_qa_pairs) < 10:
                # Use multiple themed prompts
                themes = [
                    {"name": "historical", "prompt": f"What historical context or background does {speaker} provide in this article? Explain in detail."},
                    {"name": "methodology", "prompt": f"What methodology or analytical approach does {speaker} employ in this analysis? Explain thoroughly."},
                    {"name": "criticism", "prompt": f"What criticisms or counter-arguments does {speaker} address in this text? Provide a comprehensive answer."},
                    {"name": "implications", "prompt": f"What broader implications or consequences does {speaker} suggest will result from these events or policies?"},
                    {"name": "alternatives", "prompt": f"What alternatives or solutions does {speaker} propose in this article? Explain fully."}
                ]
                
                # Try each theme
                for theme in themes:
                    if len(article_qa_pairs) >= 10:
                        break
                        
                    # Try to generate a Q&A pair for this theme
                    pair = generate_themed_qa_pair(
                        full_text,
                        speaker,
                        article['title'],
                        article['date'],
                        article['url'],
                        theme["prompt"]
                    )
                    
                    if pair and not any(calculate_similarity(pair['question'], q['question']) > 0.4 for q in article_qa_pairs):
                        article_qa_pairs.append(pair)
                        used_questions.add(pair['question'])
                        used_answers.append(pair['answer'])
            
            print(f"Generated {len(article_qa_pairs)} Q&A pairs after themed approach")
            
            # 3. Try segment-based questions if we still need more
            if len(article_qa_pairs) < 10:
                for i, segment in enumerate(segments):
                    if len(article_qa_pairs) >= 10:
                        break
                        
                    # Skip very short segments
                    if len(segment.split()) < 100:
                        continue
                        
                    # Use a higher temperature for more diversity as we generate more questions
                    temperature = min(0.7 + (len(article_qa_pairs) * 0.05), 0.9)
                    
                    # Try to generate Q&A pairs for this segment
                    segment_pairs = generate_qa_pairs_segment(
                        segment,
                        speaker,
                        article['title'],
                        article['date'],
                        article['url'],
                        used_questions,
                        temperature=temperature
                    )
                    
                    # Add non-duplicate pairs
                    for pair in segment_pairs:
                        if len(article_qa_pairs) >= 10:
                            break
                            
                        # Skip if too similar to existing questions
                        if any(calculate_similarity(pair['question'], q['question']) > 0.4 for q in article_qa_pairs):
                            continue
                            
                        # Skip if answer too similar to existing answers
                        if any(calculate_similarity(pair['answer'], q['answer']) > 0.6 for q in article_qa_pairs):
                            continue
                        
                        article_qa_pairs.append(pair)
                        used_questions.add(pair['question'])
                        used_answers.append(pair['answer'])
            
            print(f"Generated {len(article_qa_pairs)} Q&A pairs after segment approach")
            
            # Add the Q&A pairs to our result list
            qa_pairs.extend(article_qa_pairs)
            print(f"Total Q&A pairs for article: {len(article_qa_pairs)}")
    
    return qa_pairs

def generate_qa_pairs_direct(text, speaker, article_title, article_date, article_url, num_pairs=5):
    """Generate Q&A pairs directly using the Groq API"""
    # Groq API endpoint
    api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    # Headers for the API request
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Simplified prompt to ensure we get results
    prompt = f"""
Based on the following excerpt from {speaker}'s article "{article_title}", generate {num_pairs} unique Q&A pairs.

EXCERPT:
```
{text}
```

For each pair:
1. Create a specific, unique question about a different aspect of the content
2. Provide a detailed answer (3-5 sentences minimum) based directly on the text
3. Make sure each question covers a different theme or angle (historical context, methodology, criticisms, implications, etc.)

Format each pair as:
Q: [Question]
A: [Answer]

Generate EXACTLY {num_pairs} pairs, separated by blank lines.
"""
    
    # Parameters for Groq API (using LLaMA 3 model which has fast inference)
    payload = {
        "model": "llama3-70b-8192",  # Groq's LLaMA 3 model
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "top_p": 0.95,
        "max_tokens": 1500
    }
    
    try:
        print("Calling Groq API...")
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)  # Reduced timeout for faster API
        
        # Print response status for debugging
        print(f"API Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"API Error: {response.text}")
            return []
        
        response_data = response.json()
        
        # Extract the generated text
        if 'choices' in response_data and response_data['choices']:
            generated_text = response_data['choices'][0]['message']['content']
            print(f"Generated text length: {len(generated_text)}")
            
            # Parse Q&A pairs
            qa_pairs = []
            qa_pattern = r"Q: (.*?)\nA: (.*?)(?=\n\s*Q:|\Z)"
            matches = re.findall(qa_pattern, generated_text, re.DOTALL)
            
            for question, answer in matches:
                qa_pairs.append({
                    'question': question.strip(),
                    'answer': answer.strip(),
                    'speaker': speaker,
                    'article_title': article_title,
                    'article_date': article_date,
                    'article_url': article_url
                })
            
            print(f"Extracted {len(qa_pairs)} Q&A pairs")
            return qa_pairs
        else:
            print("No choices in API response")
            return []
            
    except Exception as e:
        print(f"Error in API call: {str(e)}")
        return []

def generate_themed_qa_pair(text, speaker, article_title, article_date, article_url, theme_prompt):
    """Generate a single Q&A pair based on a specific theme using Groq"""
    # Groq API endpoint
    api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    # Headers for the API request
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Craft a prompt focused on a specific theme
    prompt = f"""
Based on this excerpt from {speaker}'s article "{article_title}":

```
{text[:3000]}
```

Question: {theme_prompt}

Generate a detailed, comprehensive answer (at least 3-5 sentences) based ONLY on information in the text.
Format your response as:

Q: [Restate the question in your own words]
A: [Your detailed answer]
"""
    
    # Parameters for Groq API
    payload = {
        "model": "llama3-70b-8192",  # Fast Groq model
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 800
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"API Error: {response.text}")
            return None
        
        response_data = response.json()
        
        # Extract the generated text
        if 'choices' in response_data and response_data['choices']:
            generated_text = response_data['choices'][0]['message']['content']
            
            # Parse Q&A pair
            qa_pattern = r"Q: (.*?)\nA: (.*)"
            match = re.search(qa_pattern, generated_text, re.DOTALL)
            
            if match:
                return {
                    'question': match.group(1).strip(),
                    'answer': match.group(2).strip(),
                    'speaker': speaker,
                    'article_title': article_title,
                    'article_date': article_date,
                    'article_url': article_url
                }
            
    except Exception as e:
        print(f"Error in themed API call: {str(e)}")
    
    return None

def generate_qa_pairs_segment(segment, speaker, article_title, article_date, article_url, used_questions, temperature=0.8, num_pairs=2):
    """Generate Q&A pairs for a specific segment of the article using Groq"""
    # Groq API endpoint
    api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    # Headers for the API request
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Used questions for context
    used_q_text = "\n".join([f"- {q}" for q in list(used_questions)[:5]]) if used_questions else "None yet."
    
    # Craft a prompt focused on generating unique questions for this segment
    prompt = f"""
This is a specific segment from {speaker}'s article "{article_title}":

```
{segment}
```

Generate {num_pairs} unique Q&A pairs about THIS SPECIFIC SEGMENT that are different from these previously generated questions:
{used_q_text}

Requirements:
1. Each question must focus on content UNIQUE to this segment
2. Questions must be specific and detailed
3. Answers must be comprehensive (3-5 sentences minimum)
4. Different questions should cover different themes or aspects

Format each pair as:
Q: [Question]
A: [Answer]
"""
    
    # Parameters with variable temperature for diversity
    payload = {
        "model": "llama3-70b-8192",  # Fast Groq model
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "top_p": 0.95,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"API Error: {response.text}")
            return []
        
        response_data = response.json()
        
        # Extract the generated text
        if 'choices' in response_data and response_data['choices']:
            generated_text = response_data['choices'][0]['message']['content']
            
            # Parse Q&A pairs
            qa_pairs = []
            qa_pattern = r"Q: (.*?)\nA: (.*?)(?=\n\s*Q:|\Z)"
            matches = re.findall(qa_pattern, generated_text, re.DOTALL)
            
            for question, answer in matches:
                qa_pairs.append({
                    'question': question.strip(),
                    'answer': answer.strip(),
                    'speaker': speaker,
                    'article_title': article_title,
                    'article_date': article_date,
                    'article_url': article_url
                })
            
            return qa_pairs
            
    except Exception as e:
        print(f"Error in segment API call: {str(e)}")
    
    return []

def segment_article(text, min_segment_words=150):
    """Divide article into thematic segments for more diverse questioning"""
    # Split by paragraph breaks
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    # If very few paragraphs, just return the whole text
    if len(paragraphs) <= 3:
        return [text]
    
    segments = []
    current_segment = []
    current_word_count = 0
    
    for para in paragraphs:
        para_words = len(para.split())
        
        # If adding this paragraph would make segment too long, start a new one
        if current_word_count + para_words > 600 and current_word_count >= min_segment_words:
            segments.append("\n\n".join(current_segment))
            current_segment = [para]
            current_word_count = para_words
        else:
            current_segment.append(para)
            current_word_count += para_words
    
    # Add the final segment if not empty
    if current_segment:
        segments.append("\n\n".join(current_segment))
    
    # If we didn't create any segments (very short article), just return the whole text
    if not segments:
        return [text]
    
    return segments

def calculate_similarity(text1, text2):
    """Calculate Jaccard similarity between two texts based on significant words"""
    # Get significant words (longer than 3 chars)
    stop_words = {"and", "or", "the", "a", "an", "in", "on", "at", "to", "for", "with", "by", "about", 
                 "like", "as", "of", "do", "does", "how", "what", "when", "where", "why", "would", "could",
                 "should", "their", "they", "this", "that", "these", "those", "be", "been", "being", "is", 
                 "am", "are", "was", "were", "has", "have", "had", "not", "from"}
    
    words1 = [w.lower() for w in re.findall(r'\b\w+\b', text1) 
             if w.lower() not in stop_words and len(w) > 3]
    words2 = [w.lower() for w in re.findall(r'\b\w+\b', text2) 
             if w.lower() not in stop_words and len(w) > 3]
    
    # Convert to sets for Jaccard similarity
    set1 = set(words1)
    set2 = set(words2)
    
    if not set1 or not set2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    
    return len(intersection) / len(union)