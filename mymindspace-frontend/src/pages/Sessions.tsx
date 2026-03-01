import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import {
  therapistApi,
  sttApi,
  streamTTS,
  THERAPIST_WS,
  ChatResponse,
  SessionStartResponse,
} from '../services/api';

// ─── Constants ────────────────────────────────────────────────────────────────
const SESSION_PHASES = [
  'intake',
  'assessment',
  'therapy',
  'goal_setting',
  'homework_assignment',
  'closing',
  'completed',
];

interface Message {
  role: 'user' | 'ai';
  text: string;
  phase?: string;
}

// ─── Mic recording hook ───────────────────────────────────────────────────────
function useVoiceRecorder(onTranscript: (text: string) => void) {
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [sttError, setSttError] = useState('');

  const startRecording = useCallback(async () => {
    setSttError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunks.current = [];
      mr.ondataavailable = (e) => chunks.current.push(e.data);
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunks.current, { type: mr.mimeType });
        if (blob.size < 100) return;
        setTranscribing(true);
        try {
          const { transcript } = await sttApi.transcribe(blob);
          if (transcript) onTranscript(transcript);
          else setSttError('No speech detected. Try again.');
        } catch (err: any) {
          setSttError(err.message ?? 'STT service unavailable.');
        } finally {
          setTranscribing(false);
        }
      };
      mr.start();
      mediaRecorder.current = mr;
      setRecording(true);
    } catch {
      setSttError('Microphone access denied.');
    }
  }, [onTranscript]);

  const stopRecording = useCallback(() => {
    mediaRecorder.current?.stop();
    setRecording(false);
  }, []);

  return { recording, transcribing, sttError, startRecording, stopRecording };
}

