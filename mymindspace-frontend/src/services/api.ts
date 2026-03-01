/// <reference types="vite/client" />
// ─── Base URLs from environment ───────────────────────────────────────────────
export const THERAPIST_HTTP = import.meta.env.VITE_THERAPIST_API_URL ?? 'http://localhost:8002';
export const THERAPIST_WS = import.meta.env.VITE_THERAPIST_WS_URL ?? 'ws://localhost:8002';
export const TTS_HTTP = import.meta.env.VITE_TTS_API_URL ?? 'http://localhost:8003';
export const TTS_WS = import.meta.env.VITE_TTS_WS_URL ?? 'ws://localhost:8003';
export const STT_HTTP = import.meta.env.VITE_STT_API_URL ?? 'http://localhost:8004';
export const MEDITATION_HTTP = import.meta.env.VITE_MEDITATION_API_URL ?? 'http://localhost:8000';
export const JOURNAL_HTTP = import.meta.env.VITE_JOURNAL_PROCESSING_API_URL ?? 'http://localhost:8001';
export const GEMINI_ENGINE_HTTP = import.meta.env.VITE_GEMINI_ENGINE_URL ?? 'http://localhost:8007';

// ─── Generic fetch helper ─────────────────────────────────────────────────────
async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as any).detail ?? (err as any).message ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

const json = (body: object) => ({
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});

// ─── Types ────────────────────────────────────────────────────────────────────
export interface Patient {
  id: number;
  name: string;
  date_of_birth?: string;
  created_date: string;
  detected_symptoms?: string[];
}

export interface Session {
  id: number;
  patient_id: number;
  session_date: string;
  current_phase: string;
  conversation_history: ConversationTurn[];
  detected_symptoms: string[];
  assessment_results: Record<string, unknown>;
  generated_goals: Record<string, unknown>;
  session_completed: boolean;
  crisis_flags: string[];
  total_exchanges: number;
  goals?: TreatmentGoal[];
  homework?: HomeworkAssignment[];
}

export interface ConversationTurn {
  user: string;
  ai: string;
  timestamp: string;
  phase: string;
}

export interface TreatmentGoal {
  id: number;
  patient_id: number;
  session_id: number;
  description: string;
  status: 'active' | 'completed';
  current_progress: number;
}

export interface HomeworkAssignment {
  id: number;
  patient_id: number;
  session_id: number;
  type: string;
  description: string;
  completed: boolean;
  due_date: string;
}

export interface PatientDashboard {
  patient: Patient;
  recent_sessions: Session[];
  active_goals: TreatmentGoal[];
  pending_homework: HomeworkAssignment[];
  latest_session: Session | null;
  summary: {
    total_sessions: number;
    active_goals: number;
    pending_homework: number;
    last_session: string | null;
    detected_symptoms: string[];
  };
}

export interface SessionStartResponse {
  session_id: number;
  patient_name: string;
  initial_message: string;
  phase: string;
}

export interface ChatResponse {
  response: string;
  phase: string;
  phase_changed: boolean;
  conversation_count: number;
  detected_symptoms: string[];
  session_completed: boolean;
  crisis_alert: string | null;
}

export interface MeditationUser {
  user_id: string;
  name: string;
  email?: string;
  preferences?: MeditationPreferences;
  created_at: string;
}

export interface MeditationPreferences {
  experience_level?: 'beginner' | 'intermediate' | 'advanced';
  preferred_duration?: number;
  favorite_meditations?: string[];
  goals?: string[];
}

export interface MeditationRecommendation {
  meditation_type: string;
  confidence: number;
  rationale: string;
  source: string;
}

export interface RecommendResponse {
  session_id: string;
  recommendations: MeditationRecommendation[];
  status: string;
  method: string;
}

export interface ScriptResponse {
  meditation_type: string;
  instructions: string;
  script: string;
  duration_minutes: string;
  format: string;
}

export interface UserHistoryContext {
  writing_frequency_baseline: number;
  emotional_baseline: Record<string, number>;
  topic_preferences: string[];
  behavioral_patterns: Record<string, unknown>;
  last_entry_timestamp: string;
  total_entries: number;
  avg_session_duration: number;
  preferred_writing_times: string[];
  emotional_volatility: number;
  topic_consistency: number;
  social_connectivity: number;
}

export interface TranscribeResponse {
  transcript: string;
}

