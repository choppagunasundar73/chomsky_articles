from fpdf import FPDF
from typing import List, Dict
import textwrap
import re

class PDFGenerator(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, 'Chomsky Archive Analysis', 0, 1, 'C')
        self.line(10, 20, 200, 20)
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def chapter_title(self, title, date, url):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 0, 128)  # Dark blue
        self.cell(0, 10, self.clean_text(title), 0, 1)
        self.set_font('Arial', 'I', 10)
        self.set_text_color(128, 128, 128)  # Gray
        self.cell(0, 5, f'Date: {self.clean_text(date)}', 0, 1)
        self.cell(0, 5, f'Source: {self.clean_text(url)}', 0, 1)
        self.ln(5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(10)
    
    def clean_text(self, text):
        """Clean text to handle problematic characters"""
        if not text:
            return ""
        
        # Replace problematic characters
        text = text.replace('—', '-')  # Replace em dash with hyphen
        text = text.replace('–', '-')  # Replace en dash with hyphen
        text = text.replace(''', "'")  # Replace smart quotes
        text = text.replace(''', "'")
        text = text.replace('"', '"')
        text = text.replace('"', '"')
        text = text.replace('…', '...')  # Replace ellipsis
        
        # Remove any other non-ASCII characters to be safe
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        
        return text
    
    def qa_block(self, q, a, speaker):
        # Question formatting
        self.set_font('Arial', 'BI', 12)
        self.set_text_color(0, 0, 0)
        
        # Format question with proper text wrapping - ensure no truncation
        clean_q = self.clean_text(q)
        wrapped_q = textwrap.fill(f"Q: {clean_q}", width=80)
        self.multi_cell(0, 6, wrapped_q)
        self.ln(3)
        
        # Speaker label
        self.set_font('Arial', 'B', 11)
        self.set_text_color(0, 102, 204)  # Blue
        self.cell(0, 6, f"{speaker}:", 0, 1)
        
        # Answer formatting
        self.set_font('Arial', '', 11)
        self.set_text_color(0, 0, 0)
        
        # Format answer with proper text wrapping - ensure no truncation
        clean_a = self.clean_text(a)
        
        # For very long answers, we'll chunk them into paragraphs
        paragraphs = clean_a.split('\n\n')
        if len(paragraphs) == 1 and len(clean_a) > 1000:
            # Split by sentences for very long single paragraphs
            sentences = re.split(r'(?<=[.!?])\s+', clean_a)
            current_para = ""
            new_paragraphs = []
            
            for sentence in sentences:
                if len(current_para) + len(sentence) < 1000:
                    current_para += " " + sentence
                else:
                    if current_para:
                        new_paragraphs.append(current_para.strip())
                    current_para = sentence
            
            if current_para:
                new_paragraphs.append(current_para.strip())
            
            paragraphs = new_paragraphs
        
        # Write each paragraph with spacing between them
        for i, para in enumerate(paragraphs):
            wrapped_para = textwrap.fill(para, width=80)
            self.multi_cell(0, 6, wrapped_para)
            if i < len(paragraphs) - 1:
                self.ln(3)
        
        self.ln(10)
        self.set_draw_color(200, 200, 200)  # Light gray
        self.dashed_line(20, self.get_y(), 190, self.get_y(), 1, 1)
        self.ln(10)

def create_pdf(data: List[Dict], filename: str):
    pdf = PDFGenerator()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Group data by article
    articles = {}
    for item in data:
        article_id = f"{item['article_title']} ({item['article_date']})"
        if article_id not in articles:
            articles[article_id] = {
                'title': item['article_title'],
                'date': item['article_date'],
                'url': item['article_url'],
                'qa_pairs': []
            }
        articles[article_id]['qa_pairs'].append(item)
    
    # Process each article
    for article_id, article in articles.items():
        pdf.chapter_title(article['title'], article['date'], article['url'])
        
        # Add Q&A pairs
        for qa in article['qa_pairs']:
            pdf.qa_block(qa['question'], qa['answer'], qa['speaker'])
            
        pdf.add_page()
    
    pdf.output(filename)