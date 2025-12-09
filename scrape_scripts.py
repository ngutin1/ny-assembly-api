import requests 
from bs4 import BeautifulSoup
import json
import PyPDF2
from io import BytesIO
import gc
import re


def clean_date(raw_date):
    """Remove leading dashes, Part suffixes, and ampersand patterns from dates."""
    date = raw_date.strip('-')
    date = re.sub(r'-(&|-Part-).*$', '', date, flags=re.IGNORECASE)
    date = re.sub(r'-Part-\d+$', '', date, flags=re.IGNORECASE)
    return date


def scrape_links(n=None):
    url = "https://nystateassembly.granicus.com/ViewPublisher.php?view_id=6"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    transcripts = {}
    count = 0
    
    for row in soup.find_all('tr', class_=['odd', 'even']):
        if n and count >= n:
            break
        
        session_td = row.find('td', class_='listItem', id=True)
        if not session_td:
            continue
        
        raw_session_id = session_td.get('id', '')
        
        transcript_link = None
        for link in row.find_all('a'):
            if 'Transcript' in link.get_text():
                transcript_link = link.get('href')
                if transcript_link.startswith('//'):
                    transcript_link = 'https:' + transcript_link
                break
        
        if transcript_link:
            session_date = raw_session_id.replace('-Session', '')
            transcripts[session_date] = transcript_link
            count += 1
    
    return transcripts


def get_pdf_url_via_curl(transcript_url):
    import subprocess
    
    try:
        cmd = f'curl -LISs "{transcript_url}" | grep -i Location'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            location_line = result.stdout.strip()
            if 'Location:' in location_line or 'location:' in location_line:
                pdf_url = location_line.split(':', 1)[1].strip()
                
                if not pdf_url.startswith('http'):
                    pdf_url = 'https://nystateassembly.granicus.com/' + pdf_url.lstrip('/')
                
                return pdf_url
    except Exception as e:
        print(f"Error getting redirect: {e}")
    
    return None


def scrape_transcript_pdfs(transcript_dict, n=None):
    transcript_texts = {}
    
    # Group by cleaned date
    date_groups = {}
    for raw_date, transcript_url in transcript_dict.items():
        cleaned = clean_date(raw_date)
        
        if cleaned not in date_groups:
            date_groups[cleaned] = []
        
        date_groups[cleaned].append((raw_date, transcript_url))
    
    # Sort parts
    for cleaned in date_groups:
        date_groups[cleaned].sort(key=lambda x: x[0])
    
    count = 0
    for cleaned, parts in date_groups.items():
        if n and count >= n:
            break
        
        combined_text = ""
        
        print(f"Processing {cleaned} ({len(parts)} parts)")
        
        for idx, (raw_date, transcript_url) in enumerate(parts, 1):
            print(f"  {raw_date}...")
            
            pdf_url = get_pdf_url_via_curl(transcript_url)
            
            if not pdf_url:
                print(f"    Could not get PDF URL")
                continue
            
            try:
                pdf_response = requests.get(pdf_url, timeout=30)
                pdf_response.raise_for_status()
                
                pdf_bytes = BytesIO(pdf_response.content)
                pdf_reader = PyPDF2.PdfReader(pdf_bytes)
                
                part_text = ""
                for page in pdf_reader.pages:
                    part_text += page.extract_text() + "\n"
                
                if len(parts) > 1:
                    combined_text += f"\n\n--- PART {idx} ---\n\n"
                combined_text += part_text
                
                pdf_bytes.close()
                del pdf_bytes
                del pdf_response
                gc.collect()
                
                print(f"    Extracted {len(part_text)} chars")
                
            except Exception as e:
                print(f"    Error: {e}")
                continue
        
        if combined_text:
            transcript_texts[cleaned] = combined_text
            print(f"  Total: {len(combined_text)} chars\n")
        
        count += 1
    
    return transcript_texts