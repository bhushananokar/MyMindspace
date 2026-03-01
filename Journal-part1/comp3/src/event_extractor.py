import re
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
import sys
import os
import json
import requests
from datetime import datetime


# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.date_parser import DateParser
from data.event_patterns import EVENT_PATTERNS, classify_event_importance, CONTEXT_PATTERNS
from data.schemas import ExtractedEvent, FollowupQuestion

class EventExtractor:
    """Extract future events and generate follow-up questions (Component 8)"""
    
    def __init__(self):
        self.date_parser = DateParser()
        self.followup_templates = {
            'professional': {
                'before': [
                    "How are you feeling about your {event_type} {time_ref}? Any last-minute preparations?",
                    "Your {event_type} is coming up {time_ref}. Are you ready for it?",
                    "Getting nervous about your {event_type} {time_ref}? Want to talk through it?"
                ],
                'after': [
                    "How did your {event_type} go {time_ref}? I remember you were {emotion} about it.",
                    "Hope your {event_type} went well {time_ref}! How do you feel it turned out?",
                    "How was your {event_type} {time_ref}? Did everything go as expected?"
                ]
            },
            'medical': {
                'before': [
                    "Your {event_type} is {time_ref}. Any concerns you want to talk about?",
                    "How are you feeling about your {event_type} {time_ref}?",
                    "Your {event_type} is coming up {time_ref}. Everything going okay?"
                ],
                'after': [
                    "How was your {event_type} {time_ref}? Everything go smoothly?",
                    "Hope your {event_type} went well {time_ref}. How are you feeling?",
                    "How did your {event_type} turn out {time_ref}? Any good news?"
                ]
            },
            'social': {
                'before': [
                    "Looking forward to {event_type} {time_ref}? You seemed {emotion} when you mentioned it.",
                    "Your {event_type} is {time_ref}. Excited about it?",
                    "How are you feeling about {event_type} {time_ref}?"
                ],
                'after': [
                    "How was {event_type} {time_ref}? Did you have a good time?",
                    "Hope you enjoyed {event_type} {time_ref}! How did it go?",
                    "How was {event_type} {time_ref}? Fun catching up with everyone?"
                ]
            },
            'personal': {
                'before': [
                    "You mentioned {event_type} {time_ref}. Still planning on it?",
                    "How's your motivation for {event_type} {time_ref}?",
                    "Ready for {event_type} {time_ref}?"
                ],
                'after': [
                    "How did {event_type} go {time_ref}? Feel good about it?",
                    "Did you manage to {event_type} {time_ref}? How was it?",
                    "Hope {event_type} went well {time_ref}!"
                ]
            }
        }
    
    def extract_events(self, text: str, reference_date: datetime = None) -> List[ExtractedEvent]:
        """Extract future events from text"""
        if reference_date is None:
            reference_date = datetime.now()
        
        events = []
        
        # Check each event category
        for event_type, patterns in EVENT_PATTERNS.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                
                for match in matches:
                    event = self._create_event_from_match(
                        match, text, event_type, reference_date
                    )
                    if event:
                        events.append(event)
        
        # Remove duplicates and merge similar events
        events = self._deduplicate_events(events)
        
        return events
    
    def generate_followup_questions(self, events: List[ExtractedEvent], 
                                  reference_date: datetime = None) -> List[FollowupQuestion]:
        """Generate follow-up questions for events"""
        if reference_date is None:
            reference_date = datetime.now()
        
        followups = []
        
        for event in events:
            if not event.parsed_date:
                continue
            
            # Generate before-event questions
            days_until = (event.parsed_date - reference_date).days
            if 0 <= days_until <= 3:  # Event is 0-3 days away
                before_question = self._generate_before_question(event, days_until)
                if before_question:
                    followups.append(before_question)
            
            # Generate after-event questions
            days_since = (reference_date - event.parsed_date).days
            if 0 <= days_since <= 2:  # Event was 0-2 days ago
                after_question = self._generate_after_question(event, days_since)
                if after_question:
                    followups.append(after_question)
        
        return followups
    
    def _create_event_from_match(self, match, text: str, event_type: str, 
                               reference_date: datetime) -> Optional[ExtractedEvent]:
        """Create ExtractedEvent from regex match"""
        event_text = match.group(0)
        
        # Parse date from the matched text and surrounding context
        context_start = max(0, match.start() - 50)
        context_end = min(len(text), match.end() + 50)
        context = text[context_start:context_end]
        
        parsed_date, date_confidence, original_date_text = self.date_parser.parse_date(
            context, reference_date
        )
        
        # Skip if no date found or date is in the past
        if not parsed_date or parsed_date < reference_date:
            return None
        
        # Extract additional details
        participants = self._extract_participants(context)
        location = self._extract_location(context)
        subtype = self._extract_event_subtype(event_text, event_type)
        importance_score = classify_event_importance(context)
        
        return ExtractedEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            event_text=event_text,
            event_type=event_type,
            event_subtype=subtype,
            parsed_date=parsed_date,
            original_date_text=original_date_text,
            participants=participants,
            location=location,
            importance_score=importance_score,
            confidence=min(date_confidence, 0.8),
            emotional_context={}  # Will be filled by emotion analysis
        )
    
    def _extract_participants(self, text: str) -> List[str]:
        """Extract people mentioned in event context"""
        participants = []
        
        for pattern in CONTEXT_PATTERNS['participants']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            participants.extend(matches)
        
        return list(set(participants))
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location mentioned in event context"""
        for pattern in CONTEXT_PATTERNS['locations']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_event_subtype(self, event_text: str, event_type: str) -> Optional[str]:
        """Extract more specific event subtype"""
        event_text_lower = event_text.lower()
        
        subtypes = {
            'professional': {
                'interview': ['interview'],
                'meeting': ['meeting', 'call', 'conference'],
                'presentation': ['presentation', 'demo', 'pitch'],
                'deadline': ['deadline', 'due', 'submit'],
                'conference': ['conference', 'summit', 'seminar']
            },
            'medical': {
                'appointment': ['appointment', 'visit'],
                'checkup': ['checkup', 'check-up', 'physical'],
                'procedure': ['surgery', 'procedure', 'operation'],
                'therapy': ['therapy', 'counseling', 'session']
            },
            'social': {
                'party': ['party', 'celebration', 'birthday'],
                'meal': ['dinner', 'lunch', 'brunch', 'coffee'],
                'date': ['date', 'romantic'],
                'family': ['family', 'reunion', 'visit'],
                'wedding': ['wedding', 'marriage', 'ceremony']
            }
        }
        
        if event_type in subtypes:
            for subtype, keywords in subtypes[event_type].items():
                if any(keyword in event_text_lower for keyword in keywords):
                    return subtype
        
        return None
    
    def _deduplicate_events(self, events: List[ExtractedEvent]) -> List[ExtractedEvent]:
        """Remove duplicate and very similar events"""
        if not events:
            return events
        
        unique_events = []
        
        for event in events:
            is_duplicate = False
            
            for existing in unique_events:
                # Check if events are very similar
                if (existing.parsed_date and event.parsed_date and 
                    abs((existing.parsed_date - event.parsed_date).total_seconds()) < 3600 and  # Within 1 hour
                    existing.event_type == event.event_type):
                    
                    # Merge if confidence is higher
                    if event.confidence > existing.confidence:
                        unique_events.remove(existing)
                        unique_events.append(event)
                    
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_events.append(event)
        
        return unique_events
    
    def _generate_before_question(self, event: ExtractedEvent, days_until: int) -> Optional[FollowupQuestion]:
        """Generate question to ask before an event"""
        if event.event_type not in self.followup_templates:
            return None
        
        templates = self.followup_templates[event.event_type]['before']
        template = templates[hash(event.event_id) % len(templates)]  # Consistent selection
        
        # Format time reference
        if days_until == 0:
            time_ref = "today"
        elif days_until == 1:
            time_ref = "tomorrow"
        else:
            time_ref = f"in {days_until} days"
        
        question_text = template.format(
            event_type=event.event_subtype or event.event_type,
            time_ref=time_ref,
            emotion="excited"  # Default emotion, will be replaced with actual emotion
        )
        
        return FollowupQuestion(
            event_id=event.event_id,
            question_text=question_text,
            question_type="before_event",
            optimal_timing=event.parsed_date - timedelta(hours=6),  # 6 hours before
            context_needed={
                'event': event,
                'days_until': days_until
            }
        )
    
    def _generate_after_question(self, event: ExtractedEvent, days_since: int) -> Optional[FollowupQuestion]:
        """Generate question to ask after an event"""
        if event.event_type not in self.followup_templates:
            return None
        
        templates = self.followup_templates[event.event_type]['after']
        template = templates[hash(event.event_id) % len(templates)]
        
        # Format time reference
        if days_since == 0:
            time_ref = "today"
        elif days_since == 1:
            time_ref = "yesterday"
        else:
            time_ref = f"{days_since} days ago"
        
        question_text = template.format(
            event_type=event.event_subtype or event.event_type,
            time_ref=time_ref,
            emotion="nervous"  # Default emotion
        )
        
        return FollowupQuestion(
            event_id=event.event_id,
            question_text=question_text,
            question_type="after_event",
            optimal_timing=event.parsed_date + timedelta(hours=18),  # 18 hours after
            context_needed={
                'event': event,
                'days_since': days_since
            }
        )
    
    def store_events_to_db(self, events: List[ExtractedEvent], user_id: str, db_endpoint: str = os.getenv("TEMPORAL_DB_ENDPOINT")) -> Dict:
        """Store extracted events to database via API endpoint"""
        stored_events = []
        errors = []
        
        for event in events:
            try:
                # Prepare data matching your database schema
                event_data = {
                    "event_id": event.event_id,
                    "user_id": user_id,
                    "event_text": event.event_text,
                    "event_type": event.event_type,
                    "event_subtype": event.event_subtype,
                    "parsed_date": event.parsed_date.isoformat() if event.parsed_date else None,
                    "original_date_text": event.original_date_text,
                    "participants": event.participants,
                    "location": event.location,
                    "importance_score": event.importance_score,
                    "confidence": event.confidence,
                    "emotional_context": json.dumps(event.emotional_context),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                # POST to database endpoint
                response = requests.post(
                    db_endpoint,
                    json=event_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code == 201:
                    stored_events.append(event.event_id)
                else:
                    errors.append(f"Failed to store {event.event_id}: {response.text}")
                    
            except Exception as e:
                errors.append(f"Error storing {event.event_id}: {str(e)}")
        
        return {
            "success": len(stored_events),
            "failed": len(errors),
            "stored_event_ids": stored_events,
            "errors": errors
        }

    def extract_and_store_events(self, text: str, user_id: str, reference_date: datetime = None, db_endpoint: str = os.getenv("TEMPORAL_DB_ENDPOINT")) -> Dict:
        """Extract events from text and store them to database"""
        try:
            # Extract events
            events = self.extract_events(text, reference_date)
            
            if not events:
                return {
                    "success": True,
                    "message": "No events found in text",
                    "events_extracted": 0,
                    "events_stored": 0
                }
            
            # Store to database
            storage_result = self.store_events_to_db(events, user_id, db_endpoint)
            
            return {
                "success": True,
                "message": f"Extracted {len(events)} events, stored {storage_result['success']}",
                "events_extracted": len(events),
                "events_stored": storage_result['success'],
                "failed_storage": storage_result['failed'],
                "stored_event_ids": storage_result['stored_event_ids'],
                "errors": storage_result['errors']
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "events_extracted": 0,
                "events_stored": 0
            }