// ─── AI Therapist API ─────────────────────────────────────────────────────────
export const therapistApi = {
  health: () =>
    apiFetch<{ status: string; timestamp: string; version: string }>(`${THERAPIST_HTTP}/health`),

  createPatient: (name: string, date_of_birth?: string) =>
    apiFetch<Patient>(`${THERAPIST_HTTP}/patients`, {
      method: 'POST',
      ...json({ name, ...(date_of_birth && { date_of_birth }) }),
    }),

  getPatientSessions: (patientId: number) =>
    apiFetch<Session[]>(`${THERAPIST_HTTP}/patients/${patientId}/sessions`),

  getPatientDashboard: (patientId: number) =>
    apiFetch<PatientDashboard>(`${THERAPIST_HTTP}/patients/${patientId}/dashboard`),

  startSession: (patientId: number) =>
    apiFetch<SessionStartResponse>(`${THERAPIST_HTTP}/sessions/start`, {
      method: 'POST',
      ...json({ patient_id: patientId }),
    }),

  sendMessage: (sessionId: number, message: string) =>
    apiFetch<ChatResponse>(`${THERAPIST_HTTP}/sessions/chat`, {
      method: 'POST',
      ...json({ session_id: sessionId, message }),
    }),

  getSession: (sessionId: number) =>
    apiFetch<Session>(`${THERAPIST_HTTP}/sessions/${sessionId}`),

  completeHomework: (homeworkId: number, notes: string, rating: number) =>
    apiFetch<{ message: string; homework_id: number }>(`${THERAPIST_HTTP}/homework/${homeworkId}/complete`, {
      method: 'POST',
      ...json({ notes, rating }),
    }),

  updateGoalProgress: (goalId: number, progress: number) =>
    apiFetch<{ message: string; goal_id: number; progress: number }>(
      `${THERAPIST_HTTP}/goals/${goalId}/progress?progress=${progress}`,
    ),

  getRecommendations: (sessionId: number, count = 5) =>
    apiFetch<{ content_recommendations: unknown[]; lifestyle_recommendations: unknown[] }>(
      `${THERAPIST_HTTP}/sessions/${sessionId}/recommendations`,
      { method: 'POST', ...json({ count }) },
    ),

  getAnalytics: () =>
    apiFetch<Record<string, unknown>>(`${THERAPIST_HTTP}/analytics`),
};

// ─── STT API ──────────────────────────────────────────────────────────────────
export const sttApi = {
  health: () =>
    apiFetch<{ status: string; timestamp: string }>(`${STT_HTTP}/health`),

  transcribe: (audioBlob: Blob): Promise<TranscribeResponse> => {
    const formData = new FormData();
    const ext = audioBlob.type.includes('mp4') ? 'mp4' : audioBlob.type.includes('ogg') ? 'ogg' : 'webm';
    formData.append('file', audioBlob, `recording.${ext}`);
    return apiFetch<TranscribeResponse>(`${STT_HTTP}/transcribe`, {
      method: 'POST',
      body: formData,
    });
  },
};

// ─── Meditation API ───────────────────────────────────────────────────────────
export const meditationApi = {
  createUser: (name: string, email?: string, preferences?: MeditationPreferences) =>
    apiFetch<MeditationUser>(`${MEDITATION_HTTP}/api/users`, {
      method: 'POST',
      ...json({ name, ...(email && { email }), ...(preferences && { preferences }) }),
    }),

  getUser: (userId: string) =>
    apiFetch<MeditationUser>(`${MEDITATION_HTTP}/api/users/${userId}`),

  updatePreferences: (userId: string, preferences: Partial<MeditationPreferences>) =>
    apiFetch<{ message: string }>(`${MEDITATION_HTTP}/api/users/${userId}/preferences`, {
      method: 'PUT',
      ...json(preferences),
    }),

  recommend: (diaryText: string, userId: string) =>
    apiFetch<RecommendResponse>(`${MEDITATION_HTTP}/api/recommend`, {
      method: 'POST',
      ...json({ diary_text: diaryText, user_id: userId }),
    }),

  generateScript: (meditationType: string, userId: string, durationMinutes = 5) =>
    apiFetch<ScriptResponse>(`${MEDITATION_HTTP}/api/generate-script`, {
      method: 'POST',
      ...json({ meditation_type: meditationType, user_id: userId, duration_minutes: durationMinutes }),
    }),

  analyzeAudio: (audioBlob: Blob, userId: string, sessionId?: string) => {
    const formData = new FormData();
    formData.append('file', audioBlob, 'audio.wav');
    formData.append('user_id', userId);
    if (sessionId) formData.append('session_id', sessionId);
    return apiFetch<{ session_id: string; audio_url: string; status: string; message: string }>(
      `${MEDITATION_HTTP}/api/analyze`,
      { method: 'POST', body: formData },
    );
  },

  getSessionStatus: (sessionId: string) =>
    apiFetch<{ session_id: string; status: string; created_at: string; has_results: boolean }>(
      `${MEDITATION_HTTP}/api/sessions/${sessionId}/status`,
    ),

  getSessionResults: (sessionId: string) =>
    apiFetch<Record<string, unknown>>(`${MEDITATION_HTTP}/api/sessions/${sessionId}/results`),

  submitFeedback: (data: {
    user_id: string;
    session_id: string;
    meditation_type: string;
    rating: number;
    comment?: string;
  }) =>
    apiFetch<{ feedback_id: string; message: string }>(`${MEDITATION_HTTP}/api/feedback`, {
      method: 'POST',
      ...json(data),
    }),
};

