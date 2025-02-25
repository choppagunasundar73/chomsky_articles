from bs4 import BeautifulSoup
from typing import List, Dict
import re

def parse_dialogue(html_content: str, url: str) -> List[Dict]:
    """Parse article content into structured dialogue with better speaker detection"""
    soup = BeautifulSoup(html_content, 'html.parser')
    paragraphs = []
    
    # Extract title and date
    title = soup.find('h1').text.strip() if soup.find('h1') else "Untitled Article"
    date_tag = soup.find('time')
    date = date_tag['datetime'] if date_tag and date_tag.has_attr('datetime') else "Unknown Date"
    
    # Detect interview vs. solo article format
    content_div = soup.find('div', class_='post-content')
    if not content_div:
        # Try other common content containers
        for selector in ['.entry-content', 'article', '.article-content', '.content', 'main']:
            content_div = soup.select_one(selector)
            if content_div:
                break
        
        if not content_div:
            # Last resort - use body
            content_div = soup.find('body')
    
    if not content_div:
        return paragraphs
    
    # Extract all paragraphs from content
    all_paragraphs = content_div.find_all(['p', 'h2', 'h3', 'h4'])
    
    # List of known speakers and their patterns
    speaker_patterns = {
        'Noam Chomsky': [
            r'(?:^|\W)(?:Chomsky|NC|Noam):', 
            r'(?:^|\W)Noam Chomsky:',
            r'(?:^|\W)Professor Chomsky:'
        ],
        'Vijay Prashad': [
            r'(?:^|\W)(?:Vijay|VP|Prashad):', 
            r'(?:^|\W)Vijay Prashad:'
        ],
        'Interviewer': [
            r'(?:^|\W)(?:Question|Q|Interviewer):', 
            r'(?:^|\W)(?:Journalist|Reporter|Host):'
        ]
    }
    
    # Check if this appears to be an interview
    content_text = ' '.join([p.get_text() for p in all_paragraphs])
    is_interview = any(re.search(pattern, content_text) 
                      for patterns in speaker_patterns.values() 
                      for pattern in patterns)
    
    # For solo articles, treat everything as Chomsky
    default_speaker = 'Noam Chomsky'
    current_speaker = default_speaker
    
    # Process each paragraph
    for element in all_paragraphs:
        text = element.get_text(strip=True)
        if not text:
            continue
            
        # Try to identify speaker from text
        speaker_found = False
        for speaker, patterns in speaker_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    current_speaker = speaker
                    # Remove speaker prefix from text
                    text = re.sub(pattern, '', text, 1).strip()
                    speaker_found = True
                    break
            if speaker_found:
                break
        
        # For solo articles, assume everything is by the default speaker
        if not is_interview and not speaker_found:
            current_speaker = default_speaker
            
        # Always add content, even if no speaker is identified
        if not speaker_found and is_interview:
            # In an interview but no speaker tag - use previous speaker
            pass
        
        paragraphs.append({
            'speaker': current_speaker,
            'content': text,
            'article_title': title,
            'article_date': date,
            'article_url': url
        })
        
    # If no paragraphs were processed with speakers, create a default entry
    if not paragraphs or all(p.get('speaker') != 'Noam Chomsky' for p in paragraphs):
        paragraphs.append({
            'speaker': 'Noam Chomsky',
            'content': content_div.get_text(strip=True),
            'article_title': title,
            'article_date': date,
            'article_url': url
        })
    
    return paragraphs