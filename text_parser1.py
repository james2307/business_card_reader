import re

def extract_information(text):
    """
    Extract relevant information from OCR text
    
    Args:
        text: string containing all extracted text from the image
    
    Returns:
        dict: containing extracted information
    """
    # Initialize dictionary to store extracted information
    info = {
        'company': '',
        'phone': '',
        'email': '',
        'address': ''
    }
    
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        info['email'] = emails[0]
    
    # Phone pattern (handles various formats)
    phone_pattern = r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phones = re.findall(phone_pattern, text)
    if phones:
        info['phone'] = phones[0]
    
    # Extract potential company name (usually in all caps or followed by Inc., LLC, etc.)
    company_pattern = r'\b[A-Z][A-Z\s&]+(?:\s(?:INC|LLC|CORP|LTD|CO|COMPANY|CORPORATION|LIMITED))?\.?\b'
    companies = re.findall(company_pattern, text)
    if companies:
        info['company'] = companies[0]
    
    # Address pattern (this is a simplified version)
    # Looking for patterns like street numbers followed by text and state codes
    address_pattern = r'\d+\s+[A-Za-z0-9\s,]+(?:Road|Rd|Street|St|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Drive|Dr)[A-Za-z0-9\s,]*'
    addresses = re.findall(address_pattern, text, re.IGNORECASE)
    if addresses:
        info['address'] = addresses[0]
    
    return info