// ─── Journal Processing API ───────────────────────────────────────────────────
export const journalApi = {
  processJournal: (journalId: string, userId: string, triggerImmediate = false) =>
    apiFetch<{ success: boolean; message: string; processing_time_ms: number | null; entry_id: string }>(
      `${JOURNAL_HTTP}/process-journal`,
      {
        method: 'POST',
        ...json({ journal_id: journalId, user_id: userId, trigger_immediate: triggerImmediate }),
      },
    ),

  getUserHistory: (userId: string) =>
    apiFetch<{ success: boolean; message: string; user_history_context: UserHistoryContext | null }>(
      `${JOURNAL_HTTP}/user-history-context/${encodeURIComponent(userId)}`,
    ),
};

// ─── Gemini Engine API (Journal-part2) ───────────────────────────────────────
export interface GeminiChatResponse {
  response_id: string;
  conversation_id: string;
  enhanced_response: string;
  processing_time_ms: number;
  follow_up_suggestions: string[] | null;
  proactive_suggestions: string[] | null;
}

export const geminiEngineApi = {
  chat: (userId: string, message: string, conversationId: string) =>
    apiFetch<GeminiChatResponse>(`${GEMINI_ENGINE_HTTP}/conversation`, {
      method: 'POST',
      ...json({
        user_id: userId,
        user_message: message,
        conversation_id: conversationId,
        include_analysis: true,
      }),
    }),
};

// ─── TTS WebSocket helper ─────────────────────────────────────────────────────
/** Play text through the TTS WebSocket, streaming audio chunks as they arrive.
 *  Returns a cancel function. onDone is called when all chunks have played. */
export function streamTTS(
  text: string,
  voice = 'autumn',
  onStateChange?: (state: 'connecting' | 'generating' | 'playing' | 'done' | 'error') => void,
): () => void {
  let cancelled = false;
  let ws: WebSocket | null = null;
  const audioQueue: HTMLAudioElement[] = [];
  let isPlaying = false;

  function playNext() {
    if (cancelled || audioQueue.length === 0) {
      isPlaying = false;
      if (!cancelled) onStateChange?.('done');
      return;
    }
    isPlaying = true;
    const audio = audioQueue.shift()!;
    audio.onended = playNext;
    audio.play().catch((err) => { console.error('TTS audio play error:', err); playNext(); });
  }

  function queueChunk(base64: string) {
    try {
      const raw = atob(base64);
      const bytes = new Uint8Array(raw.length).map((_, i) => raw.charCodeAt(i));
      const blob = new Blob([bytes], { type: 'audio/wav' });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioQueue.push(audio);
      if (!isPlaying) {
        onStateChange?.('playing');
        playNext();
      }
    } catch {
      // ignore decode errors for individual chunks
    }
  }

  onStateChange?.('connecting');
  ws = new WebSocket(`${TTS_WS}/ws/tts`);

  ws.onopen = () => {
    // wait for connection ready message before sending
  };

  ws.onmessage = (event) => {
    if (cancelled) return;
    try {
      const msg = JSON.parse(event.data as string);
      if (msg.type === 'connection' && msg.data?.status === 'ready') {
        ws?.send(JSON.stringify({ type: 'text_input', data: { text, voice } }));
        onStateChange?.('generating');
      } else if (msg.type === 'audio_chunk' && msg.data?.audio_data) {
        queueChunk(msg.data.audio_data as string);
      } else if (msg.type === 'generation_complete') {
        ws?.close();
      } else if (msg.type === 'error') {
        onStateChange?.('error');
      }
    } catch {
      // ignore parse errors
    }
  };

  ws.onerror = () => onStateChange?.('error');
  ws.onclose = () => {
    if (!isPlaying && !cancelled) onStateChange?.('done');
  };

  return () => {
    cancelled = true;
    ws?.close();
    audioQueue.forEach((a) => {
      a.pause();
      a.src = '';
    });
    audioQueue.length = 0;
    isPlaying = false;
  };
}
