import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { meditationApi, therapistApi, MeditationUser, MeditationPreferences, PatientDashboard } from '../services/api';

const EXPERIENCE_LEVELS = ['beginner', 'intermediate', 'advanced'] as const;
const GOALS_OPTIONS = ['stress_reduction', 'better_sleep', 'focus', 'emotional_balance', 'anxiety_relief', 'self_awareness'];
const MEDITATION_TYPES = ['mindfulness', 'breathing', 'body_scan', 'loving_kindness', 'walking', 'sound_bath'];

export default function Profile() {
  const { user, clearUser } = useUser();

  const [medUser, setMedUser] = useState<MeditationUser | null>(null);
  const [dashboard, setDashboard] = useState<PatientDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [saveMsg, setSaveMsg] = useState('');

  const [prefs, setPrefs] = useState<MeditationPreferences>({
    experience_level: 'beginner',
    preferred_duration: 10,
    favorite_meditations: [],
    goals: [],
  });

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const promises: Promise<any>[] = [];
        if (user.meditationUserId) promises.push(meditationApi.getUser(user.meditationUserId));
        else promises.push(Promise.resolve(null));
        if (user.patientId) promises.push(therapistApi.getPatientDashboard(user.patientId));
        else promises.push(Promise.resolve(null));
        const [mu, dash] = await Promise.all(promises);
        if (mu) {
          setMedUser(mu);
          if (mu.preferences) setPrefs(mu.preferences);
        }
        if (dash) setDashboard(dash);
      } catch (err: any) {
        setError((err as any).message ?? 'Failed to load profile.');
      } finally { setLoading(false); }
    })();
  }, [user]);

  const toggleArrayPref = (key: 'goals' | 'favorite_meditations', val: string) => {
    setPrefs(prev => {
      const arr = prev[key] ?? [];
      const next = arr.includes(val) ? arr.filter(v => v !== val) : [...arr, val];
      return { ...prev, [key]: next };
    });
  };

  const savePrefs = async () => {
    if (!user.meditationUserId) return;
    setSaving(true); setSaveMsg('');
    try {
      await meditationApi.updatePreferences(user.meditationUserId, prefs);
      setSaveMsg('Preferences saved!');
      setTimeout(() => setSaveMsg(''), 3000);
    } catch (err: any) {
      setError((err as any).message ?? 'Failed to save preferences.');
    } finally { setSaving(false); }
  };

  const diagnosisList = dashboard?.latest_session?.assessment_results
    ? Object.entries(dashboard.latest_session.assessment_results as Record<string, any>).slice(0, 3)
    : [];

  return (
    <div className="relative flex h-auto min-h-screen w-full flex-col bg-background-light text-slate-900">
      <header className="flex items-center justify-between whitespace-nowrap border-b border-primary/20 bg-background-light px-10 py-3 sticky top-0 z-50">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-4 text-primary">
            <span className="material-symbols-outlined text-3xl">psychology</span>
            <h2 className="text-slate-900 text-lg font-bold">MyMindSpace</h2>
          </div>
        </div>
        <div className="flex items-center gap-9">
          <Link to="/dashboard" className="text-slate-900 text-sm font-medium hover:text-primary transition-colors">Dashboard</Link>
          <Link to="/sessions" className="text-slate-900 text-sm font-medium hover:text-primary transition-colors">Sessions</Link>
          <Link to="/profile" className="text-primary text-sm font-bold border-b-2 border-primary">Profile</Link>
          <Link to="/journal" className="text-slate-900 text-sm font-medium hover:text-primary transition-colors">Journal</Link>
        </div>
      </header>

      <main className="flex-1 px-4 md:px-10 lg:px-20 py-8">
        <div className="max-w-[1200px] mx-auto flex flex-col gap-8">

          {loading ? (
            <div className="flex items-center justify-center h-64">
              <span className="material-symbols-outlined animate-spin text-4xl text-primary">refresh</span>
            </div>
          ) : (
            <>
              {error && <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">{error}</div>}

              {/* Profile Header */}
              <section className="bg-white rounded-xl p-8 border border-primary/10 shadow-sm">
                <div className="flex flex-col md:flex-row items-center gap-8">
                  <div className="relative">
                    <div className="w-32 h-32 rounded-full bg-gradient-to-tr from-primary to-accent flex items-center justify-center border-4 border-primary/30">
                      <span className="material-symbols-outlined text-white text-5xl">person</span>
                    </div>
                  </div>

                  <div className="flex-1 text-center md:text-left">
                    <h1 className="text-3xl font-bold tracking-tight">{medUser?.name ?? user.name}</h1>
                    {medUser?.email && <p className="text-primary font-medium">{medUser.email}</p>}
                    <p className="text-slate-500 text-sm mt-1">Member since {medUser ? new Date(medUser.created_at).toLocaleDateString() : 'today'}</p>

                    <div className="flex flex-wrap gap-4 mt-6 justify-center md:justify-start">
                      <div className="flex flex-col items-center md:items-start px-6 py-2 bg-primary/5 rounded-lg border border-primary/10">
                        <span className="text-2xl font-bold">{dashboard?.summary.total_sessions ?? 0}</span>
                        <span className="text-xs text-primary uppercase font-bold tracking-wider">Therapy Sessions</span>
                      </div>
                      <div className="flex flex-col items-center md:items-start px-6 py-2 bg-primary/5 rounded-lg border border-primary/10">
                        <span className="text-2xl font-bold">{dashboard?.summary.active_goals ?? 0}</span>
                        <span className="text-xs text-primary uppercase font-bold tracking-wider">Active Goals</span>
                      </div>
                      <div className="flex flex-col items-center md:items-start px-6 py-2 bg-primary/5 rounded-lg border border-primary/10">
                        <span className="text-2xl font-bold">{dashboard?.summary.pending_homework ?? 0}</span>
                        <span className="text-xs text-primary uppercase font-bold tracking-wider">Pending Tasks</span>
                      </div>
                    </div>
                  </div>
                </div>
              </section>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 flex flex-col gap-8">

                  {/* Preferences */}
                  <section className="bg-white rounded-xl p-6 border border-primary/10">
                    <div className="flex items-center gap-2 mb-6">
                      <span className="material-symbols-outlined text-primary">auto_awesome</span>
                      <h2 className="text-lg font-bold">Meditation Preferences</h2>
                    </div>

                    <div className="space-y-6">
                      <div>
                        <label className="text-sm font-semibold text-slate-600 mb-2 block">Experience Level</label>
                        <div className="flex gap-3 flex-wrap">
                          {EXPERIENCE_LEVELS.map(level => (
                            <button key={level} onClick={() => setPrefs(p => ({ ...p, experience_level: level }))}
                              className={`px-5 py-2 rounded-full text-sm font-medium transition-all capitalize ${prefs.experience_level === level ? 'bg-primary text-white' : 'bg-primary/10 text-primary hover:bg-primary/20'}`}>
                              {level}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div>
                        <label className="text-sm font-semibold text-slate-600 mb-2 block">Preferred Session Duration: {prefs.preferred_duration} min</label>
                        <input type="range" min={1} max={30} value={prefs.preferred_duration ?? 10}
                          onChange={(e) => setPrefs(p => ({ ...p, preferred_duration: Number(e.target.value) }))}
                          className="w-full accent-primary" />
                        <div className="flex justify-between text-xs text-slate-400 mt-1"><span>1 min</span><span>30 min</span></div>
                      </div>

                      <div>
                        <label className="text-sm font-semibold text-slate-600 mb-2 block">Wellness Goals</label>
                        <div className="flex flex-wrap gap-2">
                          {GOALS_OPTIONS.map(goal => (
                            <button key={goal} onClick={() => toggleArrayPref('goals', goal)}
                              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all capitalize ${(prefs.goals ?? []).includes(goal) ? 'bg-primary text-white' : 'bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20'}`}>
                              {goal.replace(/_/g, ' ')}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div>
                        <label className="text-sm font-semibold text-slate-600 mb-2 block">Favourite Meditation Styles</label>
                        <div className="flex flex-wrap gap-2">
                          {MEDITATION_TYPES.map(type => (
                            <button key={type} onClick={() => toggleArrayPref('favorite_meditations', type)}
                              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all capitalize ${(prefs.favorite_meditations ?? []).includes(type) ? 'bg-primary text-white' : 'bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20'}`}>
                              {type.replace(/_/g, ' ')}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        <button onClick={savePrefs} disabled={saving}
                          className="flex items-center gap-2 px-6 py-2.5 bg-primary text-white rounded-full font-semibold text-sm hover:shadow-md transition-all disabled:opacity-60">
                          {saving ? <><span className="material-symbols-outlined animate-spin text-sm">refresh</span> Saving...</> : <><span className="material-symbols-outlined text-sm">save</span> Save Preferences</>}
                        </button>
                        {saveMsg && <p className="text-green-600 text-sm font-medium">{saveMsg}</p>}
                      </div>
                    </div>
                  </section>

                  {/* Detected Symptoms */}
                  {(dashboard?.summary.detected_symptoms?.length ?? 0) > 0 && (
                    <section className="bg-white rounded-xl p-6 border border-primary/10">
                      <div className="flex items-center gap-2 mb-4">
                        <span className="material-symbols-outlined text-primary">clinical_notes</span>
                        <h2 className="text-lg font-bold">Therapy Insights</h2>
                      </div>
                      <div className="space-y-3">
                        {dashboard!.summary.detected_symptoms.map((symptom, i) => (
                          <div key={i} className="flex items-center justify-between p-3 rounded-lg border border-primary/10 bg-primary/5">
                            <div className="flex items-center gap-3">
                              <span className="material-symbols-outlined text-primary">sentiment_neutral</span>
                              <p className="font-medium text-sm capitalize">{symptom}</p>
                            </div>
                            <span className="px-3 py-1 rounded-full bg-amber-100 text-amber-700 text-xs font-bold uppercase">Noted</span>
                          </div>
                        ))}
                      </div>
                    </section>
                  )}
                </div>

                {/* Settings sidebar */}
                <aside className="flex flex-col gap-6">
                  <div className="bg-white rounded-xl border border-primary/10 shadow-sm overflow-hidden sticky top-24">
                    <div className="p-6 border-b border-primary/10">
                      <h2 className="text-lg font-bold">Account</h2>
                      <p className="text-sm text-slate-500">Manage your data</p>
                    </div>

                    <nav className="flex flex-col p-2">
                      <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-primary/5 text-slate-700">
                        <span className="material-symbols-outlined text-primary">badge</span>
                        <div className="flex flex-col">
                          <span className="text-xs font-bold text-primary uppercase tracking-wider">Patient ID</span>
                          <span className="text-sm font-mono">{user.patientId ?? 'N/A'}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-primary/5 text-slate-700 mt-1">
                        <span className="material-symbols-outlined text-primary">spa</span>
                        <div className="flex flex-col">
                          <span className="text-xs font-bold text-primary uppercase tracking-wider">Meditation ID</span>
                          <span className="text-sm font-mono truncate max-w-[140px]">{user.meditationUserId ?? 'N/A'}</span>
                        </div>
                      </div>

                      <div className="h-px bg-primary/10 my-2 mx-4"></div>

                      <Link to="/sessions"
                        className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-primary/10 transition-colors group">
                        <span className="material-symbols-outlined text-primary">self_care</span>
                        <span className="text-sm font-medium">Start Therapy Session</span>
                      </Link>
                      <Link to="/meditate"
                        className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-primary/10 transition-colors group">
                        <span className="material-symbols-outlined text-primary">dark_mode</span>
                        <span className="text-sm font-medium">Open Meditation</span>
                      </Link>
                      <Link to="/journal"
                        className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-primary/10 transition-colors group">
                        <span className="material-symbols-outlined text-primary">book_5</span>
                        <span className="text-sm font-medium">Open Journal</span>
                      </Link>

                      <div className="h-px bg-primary/10 my-2 mx-4"></div>

                      <button onClick={() => { clearUser(); window.location.href = '/'; }}
                        className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-red-50 text-red-600 transition-colors w-full text-left">
                        <span className="material-symbols-outlined">logout</span>
                        <span className="text-sm font-medium">Log Out</span>
                      </button>
                    </nav>

                    <div className="p-6 bg-primary/5 mt-2">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="material-symbols-outlined text-primary text-xl">verified_user</span>
                        <p className="text-xs font-bold uppercase tracking-widest text-primary">Data Protection</p>
                      </div>
                      <p className="text-xs text-slate-600 leading-relaxed">
                        Your journal entries are stored locally. Therapy data is handled by your connected backend services.
                      </p>
                    </div>
                  </div>
                </aside>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
