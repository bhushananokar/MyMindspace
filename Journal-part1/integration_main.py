#!/usr/bin/env python3
"""
AstraDB Integration for Components 2+3+4
Combines emotion analysis, semantic analysis, and feature engineering
to produce outputs formatted for AstraDB collections
"""

import sys
import uuid
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
import logging
import numpy as np
from dotenv import load_dotenv
import os
import requests

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add AstraDB imports
try:
    from astrapy import DataAPIClient
    from astrapy.exceptions import TableInsertManyException
    logger.info("✅ AstraDB client imported successfully")
except ImportError as e:
    logger.error(f"❌ AstraDB client import failed: {e}")
    logger.info("Install with: pip install astrapy")
    raise

# Add component paths to Python path
PROJECT_ROOT = Path(__file__).resolve().parent
COMP2_PATH = PROJECT_ROOT / "comp2"
COMP3_PATH = PROJECT_ROOT / "comp3"
COMP4_PATH = PROJECT_ROOT / "comp4"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(COMP2_PATH))
sys.path.insert(0, str(COMP3_PATH))
sys.path.insert(0, str(COMP4_PATH))

# Import components
try:
    from comp2.src.emotion_analyzer import EmotionAnalyzer
    from comp2.data.schemas import EmotionAnalysis, EmotionScores
    logger.info("✅ Component 2 imported successfully")
except ImportError as e:
    logger.error(f"❌ Component 2 import failed: {e}")
    raise

try:
    from comp3.src.analyzer import Component3Analyzer
    from comp3.data.schemas import SemanticAnalysis
    from comp3.src.event_extractor import EventExtractor
    logger.info("✅ Component 3 imported successfully")
except ImportError as e:
    logger.error(f"❌ Component 3 import failed: {e}")
    raise

try:
    from comp4.src.processor import Component4Processor
    from comp4.data.schemas import EngineeredFeatures, UserHistoryContext
    logger.info("✅ Component 4 imported successfully")
except ImportError as e:
    logger.error(f"❌ Component 4 import failed: {e}")
    raise

@dataclass
class AstraDBOutput:
    """Formatted output for AstraDB storage"""
    
    # Collection 1: chat_embeddings
    chat_embeddings: Dict[str, Any]
    
    # Collection 2: semantic_search
    semantic_search: Dict[str, Any]
    
    # Processing metadata
    processing_time_ms: float
    component_versions: Dict[str, str]
    timestamp: datetime

class AstraDBConnector:
    """HTTP client for chat embeddings and semantic search endpoints"""
    
    def __init__(self):
        # Get the endpoints from environment variables
        self.endpoints = {
            "chat_embeddings": os.getenv("CHAT_EMBEDDINGS_COLLECTION_ENDPOINT"),
            "semantic_search": os.getenv("SEMANTIC_SEARCH_COLLECTION_ENDPOINT")
        }
        
        # Validate endpoints
        for name, endpoint in self.endpoints.items():
            if not endpoint:
                raise ValueError(f"Missing {name.upper()}_COLLECTION_ENDPOINT environment variable")
            
            # Ensure the endpoint ends with a slash
            if not endpoint.endswith('/'):
                self.endpoints[name] = endpoint + '/'
        
        logger.info("✅ Endpoints configured for chat_embeddings and semantic_search")
    
    def push_to_collection(self, collection_name: str, data: Dict[str, Any]) -> bool:
        """Push data to the specified collection via HTTP endpoint"""
        if collection_name not in self.endpoints:
            logger.warning(f"Unsupported collection: {collection_name}. Must be one of: {list(self.endpoints.keys())}")
            return False
            
        try:
            import requests
            if collection_name == "semantic_search":
                endpoint = self.endpoints[collection_name]

                # # Check if the entry already exists in the collection by using the entry_id, if it exists give a put request request
                # response = requests.get(
                #     f"{endpoint}api/semantic-search/entries/{data['entry_id']}",
                #     headers={"Content-Type": "application/json"},
                #     timeout=10  # 10 second timeout
                # )
                # if response.status_code == 200:
                #     logger.info(f"✅ Entry {data['entry_id']} already exists in the collection, updating it")
                #     response = requests.put(
                #         f"{endpoint}api/semantic-search/entries/{data['entry_id']}",
                #         json=data,
                #         headers={"Content-Type": "application/json"},
                #         timeout=10  # 10 second timeout
                #     )
                # else:
                    # Send POST request to the appropriate endpoint
                response = requests.post(
                    f"{endpoint}api/semantic-search/entries",
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=10  # 10 second timeout
                )
            elif collection_name == "chat_embeddings":
                endpoint = self.endpoints[collection_name]
                # Send POST request to the appropriate endpoint
                # response = requests.get(
                #     f"{endpoint}api/chat-embeddings/entries/{data['entry_id']}",
                #     headers={"Content-Type": "application/json"},
                #     timeout=10  # 10 second timeout
                # )
                # if response.status_code == 200:
                #     logger.info(f"✅ Entry {data['entry_id']} already exists in the collection, updating it")
                #     response = requests.put(
                #         f"{endpoint}api/chat-embeddings/{data['entry_id']}",
                #         json=data,
                #         headers={"Content-Type": "application/json"},
                #         timeout=10  # 10 second timeout
                #     )
                # else:
                    # Send POST request to the appropriate endpoint
                response = requests.post(
                    f"{endpoint}api/chat-embeddings",
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=10  # 10 second timeout
                )

            if response.status_code == 201:
                logger.info(f"✅ Data pushed to {collection_name} collection successfully")
                return True
            else:
                logger.error(f"❌ Failed to push to {collection_name}: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout while pushing to {collection_name}")
            return False
        except Exception as e:
            logger.error(f"❌ Error pushing to {collection_name}: {str(e)}")
            return False

