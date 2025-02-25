import requests
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import urljoin

def get_all_article_links(main_url):
    """Get all article links from the Chomsky.info articles page with improved scraping."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    try:
        response = requests.get(main_url, headers=headers, timeout=10)
        response.raise_for_status()  # Check for HTTP errors
        
        soup = BeautifulSoup(response.content, 'html.parser')
        article_links = []
        
        # Try multiple selector patterns to find articles
        article_containers = soup.select('.post-list article, article.post, .articles-list .article, .entry')
        if not article_containers:
            # If specific containers aren't found, look for any links that might be articles
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                # Look for date patterns in URLs which often indicate articles
                if re.search(r'/\d{8}/', href) or re.search(r'/\d{6}/', href) or re.search(r'/\d{4}/\d{2}/\d{2}/', href):
                    article_links.append(urljoin(main_url, href))
        else:
            for container in article_containers:
                links = container.find_all('a', href=True)
                for link in links:
                    article_links.append(urljoin(main_url, link['href']))
        
        # If still no links found, try a more general approach
        if not article_links:
            # Look for links in any list-like structure
            list_items = soup.find_all('li')
            for li in list_items:
                links = li.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    # Check if it looks like an article URL (contains a date or specific pattern)
                    if ('chomsky.info' in href and not href.endswith('.jpg') and not href.endswith('.png')):
                        article_links.append(urljoin(main_url, href))
        
        # Last resort: get any link that looks like a Chomsky article
        if not article_links:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link['href']
                # Match patterns like /20200826/ which are common in Chomsky's articles
                if re.search(r'/\d{8}/', href) or re.search(r'/\d{6}/', href):
                    article_links.append(urljoin(main_url, href))
        
        # Remove duplicates and non-article links
        article_links = list(set(article_links))
        article_links = [link for link in article_links if 'chomsky.info' in link and '#' not in link]
        
        return article_links
    
    except Exception as e:
        print(f"Error fetching article links: {str(e)}")
        return []

def extract_article_content(url):
    """Extract content from an article page with improved robustness."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    
    try:
        # Add a small delay to avoid overloading the server
        time.sleep(random.uniform(0.5, 1.5))
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try different selectors for title
        title = None
        for selector in ['h1.entry-title', 'h1.post-title', 'h1', '.article-title']:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.text.strip()
                break
        
        if not title:
            title = "Untitled Article"
        
        # Try different selectors for date
        date = None
        date_selectors = ['time', '.post-date', '.entry-date', '.date', 'meta[property="article:published_time"]']
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                if date_elem.has_attr('datetime'):
                    date = date_elem['datetime']
                    break
                else:
                    date = date_elem.text.strip()
                    break
        
        if not date:
            # Try to extract date from URL or other elements
            date_match = re.search(r'/(\d{8})/', url)
            if date_match:
                date_str = date_match.group(1)
                date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            else:
                date = "Unknown Date"
        
        # Try different selectors for content
        content = None
        content_selectors = ['.post-content', '.entry-content', 'article', '.article-content', '.content', 'main']
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content = content_elem
                break
        
        if not content:
            # If no specific content container found, use the body and remove headers/footers
            content = soup.find('body')
            # Remove navigation, header, footer, etc.
            for elem in content.select('nav, header, footer, .sidebar, .navigation, .comments'):
                if elem:
                    elem.decompose()
        
        return {
            'title': title,
            'date': date,
            'content': content.get_text('\n', strip=True) if content else "",
            'html_content': str(content) if content else "",
            'url': url
        }
    
    except Exception as e:
        print(f"Error extracting content from {url}: {str(e)}")
        return {
            'title': "Error Extracting Content",
            'date': "Unknown Date",
            'content': f"Error occurred: {str(e)}",
            'html_content': "",
            'url': url
        }