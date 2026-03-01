import aiohttp
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ExternalServiceError(Exception):
    """Raised when the external MeditationDB API returns an error."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code

# ==================== SCHEMA CONSTANTS ====================

VALID_MEDITATION_TYPES = {
    'mindfulness', 'breathing', 'body_scan', 'loving_kindness',
    'walking', 'guided_imagery', 'mantra', 'zen', 'vipassana',
    'transcendental', 'movement', 'sound_bath'
}

VALID_GOALS = {
    'stress_reduction', 'better_sleep', 'focus', 'emotional_balance',
    'anxiety_relief', 'pain_management', 'spiritual_growth', 'creativity',
    'self_awareness', 'compassion', 'patience', 'mindful_eating'
}

VALID_EXPERIENCE_LEVELS = {'beginner', 'intermediate', 'advanced'}

VALID_RECOMMENDATION_SOURCES = {
    'text_analysis', 'audio_analysis', 'user_history', 'similarity_match',
    'preference_based', 'random', 'manual', 'ai_recommendation'
}

_MEDITATION_TYPE_MAP = {
    'Mindfulness Meditation': 'mindfulness',
    'Body Scan Meditation': 'body_scan',
    'Breathing Meditation': 'breathing',
    'Loving-Kindness Meditation': 'loving_kindness',
    'Progressive Muscle Relaxation': 'mindfulness',
    'Zen Meditation': 'zen',
    'Walking Meditation': 'walking',
    'Visualization Meditation': 'guided_imagery',
    'Vipassana Meditation': 'vipassana',
    'Transcendental Meditation': 'transcendental',
    'Movement Meditation': 'movement',
    'Sound Bath Meditation': 'sound_bath',
    'Guided Imagery': 'guided_imagery',
    'Mantra Meditation': 'mantra',
}


def normalize_meditation_type(value: str) -> str:
    """Convert any meditation type string to a valid API enum value."""
    if not value:
        return 'mindfulness'
    if value in VALID_MEDITATION_TYPES:
        return value
    mapped = _MEDITATION_TYPE_MAP.get(value)
    if mapped:
        return mapped
    normalized = value.lower().replace(' ', '_').replace('-', '_')
    if normalized in VALID_MEDITATION_TYPES:
        return normalized
    return 'mindfulness'


def normalize_recommendation_source(value: str) -> str:
    """Convert any recommendation source to a valid API enum value."""
    if value in VALID_RECOMMENDATION_SOURCES:
        return value
    mapping = {
        'rule_based': 'text_analysis',
        'text_analysis_with_personalization': 'text_analysis',
        'multimodal_with_personalization': 'audio_analysis',
        'ml_enhanced': 'ai_recommendation',
        'text_processing': 'text_analysis',
        'audio_processing': 'audio_analysis',
    }
    return mapping.get(value, 'ai_recommendation')


class MeditationDBAPIClient:
    """
    HTTP client for MeditationDB API.
    Each method sends only the fields allowed by the server-side Joi schemas.
    """

    def __init__(self, base_url: str = "https://meditationdb-api-222233295505.asia-south1.run.app"):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api"
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        session = await self._get_session()
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        headers = {"Content-Type": "application/json"} if data is not None else {}

        try:
            async with session.request(
                method=method, url=url, json=data, params=params, headers=headers
            ) as response:
                if response.status in (200, 201):
                    result = await response.json()
                    return result.get('data', result) if 'data' in result else result
                if response.status == 404:
                    return None
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"API Error {response.status}: {error_text}")
                    raise ExternalServiceError(
                        f"API request failed with status {response.status}: {error_text}",
                        status_code=response.status
                    )
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise

    # ==================== HEALTH CHECK ====================

    async def health_check(self) -> Dict[str, Any]:
        """GET /health  (root level, not under /api)"""
        session = await self._get_session()
        url = f"{self.base_url}/health"
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            raise ExternalServiceError(
                f"Health check failed with status {response.status}",
                status_code=response.status
            )

    async def get_api_info(self) -> Dict[str, Any]:
        return await self._make_request("GET", "/info")

    # ==================== USER OPERATIONS ====================
    # Schema: name(req), email(opt), preferences(opt)

    async def create_user(self, user_data: Dict[str, Any]) -> str:
        preferences = dict(user_data.get("preferences") or {})

        # Normalise experience level
        if preferences.get("experience_level") not in VALID_EXPERIENCE_LEVELS:
            preferences["experience_level"] = "beginner"

        # Filter goals to valid values
        if "goals" in preferences:
            preferences["goals"] = [g for g in preferences["goals"] if g in VALID_GOALS]
        else:
            preferences["goals"] = ["stress_reduction"]

        # Normalise and filter favorite_meditations
        if "favorite_meditations" in preferences:
            preferences["favorite_meditations"] = [
                normalize_meditation_type(m) for m in preferences["favorite_meditations"]
            ]

        # Strip unknown preference keys
        allowed_pref_keys = {
            "experience_level", "preferred_duration",
            "favorite_meditations", "goals", "notification_preferences"
        }
        preferences = {k: v for k, v in preferences.items() if k in allowed_pref_keys}

        api_data: Dict[str, Any] = {
            "name": user_data.get("name", ""),
            "preferences": preferences,
        }
        email = user_data.get("email")
        if email:
            api_data["email"] = email

        result = await self._make_request("POST", "/users", api_data)
        return result.get("id") or result.get("_id")

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self._make_request("GET", f"/users/{user_id}")

    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        allowed = {"name", "email", "preferences"}
        result = await self._make_request(
            "PUT", f"/users/{user_id}", {k: v for k, v in updates.items() if k in allowed}
        )
        return result is not None

    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        allowed_keys = {
            "experience_level", "preferred_duration",
            "favorite_meditations", "goals", "notification_preferences"
        }
        filtered = {k: v for k, v in preferences.items() if k in allowed_keys}
        result = await self._make_request("PUT", f"/users/{user_id}/preferences", filtered)
        return result is not None

    async def get_users(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        result = await self._make_request("GET", "/users", params={"limit": limit, "offset": offset})
        return result if isinstance(result, list) else (result.get("users", []) if result else [])

    # ==================== SESSION OPERATIONS ====================
    # Schema: user_id(req), input_type(req: text|audio|hybrid), input_data(req)
    # input_data allowed: diary_text, audio_url, filename, file_size, content_type

    async def create_session(self, session_data: Dict[str, Any]) -> str:
        input_data = session_data.get("input_data") or {}
        allowed_input = {"diary_text", "audio_url", "filename", "file_size", "content_type"}
        filtered_input = {k: v for k, v in input_data.items() if k in allowed_input}

        input_type = session_data.get("input_type", "text")
        if input_type not in ("text", "audio", "hybrid"):
            input_type = "text"

        api_data = {
            "user_id": session_data.get("user_id"),
            "input_type": input_type,
            "input_data": filtered_input,
        }
        result = await self._make_request("POST", "/sessions", api_data)
        return result.get("id") or result.get("_id")

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return await self._make_request("GET", f"/sessions/{session_id}")

    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        allowed = {"status", "results", "error", "completed_at"}
        result = await self._make_request(
            "PUT", f"/sessions/{session_id}", {k: v for k, v in updates.items() if k in allowed}
        )
        return result is not None

    async def update_session_status(self, session_id: str, status: str) -> bool:
        if status not in {"pending", "processing", "completed", "failed"}:
            logger.warning(f"Invalid session status '{status}', skipping")
            return False
        result = await self._make_request("PUT", f"/sessions/{session_id}", {"status": status})
        return result is not None

    async def update_session_results(self, session_id: str, results: Dict[str, Any]) -> bool:
        # Normalise recommendations inside results
        if "recommendations" in results:
            clean = []
            for rec in results["recommendations"]:
                clean.append({
                    "meditation_type": normalize_meditation_type(rec.get("meditation_type", "")),
                    "confidence": float(rec.get("confidence", 0.5)),
                    "rationale": str(rec.get("rationale", ""))[:500],
                    "source": normalize_recommendation_source(rec.get("source", "")),
                })
            results = {**results, "recommendations": clean}

        # Normalise method
        if "method" in results:
            valid_methods = {"text_processing", "audio_processing", "hybrid", "similarity_match"}
            method_map = {
                "text_analysis": "text_processing",
                "text_analysis_with_personalization": "text_processing",
                "multimodal_with_personalization": "hybrid",
                "rule_based": "text_processing",
            }
            if results["method"] not in valid_methods:
                results["method"] = method_map.get(results["method"], "text_processing")

        # PUT /sessions/{id}/results — body is the results object directly
        result = await self._make_request("PUT", f"/sessions/{session_id}/results", results)
        return result is not None

    async def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        result = await self._make_request("GET", f"/sessions/user/{user_id}", params={"limit": limit})
        return result if isinstance(result, list) else (result.get("sessions", []) if result else [])

    async def get_sessions(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status
        result = await self._make_request("GET", "/sessions", params=params)
        return result if isinstance(result, list) else (result.get("sessions", []) if result else [])

    # ==================== FEEDBACK OPERATIONS ====================
    # Schema: user_id(req), session_id(req), meditation_type(req enum), rating(req 1-5)
    # Optional: comment(max 2000), effectiveness_metrics, session_context

    async def create_feedback(self, feedback_data: Dict[str, Any]) -> str:
        api_data: Dict[str, Any] = {
            "user_id": feedback_data.get("user_id"),
            "session_id": feedback_data.get("session_id"),
            "meditation_type": normalize_meditation_type(
                feedback_data.get("meditation_type", "mindfulness")
            ),
            "rating": feedback_data.get("rating"),
        }
        comment = feedback_data.get("comment") or feedback_data.get("feedback_text")
        if comment:
            api_data["comment"] = str(comment)[:2000]
        result = await self._make_request("POST", "/feedback", api_data)
        return result.get("id") or result.get("_id")

    async def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        return await self._make_request("GET", f"/feedback/{feedback_id}")

    async def get_user_feedback(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        result = await self._make_request("GET", f"/feedback/user/{user_id}", params={"limit": limit})
        return result if isinstance(result, list) else (result.get("feedback", []) if result else [])

    async def get_session_feedback(self, session_id: str) -> List[Dict[str, Any]]:
        result = await self._make_request("GET", f"/feedback/session/{session_id}")
        return result if isinstance(result, list) else (result.get("feedback", []) if result else [])

    # ==================== VECTOR OPERATIONS ====================
    # Schema: entity_id(req), entity_type(req enum), embedding(req 384-dim), metadata(req)
    # metadata allowed: dimension, version, success_rate, session_count, favorite_meditations,
    #                   avg_rating, last_meditation, total_duration, preferred_times,
    #                   stress_patterns, emotion_trends

    _ALLOWED_META_KEYS = {
        "dimension", "version", "success_rate", "session_count",
        "favorite_meditations", "avg_rating", "last_meditation",
        "total_duration", "preferred_times", "stress_patterns", "emotion_trends"
    }

    async def create_vector(self, vector_data: Dict[str, Any]) -> str:
        entity_type = vector_data.get("entity_type", "user")
        if entity_type not in ("user", "session", "meditation", "audio"):
            entity_type = "user"

        raw_meta = vector_data.get("metadata") or {}
        metadata = {k: v for k, v in raw_meta.items() if k in self._ALLOWED_META_KEYS}

        api_data = {
            "entity_id": vector_data.get("entity_id"),
            "entity_type": entity_type,
            "embedding": vector_data.get("embedding", []),
            "metadata": metadata,
        }
        result = await self._make_request("POST", "/vectors", api_data)
        return result.get("id") or result.get("_id")

    async def get_vector(self, vector_id: str) -> Optional[Dict[str, Any]]:
        return await self._make_request("GET", f"/vectors/{vector_id}")

    async def get_vectors_by_entity_type(self, entity_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        result = await self._make_request("GET", f"/vectors/type/{entity_type}", params={"limit": limit})
        return result if isinstance(result, list) else (result.get("data", []) if result else [])

    async def get_vectors_by_entity_id(self, entity_id: str, entity_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"limit": limit}
        if entity_type:
            params["source_type"] = entity_type
        result = await self._make_request("GET", f"/vectors/source/{entity_id}", params=params)
        return result if isinstance(result, list) else (result.get("data", []) if result else [])

    async def vector_similarity_search(
        self,
        query_vector: List[float],
        entity_type: str = "user",
        limit: int = 10,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        # POST /vectors/similarity/search
        api_data = {
            "query_vector": query_vector,
            "vector_type": entity_type,
            "limit": limit,
            "min_similarity": min_similarity,
        }
        result = await self._make_request("POST", "/vectors/similarity/search", api_data)
        return result if isinstance(result, list) else (result.get("results", []) if result else [])

    async def get_meditation_recommendations_by_vector(
        self,
        user_vector: List[float],
        user_preferences: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        # POST /vectors/recommendations/meditation
        api_data = {
            "user_vector": user_vector,
            "user_preferences": user_preferences or {},
            "limit": limit,
        }
        result = await self._make_request("POST", "/vectors/recommendations/meditation", api_data)
        return result if isinstance(result, list) else (result.get("recommendations", []) if result else [])

    # kept for backwards compat — returns empty since we don't have the vector here
    async def get_meditation_recommendations(
        self,
        user_id: str,  # noqa: ARG002
        user_preferences: Optional[Dict[str, Any]] = None,  # noqa: ARG002
        limit: int = 5  # noqa: ARG002
    ) -> List[Dict[str, Any]]:
        return []

    # ==================== HISTORY OPERATIONS ====================
    # Schema required: user_id, session_id, meditation_type(enum), confidence_score(0-1),
    #                  duration_planned(positive), recommendation_source(enum)

    async def create_history_entry(self, history_data: Dict[str, Any]) -> str:
        duration_planned = (
            history_data.get("duration_planned")
            or history_data.get("duration")
            or 10
        )
        api_data: Dict[str, Any] = {
            "user_id": history_data.get("user_id"),
            "session_id": history_data.get("session_id"),
            "meditation_type": normalize_meditation_type(
                history_data.get("meditation_type", "mindfulness")
            ),
            "confidence_score": max(0.0, min(1.0, float(history_data.get("confidence_score", 0.5)))),
            "duration_planned": duration_planned,
            "recommendation_source": normalize_recommendation_source(
                history_data.get("recommendation_source", "ai_recommendation")
            ),
        }
        rating = history_data.get("success_rating") or history_data.get("rating")
        if rating is not None:
            api_data["success_rating"] = rating
        notes = history_data.get("notes", "")
        if notes:
            api_data["notes"] = str(notes)[:1000]
        duration_completed = history_data.get("duration_completed")
        if duration_completed is not None:
            api_data["duration_completed"] = duration_completed

        result = await self._make_request("POST", "/history", api_data)
        return result.get("id") or result.get("_id")

    async def get_user_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        result = await self._make_request("GET", f"/history/user/{user_id}", params={"limit": limit})
        return result if isinstance(result, list) else (result.get("history", []) if result else [])

    async def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        result = await self._make_request("GET", f"/history/user/{user_id}/progress")
        return result or {}

    # ==================== ANALYTICS ====================

    async def get_analytics_overview(self, timeframe: str = "30d") -> Dict[str, Any]:
        result = await self._make_request("GET", "/analytics/overview", params={"timeframe": timeframe})
        return result or {}

    async def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        result = await self._make_request("GET", f"/users/{user_id}/analytics")
        return result or {}


# ==================== SINGLETON ====================

_api_client: Optional[MeditationDBAPIClient] = None


def get_api_client() -> MeditationDBAPIClient:
    global _api_client
    if _api_client is None:
        _api_client = MeditationDBAPIClient()
    return _api_client


async def close_api_client():
    global _api_client
    if _api_client:
        await _api_client.close()
        _api_client = None
