import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'motion/react';
import { useUser } from '../context/UserContext';
import { journalApi, sttApi, geminiEngineApi } from '../services/api';

function generateId(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

interface JournalPage {
  id: string;
  text: string;
  date: string;
  processed: boolean;
  processing: boolean;
}

interface ChatMessage {
  role: 'user' | 'ai';
  text: string;
  suggestions?: string[];
}

const STORAGE_KEY = 'mymindspace_journal';
const CONV_ID = 'journal_conv_' + new Date().toISOString().slice(0, 10);

function loadPages(): JournalPage[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function savePages(pages: JournalPage[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(pages));
}

function todayLabel() {
  return new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
}

interface PageContentProps {
  page: JournalPage;
  pageNum: number;
  isLeft: boolean;
  onChange: (text: string) => void;
  today: string;
  onSave: () => void;
  onVoiceRecord: () => void;
  transcribing: boolean;
  sttError: string;
  onOpenChat: () => void;
  chatOpen: boolean;
}

const PageContent = ({ page, pageNum, isLeft, onChange, today, onSave, onVoiceRecord, transcribing, sttError, onOpenChat, chatOpen }: PageContentProps) => (
  <div className={`w-1/2 h-full p-12 flex flex-col relative overflow-hidden ${isLeft ? '' : 'bg-[#FEFCF8]'}`}>
    <div className="absolute inset-0 opacity-50 pointer-events-none"
      style={{ backgroundImage: 'url("https://www.transparenttextures.com/patterns/lined-paper.png")' }}></div>

    <div className="relative z-10 flex-1 flex flex-col">
      <div className="flex justify-between items-end mb-8 border-b-2 border-primary/20 pb-4">
        <div>
          <h2 className="font-serif text-3xl text-slate-800 italic">{page.date === today ? 'Dear Diary,' : 'Entry'}</h2>
          <p className="text-xs text-slate-500 font-sans uppercase tracking-widest mt-2">{page.date}</p>
        </div>
        {!isLeft && (
          <div className="flex gap-2 items-center">
            {sttError && <p className="text-red-400 text-xs max-w-[100px] text-right">{sttError}</p>}
            <button onClick={onVoiceRecord} disabled={transcribing}
              title="Record voice note"
              className={`p-2 rounded-full hover:bg-primary/5 transition-colors ${transcribing ? 'text-primary animate-pulse' : 'text-slate-400 hover:text-primary'}`}>
              <span className="material-symbols-outlined text-xl">{transcribing ? 'mic' : 'mic_none'}</span>
            </button>
          </div>
        )}
      </div>

      <div className="flex-1 relative">
        <div className="absolute inset-0 pointer-events-none" style={{
          backgroundImage: 'repeating-linear-gradient(transparent, transparent 31px, #E5E0D8 31px, #E5E0D8 32px)',
          backgroundPosition: '0 4px'
        }}></div>
        <textarea
          className="w-full h-full bg-transparent border-none resize-none focus:ring-0 text-slate-700 font-serif text-lg leading-[32px] p-0 m-0 outline-none"
          placeholder="Start writing your thoughts here..."
          value={page.text}
          onChange={(e) => onChange(e.target.value)}
          style={{ lineHeight: '32px' }}
        />
      </div>

      <div className="mt-6 flex justify-between items-center pt-4">
        <div className="flex gap-2 items-center flex-wrap">
          {page.text.length > 0 && !isLeft && (
            <>
              {page.processed ? (
                <>
                  <span className="px-3 py-1 bg-green-100 text-green-600 rounded-full text-[10px] font-bold uppercase tracking-wider border border-green-200 flex items-center gap-1">
                    <span className="material-symbols-outlined text-xs">check_circle</span> Analysed
                  </span>
                  <button onClick={onOpenChat}
                    className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 transition-colors ${chatOpen ? 'bg-primary text-white' : 'bg-primary/10 text-primary hover:bg-primary/20 border border-primary/20'}`}>
                    <span className="material-symbols-outlined text-xs">chat</span>
                    {chatOpen ? 'Chat open' : 'Chat with AI'}
                  </button>
                </>
              ) : page.processing ? (
                <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-[10px] font-bold uppercase tracking-wider border border-primary/20 flex items-center gap-1">
                  <span className="material-symbols-outlined text-xs animate-spin">refresh</span> Processing
                </span>
              ) : (
                <button onClick={onSave}
                  className="px-3 py-1 bg-primary text-white rounded-full text-[10px] font-bold uppercase tracking-wider hover:bg-primary/90 transition-colors flex items-center gap-1">
                  <span className="material-symbols-outlined text-xs">save</span> Save & Analyse
                </button>
              )}
            </>
          )}
        </div>
      </div>

      <div className="mt-4 text-center text-slate-400 font-serif text-sm">- {pageNum} -</div>
    </div>
  </div>
);

export default function Journal() {
  const { user } = useUser();
  const today = todayLabel();

  const [pages, setPages] = useState<JournalPage[]>(() => {
    const stored = loadPages();
    if (stored.length === 0 || stored[stored.length - 1].date !== today) {
      const initial: JournalPage[] = [
        ...stored,
        { id: generateId(), text: '', date: today, processed: false, processing: false },
        { id: generateId(), text: '', date: today, processed: false, processing: false },
      ];
      savePages(initial);
      return initial;
    }
    return stored;
  });

  const [spreadIndex, setSpreadIndex] = useState(() => {
    const stored = loadPages();
    return Math.max(0, Math.floor((stored.length - 1) / 2));
  });
  const [direction, setDirection] = useState(0);
  const [transcribing, setTranscribing] = useState(false);
  const [sttError, setSttError] = useState('');

  // Chat state
  const [chatOpen, setChatOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState('');
  const chatBottomRef = useRef<HTMLDivElement>(null);

  const mediaRecorderRef = React.useRef<MediaRecorder | null>(null);
  const chunksRef = React.useRef<Blob[]>([]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, chatLoading]);

  const handleOpenChat = useCallback(() => {
    setChatOpen(true);
    if (messages.length === 0) {
      setMessages([{
        role: 'ai',
        text: "Hi! I've read your journal entry. How are you feeling right now, or is there something you'd like to explore further?",
      }]);
    }
  }, [messages.length]);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || chatLoading || !user.meditationUserId) return;
    const userMsg: ChatMessage = { role: 'user', text: text.trim() };
    setMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setChatLoading(true);
    setChatError('');
    try {
      const res = await geminiEngineApi.chat(user.meditationUserId, text.trim(), CONV_ID);
      const aiMsg: ChatMessage = {
        role: 'ai',
        text: res.enhanced_response,
        suggestions: res.follow_up_suggestions ?? undefined,
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (e: any) {
      setChatError(e.message ?? 'Could not reach the AI engine.');
    } finally {
      setChatLoading(false);
    }
  }, [chatLoading, user.meditationUserId]);

  const handleVoiceRecord = useCallback(async () => {
    if (transcribing) return;
    setSttError('');
    setTranscribing(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => chunksRef.current.push(e.data);
      mr.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const blob = new Blob(chunksRef.current, { type: 'audio/wav' });
        try {
          const { transcript } = await sttApi.transcribe(blob);
          if (transcript) {
            const rightIdx = spreadIndex * 2 + 1;
            updatePageText(rightIdx, pages[rightIdx]?.text + (pages[rightIdx]?.text ? '\n' : '') + transcript);
          } else { setSttError('No speech detected.'); }
        } catch (err: any) { setSttError((err as any).message ?? 'STT unavailable.'); }
        setTranscribing(false);
      };
      mr.start();
      mediaRecorderRef.current = mr;
      setTimeout(() => { if (mr.state === 'recording') mr.stop(); }, 30000);
      setTimeout(() => { if (mr.state === 'recording') mr.stop(); }, 5000);
    } catch { setSttError('Microphone access denied.'); setTranscribing(false); }
  }, [transcribing, spreadIndex, pages]);

  const handleNext = () => {
    setDirection(1);
    if ((spreadIndex + 1) * 2 >= pages.length) {
      const newPages = [
        ...pages,
        { id: generateId(), text: '', date: today, processed: false, processing: false },
        { id: generateId(), text: '', date: today, processed: false, processing: false },
      ];
      setPages(newPages);
      savePages(newPages);
    }
    setSpreadIndex(spreadIndex + 1);
  };

  const handlePrev = () => {
    if (spreadIndex > 0) { setDirection(-1); setSpreadIndex(spreadIndex - 1); }
  };

  const updatePageText = (index: number, text: string) => {
    const newPages = [...pages];
    if (newPages[index]) {
      newPages[index] = { ...newPages[index], text };
      setPages(newPages);
      savePages(newPages);
    }
  };

  const handleSave = async (pageIndex: number) => {
    const page = pages[pageIndex];
    if (!page || !page.text.trim()) return;
    const newPages = [...pages];
    newPages[pageIndex] = { ...page, processing: true };
    setPages(newPages);
    savePages(newPages);

    if (user.meditationUserId) {
      try {
        await journalApi.processJournal(page.id, user.meditationUserId, false);
        const updated = [...newPages];
        updated[pageIndex] = { ...updated[pageIndex], processing: false, processed: true };
        setPages(updated);
        savePages(updated);
      } catch {
        const updated = [...newPages];
        updated[pageIndex] = { ...updated[pageIndex], processing: false };
        setPages(updated);
        savePages(updated);
      }
    } else {
      const updated = [...newPages];
      updated[pageIndex] = { ...updated[pageIndex], processing: false };
      setPages(updated);
      savePages(updated);
    }
  };

  const leftPage = pages[spreadIndex * 2];
  const rightPage = pages[spreadIndex * 2 + 1];
  const rightIndex = spreadIndex * 2 + 1;
  const hasProcessedEntry = pages.some(p => p.processed);

  const variants = {
    enter: (dir: number) => ({ x: dir > 0 ? 50 : -50, opacity: 0 }),
    center: { zIndex: 1, x: 0, opacity: 1 },
    exit: (dir: number) => ({ zIndex: 0, x: dir < 0 ? 50 : -50, opacity: 0 }),
  };

  return (
    <div className="flex h-screen overflow-hidden bg-soft-sand text-deep-midnight font-display">
      {/* Left sidebar nav */}
      <aside className="w-64 flex-shrink-0 flex flex-col border-r border-primary/10 bg-white/50 backdrop-blur-md p-6 z-10">
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
            { to: '/journal', icon: 'book_5', label: 'Journal', active: true },
            { to: '/sessions', icon: 'self_care', label: 'Therapy' },
            { to: '/meditate', icon: 'dark_mode', label: 'Meditate' },
            { to: '/profile', icon: 'account_circle', label: 'Profile' },
          ].map(({ to, icon, label, active }) => (
            <Link key={to} to={to}
              className={`flex items-center gap-3 px-4 py-3 rounded-full font-medium transition-colors ${active ? 'bg-primary text-white' : 'text-deep-midnight/70 hover:bg-primary/10'}`}>
              <span className="material-symbols-outlined">{icon}</span>
              <span className="text-sm">{label}</span>
            </Link>
          ))}
        </nav>

        <div className="mt-6 p-4 rounded-xl bg-primary/5 border border-primary/10">
          <p className="text-xs text-primary font-bold uppercase tracking-wider mb-1">Entries</p>
          <p className="text-2xl font-black">{pages.filter(p => p.text.trim().length > 0).length}</p>
          <p className="text-xs text-deep-midnight/50">pages written</p>
        </div>
      </aside>

      {/* Main journal book area */}
      <main className="flex-1 overflow-hidden relative bg-[#EBE7DF] flex items-center justify-center p-8 min-w-0">
        <div className="absolute inset-0 opacity-40 mix-blend-multiply pointer-events-none"
          style={{ backgroundImage: 'url("https://www.transparenttextures.com/patterns/cream-paper.png")' }}></div>

        <div className="absolute left-12 top-1/2 -translate-y-1/2 z-30">
          <button onClick={handlePrev} disabled={spreadIndex === 0}
            className="p-4 bg-white/80 hover:bg-white rounded-full shadow-lg disabled:opacity-30 transition-all text-primary">
            <span className="material-symbols-outlined text-3xl">chevron_left</span>
          </button>
        </div>
        <div className="absolute right-12 top-1/2 -translate-y-1/2 z-30">
          <button onClick={handleNext}
            className="p-4 bg-white/80 hover:bg-white rounded-full shadow-lg transition-all text-primary">
            <span className="material-symbols-outlined text-3xl">chevron_right</span>
          </button>
        </div>

        <div className="relative w-full max-w-5xl h-[85vh] flex shadow-2xl rounded-r-xl rounded-l-sm bg-[#FDFBF7] border border-[#D1C9B8] z-10">
          <div className="absolute left-1/2 top-0 bottom-0 w-12 -ml-6 bg-gradient-to-r from-transparent via-black/10 to-transparent pointer-events-none z-20"></div>
          <div className="absolute left-1/2 top-0 bottom-0 w-px bg-[#D1C9B8] pointer-events-none z-20"></div>

          <div className="relative w-full h-full overflow-hidden rounded-r-xl rounded-l-sm">
            <AnimatePresence mode="wait" custom={direction}>
              <motion.div key={spreadIndex} custom={direction} variants={variants}
                initial="enter" animate="center" exit="exit"
                transition={{ duration: 0.3, ease: 'easeInOut' }}
                className="absolute inset-0 flex">
                {leftPage && (
                  <PageContent page={leftPage} pageNum={spreadIndex * 2 + 1} isLeft={true}
                    onChange={(text) => updatePageText(spreadIndex * 2, text)}
                    today={today} onSave={() => handleSave(spreadIndex * 2)}
                    onVoiceRecord={handleVoiceRecord} transcribing={false} sttError=""
                    onOpenChat={handleOpenChat} chatOpen={chatOpen} />
                )}
                {rightPage && (
                  <PageContent page={rightPage} pageNum={spreadIndex * 2 + 2} isLeft={false}
                    onChange={(text) => updatePageText(rightIndex, text)}
                    today={today} onSave={() => handleSave(rightIndex)}
                    onVoiceRecord={handleVoiceRecord} transcribing={transcribing} sttError={sttError}
                    onOpenChat={handleOpenChat} chatOpen={chatOpen} />
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </main>

      {/* AI Chat panel */}
      <AnimatePresence>
        {chatOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 380, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="flex-shrink-0 h-full flex flex-col bg-white border-l border-primary/10 overflow-hidden"
          >
            {/* Chat header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-primary/10 bg-primary/5">
              <div className="flex items-center gap-2">
                <div className="size-8 rounded-full bg-primary flex items-center justify-center text-white">
                  <span className="material-symbols-outlined text-sm">psychology</span>
                </div>
                <div>
                  <p className="text-sm font-bold text-deep-midnight">Journal AI</p>
                  <p className="text-[10px] text-primary">Powered by Gemini + Memory</p>
                </div>
              </div>
              <button onClick={() => setChatOpen(false)}
                className="p-1 rounded-full hover:bg-primary/10 text-slate-400 hover:text-primary transition-colors">
                <span className="material-symbols-outlined text-xl">close</span>
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
              {messages.map((msg, i) => (
                <div key={i} className={`flex flex-col gap-1 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-primary text-white rounded-br-sm'
                      : 'bg-primary/8 text-deep-midnight rounded-bl-sm border border-primary/10'
                  }`}>
                    {msg.text}
                  </div>
                  {msg.suggestions && msg.suggestions.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1 max-w-[90%]">
                      {msg.suggestions.map((s, j) => (
                        <button key={j} onClick={() => sendMessage(s)}
                          className="px-2 py-1 bg-primary/10 text-primary text-[10px] rounded-full border border-primary/20 hover:bg-primary/20 transition-colors text-left">
                          {s}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {chatLoading && (
                <div className="flex items-start">
                  <div className="bg-primary/8 border border-primary/10 px-4 py-3 rounded-2xl rounded-bl-sm flex gap-1 items-center">
                    {[0, 1, 2].map(i => (
                      <span key={i} className="size-1.5 bg-primary rounded-full animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }} />
                    ))}
                  </div>
                </div>
              )}
              {chatError && (
                <p className="text-xs text-red-400 text-center px-4">{chatError}</p>
              )}
              <div ref={chatBottomRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-primary/10">
              <div className="flex gap-2 items-end">
                <textarea
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage(chatInput);
                    }
                  }}
                  placeholder="Ask about your entry…"
                  rows={2}
                  className="flex-1 resize-none rounded-xl border border-primary/20 px-3 py-2 text-sm text-deep-midnight placeholder:text-slate-400 focus:outline-none focus:border-primary/50 bg-primary/3"
                />
                <button
                  onClick={() => sendMessage(chatInput)}
                  disabled={!chatInput.trim() || chatLoading}
                  className="p-2.5 bg-primary text-white rounded-xl hover:bg-primary/90 disabled:opacity-40 transition-colors flex-shrink-0">
                  <span className="material-symbols-outlined text-xl">send</span>
                </button>
              </div>
              <p className="text-[10px] text-slate-400 mt-2 text-center">Enter to send · Shift+Enter for new line</p>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>
    </div>
  );
}
