import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import { therapistApi, meditationApi } from '../services/api';

export default function Welcome() {
  const navigate = useNavigate();
  const { user, setUser, isLoggedIn } = useUser();

  const [name, setName] = useState('');
  const [dob, setDob] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);

  // If already registered, offer to continue
  useEffect(() => {
    if (isLoggedIn) {
      // do nothing – show buttons below
    }
  }, [isLoggedIn]);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) { setError('Please enter your name.'); return; }
    setError('');
    setLoading(true);
    try {
      const [patient, medUser] = await Promise.all([
        therapistApi.createPatient(name.trim(), dob || undefined),
        meditationApi.createUser(name.trim()),
      ]);
      setUser({
        patientId: patient.id,
        meditationUserId: medUser.user_id,
        name: name.trim(),
      });
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message ?? 'Could not connect to the service. Check your backend URLs.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen w-full flex-col items-center justify-center p-6 bg-background-light dark:bg-background-dark overflow-hidden">
      {/* Background Orb */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden">
        <div className="orb-gradient w-[500px] h-[500px] rounded-full mix-blend-multiply opacity-40 animate-pulse"></div>
      </div>

      <div className="relative z-10 w-full max-w-xl flex flex-col items-center text-center">
        {/* Logo Orb */}
        <div className="w-full max-w-[400px] aspect-square flex items-center justify-center mb-12">
          <div className="relative w-full h-full flex items-center justify-center">
            <div className="w-64 h-64 rounded-full bg-gradient-to-tr from-primary to-accent shadow-2xl shadow-primary/30 flex items-center justify-center">
              <span className="material-symbols-outlined text-7xl text-white/90">spa</span>
            </div>
            <div className="absolute top-10 right-10 w-12 h-12 rounded-full bg-primary/20 backdrop-blur-sm"></div>
            <div className="absolute bottom-10 left-10 w-16 h-16 rounded-full bg-accent/20 backdrop-blur-sm"></div>
          </div>
        </div>

        <div className="space-y-6 w-full">
          <h1 className="font-serif text-6xl md:text-7xl text-dark-text dark:text-slate-100">
            MyMindSpace
          </h1>
          <p className="text-lg md:text-xl font-normal text-dark-text/70 dark:text-slate-300 max-w-md mx-auto">
            Your safe space to breathe, reflect, and grow.
          </p>

          {/* Registration form */}
          {showForm ? (
            <form onSubmit={handleRegister} className="flex flex-col gap-4 pt-4 w-full max-w-sm mx-auto">
              <input
                type="text"
                placeholder="Your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="h-12 rounded-full px-6 border-2 border-primary/30 bg-white/80 text-slate-800 text-base focus:outline-none focus:border-primary transition-all"
              />
              <input
                type="date"
                placeholder="Date of birth (optional)"
                value={dob}
                onChange={(e) => setDob(e.target.value)}
                className="h-12 rounded-full px-6 border-2 border-primary/30 bg-white/80 text-slate-600 text-base focus:outline-none focus:border-primary transition-all"
              />
              {error && (
                <p className="text-red-500 text-sm px-2">{error}</p>
              )}
              <button
                type="submit"
                disabled={loading}
                className="flex h-14 w-full items-center justify-center rounded-full bg-primary text-white text-lg font-semibold tracking-wide hover:shadow-lg hover:shadow-primary/20 transition-all disabled:opacity-60"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="material-symbols-outlined animate-spin text-xl">refresh</span>
                    Setting up your space…
                  </span>
                ) : 'Begin My Journey'}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="text-sm text-primary/70 hover:text-primary transition-colors"
              >
                ← Back
              </button>
            </form>
          ) : (
            <div className="flex flex-col gap-4 pt-8 w-full max-w-sm mx-auto">
              {isLoggedIn ? (
                <>
                  <p className="text-sm text-primary font-semibold">
                    Welcome back, {user.name} ✨
                  </p>
                  <button
                    onClick={() => navigate('/dashboard')}
                    className="flex h-14 w-full items-center justify-center rounded-full bg-primary text-white text-lg font-semibold tracking-wide hover:shadow-lg hover:shadow-primary/20 transition-all"
                  >
                    Continue to Dashboard
                  </button>
                  <button
                    onClick={() => setShowForm(true)}
                    className="flex h-14 w-full items-center justify-center rounded-full border-2 border-primary/40 bg-transparent text-primary text-lg font-semibold tracking-wide hover:bg-primary/5 transition-all"
                  >
                    Register New Account
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setShowForm(true)}
                    className="flex h-14 w-full items-center justify-center rounded-full bg-primary text-white text-lg font-semibold tracking-wide hover:shadow-lg hover:shadow-primary/20 transition-all"
                  >
                    Get Started
                  </button>
                  <button
                    onClick={() => setShowForm(true)}
                    className="flex h-14 w-full items-center justify-center rounded-full border-2 border-primary/40 bg-transparent text-primary text-lg font-semibold tracking-wide hover:bg-primary/5 transition-all"
                  >
                    I already have an account
                  </button>
                </>
              )}
            </div>
          )}

          <div className="pt-12 flex flex-col items-center gap-2">
            <div className="flex items-center gap-2 text-dark-text/50 dark:text-slate-400 text-sm font-medium">
              <span className="material-symbols-outlined text-sm">lock</span>
              <span>Your thoughts are private. Always.</span>
            </div>
          </div>
        </div>
      </div>

      <div className="absolute top-0 left-0 -translate-x-1/2 -translate-y-1/2 w-[40vw] h-[40vw] rounded-full bg-primary/5"></div>
      <div className="absolute bottom-0 right-0 translate-x-1/3 translate-y-1/3 w-[30vw] h-[30vw] rounded-full bg-accent/5"></div>
    </div>
  );
}
