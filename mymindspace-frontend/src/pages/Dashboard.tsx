import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { therapistApi, journalApi, PatientDashboard, UserHistoryContext } from '../services/api';

function Sidebar({ pathname }: { pathname: string }) {
  const { user } = useUser();
  return (
    <aside className="w-64 flex flex-col border-r border-primary/10 bg-white/50 backdrop-blur-md p-6">
      <div className="flex items-center gap-3 mb-12">
        <div className="size-10 rounded-full bg-primary flex items-center justify-center text-white">
          <span className="material-symbols-outlined">psychology</span>
        </div>
        <div className="flex flex-col">
          <h1 className="text-deep-midnight text-lg font-bold leading-none">MyMindSpace</h1>
          <p className="text-primary text-xs font-medium">Your sanctuary</p>
        </div>
      </div>

      <nav className="flex flex-col gap-2 flex-1">
        {[
          { to: '/dashboard', icon: 'home', label: 'Home' },
          { to: '/journal', icon: 'book_5', label: 'Journal' },
          { to: '/sessions', icon: 'self_care', label: 'Therapy' },
          { to: '/meditate', icon: 'dark_mode', label: 'Meditate' },
          { to: '/profile', icon: 'account_circle', label: 'Profile' },
        ].map(({ to, icon, label }) => (
          <Link
            key={to}
            to={to}
            className={`flex items-center gap-3 px-4 py-3 rounded-full font-medium transition-colors ${
              pathname === to ? 'bg-primary text-white' : 'text-deep-midnight/70 hover:bg-primary/10'
            }`}
          >
            <span className="material-symbols-outlined">{icon}</span>
            <span className="text-sm">{label}</span>
          </Link>
        ))}
      </nav>

      {user.name && (
        <div className="mt-auto p-4 rounded-xl bg-primary/5 border border-primary/10">
          <p className="text-xs text-primary font-bold uppercase tracking-wider mb-1">Logged in as</p>
          <p className="text-sm font-semibold text-deep-midnight">{user.name}</p>
        </div>
      )}
    </aside>
  );
}

