import requests 
import PyPDF2
from io import BytesIO
import re

PATTERNS = {
        #Member speaking 
        'speaker': re.compile(
            r'^(MR\.|MRS\.|MS\.|ACTING SPEAKER|THE CLERK)\s+([A-Z\-\']+):\s+(.+?)(?=^(?:MR\.|MRS\.|MS\.|ACTING SPEAKER|THE CLERK|\(|\[))',
            re.MULTILINE | re.DOTALL
        ),
        
        #Bill information
        'bill_number': re.compile(r'(?:Assembly|Senate) No\.\s+([AS]\d{5}(?:-[A-Z])?)', re.IGNORECASE),
        'calendar_number': re.compile(r'Calendar No\.\s+(\d+)', re.IGNORECASE),
        'rules_report': re.compile(r'Rules Report No\.\s+(\d+)', re.IGNORECASE),
        
        #Session metadata
        'session_date': re.compile(r'^[\d]*([A-Z]+,\s+[A-Z]+\s+\d{1,2},\s+\d{4})', re.MULTILINE),
        'page_number': re.compile(r'NYS ASSEMBLY\s+JUNE \d{1,2}, \d{4}\s*\n\s*(\d+)', re.MULTILINE),
        
        #Interaction patterns
        'yield_question': re.compile(
            r'Will\s+(?:the\s+sponsor|(?:Mr\.|Mrs\.|Ms\.)\s+([A-Z\-\']+))\s+yield',
            re.IGNORECASE
        ),
        'direct_address': re.compile(
            r'((?:Mr\.|Mrs\.|Ms\.)\s+[A-Z\-\']+)',
            re.IGNORECASE
        ),
        'thank_response': re.compile(
            r'Thank you,?\s+((?:Mr\.|Mrs\.|Ms\.)\s+[A-Z\-\']+)',
            re.IGNORECASE
        ),
        
        #Questions (for counting)
        'question_mark': re.compile(r'\?'),
        
        #Procedural
        'motion': re.compile(r'\bmove\b', re.IGNORECASE),
        'call_committee': re.compile(r'call.*?committee', re.IGNORECASE),
        
        #Sentiment patterns (NEW)
        'agreement': re.compile(
            r'\b(I agree|I support|I\'m in favor|absolutely|exactly|correct|that\'s right|I concur|yes)\b',
            re.IGNORECASE
        ),
        'disagreement': re.compile(
            r'\b(I disagree|I oppose|I\'m against|I object|that\'s incorrect|that\'s wrong|respectfully disagree|I don\'t think|I would argue)\b',
            re.IGNORECASE
        ),
        'amendment_offer': re.compile(
            r'\b(I offer (?:the following )?amendment|I have an amendment|amendment to|propose an amendment|following amendment)\b',
            re.IGNORECASE
        ),
        'amendment_number': re.compile(
            r'amendment\s+(?:number\s+)?(\d+)',
            re.IGNORECASE
        ),
    }


