import re

# Event detection patterns for different categories
EVENT_PATTERNS = {
    'professional': [
        r'\binterview\b.*(?:tomorrow|today|next|this|\d)',
        r'\bmeeting\b.*(?:tomorrow|today|next|this|\d)',
        r'\bpresentation\b.*(?:tomorrow|today|next|this|\d)',
        r'\bdeadline\b.*(?:tomorrow|today|next|this|\d)',
        r'\bconference\b.*(?:tomorrow|today|next|this|\d)',
        r'\bwork\b.*(?:tomorrow|today|next|this|\d)',
        r'\b(?:have to|need to)\b.*(?:submit|deliver|present|finish)',
        r'\bdue\b.*(?:tomorrow|today|next|this|\d)',
    ],
    
    'medical': [
        r'\b(?:doctor|dentist|physician|therapist)\b.*(?:appointment|visit)',
        r'\b(?:appointment|visit)\b.*(?:doctor|dentist|physician|therapist)',
        r'\bcheckup\b.*(?:tomorrow|today|next|this|\d)',
        r'\b(?:medical|dental|therapy)\b.*(?:appointment|session)',
        r'\bsurgery\b.*(?:tomorrow|today|next|this|\d)',
        r'\b(?:prescription|medication)\b.*(?:pickup|refill)',
    ],
    
    'social': [
        r'\b(?:party|celebration|birthday)\b.*(?:tomorrow|today|next|this|\d)',
        r'\b(?:dinner|lunch|coffee|drinks)\b.*(?:with|tomorrow|today|next|this|\d)',
        r'\b(?:date|hanging out|meetup)\b.*(?:tomorrow|today|next|this|\d)',
        r'\b(?:wedding|funeral|graduation)\b.*(?:tomorrow|today|next|this|\d)',
        r'\b(?:visit|visiting)\b.*(?:family|friends|parents)',
        r'\b(?:going out|going to)\b.*(?:tomorrow|today|next|this|\d)',
    ],
    
    'personal': [
        r'\b(?:gym|workout|exercise)\b.*(?:tomorrow|today|next|this|\d)',
        r'\b(?:shopping|groceries|errands)\b.*(?:tomorrow|today|next|this|\d)',
        r'\b(?:clean|cleaning|laundry)\b.*(?:tomorrow|today|next|this|\d)',
        r'\b(?:haircut|spa|massage)\b.*(?:tomorrow|today|next|this|\d)',
        r'\b(?:hobby|practice|lesson)\b.*(?:tomorrow|today|next|this|\d)',
    ],
    
    'travel': [
        r'\b(?:flight|plane|airport)\b.*(?:tomorrow|today|next|this|\d)',
        r'\b(?:trip|vacation|travel)\b.*(?:tomorrow|today|next|this|\d)',
        r'\b(?:hotel|accommodation)\b.*(?:check|booking)',
        r'\b(?:train|bus|uber|taxi)\b.*(?:tomorrow|today|next|this|\d)',
        r'\b(?:leaving|departing|arriving)\b.*(?:tomorrow|today|next|this|\d)',
    ],
    
    'academic': [
        r'\b(?:exam|test|quiz)\b.*(?:tomorrow|today|next|this|\d)',
        r'\b(?:assignment|homework|project)\b.*(?:due|submit)',
        r'\b(?:class|lecture|seminar)\b.*(?:tomorrow|today|next|this|\d)',
        r'\b(?:study|studying)\b.*(?:tomorrow|today|next|this|\d)',
        r'\b(?:graduation|defense)\b.*(?:tomorrow|today|next|this|\d)',
    ],
    
    'financial': [
        r'\b(?:bill|payment|invoice)\b.*(?:due|pay)',
        r'\b(?:bank|financial|investment)\b.*(?:meeting|appointment)',
        r'\b(?:tax|taxes)\b.*(?:due|file|submit)',
        r'\b(?:budget|financial planning)\b.*(?:session|meeting)',
    ]
}

# Importance keywords that boost event significance scores
IMPORTANCE_KEYWORDS = {
    'high': ['important', 'crucial', 'critical', 'urgent', 'must', 'cannot miss', 'essential'],
    'medium': ['should', 'need to', 'have to', 'supposed to', 'scheduled'],
    'low': ['maybe', 'might', 'possibly', 'thinking about', 'considering']
}

# Context patterns that help determine event participants and locations
CONTEXT_PATTERNS = {
    'participants': [
        r'\bwith\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "with John", "with Mary Smith"
        r'\band\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',    # "John and Sarah"
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:is|will be|are)',  # "Sarah is coming"
    ],
    
    'locations': [
        r'\bat\s+([A-Z][a-zA-Z\s]+)',  # "at the hospital", "at Google"
        r'\bin\s+([A-Z][a-zA-Z\s]+)',  # "in New York", "in the office"
        r'\b(?:going to|headed to)\s+([A-Z][a-zA-Z\s]+)',
    ]
}

# Time-sensitive event patterns that need immediate follow-up
URGENT_EVENT_PATTERNS = [
    r'\b(?:today|tonight|this morning|this afternoon|this evening)\b',
    r'\bin\s+\d+\s+(?:hour|minute)s?\b',
    r'\b(?:emergency|urgent|asap|immediately)\b',
]

def classify_event_importance(text: str) -> float:
    """Calculate importance score based on text content"""
    text_lower = text.lower()
    score = 0.5  # Base score
    
    # Check for importance keywords
    for level, keywords in IMPORTANCE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                if level == 'high':
                    score += 0.3
                elif level == 'medium':
                    score += 0.2
                elif level == 'low':
                    score -= 0.1
    
    # Check for urgent patterns
    for pattern in URGENT_EVENT_PATTERNS:
        if re.search(pattern, text_lower):
            score += 0.2
    
    return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1