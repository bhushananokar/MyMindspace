import spacy
import re
from typing import List, Dict, Set
from collections import defaultdict, Counter
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from data.schemas import PersonEntity, LocationEntity, OrganizationEntity

class EntityExtractor:
    """Extract people, locations, and organizations using spaCy NER"""
    
    def __init__(self, model_name: str = "en_core_web_lg"):
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            print(f"Model {model_name} not found. Install with: python -m spacy download {model_name}")
            # Fallback to smaller model
            self.nlp = spacy.load("en_core_web_sm")
        
        # Relationship context patterns
        self.relationship_patterns = {
            'family': ['mom', 'dad', 'mother', 'father', 'brother', 'sister', 'son', 'daughter', 
                      'husband', 'wife', 'grandmother', 'grandfather', 'aunt', 'uncle', 'cousin'],
            'friend': ['friend', 'buddy', 'pal', 'bestie', 'bff'],
            'colleague': ['colleague', 'coworker', 'boss', 'manager', 'teammate', 'supervisor'],
            'romantic': ['boyfriend', 'girlfriend', 'partner', 'spouse', 'fiance', 'fiancee'],
            'professional': ['doctor', 'dentist', 'therapist', 'teacher', 'lawyer', 'accountant']
        }
        
        # Common organization indicators
        self.org_indicators = {
            'company': ['inc', 'corp', 'llc', 'ltd', 'company', 'corporation'],
            'school': ['university', 'college', 'school', 'institute', 'academy'],
            'medical': ['hospital', 'clinic', 'medical center', 'health center'],
            'government': ['department', 'ministry', 'agency', 'bureau', 'office']
        }
    
    def extract_entities(self, text: str) -> tuple:
        """Extract all entities and return (people, locations, organizations)"""
        doc = self.nlp(text)
        
        # Extract entities using spaCy
        people = self._extract_people(doc, text)
        locations = self._extract_locations(doc)
        organizations = self._extract_organizations(doc, text)
        
        # Build entity relationships
        relationships = self._build_relationships(people, doc, text)
        
        return people, locations, organizations, relationships
    
    def _extract_people(self, doc, text: str) -> List[PersonEntity]:
        """Extract people with relationship context"""
        people = []
        person_counts = Counter()
        
        # Get PERSON entities from spaCy
        for ent in doc.ents:
            if ent.label_ == "PERSON" and len(ent.text.strip()) > 1:
                name = ent.text.strip()
                person_counts[name] += 1
        
        # Create PersonEntity objects with relationship context
        for name, count in person_counts.items():
            relationship_type = self._detect_relationship(name, text)
            context_clues = self._get_person_context(name, text)
            
            person = PersonEntity(
                name=name,
                relationship_type=relationship_type,
                context_clues=context_clues,
                confidence=min(0.9, 0.6 + (count * 0.1)),  # Higher confidence for multiple mentions
                mentions=count
            )
            people.append(person)
        
        return people
    
    def _extract_locations(self, doc) -> List[LocationEntity]:
        """Extract locations and classify them"""
        locations = []
        location_counts = Counter()
        
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC"] and len(ent.text.strip()) > 1:
                name = ent.text.strip()
                location_counts[name] += 1
        
        for name, count in location_counts.items():
            loc_type = self._classify_location(name)
            
            location = LocationEntity(
                name=name,
                location_type=loc_type,
                confidence=min(0.9, 0.7 + (count * 0.05))
            )
            locations.append(location)
        
        return locations
    
    def _extract_organizations(self, doc, text: str) -> List[OrganizationEntity]:
        """Extract organizations and classify them"""
        organizations = []
        org_counts = Counter()
        
        for ent in doc.ents:
            if ent.label_ == "ORG" and len(ent.text.strip()) > 1:
                name = ent.text.strip()
                org_counts[name] += 1
        
        for name, count in org_counts.items():
            org_type = self._classify_organization(name, text)
            context = self._get_org_context(name, text)
            
            organization = OrganizationEntity(
                name=name,
                org_type=org_type,
                context=context,
                confidence=min(0.9, 0.6 + (count * 0.1))
            )
            organizations.append(organization)
        
        return organizations
    
    def _detect_relationship(self, name: str, text: str) -> str:
        """Detect relationship type based on context"""
        text_lower = text.lower()
        name_lower = name.lower()
        
        # Look for relationship indicators near the name
        for rel_type, indicators in self.relationship_patterns.items():
            for indicator in indicators:
                # Check patterns like "my friend John" or "John, my friend"
                patterns = [
                    f"my {indicator} {name_lower}",
                    f"{name_lower}, my {indicator}",
                    f"{name_lower} is my {indicator}",
                    f"with my {indicator} {name_lower}"
                ]
                
                for pattern in patterns:
                    if pattern in text_lower:
                        return rel_type
        
        return "unknown"
    
    def _get_person_context(self, name: str, text: str) -> List[str]:
        """Get context clues around person mentions"""
        sentences = text.split('.')
        context_clues = []
        
        for sentence in sentences:
            if name in sentence:
                # Extract relevant context words
                words = sentence.split()
                name_indices = [i for i, word in enumerate(words) if name.lower() in word.lower()]
                
                for idx in name_indices:
                    # Get words around the name
                    start = max(0, idx - 3)
                    end = min(len(words), idx + 4)
                    context = ' '.join(words[start:end])
                    context_clues.append(context.strip())
        
        return list(set(context_clues))
    
    def _classify_location(self, name: str) -> str:
        """Classify location type"""
        name_lower = name.lower()
        
        # Check for common location indicators
        if any(indicator in name_lower for indicator in ['city', 'town', 'village']):
            return 'city'
        elif any(indicator in name_lower for indicator in ['country', 'nation']):
            return 'country'
        elif any(indicator in name_lower for indicator in ['street', 'avenue', 'road', 'drive']):
            return 'address'
        elif any(indicator in name_lower for indicator in ['hospital', 'school', 'office', 'mall']):
            return 'building'
        else:
            return 'place'
    
    def _classify_organization(self, name: str, text: str) -> str:
        """Classify organization type"""
        name_lower = name.lower()
        text_lower = text.lower()
        
        for org_type, indicators in self.org_indicators.items():
            if any(indicator in name_lower for indicator in indicators):
                return org_type
        
        # Check context for additional clues
        if any(word in text_lower for word in ['work', 'job', 'office', 'company']):
            return 'company'
        elif any(word in text_lower for word in ['class', 'study', 'learn']):
            return 'school'
        
        return 'organization'
    
    def _get_org_context(self, name: str, text: str) -> str:
        """Get context around organization mentions"""
        sentences = text.split('.')
        
        for sentence in sentences:
            if name in sentence:
                return sentence.strip()
        
        return ""
    
    def _build_relationships(self, people: List[PersonEntity], doc, text: str) -> Dict[str, List[str]]:
        """Build relationships between entities"""
        relationships = defaultdict(list)
        
        # Simple co-occurrence relationship building
        person_names = [p.name for p in people]
        
        for i, person1 in enumerate(person_names):
            for j, person2 in enumerate(person_names):
                if i != j:
                    # Check if they appear in the same sentence
                    sentences = text.split('.')
                    for sentence in sentences:
                        if person1 in sentence and person2 in sentence:
                            relationships[person1].append(person2)
        
        return dict(relationships)