export default function Dashboard() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isLoggedIn } = useUser();

  const [dashboard, setDashboard] = useState<PatientDashboard | null>(null);
  const [history, setHistory] = useState<UserHistoryContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isLoggedIn) {
      navigate('/');
      return;
    }
    (async () => {
      setLoading(true);
      try {
        const promises: Promise<any>[] = [];
        if (user.patientId) promises.push(therapistApi.getPatientDashboard(user.patientId));
        else promises.push(Promise.resolve(null));
        if (user.meditationUserId) promises.push(journalApi.getUserHistory(user.meditationUserId));
        else promises.push(Promise.resolve({ success: false, user_history_context: null }));
        const [dash, hist] = await Promise.all(promises);
        setDashboard(dash);
        setHistory(hist?.user_history_context ?? null);
      } catch (err: any) {
        setError(err.message ?? 'Failed to load dashboard data.');
      } finally {
        setLoading(false);
      }
    })();
  }, [user, isLoggedIn]);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  const emotionEntries: [string, number][] = history
    ? (Object.entries(history.emotional_baseline) as [string, number][]).sort((a, b) => b[1] - a[1]).slice(0, 3)
    : [];

  return (
    <div className="flex h-screen overflow-hidden bg-soft-sand text-deep-midnight font-display">
      <Sidebar pathname={location.pathname} />

      <main className="flex-1 overflow-y-auto relative">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full digital-twin-orb -z-10"></div>

        <div className="max-w-5xl mx-auto p-10">
          <header className="mb-10">
            <h2 className="text-4xl font-black text-deep-midnight mb-2">
              {greeting}, {user.name || 'friend'} 🌿
            </h2>
            <p className="text-lg text-deep-midnight/60">
              {loading ? 'Loading your wellness data…' : error ? error : 'Here\'s your wellness overview.'}
            </p>
          </header>

          {loading ? (
            <div className="flex items-center justify-center h-64">
              <span className="material-symbols-outlined animate-spin text-4xl text-primary">refresh</span>
            </div>
          ) : (
            <>
              {/* Stats Row */}
              <div className="grid grid-cols-3 gap-6 mb-10">
                <div className="glass p-6 rounded-xl flex flex-col gap-2">
                  <span className="material-symbols-outlined text-primary">calendar_today</span>
                  <p className="text-3xl font-black">{dashboard?.summary.total_sessions ?? '—'}</p>
                  <p className="text-sm text-deep-midnight/60">Total Sessions</p>
                </div>
                <div className="glass p-6 rounded-xl flex flex-col gap-2">
                  <span className="material-symbols-outlined text-primary">task_alt</span>
                  <p className="text-3xl font-black">{dashboard?.summary.active_goals ?? '—'}</p>
                  <p className="text-sm text-deep-midnight/60">Active Goals</p>
                </div>
                <div className="glass p-6 rounded-xl flex flex-col gap-2">
                  <span className="material-symbols-outlined text-primary">book_5</span>
                  <p className="text-3xl font-black">{history?.total_entries ?? '—'}</p>
                  <p className="text-sm text-deep-midnight/60">Journal Entries</p>
                </div>
              </div>

              {/* Mood / Emotional baseline */}
              {emotionEntries.length > 0 && (
                <section className="mb-10">
                  <h3 className="text-2xl font-bold mb-6">Emotional Baseline</h3>
                  <div className="flex gap-6 flex-wrap">
                    {emotionEntries.map(([emotion, score]) => (
                      <div key={emotion} className="glass p-4 rounded-xl flex-1 min-w-[140px]">
                        <p className="text-sm font-semibold capitalize text-deep-midnight/80">{emotion}</p>
                        <div className="w-full bg-primary/10 h-2 rounded-full mt-2">
                          <div
                            className="bg-primary h-full rounded-full"
                            style={{ width: `${Math.round(score * 100)}%` }}
                          ></div>
                        </div>
                        <p className="text-xs text-deep-midnight/50 mt-1">{Math.round(score * 100)}%</p>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* Wellness Insights */}
              <section>
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-2xl font-bold">Wellness Insights</h3>
                </div>
                <div className="flex gap-6 overflow-x-auto pb-4 scrollbar-hide">
                  {history && (
                    <div className="min-w-[280px] glass p-6 rounded-xl flex flex-col gap-4">
                      <div className="size-12 rounded-full bg-primary/20 flex items-center justify-center text-primary">
                        <span className="material-symbols-outlined">edit_note</span>
                      </div>
                      <div>
                        <h4 className="font-bold text-lg">Writing Habit</h4>
                        <p className="text-sm text-deep-midnight/70">
                          {history.writing_frequency_baseline.toFixed(1)} entries per week avg.
                        </p>
                      </div>
                      <div className="mt-auto pt-4 border-t border-primary/10">
                        <span className="text-xs font-bold text-primary">
                          Favourite times: {history.preferred_writing_times.join(', ')}
                        </span>
                      </div>
                    </div>
                  )}

                  {history && (
                    <div className="min-w-[280px] glass p-6 rounded-xl flex flex-col gap-4">
                      <div className="size-12 rounded-full bg-lavender/20 flex items-center justify-center text-lavender">
                        <span className="material-symbols-outlined">psychology</span>
                      </div>
                      <div>
                        <h4 className="font-bold text-lg">Emotional Stability</h4>
                        <p className="text-sm text-deep-midnight/70">
                          Volatility score: {Math.round(history.emotional_volatility * 100)}%
                          {history.emotional_volatility < 0.4 ? ' — quite stable' : ' — some variation'}
                        </p>
                      </div>
                      <div className="mt-auto pt-4 border-t border-primary/10">
                        <span className="text-xs font-bold text-primary">
                          Topics: {history.topic_preferences.slice(0, 3).join(', ')}
                        </span>
                      </div>
                    </div>
                  )}

                  {dashboard?.summary.detected_symptoms && dashboard.summary.detected_symptoms.length > 0 && (
                    <div className="min-w-[280px] glass p-6 rounded-xl flex flex-col gap-4">
                      <div className="size-12 rounded-full bg-sage/20 flex items-center justify-center text-sage">
                        <span className="material-symbols-outlined">monitor_heart</span>
                      </div>
                      <div>
                        <h4 className="font-bold text-lg">Detected Patterns</h4>
                        <p className="text-sm text-deep-midnight/70">
                          {dashboard.summary.detected_symptoms.slice(0, 3).join(', ')}
                        </p>
                      </div>
                      <div className="mt-auto pt-4 border-t border-primary/10">
                        <Link to="/sessions" className="text-xs font-bold text-primary">
                          Start a Therapy Session →
                        </Link>
                      </div>
                    </div>
                  )}

                  {!history && !dashboard && (
                    <div className="min-w-[280px] glass p-6 rounded-xl flex flex-col gap-4">
                      <div className="size-12 rounded-full bg-primary/20 flex items-center justify-center text-primary">
                        <span className="material-symbols-outlined">wb_sunny</span>
                      </div>
                      <div>
                        <h4 className="font-bold text-lg">Getting Started</h4>
                        <p className="text-sm text-deep-midnight/70">
                          Write your first journal entry or start a therapy session to see insights here.
                        </p>
                      </div>
                      <div className="mt-auto pt-4 border-t border-primary/10">
                        <Link to="/journal" className="text-xs font-bold text-primary">
                          Open Journal →
                        </Link>
                      </div>
                    </div>
                  )}
                </div>
              </section>
            </>
          )}
        </div>
      </main>

      {/* Right Sidebar */}
      <aside className="w-80 border-l border-primary/10 bg-white/40 backdrop-blur-md p-8 flex flex-col gap-10 overflow-y-auto">
        {/* Active Goals */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-lg">Active Goals</h3>
            <Link to="/sessions">
              <span className="material-symbols-outlined text-primary cursor-pointer">add_circle</span>
            </Link>
          </div>
          <div className="flex flex-col gap-4">
            {dashboard?.active_goals.length ? (
              dashboard.active_goals.slice(0, 3).map((goal) => (
                <div key={goal.id} className="p-4 rounded-xl bg-white shadow-sm border border-primary/5">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium line-clamp-1">{goal.description}</span>
                    <span className="text-xs font-bold text-primary ml-2 flex-shrink-0">
                      {goal.current_progress}%
                    </span>
                  </div>
                  <div className="w-full bg-primary/10 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-primary h-full rounded-full"
                      style={{ width: `${goal.current_progress}%` }}
                    ></div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-deep-midnight/50 italic">
                No active goals yet. Start a therapy session to set your goals.
              </p>
            )}
          </div>
        </section>

        {/* Pending Homework */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-lg">Pending Homework</h3>
          </div>
          <div className="flex flex-col gap-3">
            {dashboard?.pending_homework.length ? (
              dashboard.pending_homework.slice(0, 4).map((hw) => (
                <div
                  key={hw.id}
                  className="flex items-start gap-3 p-3 rounded-lg hover:bg-white transition-colors group cursor-pointer"
                >
                  <div className="mt-1 size-5 rounded border-2 border-primary/30 flex items-center justify-center group-hover:border-primary flex-shrink-0">
                    <span className="material-symbols-outlined text-xs text-white">check</span>
                  </div>
                  <div>
                    <p className="text-sm font-semibold line-clamp-1">{hw.description}</p>
                    <p className="text-xs text-deep-midnight/50">
                      {hw.type} • Due {new Date(hw.due_date).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-deep-midnight/50 italic">No pending homework.</p>
            )}
          </div>
        </section>

        {/* Start Session CTA */}
        <div className="mt-auto bg-deep-midnight text-white p-6 rounded-xl">
          <p className="text-xs text-white/60 font-medium uppercase tracking-widest mb-2">AI Therapist</p>
          <h4 className="font-bold text-lg mb-2">Dr. Maya</h4>
          <p className="text-sm text-white/70 mb-4">
            {dashboard?.latest_session
              ? `Last session: ${new Date(dashboard.latest_session.session_date).toLocaleDateString()}`
              : 'Ready for your first session'}
          </p>
          <Link
            to="/sessions"
            className="block text-center w-full bg-primary hover:bg-primary/90 py-3 rounded-full font-bold text-sm transition-transform active:scale-95"
          >
            Start Session
          </Link>
        </div>
      </aside>
    </div>
  );
}
