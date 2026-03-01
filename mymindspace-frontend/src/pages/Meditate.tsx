import React, { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { meditationApi, streamTTS, MeditationRecommendation, ScriptResponse } from '../services/api';

const MEDITATION_CATEGORIES = [
  { type: 'breathing', icon: 'air', label: 'Breath', desc: 'Pranayama and rhythmic breathing' },
  { type: 'mindfulness', icon: 'center_focus_strong', label: 'Focus', desc: 'Clarity for deep work' },
  { type: 'body_scan', icon: 'nights_stay', label: 'Sleep', desc: 'Gentle drift into deep rest' },
  { type: 'loving_kindness', icon: 'favorite', label: 'Gratitude', desc: 'Open your heart' },
];

const MOODS = ['Calm', 'Anxious', 'Tired', 'Focused', 'Sad', 'Stressed'];
type TtsStatus = 'idle' | 'connecting' | 'generating' | 'playing' | 'done' | 'error';

export default function Meditate() {
  const { user } = useUser();
  const [diaryText, setDiaryText] = useState('');
  const [selectedMood, setSelectedMood] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [duration, setDuration] = useState(8);
  const [recommendations, setRecommendations] = useState<MeditationRecommendation[]>([]);
  const [script, setScript] = useState<ScriptResponse | null>(null);
  const [loadingRec, setLoadingRec] = useState(false);
  const [loadingScript, setLoadingScript] = useState(false);
  const [ttsStatus, setTtsStatus] = useState<TtsStatus>('idle');
  const [error, setError] = useState('');
  const cancelTts = useRef<(() => void) | null>(null);

  const getRecommendations = async () => {
    if (!user.meditationUserId) { setError('Please register from the Welcome page first.'); return; }
    const text = diaryText.trim() || ('Feeling ' + (selectedMood || 'neutral') + ' today');
    setError(''); setLoadingRec(true); setRecommendations([]); setScript(null);
    try {
      const res = await meditationApi.recommend(text, user.meditationUserId);
      setRecommendations(res.recommendations);
    } catch (err: any) {
      setError((err as any).message ?? 'Could not get recommendations.');
    } finally { setLoadingRec(false); }
  };

  const generateAndPlay = async (type: string) => {
    if (!user.meditationUserId) { setError('No user account.'); return; }
    setSelectedType(type); setError(''); setLoadingScript(true); setScript(null);
    cancelTts.current?.(); setTtsStatus('idle');
    try {
      const res = await meditationApi.generateScript(type, user.meditationUserId, duration);
      setScript(res);
      cancelTts.current = streamTTS(res.script, 'hannah', (s) => setTtsStatus(s as TtsStatus));
    } catch (err: any) {
      setError((err as any).message ?? 'Script generation failed.');
    } finally { setLoadingScript(false); }
  };

  const stopAudio = () => { cancelTts.current?.(); setTtsStatus('idle'); };
  const isSpeaking = ttsStatus === 'playing' || ttsStatus === 'generating';

  return (
    <div className="bg-background-light font-display text-slate-900 min-h-screen relative overflow-x-hidden flex flex-col">
      <header className="flex items-center justify-between px-10 py-5 border-b border-primary/10 sticky top-0 bg-background-light/80 backdrop-blur-md z-50">
        <div className="flex items-center gap-4">
          <span className="material-symbols-outlined text-primary text-4xl">filter_vintage</span>
          <h2 className="text-xl font-bold">MyMindSpace</h2>
        </div>
        <nav className="flex flex-1 justify-center gap-12">
          <Link to="/dashboard" className="text-sm font-semibold hover:text-primary transition-colors">Home</Link>
          <Link to="/meditate" className="text-primary text-sm font-bold border-b-2 border-primary pb-1">Meditate</Link>
          <Link to="/journal" className="text-sm font-semibold hover:text-primary transition-colors">Journal</Link>
        </nav>
        <Link to="/profile">
          <div className="bg-primary/20 rounded-full w-10 h-10 flex items-center justify-center border border-primary/30">
            <span className="material-symbols-outlined text-primary">person</span>
          </div>
        </Link>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-12 space-y-16 z-10">
        <section className="text-center space-y-8">
          <h1 className="text-5xl font-bold tracking-tight text-slate-800">How are you feeling today?</h1>
          <div className="relative h-64 flex items-center justify-center">
            <div className="absolute inset-0 lotus-gradient rounded-full scale-150"></div>
            <span className="relative material-symbols-outlined text-primary opacity-80" style={{fontSize:'160px'}}>spa</span>
          </div>
          <div className="flex justify-center flex-wrap gap-3">
            {MOODS.map((mood) => (
              <button key={mood} onClick={() => setSelectedMood(mood === selectedMood ? '' : mood)}
                className={`px-6 py-2 rounded-full text-sm font-medium transition-all ${selectedMood === mood ? 'bg-primary text-white shadow-md' : 'bg-white/60 border border-primary/20 hover:bg-primary hover:text-white'}`}>
                {mood}
              </button>
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="text-2xl font-bold">What is on your mind?</h2>
          <p className="text-slate-500">Share a few thoughts and we will find the right meditation for you.</p>
          <textarea value={diaryText} onChange={(e) => setDiaryText(e.target.value)}
            placeholder="How are you feeling? What happened today?"
            rows={4} className="w-full p-4 rounded-xl border-2 border-primary/20 bg-white/80 text-slate-700 resize-none focus:outline-none focus:border-primary transition-all"/>
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium text-slate-600">Duration:</label>
              <select value={duration} onChange={(e) => setDuration(Number(e.target.value))}
                className="h-10 px-3 rounded-full border-2 border-primary/20 bg-white text-sm focus:outline-none focus:border-primary">
                {[3, 5, 8, 10, 15, 20, 30].map(d => <option key={d} value={d}>{d} min</option>)}
              </select>
            </div>
            <button onClick={getRecommendations} disabled={loadingRec}
              className="flex items-center gap-2 px-8 py-3 bg-primary text-white rounded-full font-semibold hover:shadow-lg transition-all disabled:opacity-60">
              {loadingRec
                ? <><span className="material-symbols-outlined animate-spin">refresh</span> Finding...</>
                : <><span className="material-symbols-outlined">auto_awesome</span> Get Recommendations</>}
            </button>
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
        </section>

        {recommendations.length > 0 && (
          <section className="space-y-6">
            <h2 className="text-2xl font-bold">Recommended for You</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recommendations.map((rec, i) => (
                <div key={i} className="glass-card p-6 rounded-xl flex flex-col gap-3 border border-transparent hover:border-primary/30 transition-all">
                  <div className="flex items-start justify-between">
                    <h3 className="font-bold text-lg capitalize">{rec.meditation_type.replace(/_/g, ' ')}</h3>
                    <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">{Math.round(rec.confidence * 100)}% match</span>
                  </div>
                  <p className="text-sm text-slate-500 flex-1">{rec.rationale}</p>
                  <button onClick={() => generateAndPlay(rec.meditation_type)}
                    disabled={loadingScript && selectedType === rec.meditation_type}
                    className="flex items-center justify-center gap-2 w-full py-2.5 bg-primary text-white rounded-full text-sm font-semibold hover:shadow-md transition-all disabled:opacity-60">
                    {loadingScript && selectedType === rec.meditation_type
                      ? <><span className="material-symbols-outlined animate-spin text-sm">refresh</span> Generating...</>
                      : <><span className="material-symbols-outlined text-sm">play_circle</span> Generate and Play</>}
                  </button>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold">Browse Categories</h2>
            <p className="text-slate-500 mt-1">Pick any style and generate a custom script</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {MEDITATION_CATEGORIES.map(({ type, icon, label, desc }) => (
              <div key={type} onClick={() => generateAndPlay(type)}
                className={`glass-card p-8 rounded-xl flex flex-col items-center text-center gap-4 group cursor-pointer hover:shadow-xl hover:shadow-primary/10 transition-all border hover:border-primary/30 ${selectedType === type ? 'border-primary/40 bg-primary/5' : 'border-transparent'}`}>
                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                  <span className="material-symbols-outlined text-3xl">{icon}</span>
                </div>
                <div>
                  <h3 className="font-bold text-lg">{label}</h3>
                  <p className="text-slate-500 text-sm">{desc}</p>
                </div>
                {loadingScript && selectedType === type && <span className="material-symbols-outlined animate-spin text-primary">refresh</span>}
              </div>
            ))}
          </div>
        </section>
      </main>

      <div className="h-48"></div>

      {script && (
        <footer className="fixed bottom-6 left-1/2 -translate-x-1/2 w-[90%] max-w-5xl z-50">
          <div className="bg-white/90 backdrop-blur-xl rounded-xl shadow-2xl border border-primary/20 p-6 flex items-center gap-8">
            <div className="flex-1 h-24 flex items-center px-6 border-r border-primary/10 overflow-hidden">
              <p className="font-serif-alt italic text-lg text-slate-700 leading-relaxed line-clamp-3">
                {'"' + script.script.slice(0, 220) + '..."'}
              </p>
            </div>
            <div className="flex flex-col items-center gap-3 min-w-[280px]">
              {isSpeaking && (
                <div className="flex items-end gap-1 h-8 w-full justify-center">
                  {[0,1,2,3,4,5,6,7,8,9,10,11].map((idx) => (
                    <div key={idx} className="w-1 bg-primary rounded-full animate-bounce"
                      style={{height:'16px', animationDelay: (idx * 80) + 'ms'}}></div>
                  ))}
                </div>
              )}
              <div className="flex items-center gap-6">
                <button onClick={isSpeaking ? stopAudio : () => generateAndPlay(script.meditation_type)}
                  className="bg-primary text-white w-14 h-14 rounded-full flex items-center justify-center shadow-lg shadow-primary/20 hover:scale-105 transition-transform">
                  <span className="material-symbols-outlined text-3xl">{isSpeaking ? 'stop' : 'play_arrow'}</span>
                </button>
              </div>
              <div className="text-xs text-center text-slate-500 capitalize">
                {script.meditation_type.replace(/_/g, ' ')} � {script.duration_minutes} min � {ttsStatus}
              </div>
            </div>
            <div className="flex flex-col items-end gap-2 px-4">
              <span className="text-xs text-primary font-bold uppercase tracking-wider">{script.format}</span>
              <p className="text-xs text-slate-400 max-w-[120px] text-right line-clamp-2">{script.instructions}</p>
            </div>
          </div>
        </footer>
      )}
    </div>
  );
}