def clean_speech_text(text: str) -> str:
    """
    Clean up speech text by removing date artifacts and other noise.
    
    Removes:
    - Date lines like "NYS ASSEMBLY                     JUNE 11, 2025"
    - Standalone page numbers
    - Excessive whitespace
    - Leading/trailing newlines
    
    """
    # Remove the NYS ASSEMBLY date line pattern
    # Pattern: "NYS ASSEMBLY" followed by spaces and date
    text = re.sub(
        r'\n?NYS ASSEMBLY\s+[A-Z]+\s+\d{1,2},\s+\d{4}\s*\n?',
        '\n',
        text
    )
    
    # Remove standalone page numbers (just digits on their own line)
    text = re.sub(r'\n\d{1,4}\n', '\n', text)
    
    # Remove page numbers at start of lines (like "2to dispense")
    text = re.sub(r'\n\d{1,3}([a-z])', r'\n\1', text)
    
    # Clean up multiple newlines to max 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Clean up multiple spaces
    text = re.sub(r' {2,}', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text

def extract_bill_context(text: str) -> dict:
        """Extract current bill context from text"""
        context = {}
        
        # Extract bill number
        bill_match = PATTERNS['bill_number'].search(text)
        if bill_match:
            context['bill_number'] = bill_match.group(1)
        
        # Extract calendar number
        cal_match = PATTERNS['calendar_number'].search(text)
        if cal_match:
            context['calendar_number'] = cal_match.group(1)
        
        # Extract rules report
        rules_match = PATTERNS['rules_report'].search(text)
        if rules_match:
            context['rules_report_number'] = rules_match.group(1)
        
        return context


def analyze_sentiment(text: str) -> str:
    """
    Determine sentiment/tone of the text.
    
    Returns:
        'agreement', 'disagreement', 'amendment_offer', or 'neutral'
    """
    # Check in priority order
    if PATTERNS['amendment_offer'].search(text):
        return 'amendment_offer'
    elif PATTERNS['disagreement'].search(text):
        return 'disagreement'
    elif PATTERNS['agreement'].search(text):
        return 'agreement'
    else:
        return 'neutral'

    
def extract_interactions(
    speaker_data: list[dict],
    mem_table = None
) -> list[dict]:
    interactions = []
    
    # Extract all member names and create lookup
    member_name_set = set()
    member_name_to_id = {}
    
    for entry in speaker_data:
        name = entry['name'].upper().strip()
        member_id = entry.get('member_id')
        
        # Only include actual members (not speakers/clerks without IDs)
        if member_id is not None:
            member_name_set.add(name)
            member_name_to_id[name] = member_id
    
    # Process each speaker entry
    for idx, entry in enumerate(speaker_data):
        from_member_name = entry['name'].upper().strip()
        from_member_id = entry.get('member_id')
        speech_text = entry['text']
        date = entry['date']
        sequence = entry['sequence']
        
        # Skip if not a member OR if it's an acting speaker/clerk
        if from_member_id is None or 'ACTING SPEAKER' in from_member_name or 'CLERK' in from_member_name:
            continue
        
        # Analyze sentiment for this speech
        sentiment = analyze_sentiment(speech_text)
        
        # Check for yield/question pattern
        yield_match = PATTERNS['yield_question'].search(speech_text)
        if yield_match:
            # If named member, construct normalized name
            if yield_match.group(1):
                last_name = yield_match.group(1).upper()
                to_member_name = _find_matching_member(last_name, member_name_set)
                to_member_id = member_name_to_id.get(to_member_name)
            # If "the sponsor", try to find from context
            else:
                to_member_name, to_member_id = _find_sponsor_from_context(speaker_data, idx, member_name_to_id)
            
            if to_member_name and to_member_id and to_member_id != from_member_id:
                interactions.append({
                    'from_member_id': from_member_id,
                    'from_member_name': from_member_name,
                    'to_member_id': to_member_id,
                    'to_member_name': to_member_name,
                    'interaction_type': 'question',
                    'sentiment': sentiment,  # NEW
                    'text_snippet': yield_match.group(0),
                    'date': date,
                    'sequence': sequence
                })
        
        # Check for direct address
        address_matches = PATTERNS['direct_address'].finditer(speech_text)
        
        for match in address_matches:
            # Normalize the full address - REMOVE NEWLINES!
            addressed_name = match.group(1).upper().strip()
            addressed_name = re.sub(r'\s+', ' ', addressed_name)  # This replaces newlines with spaces
            
            to_member_id = member_name_to_id.get(addressed_name)
            
            # Only include if it's a known member and not self
            if addressed_name in member_name_set and to_member_id and to_member_id != from_member_id:
                # Avoid duplicates from yield pattern
                if not any(
                    i['from_member_id'] == from_member_id and 
                    i['to_member_id'] == to_member_id and 
                    i['sequence'] == sequence
                    for i in interactions
                ):
                    interactions.append({
                        'from_member_id': from_member_id,
                        'from_member_name': from_member_name,
                        'to_member_id': to_member_id,
                        'to_member_name': addressed_name,
                        'interaction_type': 'address',
                        'sentiment': sentiment,  # NEW
                        'text_snippet': match.group(0),
                        'date': date,
                        'sequence': sequence
                    })
                break  # Only record first address per speech
        
        # Check for thank you response
        thank_match = PATTERNS['thank_response'].search(speech_text)
        if thank_match:
            addressed_name = thank_match.group(1).upper().strip()
            addressed_name = re.sub(r'\s+', ' ', addressed_name)
            
            to_member_id = member_name_to_id.get(addressed_name)
            
            if addressed_name in member_name_set and to_member_id and to_member_id != from_member_id:
                if not any(
                    i['from_member_id'] == from_member_id and 
                    i['to_member_id'] == to_member_id and 
                    i['sequence'] == sequence
                    for i in interactions
                ):
                    interactions.append({
                        'from_member_id': from_member_id,
                        'from_member_name': from_member_name,
                        'to_member_id': to_member_id,
                        'to_member_name': addressed_name,
                        'interaction_type': 'response',
                        'sentiment': sentiment,  # NEW
                        'text_snippet': thank_match.group(0),
                        'date': date,
                        'sequence': sequence
                    })
    
    return interactions


def _find_matching_member(last_name: str, member_name_set: set) -> str:
    last_name_upper = last_name.upper()
    for full_name in member_name_set:
        # Check if this full name ends with the last name
        if full_name.endswith(last_name_upper):
            return full_name
    return None


def _find_sponsor_from_context(speaker_data: list[dict], current_idx: int, member_name_to_id: dict) -> tuple:
    '''
    Find the sponsor from context by looking back at recent speakers.
    Returns (member_name, member_id) tuple or (None, None)
    '''
    # Look back up to 5 entries
    for i in range(current_idx - 1, max(0, current_idx - 6), -1):
        entry = speaker_data[i]
        name = entry['name'].upper().strip()
        member_id = entry.get('member_id')
        
        # Skip acting speaker entries and non-members
        if member_id is None:
            continue
        if 'ACTING SPEAKER' in name or 'CLERK' in name:
            continue
        
        # Return the name and ID
        return (name, member_id)
    
    return (None, None)