// ─── Component ────────────────────────────────────────────────────────────────
export default function Sessions() {
  const navigate = useNavigate();
  const { user, isLoggedIn } = useUser();

  // Session state
  const [sessionInfo, setSessionInfo] = useState<SessionStartResponse | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [phase, setPhase] = useState('intake');
  const [completed, setCompleted] = useState(false);
  const [crisisAlert, setCrisisAlert] = useState<string | null>(null);
  const [symptoms, setSymptoms] = useState<string[]>([]);

  // UI state
  const [starting, setStarting] = useState(false);
  const [sending, setSending] = useState(false);
  const [ttsState, setTtsState] = useState<'idle' | 'connecting' | 'generating' | 'playing' | 'done' | 'error'>('idle');
  const [inputText, setInputText] = useState('');
  const [error, setError] = useState('');
  const cancelTtsRef = useRef<(() => void) | null>(null);

  // Live conversation mode
  const [liveMode, setLiveMode] = useState(false);
  const [liveStatus, setLiveStatus] = useState<'idle' | 'listening' | 'thinking'>('idle');
  const [readyToSpeak, setReadyToSpeak] = useState(false);
  const liveModeRef = useRef(false);
  const liveRecorderRef = useRef<MediaRecorder | null>(null);
  const liveAudioCtxRef = useRef<AudioContext | null>(null);
  // Stable refs to avoid stale closures in live mode callbacks
  const sessionInfoRef = useRef<SessionStartResponse | null>(null);
  const completedRef = useRef(false);
  const startLiveRef = useRef<() => void>(() => {});
  const playTTSRef = useRef<(text: string) => void>(() => {});

  // WebSocket ref for therapy session
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isLoggedIn) { navigate('/'); }
    return () => {
      wsRef.current?.close();
      cancelTtsRef.current?.();
      liveModeRef.current = false;
      if (liveRecorderRef.current?.state === 'recording') liveRecorderRef.current.stop();
      liveAudioCtxRef.current?.close().catch(() => {});
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ─── Send a transcript from STT to the therapist ─────────────────────────
  const handleTranscript = useCallback(async (text: string) => {
    setInputText(text);
  }, []);

  const { recording, transcribing, sttError, startRecording, stopRecording } =
    useVoiceRecorder(handleTranscript);

  // ─── Start a therapy session ──────────────────────────────────────────────
  const startSession = async () => {
    if (!user.patientId) {
      setError('No patient account found. Please register first.');
      return;
    }
    // Unlock browser audio context synchronously before any await
    try {
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
      ctx.resume();
    } catch {}
    setStarting(true);
    setError('');
    try {
      const info = await therapistApi.startSession(user.patientId);
      setSessionInfo(info);
      setPhase(info.phase);
      setMessages([{ role: 'ai', text: info.initial_message, phase: info.phase }]);
      playTTS(info.initial_message);

      // Open WebSocket for subsequent messages
      const ws = new WebSocket(`${THERAPIST_WS}/ws/${info.session_id}`);
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data as string) as ChatResponse & { error?: string };
          if (data.error) { setError(data.error); return; }
          setMessages((prev) => [...prev, { role: 'ai', text: data.response, phase: data.phase }]);
          setPhase(data.phase);
          setSymptoms(data.detected_symptoms ?? []);
          if (data.crisis_alert) setCrisisAlert(data.crisis_alert);
          if (data.session_completed) { setCompleted(true); ws.close(); }
          playTTS(data.response);
        } catch {}
      };
      ws.onerror = () => setError('WebSocket connection error.');
      wsRef.current = ws;
    } catch (err: any) {
      setError(err.message ?? 'Could not start session. Is the Therapist API running?');
    } finally {
      setStarting(false);
    }
  };

  // ─── Send a message ───────────────────────────────────────────────────────
  const sendMessage = async () => {
    const text = inputText.trim();
    if (!text || !sessionInfo || completed) return;
    setInputText('');
    setMessages((prev) => [...prev, { role: 'user', text }]);
    setSending(true);
    try {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ message: text }));
      } else {
        // Fallback to HTTP
        const res = await therapistApi.sendMessage(sessionInfo.session_id, text);
        setMessages((prev) => [...prev, { role: 'ai', text: res.response, phase: res.phase }]);
        setPhase(res.phase);
        setSymptoms(res.detected_symptoms ?? []);
        if (res.crisis_alert) setCrisisAlert(res.crisis_alert);
        if (res.session_completed) setCompleted(true);
        playTTS(res.response);
      }
    } catch (err: any) {
      setError(err.message ?? 'Failed to send message.');
    } finally {
      setSending(false);
    }
  };

  // ─── TTS ──────────────────────────────────────────────────────────────────
  const playTTS = (text: string) => {
    cancelTtsRef.current?.();
    cancelTtsRef.current = streamTTS(text, 'autumn', (state) =>
      setTtsState(state as any),
    );
  };

  const stopTTS = () => {
    cancelTtsRef.current?.();
    setTtsState('idle');
  };

  // Keep stable refs up-to-date each render
  sessionInfoRef.current = sessionInfo;
  completedRef.current = completed;
  playTTSRef.current = playTTS;

  // ─── Push-to-talk live recording ─────────────────────────────────────────
  const startLivePTT = () => {
    if (!liveModeRef.current || completedRef.current) return;
    if (liveRecorderRef.current?.state === 'recording') return;
    // Stop Dr. Maya before activating mic (avoids getUserMedia audio interference)
    cancelTtsRef.current?.();
    setTtsState('idle');
    setReadyToSpeak(false);
    setLiveStatus('listening');
    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
      if (!liveModeRef.current) { stream.getTracks().forEach((t) => t.stop()); return; }
      const chunks: Blob[] = [];
      const mr = new MediaRecorder(stream);
      liveRecorderRef.current = mr;
      mr.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        liveRecorderRef.current = null;
        if (!liveModeRef.current) return;
        const blob = new Blob(chunks, { type: mr.mimeType });
        if (blob.size < 500) { setReadyToSpeak(true); setLiveStatus('idle'); return; }
        setLiveStatus('thinking');
        try {
          const { transcript } = await sttApi.transcribe(blob);
          if (transcript?.trim() && sessionInfoRef.current) {
            const text = transcript.trim();
            setMessages((prev) => [...prev, { role: 'user', text }]);
            if (wsRef.current?.readyState === WebSocket.OPEN) {
              wsRef.current.send(JSON.stringify({ message: text }));
            } else {
              const res = await therapistApi.sendMessage(sessionInfoRef.current.session_id, text);
              setMessages((prev) => [...prev, { role: 'ai', text: res.response, phase: res.phase }]);
              setPhase(res.phase);
              if (res.crisis_alert) setCrisisAlert(res.crisis_alert);
              if (res.session_completed) { setCompleted(true); setLiveMode(false); liveModeRef.current = false; return; }
              playTTSRef.current(res.response);
            }
          } else {
            setReadyToSpeak(true); setLiveStatus('idle');
          }
        } catch { setReadyToSpeak(true); setLiveStatus('idle'); }
      };
      mr.start();
    }).catch(() => setLiveStatus('idle'));
  };

  startLiveRef.current = startLivePTT;

  const toggleLiveMode = () => {
    const next = !liveMode;
    liveModeRef.current = next;
    setLiveMode(next);
    if (next) {
      try { new (window.AudioContext || (window as any).webkitAudioContext)().resume(); } catch {}
      cancelTtsRef.current?.();
      setTtsState('idle');
      setLiveStatus('idle');
      setReadyToSpeak(false);
    } else {
      if (liveRecorderRef.current?.state === 'recording') liveRecorderRef.current.stop();
      liveAudioCtxRef.current?.close().catch(() => {});
      liveAudioCtxRef.current = null;
      setLiveStatus('idle');
      setReadyToSpeak(false);
    }
  };

  // After TTS finishes in live mode, mark AI as done and let user speak
  useEffect(() => {
    if (liveMode && (ttsState === 'done' || ttsState === 'error') && !completed) {
      setReadyToSpeak(true);
      setLiveStatus('idle');
    }
  }, [ttsState, liveMode, completed]);

  // Spacebar push-to-talk: hold to record, release to send
  useEffect(() => {
    if (!liveMode) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code !== 'Space' || e.repeat) return;
      e.preventDefault();
      startLiveRef.current();
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code !== 'Space') return;
      e.preventDefault();
      if (liveRecorderRef.current?.state === 'recording') liveRecorderRef.current.stop();
    };
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [liveMode]);

  const phaseIndex = SESSION_PHASES.indexOf(phase);
  const isSpeaking = ttsState === 'playing' || ttsState === 'generating';

  // ─── Render: No session yet ───────────────────────────────────────────────
  if (!sessionInfo) {
    return (
      <div className="flex h-screen items-center justify-center bg-background-light font-display">
        <div className="flex flex-col items-center gap-8 max-w-md text-center p-8">
          <div className="w-40 h-40 rounded-full bg-gradient-to-tr from-primary to-accent flex items-center justify-center shadow-2xl">
            <span className="material-symbols-outlined text-white text-6xl">self_care</span>
          </div>
          <div>
            <h1 className="text-4xl font-black text-deep-midnight mb-3">Dr. Maya</h1>
            <p className="text-lg text-deep-midnight/60">
              Your AI therapist is ready to listen. Sessions are private, guided, and structured.
            </p>
          </div>
          {error && (
            <div className="w-full p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">
              {error}
            </div>
          )}
          <div className="flex flex-col gap-3 w-full">
            <button
              onClick={startSession}
              disabled={starting || !user.patientId}
              className="flex h-14 w-full items-center justify-center gap-3 rounded-full bg-primary text-white text-lg font-semibold hover:shadow-lg hover:shadow-primary/20 transition-all disabled:opacity-60"
            >
              {starting ? (
                <>
                  <span className="material-symbols-outlined animate-spin">refresh</span>
                  Starting session…
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined">play_arrow</span>
                  Start Session
                </>
              )}
            </button>
            <Link
              to="/dashboard"
              className="text-sm text-primary/70 hover:text-primary transition-colors text-center"
            >
              ← Back to Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // ─── Render: Active session ───────────────────────────────────────────────
  return (
    <div className="flex h-screen overflow-hidden bg-background-light font-display">
      {/* Crisis Alert Banner */}
      {crisisAlert && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-red-600 text-white px-6 py-4 flex items-center gap-4">
          <span className="material-symbols-outlined text-3xl">emergency</span>
          <div className="flex-1">
            <p className="font-bold">Crisis Support Needed</p>
            <p className="text-sm">{crisisAlert}</p>
          </div>
          <button onClick={() => setCrisisAlert(null)} className="text-white/80 hover:text-white">
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
      )}

      {/* Left Info Panel */}
      <aside className="w-72 flex flex-col border-r border-primary/10 bg-white/50 backdrop-blur-md p-6">
        <Link to="/dashboard" className="flex items-center gap-2 text-primary/70 hover:text-primary mb-8 transition-colors">
          <span className="material-symbols-outlined">arrow_back</span>
          <span className="text-sm font-medium">Dashboard</span>
        </Link>

        {/* Dr Maya */}
        <div className="flex flex-col items-center text-center mb-8">
          <div className="relative mb-4">
            {isSpeaking && (
              <div className="absolute inset-0 rounded-full bg-primary/20 animate-ping scale-125"></div>
            )}
            <img
              src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=200"
              alt="Dr. Maya"
              className="relative z-10 w-24 h-24 rounded-full border-4 border-white shadow-lg object-cover"
            />
          </div>
          <h3 className="font-bold text-lg">Dr. Maya</h3>
          <p className="text-xs text-deep-midnight/50">AI Therapist</p>
          {isSpeaking && (
            <div className="mt-2 flex gap-1 h-4 items-end">
              <div className="w-1 bg-primary h-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-1 bg-primary h-2/3 animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-1 bg-primary h-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          )}
        </div>

        {/* Phase Progress */}
        <div className="mb-8">
          <p className="text-xs font-bold uppercase tracking-wider text-primary/70 mb-3">Session Progress</p>
          <div className="flex flex-col gap-2">
            {SESSION_PHASES.map((p, i) => (
              <div key={p} className="flex items-center gap-2">
                <div
                  className={`w-2 h-2 rounded-full flex-shrink-0 ${
                    i < phaseIndex ? 'bg-primary' : i === phaseIndex ? 'bg-primary animate-pulse' : 'bg-primary/20'
                  }`}
                ></div>
                <span
                  className={`text-xs capitalize ${
                    i === phaseIndex ? 'font-bold text-primary' : 'text-deep-midnight/50'
                  }`}
                >
                  {p.replace(/_/g, ' ')}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Detected Symptoms */}
        {symptoms.length > 0 && (
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-primary/70 mb-2">Noted Themes</p>
            <div className="flex flex-wrap gap-1">
              {symptoms.map((s) => (
                <span key={s} className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded-full capitalize">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}

        {completed && (
          <div className="mt-auto p-4 bg-primary/10 rounded-xl border border-primary/20 text-center">
            <span className="material-symbols-outlined text-primary text-2xl">task_alt</span>
            <p className="text-sm font-bold text-primary mt-1">Session Complete</p>
            <Link to="/dashboard" className="text-xs text-primary/70 hover:text-primary underline mt-1 block">
              View Dashboard
            </Link>
          </div>
        )}
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col bg-gradient-to-b from-white to-primary/5">
        {/* Header */}
        <div className="px-6 py-4 border-b border-primary/10 flex items-center justify-between bg-white/80">
          <div className="flex items-center gap-3">
            <div className="size-2 bg-green-500 rounded-full animate-pulse"></div>
            <p className="text-slate-700 text-sm font-semibold tracking-wide uppercase">
              Secure Therapy Session — Phase: {phase.replace(/_/g, ' ')}
            </p>
          </div>
          <div className="flex gap-3 items-center">
            {isSpeaking && !liveMode && (
              <button
                onClick={stopTTS}
                className="flex items-center gap-1 px-3 py-1 bg-primary/10 text-primary rounded-full text-xs font-bold"
              >
                <span className="material-symbols-outlined text-sm">stop</span>
                Stop Audio
              </button>
            )}
            {!completed && (
              <button
                onClick={toggleLiveMode}
                className={`flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold transition-all ${
                  liveMode
                    ? 'bg-primary text-white shadow-lg shadow-primary/30'
                    : 'bg-primary/10 text-primary hover:bg-primary/20'
                }`}
                title="Toggle live conversation mode"
              >
                <span className="material-symbols-outlined text-sm">
                  {liveMode ? 'radio_button_checked' : 'mic_external_on'}
                </span>
                {liveMode ? 'End Voice Mode' : 'Voice Mode'}
              </button>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[70%] p-4 rounded-2xl text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-primary text-white rounded-br-sm'
                    : 'bg-white border border-primary/10 text-slate-700 rounded-bl-sm shadow-sm'
                }`}
              >
                {msg.role === 'ai' && (
                  <p className="text-[10px] font-bold text-primary/60 uppercase tracking-wider mb-1">
                    Dr. Maya {msg.phase && `· ${msg.phase.replace(/_/g, ' ')}`}
                  </p>
                )}
                <p className={msg.role === 'ai' ? 'font-serif text-base italic' : ''}>{msg.text}</p>
              </div>
            </div>
          ))}
          {sending && (
            <div className="flex justify-start">
              <div className="bg-white border border-primary/10 rounded-2xl rounded-bl-sm px-5 py-4 shadow-sm">
                <div className="flex gap-1 h-3 items-end">
                  <div className="w-1.5 h-1.5 bg-primary/50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-1.5 h-1.5 bg-primary/50 rounded-full animate-bounce" style={{ animationDelay: '200ms' }}></div>
                  <div className="w-1.5 h-1.5 bg-primary/50 rounded-full animate-bounce" style={{ animationDelay: '400ms' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        {!completed && (
          <div className="border-t border-primary/10 bg-white/80">
            {liveMode ? (
              /* ── Live voice mode overlay ── */
              <div className="flex flex-col items-center justify-center gap-4 py-6 px-6">
                <div className="relative flex items-center justify-center">
                  {/* Pulse rings */}
                  {liveStatus === 'listening' && (
                    <>
                      <div className="absolute w-24 h-24 rounded-full bg-red-400/20 animate-ping" />
                      <div className="absolute w-16 h-16 rounded-full bg-red-400/30 animate-ping" style={{ animationDelay: '200ms' }} />
                    </>
                  )}
                  {isSpeaking && (
                    <>
                      <div className="absolute w-24 h-24 rounded-full bg-primary/20 animate-ping" />
                      <div className="absolute w-16 h-16 rounded-full bg-primary/30 animate-ping" style={{ animationDelay: '200ms' }} />
                    </>
                  )}
                  <div className={`relative z-10 w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-colors ${
                    liveStatus === 'listening' ? 'bg-red-500' : isSpeaking ? 'bg-primary' : 'bg-slate-300'
                  }`}>
                    <span className="material-symbols-outlined text-white text-2xl">
                      {liveStatus === 'listening' ? 'mic' : isSpeaking ? 'volume_up' : 'hourglass_empty'}
                    </span>
                  </div>
                </div>
                <p className="text-sm font-semibold text-slate-600">
                  {liveStatus === 'listening' && 'Listening…'}
                  {liveStatus === 'thinking' && !isSpeaking && 'Dr. Maya is thinking…'}
                  {isSpeaking && 'Dr. Maya is speaking…'}
                  {liveStatus === 'idle' && readyToSpeak && 'Hold SPACE to speak…'}
                </p>
                <p className="text-[10px] text-slate-400 uppercase tracking-widest">
                  Hold SPACE to speak · release to send · click "End Voice Mode" to exit
                </p>
                {error && <p className="text-red-500 text-xs">{error}</p>}
              </div>
            ) : (
              /* ── Normal text / hold-mic mode ── */
              <div className="p-6">
                {error && <p className="text-red-500 text-sm mb-3">{error}</p>}
                {sttError && <p className="text-amber-500 text-sm mb-3">{sttError}</p>}
                {transcribing && (
                  <p className="text-primary text-sm mb-3 flex items-center gap-2">
                    <span className="material-symbols-outlined animate-spin text-sm">refresh</span>
                    Transcribing…
                  </p>
                )}
                <div className="flex items-center gap-4">
                  <button
                    onMouseDown={startRecording}
                    onMouseUp={stopRecording}
                    onTouchStart={startRecording}
                    onTouchEnd={stopRecording}
                    disabled={transcribing || sending}
                    className={`w-12 h-12 rounded-full flex items-center justify-center transition-all flex-shrink-0 ${
                      recording ? 'bg-red-500 text-white shadow-lg shadow-red-400/40 scale-110' : 'bg-primary/10 text-primary hover:bg-primary/20'
                    } disabled:opacity-50`}
                    title="Hold to record voice"
                  >
                    <span className="material-symbols-outlined">{recording ? 'mic' : 'mic_none'}</span>
                  </button>
                  <input
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                    placeholder={recording ? 'Release to transcribe…' : 'Type or hold mic to speak…'}
                    disabled={sending || completed}
                    className="flex-1 h-12 px-5 rounded-full border-2 border-primary/20 bg-white text-slate-800 focus:outline-none focus:border-primary transition-all disabled:opacity-60"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={!inputText.trim() || sending || completed}
                    className="w-12 h-12 rounded-full bg-primary text-white flex items-center justify-center hover:bg-primary/90 transition-all disabled:opacity-50 flex-shrink-0"
                  >
                    <span className="material-symbols-outlined">send</span>
                  </button>
                </div>
                <p className="text-[10px] text-slate-400 text-center mt-2 uppercase tracking-widest">
                  Hold mic button to speak · Press Enter or → to send
                </p>
              </div>
            )}
          </div>
        )}

        {completed && (
          <div className="p-6 border-t border-primary/10 bg-white/80 text-center">
            <p className="text-primary font-bold mb-3">Session complete. Thank you for sharing today.</p>
            <Link
              to="/dashboard"
              className="inline-block px-8 py-3 bg-primary text-white rounded-full font-semibold hover:shadow-lg transition-all"
            >
              Return to Dashboard
            </Link>
          </div>
        )}
      </main>
    </div>
  );
}
