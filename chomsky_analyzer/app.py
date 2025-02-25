import streamlit as st
from scraper.content_fetcher import get_all_article_links, extract_article_content
from scraper.article_parser import parse_dialogue
from processing.qa_generator import create_qa_pairs
from processing.pdf_builder import create_pdf
import tempfile
import os
import time
import pandas as pd

def main():
    st.set_page_config(page_title="Chomsky Archive Analyzer", page_icon="📚", layout="wide")
    
    st.title("🧠 Chomsky Archive Analyzer")
    st.markdown("""
    This tool analyzes articles from Chomsky.info, converts them into Q&A format, 
    and generates a comprehensive PDF for better understanding of Chomsky's views.
    """)
    
    # Sidebar controls
    st.sidebar.header("Configuration")
    
    # API key input with default
    api_key = st.sidebar.text_input(
        "OpenRouter API Key", 
        value="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",
        type="password"
    )
    
    # Article limit
    article_limit = st.sidebar.slider(
        "Number of articles to process", 
        min_value=1, 
        max_value=20, 
        value=3,
        help="Higher values will take longer to process"
    )
    
    # Filter options
    include_interviews = st.sidebar.checkbox("Include interviews", value=True)
    include_solo_articles = st.sidebar.checkbox("Include solo articles", value=True)
    
    # Speaker filter
    speaker_filter = st.sidebar.multiselect(
        "Filter by speakers",
        ["Noam Chomsky", "Vijay Prashad", "All other speakers"],
        default=["Noam Chomsky"]
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Process Articles"):
            if not api_key:
                st.error("Please enter your OpenRouter API key first!")
                return
                
            with st.spinner("Fetching article links..."):
                # Scrape articles
                base_url = "https://chomsky.info/articles/"
                articles = get_all_article_links(base_url)
                st.success(f"Found {len(articles)} articles")
                
                # Display progress bar
                progress_bar = st.progress(0)
                article_status = st.empty()
                
                processed_data = []
                
                for i, url in enumerate(articles[:article_limit]):
                    article_status.info(f"Processing article {i+1}/{article_limit}: {url}")
                    
                    try:
                        content = extract_article_content(url)
                        paragraphs = parse_dialogue(content['html_content'], url)
                        
                        # Debug information
                        st.write(f"Found {len(paragraphs)} paragraphs in {url}")
                        speakers = set(p['speaker'] for p in paragraphs)
                        st.write(f"Detected speakers: {', '.join(speakers)}")
                        
                        # Apply filters
                        if paragraphs:
                            # Skip based on interview/solo filters
                            if len(speakers) > 1 and not include_interviews:
                                continue
                            if len(speakers) == 1 and not include_solo_articles:
                                continue
                                
                            # Skip based on speaker filter
                            if "Noam Chomsky" not in speaker_filter and "Noam Chomsky" in speakers:
                                if "All other speakers" not in speaker_filter:
                                    continue
                            if "Vijay Prashad" not in speaker_filter and "Vijay Prashad" in speakers:
                                if "All other speakers" not in speaker_filter:
                                    continue
                        
                        qa_pairs = create_qa_pairs(paragraphs)
                        
                        # More debug information
                        st.write(f"Generated {len(qa_pairs)} Q&A pairs")
                        
                        processed_data.extend(qa_pairs)
                        
                    except Exception as e:
                        st.error(f"Error processing {url}: {str(e)}")
                        import traceback
                        st.error(traceback.format_exc())
                    
                    # Update progress
                    progress_bar.progress((i + 1) / article_limit)
                    time.sleep(0.1)  # Small delay for better UI experience
                
                article_status.success(f"Processing complete! Generated {len(processed_data)} Q&A pairs")
                
                # Generate PDF
                if processed_data:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        create_pdf(processed_data, tmp.name)
                        
                        with open(tmp.name, "rb") as f:
                            pdf_data = f.read()
                            
                        st.session_state['pdf_data'] = pdf_data
                        st.session_state['pdf_filename'] = f"chomsky_analysis_{len(processed_data)}_qa_pairs.pdf"
                        st.session_state['processed_data'] = processed_data
                        
                    os.unlink(tmp.name)
                else:
                    st.error("No data was processed. Try adjusting your filters.")
    
    with col2:
        if 'pdf_data' in st.session_state:
            st.success("✅ PDF Generated Successfully!")
            st.download_button(
                "📥 Download PDF",
                st.session_state['pdf_data'],
                file_name=st.session_state['pdf_filename'],
                mime="application/pdf"
            )
            
            # Show a preview of the data
            if 'processed_data' in st.session_state and st.session_state['processed_data']:
                st.subheader("Q&A Preview")
                
                sample_data = st.session_state['processed_data'][:5]  # Show first 5 items
                
                for i, qa in enumerate(sample_data):
                    with st.expander(f"Q: {qa['question'][:50]}..."):
                        st.markdown(f"**Speaker:** {qa['speaker']}")
                        st.markdown(f"**Article:** {qa['article_title']}")
                        st.markdown(f"**Answer:** {qa['answer'][:200]}...")

if __name__ == "__main__":
    main()