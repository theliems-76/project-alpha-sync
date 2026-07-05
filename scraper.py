import os
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

def fetch_data(url, result_key):
    response = requests.get(url)
    response.raise_for_status()
    return response.json().get(result_key, [])

def clean_html_to_markdown(html_content):
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for elem in soup.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style', 'iframe']):
        elem.decompose()
        
    markdown_content = md(str(soup), heading_style="ATX", escape_asterisks=False)
    return markdown_content

def save_markdown(article, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    article_id = article.get('id', '')
    title = article.get('title', 'Untitled')
    url = article.get('html_url', '')
    
    slug = "".join(c if c.isalnum() else "-" for c in title.lower())
    import re
    slug = re.sub(r'-+', '-', slug).strip('-')
    
    file_name = f"{article_id}-{slug}.md"
    file_path = os.path.join(output_dir, file_name)
    
    markdown_body = clean_html_to_markdown(article.get('body', ''))
    
    final_content = f"# {title}\n\nArticle URL: {url}\n\n{markdown_body}"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
        
    return file_path

def run_scraper(output_dir="docs", min_articles=30, priority_keyword="youtube"):
    articles_processed = 0
    saved_ids = set()
    
    if priority_keyword:
        search_url = f"https://support.optisigns.com/api/v2/help_center/articles/search.json?query={priority_keyword}"
        results = fetch_data(search_url, 'results')
        for article in results:
            if articles_processed >= min_articles:
                break
            save_markdown(article, output_dir)
            saved_ids.add(article.get('id'))
            articles_processed += 1
            
    base_url = "https://support.optisigns.com/api/v2/help_center/en-us/articles.json"
    page = 1
    
    while articles_processed < min_articles:
        url = f"{base_url}?page={page}&per_page=30"
        articles = fetch_data(url, 'articles')
        
        if not articles:
            break
            
        for article in articles:
            if article.get('id') in saved_ids:
                continue
                
            save_markdown(article, output_dir)
            saved_ids.add(article.get('id'))
            articles_processed += 1
            if articles_processed >= min_articles:
                break
                
        page += 1
        
    return articles_processed

if __name__ == "__main__":
    count = run_scraper()
    print(f"Successfully scraped and converted {count} articles.")