class UserHistoryContextClient:
    """Client for interacting with the User History Context API"""
    
    def __init__(self):
        self.base_url = os.getenv("USER_HISTORY_CONTEXT_ENDPOINT", "https://user-history-context-service-222233295505.asia-south1.run.app")
        
        # Ensure the base URL doesn't end with a slash for proper endpoint construction
        if self.base_url.endswith('/'):
            self.base_url = self.base_url.rstrip('/')
        
        logger.info(f"✅ User History Context client initialized with endpoint: {self.base_url}")
    
    def get_user_history_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user's history context from the database
        
        Args:
            user_id: User identifier
            
        Returns:
            User history context data or None if not found
        """
        try:
            # Get user's history context
            response = requests.get(
                f"{self.base_url}/api/user-history/user/{user_id}",
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Handle the API response format: {"success": true, "data": [...], "count": N}
                if isinstance(response_data, dict) and "data" in response_data:
                    contexts = response_data["data"]
                    if contexts:
                        # Return the most recent context (first in the list)
                        logger.info(f"✅ Retrieved user history context for user {user_id}")
                        return contexts[0]
                    else:
                        logger.info(f"ℹ️ No user history context found for user {user_id}")
                        return None
                elif isinstance(response_data, list) and response_data:
                    # Fallback: if response is directly a list
                    logger.info(f"✅ Retrieved user history context for user {user_id}")
                    return response_data[0]
                else:
                    logger.info(f"ℹ️ No user history context found for user {user_id}")
                    return None
            elif response.status_code == 404:
                logger.info(f"ℹ️ No user history context found for user {user_id}")
                return None
            else:
                logger.error(f"❌ Failed to retrieve user history context for user {user_id}: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout while retrieving user history context for user {user_id}")
            return None
        except Exception as e:
            logger.error(f"❌ Error retrieving user history context for user {user_id}: {str(e)}")
            return None
    
    def create_user_history_context(self, user_id: str, context_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new user history context entry
        
        Args:
            user_id: User identifier
            context_data: User history context data
            
        Returns:
            Context ID if successful, None otherwise
        """
        try:
            # Prepare the data with user_id
            context_data["user_id"] = user_id
            
            response = requests.post(
                f"{self.base_url}/api/user-history",
                json=context_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 201:
                response_data = response.json()
                if isinstance(response_data, dict) and "data" in response_data:
                    context_id = response_data["data"].get("id")
                    logger.info(f"✅ Created user history context for user {user_id}")
                    return context_id
                else:
                    logger.error(f"❌ Unexpected response format when creating user history context: {type(response_data)}")
                    return None
            else:
                logger.error(f"❌ Failed to create user history context for user {user_id}: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout while creating user history context for user {user_id}")
            return None
        except Exception as e:
            logger.error(f"❌ Error creating user history context for user {user_id}: {str(e)}")
            return None
    
    def update_user_history_context(self, context_id: str, context_data: Dict[str, Any]) -> bool:
        """
        Update an existing user history context entry
        
        Args:
            context_id: Context identifier
            context_data: Updated user history context data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.put(
                f"{self.base_url}/api/user-history/{context_id}",
                json=context_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Updated user history context {context_id}")
                return True
            else:
                logger.error(f"❌ Failed to update user history context {context_id}: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout while updating user history context {context_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Error updating user history context {context_id}: {str(e)}")
            return False

class JournalCRUDClient:
    """Client for interacting with the Journal CRUD API"""
    
    def __init__(self):
        self.base_url = os.getenv("JOURNAL_CRUD_ENDPOINT", "https://journal-crud-service-222233295505.asia-south1.run.app")
        
        # Ensure the base URL doesn't end with a slash for proper endpoint construction
        if self.base_url.endswith('/'):
            self.base_url = self.base_url.rstrip('/')
        
        logger.info(f"✅ Journal CRUD client initialized with endpoint: {self.base_url}")
    
    def get_user_journals(self, user_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve user's journal entries from the database
        
        Args:
            user_id: User identifier
            limit: Maximum number of entries to retrieve
            offset: Number of entries to skip (for pagination)
            
        Returns:
            List of journal entries
        """
        try:
            # Get user's journals with pagination
            response = requests.get(
                f"{self.base_url}/api/journals/user/{user_id}",
                params={"limit": limit, "offset": offset},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Handle the API response format: {"success": true, "data": [...], "count": N}
                if isinstance(response_data, dict) and "data" in response_data:
                    journals = response_data["data"]
                    logger.info(f"✅ Retrieved {len(journals)} journal entries for user {user_id}")
                    return journals
                elif isinstance(response_data, list):
                    # Fallback: if response is directly a list
                    journals = response_data
                    logger.info(f"✅ Retrieved {len(journals)} journal entries for user {user_id}")
                    return journals
                else:
                    logger.error(f"❌ Unexpected response format: {type(response_data)}")
                    return []
            else:
                logger.error(f"❌ Failed to retrieve journals for user {user_id}: {response.status_code} - {response.text}")
                return []
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout while retrieving journals for user {user_id}")
            return []
        except Exception as e:
            logger.error(f"❌ Error retrieving journals for user {user_id}: {str(e)}")
            return []
    
    def get_journal_by_id(self, journal_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific journal entry by ID
        
        Args:
            journal_id: Journal entry identifier
            
        Returns:
            Journal entry data or None if not found
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/journals/{journal_id}",
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Handle the API response format: {"success": true, "data": {...}}
                if isinstance(response_data, dict) and "data" in response_data:
                    journal = response_data["data"]
                    logger.info(f"✅ Retrieved journal entry {journal_id}")
                    return journal
                elif isinstance(response_data, dict) and "id" in response_data:
                    # Fallback: if response is directly the journal object
                    journal = response_data
                    logger.info(f"✅ Retrieved journal entry {journal_id}")
                    return journal
                else:
                    logger.error(f"❌ Unexpected response format for journal {journal_id}: {type(response_data)}")
                    return None
            elif response.status_code == 404:
                logger.warning(f"⚠️ Journal entry {journal_id} not found")
                return None
            else:
                logger.error(f"❌ Failed to retrieve journal {journal_id}: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout while retrieving journal {journal_id}")
            return None
        except Exception as e:
            logger.error(f"❌ Error retrieving journal {journal_id}: {str(e)}")
            return None
    
    def search_user_journals(self, user_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search user's journal entries by title, content, or tags
        
        Args:
            user_id: User identifier
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching journal entries
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/journals/user/{user_id}/search",
                params={"q": query, "limit": limit},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Handle the API response format: {"success": true, "data": [...], "count": N}
                if isinstance(response_data, dict) and "data" in response_data:
                    journals = response_data["data"]
                    logger.info(f"✅ Found {len(journals)} journal entries matching query '{query}' for user {user_id}")
                    return journals
                elif isinstance(response_data, list):
                    # Fallback: if response is directly a list
                    journals = response_data
                    logger.info(f"✅ Found {len(journals)} journal entries matching query '{query}' for user {user_id}")
                    return journals
                else:
                    logger.error(f"❌ Unexpected search response format: {type(response_data)}")
                    return []
            else:
                logger.error(f"❌ Failed to search journals for user {user_id}: {response.status_code} - {response.text}")
                return []
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout while searching journals for user {user_id}")
            return []
        except Exception as e:
            logger.error(f"❌ Error searching journals for user {user_id}: {str(e)}")
            return []

class AstraDBIntegrator:
    """
    Integrates Components 2+3+4 to produce AstraDB-formatted outputs
    """
    
    def __init__(self, config_path: str = "unified_config.yaml"):
        """Initialize the integrator with all components"""
        self.config_path = config_path
        
        # Initialize AstraDB connector
        self.astra_connector = AstraDBConnector()
        
        # Initialize Journal CRUD client
        self.journal_client = JournalCRUDClient()
        
        # Initialize User History Context client
        self.user_history_client = UserHistoryContextClient()
        
        # Initialize Component 2: Emotion Analysis
        self.emotion_analyzer = EmotionAnalyzer()
        
        # Initialize Component 3: Semantic Analysis
        self.semantic_analyzer = Component3Analyzer()
        
        # Initialize Event Extractor for temporal events
        self.event_extractor = EventExtractor()
        
        # Initialize Component 4: Feature Engineering
        self.feature_processor = Component4Processor()
        
        logger.info("✅ AstraDB Integrator initialized with all components")
    
    def _is_valid_uuid(self, uuid_string: str) -> bool:
        """Check if string is a valid UUID"""
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False
    
    def _generate_consistent_uuid(self, input_string: str) -> str:
        """Generate a consistent UUID from a string using MD5 hash"""
        import hashlib
        # Create a namespace UUID for consistent generation
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        # Generate UUID5 from the input string
        return str(uuid.uuid5(namespace, input_string))
    
    def _ensure_uuid_format(self, input_id: str) -> str:
        """Ensure the input ID is in proper UUID format"""
        if self._is_valid_uuid(input_id):
            return input_id
        else:
            # Generate a consistent UUID from the input string
            return self._generate_consistent_uuid(input_id)
    
    def _convert_api_to_user_history_context(self, api_data: Dict[str, Any]) -> Optional[UserHistoryContext]:
        """Convert API response to UserHistoryContext object"""
        try:
            if not api_data:
                return None
            
            # Parse timestamp if it exists
            last_entry_timestamp = None
            if api_data.get("last_entry_timestamp"):
                try:
                    if isinstance(api_data["last_entry_timestamp"], str):
                        last_entry_timestamp = datetime.fromisoformat(api_data["last_entry_timestamp"].replace('Z', '+00:00'))
                    else:
                        last_entry_timestamp = datetime.now()
                except (ValueError, TypeError):
                    last_entry_timestamp = datetime.now()
            
            return UserHistoryContext(
                writing_frequency_baseline=api_data.get("writing_frequency_baseline", 0.0),
                emotional_baseline=api_data.get("emotional_baseline", {}),
                topic_preferences=api_data.get("topic_preferences", []),
                behavioral_patterns=api_data.get("behavioral_patterns", {}),
                last_entry_timestamp=last_entry_timestamp,
                total_entries=api_data.get("total_entries", 0),
                avg_session_duration=api_data.get("avg_session_duration", 0.0),
                preferred_writing_times=api_data.get("preferred_writing_times", []),
                emotional_volatility=api_data.get("emotional_volatility", 0.0),
                topic_consistency=api_data.get("topic_consistency", 0.0),
                social_connectivity=api_data.get("social_connectivity", 0.0)
            )
        except Exception as e:
            logger.error(f"❌ Error converting API data to UserHistoryContext: {e}")
            return None
    
    def _convert_user_history_context_to_api(self, user_history: UserHistoryContext) -> Dict[str, Any]:
        """Convert UserHistoryContext object to API format"""
        try:
            return {
                "writing_frequency_baseline": user_history.writing_frequency_baseline,
                "emotional_baseline": user_history.emotional_baseline,
                "topic_preferences": user_history.topic_preferences,
                "behavioral_patterns": user_history.behavioral_patterns,
                "last_entry_timestamp": user_history.last_entry_timestamp.isoformat() + "Z" if user_history.last_entry_timestamp else None,
                "total_entries": user_history.total_entries,
                "avg_session_duration": user_history.avg_session_duration,
                "preferred_writing_times": user_history.preferred_writing_times,
                "emotional_volatility": user_history.emotional_volatility,
                "topic_consistency": user_history.topic_consistency,
                "social_connectivity": user_history.social_connectivity
            }
        except Exception as e:
            logger.error(f"❌ Error converting UserHistoryContext to API format: {e}")
            return {}
    
    def _fetch_user_history_context(self, user_id: str) -> Optional[UserHistoryContext]:
        """Fetch user history context from the database"""
        try:
            api_data = self.user_history_client.get_user_history_context(user_id)
            if api_data:
                return self._convert_api_to_user_history_context(api_data)
            else:
                logger.info(f"ℹ️ No user history context found for user {user_id}, will create new one")
                return None
        except Exception as e:
            logger.error(f"❌ Error fetching user history context for user {user_id}: {e}")
            return None
    
    def _save_user_history_context(self, user_id: str, user_history: UserHistoryContext) -> bool:
        """Save or update user history context in the database"""
        try:
            # First try to get existing context
            existing_context = self.user_history_client.get_user_history_context(user_id)
            
            if existing_context:
                # Update existing context
                context_id = existing_context.get("id")
                if context_id:
                    api_data = self._convert_user_history_context_to_api(user_history)
                    return self.user_history_client.update_user_history_context(context_id, api_data)
                else:
                    logger.warning(f"⚠️ Existing context found but no ID, creating new one for user {user_id}")
            else:
                # Create new context
                api_data = self._convert_user_history_context_to_api(user_history)
                context_id = self.user_history_client.create_user_history_context(user_id, api_data)
                return context_id is not None
                
        except Exception as e:
            logger.error(f"❌ Error saving user history context for user {user_id}: {e}")
            return False
    

    def process_journal_entry(
        self,
        text: str,
        user_id: str,
        session_id: str = None,
        entry_timestamp: datetime = None,
        entry_id: str = None,
        message_type: str = "user_message",
        user_history: Optional[UserHistoryContext] = None
    ) -> AstraDBOutput:
        """
        Process journal entry through complete pipeline and format for AstraDB
        
        Args:
            text: Journal entry text
            user_id: User identifier
            session_id: Session identifier
            entry_timestamp: Entry timestamp
            entry_id: Entry identifier
            message_type: Type of message (user_message, ai_response, system_message)
            user_history: User's historical context for personalized feature engineering
            
        Returns:
            AstraDBOutput with formatted data for both collections
        """
        start_time = time.time()
        
        # Set defaults
        entry_timestamp = entry_timestamp or datetime.now()
        entry_id = entry_id or str(uuid.uuid4())
        # Generate a proper UUID for session_id if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())
        elif not self._is_valid_uuid(session_id):
            # If provided session_id is not a valid UUID, generate one
            session_id = str(uuid.uuid4())

        
        logger.info(f"🔄 Processing entry {entry_id} for user {user_id}")
        
        # Fetch user history context if not provided
        if user_history is None:
            logger.info("📊 Fetching user history context from database...")
            user_history = self._fetch_user_history_context(user_id)
            if user_history is None:
                # Create a default user history context if none exists
                user_history = UserHistoryContext(
                    writing_frequency_baseline=0.0,
                    emotional_baseline={},
                    topic_preferences=[],
                    behavioral_patterns={},
                    last_entry_timestamp=None,
                    total_entries=0,
                    avg_session_duration=0.0,
                    preferred_writing_times=[],
                    emotional_volatility=0.0,
                    topic_consistency=0.0,
                    social_connectivity=0.0
                )
                logger.info("📊 Created default user history context")
        
        try:
            # Step 1: Component 2 - Emotion Analysis
            logger.info("📊 Processing emotion analysis (Component 2)...")
            emotion_result = self.emotion_analyzer.analyze_emotion(
                text=text,
                user_id=user_id
            )
            
            # Step 2: Component 3 - Semantic Analysis
            logger.info("🔍 Processing semantic analysis (Component 3)...")
            semantic_result = self.semantic_analyzer.analyze(
                processed_text=text,
                user_id=user_id,
                entry_timestamp=entry_timestamp
            )
            
            # Step 3: Extract and Store Events
            logger.info("📅 Extracting and storing temporal events...")
            event_result = self.event_extractor.extract_and_store_events(
                text=text,
                user_id=user_id,
                reference_date=entry_timestamp
            )
            logger.info(f"📅 Events processed: {event_result.get('events_extracted', 0)} extracted, {event_result.get('events_stored', 0)} stored")
            
            # Step 4: Component 4 - Feature Engineering
            logger.info("⚙️ Processing feature engineering (Component 4)...")
            
            # Create journal entry for Component 4
            journal_entry = {
                'entry_id': entry_id,
                'user_id': user_id,
                'content': text,
                'timestamp': entry_timestamp,
                'session_id': session_id,
                'emotion_analysis': emotion_result,
                'semantic_analysis': semantic_result,
                'user_history': user_history
            }
            
            engineered_features = self.feature_processor.process_journal_entry(
                emotion_analysis=emotion_result,
                semantic_analysis=semantic_result,
                user_id=user_id,
                entry_id=entry_id,
                session_id=session_id,
                entry_timestamp=entry_timestamp,
                raw_text=text,
                user_history=user_history
            )
            
            # Step 5: Format for AstraDB
            logger.info("🗄️ Formatting for AstraDB...")
            chat_embeddings = self._format_chat_embeddings(
                text=text,
                user_id=user_id,
                entry_id=entry_id,
                session_id=session_id,
                entry_timestamp=entry_timestamp,
                message_type=message_type,
                emotion_analysis=emotion_result,
                semantic_analysis=semantic_result,
                engineered_features=engineered_features
            )
            
            semantic_search = self._format_semantic_search(
                text=text,
                user_id=user_id,
                entry_id=entry_id,
                session_id=session_id,
                entry_timestamp=entry_timestamp,
                emotion_analysis=emotion_result,
                semantic_analysis=semantic_result,
                engineered_features=engineered_features
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            # Create output
            output = AstraDBOutput(
                chat_embeddings=chat_embeddings,
                semantic_search=semantic_search,
                processing_time_ms=processing_time,
                component_versions={
                    "component2": "2.0",
                    "component3": "3.0", 
                    "component4": "4.0"
                },
                timestamp=datetime.now()
            )
            
            logger.info(f"✅ Processing completed in {processing_time:.1f}ms")
            
            # Update and save user history context after processing
            try:
                logger.info("💾 Updating user history context...")
                # Update user history context with new entry information
                user_history.total_entries += 1
                user_history.last_entry_timestamp = entry_timestamp
                
                # Update preferred writing times
                hour = entry_timestamp.hour
                if hour not in user_history.preferred_writing_times:
                    user_history.preferred_writing_times.append(hour)
                    # Keep only the last 5 preferred times
                    if len(user_history.preferred_writing_times) > 5:
                        user_history.preferred_writing_times = user_history.preferred_writing_times[-5:]
                
                # Update average session duration (simplified calculation)
                if user_history.avg_session_duration == 0:
                    user_history.avg_session_duration = len(text.split()) * 0.5  # Rough estimate
                else:
                    # Update with exponential moving average
                    new_duration = len(text.split()) * 0.5
                    user_history.avg_session_duration = (user_history.avg_session_duration * 0.9) + (new_duration * 0.1)
                
                # Save updated user history context
                save_success = self._save_user_history_context(user_id, user_history)
                if save_success:
                    logger.info("✅ User history context updated successfully")
                else:
                    logger.warning("⚠️ Failed to save user history context")
                    
            except Exception as e:
                logger.error(f"❌ Error updating user history context: {e}")
                # Don't fail the entire process if user history update fails
            
            return output
            
        except Exception as e:
            logger.error(f"❌ Processing failed: {e}")
            raise

    def push_to_astra_db(self, output: AstraDBOutput) -> bool:
        """
        Push the processed data to AstraDB collections
        
        Args:
            output: AstraDBOutput containing formatted data
            
        Returns:
            bool: True if both pushes successful, False otherwise
        """
        logger.info("🚀 Pushing data to AstraDB collections...")
        
        try:
            # Push to chat_embeddings collection
            chat_success = self.astra_connector.push_to_collection(
                "chat_embeddings", 
                output.chat_embeddings
            )
            
            # Push to semantic_search collection
            search_success = self.astra_connector.push_to_collection(
                "semantic_search", 
                output.semantic_search
            )
            
            if chat_success and search_success:
                logger.info("✅ Successfully pushed data to both collections")
                return True
            else:
                logger.error("❌ Failed to push to one or both collections")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error pushing to AstraDB: {e}")
            return False

    # [Keep all the existing formatting methods unchanged]
    def _format_chat_embeddings(
        self,
        text: str,
        user_id: str,
        entry_id: str,
        session_id: str,
        entry_timestamp: datetime,
        message_type: str,
        emotion_analysis: EmotionAnalysis,
        semantic_analysis: SemanticAnalysis,
        engineered_features: EngineeredFeatures
    ) -> Dict[str, Any]:
        """Format data for chat_embeddings collection - STRICTLY following the provided schema"""
        
        # Extract embeddings from Component 3 and ensure they are proper float arrays
        primary_embedding = semantic_analysis.embeddings.primary_embedding
        lightweight_embedding = semantic_analysis.embeddings.lightweight_embedding
        
        # Convert to proper float arrays and ensure correct dimensions
        if len(primary_embedding) != 768:
            logger.warning(f"Primary embedding dimension mismatch: {len(primary_embedding)} != 768")
            primary_embedding = self._pad_or_truncate_embedding(primary_embedding, 768)
        
        if len(lightweight_embedding) != 384:
            logger.warning(f"Lightweight embedding dimension mismatch: {len(lightweight_embedding)} != 384")
            lightweight_embedding = self._pad_or_truncate_embedding(lightweight_embedding, 384)
        
        # CRITICAL: Convert to proper float arrays for AstraDB vector operations
        primary_embedding = [float(x) for x in primary_embedding]
        lightweight_embedding = [float(x) for x in lightweight_embedding]
        
        # Format emotion context - EXACTLY as per schema
        emotion_context = {
            "dominant_emotion": emotion_analysis.dominant_emotion,
            "intensity": float(emotion_analysis.intensity),
            "emotions": {
                "joy": float(emotion_analysis.emotions.joy),
                "sadness": float(emotion_analysis.emotions.sadness),
                "anger": float(emotion_analysis.emotions.anger),
                "fear": float(emotion_analysis.emotions.fear),
                "surprise": float(emotion_analysis.emotions.surprise),
                "disgust": float(emotion_analysis.emotions.disgust),
                "anticipation": float(emotion_analysis.emotions.anticipation),
                "trust": float(emotion_analysis.emotions.trust)
            }
        }
        
        # Format entities - EXACTLY as per schema
        entities_mentioned = {
            "people": [p.name for p in semantic_analysis.people],
            "locations": [l.name for l in semantic_analysis.locations],
            "organizations": [o.name for o in semantic_analysis.organizations]
        }
        
        # Format temporal context - EXACTLY as per schema
        temporal_context = {
            "hour_of_day": int(entry_timestamp.hour),
            "day_of_week": int(entry_timestamp.weekday()),
            "is_weekend": bool(entry_timestamp.weekday() >= 5)
        }
        
        # Extract semantic tags from Component 4
        semantic_tags = getattr(engineered_features.metadata, 'retrieval_triggers', []) if hasattr(engineered_features, 'metadata') else []
        
        # Extract Component 4 feature vectors and quality metrics
        feature_vector_90d = getattr(engineered_features, 'feature_vector', [])
        temporal_features_25d = getattr(engineered_features, 'temporal_features', [])
        emotional_features_20d = getattr(engineered_features, 'emotional_features', [])
        semantic_features_30d = getattr(engineered_features, 'semantic_features', [])
        user_features_15d = getattr(engineered_features, 'user_features', [])
        
        # Extract quality metrics
        feature_completeness = getattr(engineered_features, 'feature_completeness', 0.0)
        confidence_score = getattr(engineered_features, 'confidence_score', 0.0)
        
        # Generate conversation context
        conversation_context = f"Journal entry by {user_id} discussing {', '.join(semantic_tags[:3]) if semantic_tags else 'various topics'}"
        
        # STRICTLY follow the exact schema provided
        return {
            "id": str(uuid.uuid4()),
            "user_id": self._ensure_uuid_format(user_id),  # Ensure UUID format
            "entry_id": self._ensure_uuid_format(entry_id),  # Ensure UUID format
            "message_content": text,  # EXACT field name as per schema
            "message_type": message_type if message_type in ["user_message", "ai_response", "system_message"] else "user_message",
            "timestamp": entry_timestamp.isoformat() + "Z",  # ISO format with Z suffix as per schema
            "session_id": session_id,
            "conversation_context": conversation_context,
            "primary_embedding": primary_embedding,  # 768 dimensions - PROPER FLOAT ARRAY
            "lightweight_embedding": lightweight_embedding,  # 384 dimensions - PROPER FLOAT ARRAY
            "text_length": int(len(text)),  # integer as per schema
            "processing_time_ms": float(engineered_features.processing_time_ms),  # float as per schema
            "model_version": f"C2:{emotion_analysis.model_version}, C3:3.0, C4:4.0",
            "semantic_tags": semantic_tags,
            "emotion_context": emotion_context,
            "entities_mentioned": entities_mentioned,
            "temporal_context": temporal_context,
            
            # ADDITIONAL COMPONENT 4 FEATURES (Enhanced functionality)
            "feature_vector": self._safe_convert_to_float_list(feature_vector_90d),
            "temporal_features": self._safe_convert_to_float_list(temporal_features_25d),
            "emotional_features": self._safe_convert_to_float_list(emotional_features_20d),
            "semantic_features": self._safe_convert_to_float_list(semantic_features_30d),
            "user_features": self._safe_convert_to_float_list(user_features_15d),
            "feature_completeness": float(feature_completeness),
            "confidence_score": float(confidence_score)
        }
    
    def _format_semantic_search(
        self,
        text: str,
        user_id: str,
        entry_id: str,
        session_id: str,
        entry_timestamp: datetime,
        emotion_analysis: EmotionAnalysis,
        semantic_analysis: SemanticAnalysis,
        engineered_features: EngineeredFeatures
    ) -> Dict[str, Any]:
        """Format data for semantic_search collection - STRICTLY following the provided schema"""
        
        # Extract primary embedding and ensure it's a proper float array
        primary_embedding = semantic_analysis.embeddings.primary_embedding
        if len(primary_embedding) != 768:
            primary_embedding = self._pad_or_truncate_embedding(primary_embedding, 768)
        
        # CRITICAL: Convert to proper float array for AstraDB vector operations
        primary_embedding = [float(x) for x in primary_embedding]
        
        # Determine content type based on analysis
        content_type = self._determine_content_type(
            emotion_analysis, semantic_analysis, engineered_features
        )
        
        # Generate title from content
        title = self._generate_title(text, content_type)
        
        # Extract tags and Component 4 features
        tags = getattr(engineered_features.metadata, 'retrieval_triggers', []) if hasattr(engineered_features, 'metadata') else []
        
        # Extract Component 4 feature vectors for enhanced search capabilities
        feature_vector_90d = getattr(engineered_features, 'feature_vector', [])
        temporal_features_25d = getattr(engineered_features, 'temporal_features', [])
        emotional_features_20d = getattr(engineered_features, 'emotional_features', [])
        semantic_features_30d = getattr(engineered_features, 'semantic_features', [])
        user_features_15d = getattr(engineered_features, 'user_features', [])
        
        # Format linked entities - EXACTLY as per schema
        linked_entities = {
            "people": [p.name for p in semantic_analysis.people],
            "locations": [l.name for l in semantic_analysis.locations],
            "events": [e.event_text for e in semantic_analysis.future_events],
            "topics": tags
        }
        
        # Calculate search metadata - EXACTLY as per schema
        search_metadata = {
            "boost_factor": float(engineered_features.metadata.importance_score if hasattr(engineered_features.metadata, 'importance_score') else 0.5),
            "recency_weight": float(1.0),  # Can be adjusted based on business logic
            "user_preference_alignment": float(engineered_features.metadata.confidence if hasattr(engineered_features.metadata, 'confidence') else 0.5)
        }
        
        # STRICTLY follow the exact schema provided
        return {
            "id": str(uuid.uuid4()),
            "user_id": self._ensure_uuid_format(user_id),  # Ensure UUID format
            "entry_id": self._ensure_uuid_format(entry_id),  # Ensure UUID format
            "session_id": session_id,
            "content_type": content_type,
            "title": title,
            "content": text,  # EXACT field name as per schema
            "primary_embedding": primary_embedding,  # 768 dimensions - PROPER FLOAT ARRAY
            "created_at": entry_timestamp.isoformat() + "Z",  # ISO format with Z suffix as per schema
            "updated_at": entry_timestamp.isoformat() + "Z",  # ISO format with Z suffix as per schema
            "tags": tags,
            "linked_entities": linked_entities,
            "search_metadata": search_metadata,
            
            # ADDITIONAL COMPONENT 4 FEATURES (Enhanced search capabilities)
            "feature_vector": self._safe_convert_to_float_list(feature_vector_90d),
            "temporal_features": self._safe_convert_to_float_list(temporal_features_25d),
            "emotional_features": self._safe_convert_to_float_list(emotional_features_20d),
            "semantic_features": self._safe_convert_to_float_list(semantic_features_30d),
            "user_features": self._safe_convert_to_float_list(user_features_15d)
        }
    
    def _pad_or_truncate_embedding(self, embedding: List[float], target_dim: int) -> List[float]:
        """Ensure embedding has correct dimensions and proper float format"""
        # Convert to proper float array first
        float_embedding = [float(x) for x in embedding]
        
        if len(float_embedding) > target_dim:
            return float_embedding[:target_dim]
        elif len(float_embedding) < target_dim:
            return float_embedding + [0.0] * (target_dim - len(float_embedding))
        return float_embedding
    
    def _safe_convert_to_float_list(self, feature_vector) -> List[float]:
        """Safely convert numpy arrays or other iterables to float lists"""
        if feature_vector is None:
            return []
        
        try:
            # Handle numpy arrays
            if hasattr(feature_vector, 'tolist'):
                return [float(x) for x in feature_vector.tolist()]
            # Handle regular lists/iterables
            elif hasattr(feature_vector, '__iter__') and not isinstance(feature_vector, str):
                return [float(x) for x in feature_vector]
            else:
                return []
        except (ValueError, TypeError):
            return []
    
    def _determine_content_type(
        self,
        emotion_analysis: EmotionAnalysis,
        semantic_analysis: SemanticAnalysis,
        engineered_features: EngineeredFeatures
    ) -> str:
        """Determine the content type based on analysis results"""
        
        # Check for events
        if semantic_analysis.future_events:
            return "event"
        
        # Check for people mentions
        if semantic_analysis.people:
            return "person"
        
        # Check for location mentions
        if semantic_analysis.locations:
            return "location"
        
        # Check for topic diversity
        if hasattr(engineered_features.metadata, 'retrieval_triggers'):
            if len(engineered_features.metadata.retrieval_triggers) > 3:
                return "topic"
        
        # Default to journal entry
        return "journal_entry"
    
    def _generate_title(self, text: str, content_type: str) -> str:
        """Generate a title for the content"""
        if content_type == "event":
            return f"Event: {text[:50]}..."
        elif content_type == "person":
            return f"Person Mention: {text[:50]}..."
        elif content_type == "location":
            return f"Location: {text[:50]}..."
        elif content_type == "topic":
            return f"Topic Discussion: {text[:50]}..."
        else:
            return f"Journal Entry: {text[:50]}..."
    
    def batch_process(
        self,
        entries: List[Dict[str, Any]]
    ) -> List[AstraDBOutput]:
        """Process multiple journal entries in batch"""
        results = []
        session_id = str(uuid.uuid4())
        for entry in entries:
            try:
                result = self.process_journal_entry(
                    text=entry["text"],
                    user_id=entry["user_id"],
                    session_id=session_id,
                    entry_timestamp=entry.get("entry_timestamp"),
                    entry_id=entry.get("entry_id"),
                    message_type=entry.get("message_type", "user_message")
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process entry: {e}")
                continue
        
        return results
    
    def process_user_journals_from_db(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0,
        push_to_astra: bool = True
    ) -> List[AstraDBOutput]:
        """
        Process user's journal entries from the database
        
        Args:
            user_id: User identifier
            limit: Maximum number of entries to process
            offset: Number of entries to skip (for pagination)
            push_to_astra: Whether to push results to AstraDB
            
        Returns:
            List of AstraDBOutput objects
        """
        logger.info(f"🔄 Processing journal entries for user {user_id} from database...")
        
        # Retrieve journal entries from database
        journal_entries = self.journal_client.get_user_journals(user_id, limit, offset)
        
        if not journal_entries:
            logger.warning(f"⚠️ No journal entries found for user {user_id}")
            return []
        
        results = []
        successful_pushes = 0
        
        for journal_entry in journal_entries:
            try:
                # Handle case where journal_entry might be a string (API response format issue)
                if isinstance(journal_entry, str):
                    logger.warning(f"⚠️ Journal entry is a string, skipping: {journal_entry}")
                    continue
                
                # Extract data from journal entry
                journal_id = journal_entry.get("id")
                title = journal_entry.get("title", "")
                content = journal_entry.get("content", "")
                mood = journal_entry.get("mood", "neutral")
                tags = journal_entry.get("tags", [])
                created_at = journal_entry.get("createdAt")
                updated_at = journal_entry.get("updatedAt")
                
                # Parse timestamps (handle Firestore timestamp format)
                entry_timestamp = None
                if created_at:
                    try:
                        # Handle Firestore timestamp format: {"_seconds": 1757973328, "_nanoseconds": 927000000}
                        if isinstance(created_at, dict) and "_seconds" in created_at:
                            entry_timestamp = datetime.fromtimestamp(created_at["_seconds"])
                        # Handle ISO string format
                        elif isinstance(created_at, str):
                            entry_timestamp = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            entry_timestamp = datetime.now()
                    except (ValueError, TypeError, KeyError):
                        entry_timestamp = datetime.now()
                else:
                    entry_timestamp = datetime.now()
                
                # Combine title and content for processing
                full_text = f"{title}\n\n{content}" if title else content
                
                if not full_text.strip():
                    logger.warning(f"⚠️ Skipping empty journal entry {journal_id}")
                    continue
                
                logger.info(f"📝 Processing journal entry: {title[:50]}...")
                
                # Process the journal entry
                result = self.process_journal_entry(
                    text=full_text,
                    user_id=user_id,
                    entry_id=journal_id,
                    entry_timestamp=entry_timestamp,
                    message_type="user_message"  # Use valid message type for journal entries
                )
                
                results.append(result)
                
                # Push to AstraDB if requested
                if push_to_astra:
                    success = self.push_to_astra_db(result)
                    if success:
                        successful_pushes += 1
                
            except Exception as e:
                # Safe way to get journal ID for error logging
                journal_id_for_error = "unknown"
                if isinstance(journal_entry, dict):
                    journal_id_for_error = journal_entry.get('id', 'unknown')
                elif isinstance(journal_entry, str):
                    journal_id_for_error = journal_entry
                
                logger.error(f"❌ Failed to process journal entry {journal_id_for_error}: {e}")
                continue
        
        logger.info(f"✅ Processed {len(results)} journal entries, {successful_pushes} successfully pushed to AstraDB")
        return results
    
    def process_specific_journal_from_db(
        self,
        journal_id: str,
        push_to_astra: bool = True
    ) -> Optional[AstraDBOutput]:
        """
        Process a specific journal entry from the database by ID
        
        Args:
            journal_id: Journal entry identifier
            push_to_astra: Whether to push result to AstraDB
            
        Returns:
            AstraDBOutput object or None if not found
        """
        logger.info(f"🔄 Processing specific journal entry {journal_id} from database...")
        
        # Retrieve journal entry from database
        journal_entry = self.journal_client.get_journal_by_id(journal_id)
        
        if not journal_entry:
            logger.warning(f"⚠️ Journal entry {journal_id} not found")
            return None
        
        try:
            # Extract data from journal entry
            user_id = journal_entry.get("userId")
            title = journal_entry.get("title", "")
            content = journal_entry.get("content", "")
            mood = journal_entry.get("mood", "neutral")
            tags = journal_entry.get("tags", [])
            created_at = journal_entry.get("createdAt")
            
            if not user_id:
                logger.error(f"❌ Journal entry {journal_id} missing userId")
                return None
            
            # Parse timestamp (handle Firestore timestamp format)
            entry_timestamp = None
            if created_at:
                try:
                    # Handle Firestore timestamp format: {"_seconds": 1757973328, "_nanoseconds": 927000000}
                    if isinstance(created_at, dict) and "_seconds" in created_at:
                        entry_timestamp = datetime.fromtimestamp(created_at["_seconds"])
                    # Handle ISO string format
                    elif isinstance(created_at, str):
                        entry_timestamp = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        entry_timestamp = datetime.now()
                except (ValueError, TypeError, KeyError):
                    entry_timestamp = datetime.now()
            else:
                entry_timestamp = datetime.now()
            
            # Combine title and content for processing
            full_text = f"{title}\n\n{content}" if title else content
            
            if not full_text.strip():
                logger.warning(f"⚠️ Journal entry {journal_id} has empty content")
                return None
            
            logger.info(f"📝 Processing journal entry: {title[:50]}...")
            
            # Process the journal entry
            result = self.process_journal_entry(
                text=full_text,
                user_id=user_id,
                entry_id=journal_id,
                entry_timestamp=entry_timestamp,
                message_type="user_message"  # Use valid message type for journal entries
            )
            
            # Push to AstraDB if requested
            if push_to_astra:
                success = self.push_to_astra_db(result)
                if success:
                    logger.info(f"✅ Successfully pushed journal entry {journal_id} to AstraDB")
                else:
                    logger.error(f"❌ Failed to push journal entry {journal_id} to AstraDB")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to process journal entry {journal_id}: {e}")
            return None
    
    def export_for_astra_db(self, output: AstraDBOutput) -> Dict[str, Any]:
        """Export formatted data ready for AstraDB insertion"""
        return {
            "chat_embeddings": output.chat_embeddings,
            "semantic_search": output.semantic_search,
            "metadata": {
                "processing_time_ms": output.processing_time_ms,
                "component_versions": output.component_versions,
                "timestamp": output.timestamp.isoformat()
            }
        }

# Example usage and testing
if __name__ == "__main__":
    # Initialize integrator
    integrator = AstraDBIntegrator()
    
    # Example 1: Process journal entries from database for a specific user
    print("=" * 60)
    print("🔄 PROCESSING JOURNAL ENTRIES FROM DATABASE")
    print("=" * 60)
    
    # Replace with actual user ID from your database
    test_user_id = "ninad"  # Using the example user ID from the API documentation
    
    try:
        # Process user's journal entries from database
        results = integrator.process_user_journals_from_db(
            user_id=test_user_id,
            limit=5,  # Process up to 5 entries
            offset=0,
            push_to_astra=True
        )
        
        if results:
            print(f"✅ Successfully processed {len(results)} journal entries for user {test_user_id}")
            
            # Save sample output for the first entry
            if results:
                astra_data = integrator.export_for_astra_db(results[0])
                with open("astra_db_sample_output.json", "w") as f:
                    json.dump(astra_data, f, indent=2, default=str)
                print("📁 Sample output saved to astra_db_sample_output.json")
        else:
            print(f"⚠️ No journal entries found for user {test_user_id}")
            
    except Exception as e:
        print(f"❌ Database processing failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🔄 PROCESSING SPECIFIC JOURNAL ENTRY BY ID")
    print("=" * 60)
    
    # Example 2: Process a specific journal entry by ID
    # Replace with an actual journal ID from your database
    test_journal_id = "your-journal-id-here"  # Replace with actual ID
    
    try:
        # Uncomment the following lines when you have a specific journal ID
        # result = integrator.process_specific_journal_from_db(
        #     journal_id=test_journal_id,
        #     push_to_astra=True
        # )
        # 
        # if result:
        #     print(f"✅ Successfully processed journal entry {test_journal_id}")
        #     print(f"Processing time: {result.processing_time_ms:.1f}ms")
        # else:
        #     print(f"❌ Failed to process journal entry {test_journal_id}")
        
        print("ℹ️ To test specific journal processing, replace 'test_journal_id' with an actual journal ID")
        
    except Exception as e:
        print(f"❌ Specific journal processing failed: {e}")
    
    print("\n" + "=" * 60)
    print("🔄 FALLBACK: PROCESSING HARDCODED EXAMPLE")
    print("=" * 60)
    
    # Example 3: Fallback to hardcoded example (original functionality)
    try:
        # Create sample user history context
        user_history = UserHistoryContext(
            writing_frequency_baseline=0.75,
            emotional_baseline={
                "joy": 0.6,
                "sadness": 0.2,
                "anger": 0.1,
                "fear": 0.1,
                "surprise": 0.3,
                "disgust": 0.05,
                "anticipation": 0.4,
                "trust": 0.7
            },
            topic_preferences=["personal_growth", "relationships", "work", "health"],
            behavioral_patterns={
                "writing_style": "reflective",
                "session_length": "medium",
                "emotional_expression": "moderate"
            },
            last_entry_timestamp=datetime.now(),
            total_entries=25,
            avg_session_duration=15.5,
            preferred_writing_times=[9, 14, 21],
            emotional_volatility=0.3,
            topic_consistency=0.8,
            social_connectivity=0.6
        )
        
        # Test with sample journal entry
        sample_text = "I have an event at Google on 2nd of September with my friend Sarah."
        
        # Process the journal entry
        result = integrator.process_journal_entry(
            text=sample_text,
            user_id="550e8400-e29b-41d4-a716-446655440000",
            session_id="session-456",
            user_history=user_history
        )
        
        # Push to AstraDB collections
        success = integrator.push_to_astra_db(result)
        
        if success:
            print("✅ Integration and AstraDB push successful!")
            print(f"Processing time: {result.processing_time_ms:.1f}ms")
            print(f"Chat embeddings ID: {result.chat_embeddings['id']}")
            print(f"Semantic search ID: {result.semantic_search['id']}")
        else:
            print("❌ Failed to push data to AstraDB")
            
    except Exception as e:
        print(f"❌ Fallback processing failed: {e}")
        import traceback
        traceback.print_exc()
