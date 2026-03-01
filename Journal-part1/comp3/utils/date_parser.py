import re
from datetime import datetime, timedelta
from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta
from typing import Optional, Tuple

class DateParser:
    """Handles relative and absolute date parsing for event extraction"""
    
    def __init__(self):
        self.relative_patterns = {
            # Today/Tomorrow patterns
            r'\btomorrow\b': lambda base: base + timedelta(days=1),
            r'\btoday\b': lambda base: base,
            r'\byesterday\b': lambda base: base - timedelta(days=1),
            
            # This/Next week patterns
            r'\bthis (\w+)\b': self._parse_this_weekday,
            r'\bnext (\w+)\b': self._parse_next_weekday,
            
            # In X time patterns
            r'\bin (\d+) days?\b': lambda base, match: base + timedelta(days=int(match.group(1))),
            r'\bin (\d+) weeks?\b': lambda base, match: base + timedelta(weeks=int(match.group(1))),
            r'\bin (\d+) months?\b': lambda base, match: base + relativedelta(months=int(match.group(1))),
            
            # X days/weeks from now
            r'(\d+) days? from now': lambda base, match: base + timedelta(days=int(match.group(1))),
            r'(\d+) weeks? from now': lambda base, match: base + timedelta(weeks=int(match.group(1))),
            
            # Next month/year
            r'\bnext month\b': lambda base: base + relativedelta(months=1),
            r'\bnext year\b': lambda base: base + relativedelta(years=1),
        }
        
        self.weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
    
    def parse_date(self, text: str, reference_date: datetime = None) -> Tuple[Optional[datetime], float, str]:
        """
        Parse date from text, return (datetime, confidence, original_text)
        """
        if reference_date is None:
            reference_date = datetime.now()
        
        text_lower = text.lower()
        
        # Try relative date patterns first
        for pattern, parser_func in self.relative_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                try:
                    if 'this' in pattern or 'next' in pattern:
                        parsed_date = parser_func(reference_date, match.group(1))
                    elif callable(parser_func) and match.groups():
                        parsed_date = parser_func(reference_date, match)
                    else:
                        parsed_date = parser_func(reference_date)
                    
                    return parsed_date, 0.9, match.group(0)
                except Exception:
                    continue
        
        # Try absolute date parsing with dateutil
        try:
            # Look for date-like patterns
            date_patterns = [
                r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
                r'\b(\w+ \d{1,2},? \d{4})\b',
                r'\b(\w+ \d{1,2})\b',
                r'\b(\d{1,2} \w+)\b',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    date_str = match.group(1)
                    try:
                        parsed_date = dateutil_parser.parse(date_str, default=reference_date)
                        # If year not specified and date is in past, assume next year
                        if parsed_date < reference_date and len(date_str.split()) < 3:
                            parsed_date = parsed_date.replace(year=reference_date.year + 1)
                        return parsed_date, 0.8, date_str
                    except Exception:
                        continue
        except Exception:
            pass
        
        return None, 0.0, ""
    
    def _parse_this_weekday(self, base_date: datetime, weekday: str) -> datetime:
        """Parse 'this Monday', 'this Friday', etc."""
        weekday = weekday.lower()
        if weekday not in self.weekdays:
            raise ValueError(f"Unknown weekday: {weekday}")
        
        target_weekday = self.weekdays[weekday]
        current_weekday = base_date.weekday()
        
        days_ahead = target_weekday - current_weekday
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        return base_date + timedelta(days=days_ahead)
    
    def _parse_next_weekday(self, base_date: datetime, weekday: str) -> datetime:
        """Parse 'next Monday', 'next Friday', etc."""
        weekday = weekday.lower()
        if weekday not in self.weekdays:
            raise ValueError(f"Unknown weekday: {weekday}")
        
        target_weekday = self.weekdays[weekday]
        current_weekday = base_date.weekday()
        
        days_ahead = target_weekday - current_weekday
        if days_ahead <= 0:
            days_ahead += 7
        days_ahead += 7  # Next week, not this week
        
        return base_date + timedelta(days=days_ahead)
    
    def extract_time_from_text(self, text: str) -> Tuple[Optional[str], float]:
        """Extract time patterns like '3pm', '10:30', 'morning', etc."""
        time_patterns = [
            r'\b(\d{1,2}:\d{2})\s*(am|pm)?\b',
            r'\b(\d{1,2})\s*(am|pm)\b',
            r'\b(morning)\b',
            r'\b(afternoon)\b',
            r'\b(evening)\b',
            r'\b(night)\b',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(0), 0.8
        
        return None, 0.0