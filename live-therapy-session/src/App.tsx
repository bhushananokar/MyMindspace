import React, { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Mic, MicOff, PhoneOff, Phone, Send } from 'lucide-react';
import { GoogleGenAI, LiveServerMessage, Modality } from '@google/genai';
import { AudioStreamer } from './AudioStreamer';

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

export default function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isMicActive, setIsMicActive] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [textInput, setTextInput] = useState('');
  
  const sessionRef = useRef<any>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioStreamerRef = useRef<AudioStreamer | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);

  const startSession = async () => {
    try {
      setIsConnecting(true);
      
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
      audioContextRef.current = audioCtx;
      audioStreamerRef.current = new AudioStreamer(audioCtx);

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      const source = audioCtx.createMediaStreamSource(stream);

      const workletCode = `
        class PCMProcessor extends AudioWorkletProcessor {
          process(inputs, outputs, parameters) {
            const input = inputs[0];
            if (input && input.length > 0) {
              const channelData = input[0];
              const pcm16 = new Int16Array(channelData.length);
              for (let i = 0; i < channelData.length; i++) {
                pcm16[i] = Math.max(-1, Math.min(1, channelData[i])) * 0x7FFF;
              }
              this.port.postMessage(pcm16.buffer, [pcm16.buffer]);
            }
            return true;
          }
        }
        registerProcessor('pcm-processor', PCMProcessor);
      `;
      const blob = new Blob([workletCode], { type: 'application/javascript' });
      const workletUrl = URL.createObjectURL(blob);
      await audioCtx.audioWorklet.addModule(workletUrl);
      
      const workletNode = new AudioWorkletNode(audioCtx, 'pcm-processor');
      workletNodeRef.current = workletNode;
      source.connect(workletNode);
      workletNode.connect(audioCtx.destination);

      const sessionPromise = ai.live.connect({
        model: "gemini-2.5-flash-native-audio-preview-09-2025",
        config: {
          responseModalities: [Modality.AUDIO],
          speechConfig: {
            voiceConfig: { prebuiltVoiceConfig: { voiceName: "Aoede" } },
          },
          systemInstruction: "You are Dr. Maya, an empathetic, professional, and warm AI therapist. You listen actively and provide thoughtful, supportive responses. Keep your responses concise and conversational, suitable for a voice interaction.",
        },
        callbacks: {
          onopen: () => {
            setIsConnected(true);
            setIsConnecting(false);
            setIsMicActive(true);
            setIsListening(true);
            
            workletNode.port.onmessage = (e) => {
              const pcmBuffer = e.data;
              const base64 = btoa(String.fromCharCode(...new Uint8Array(pcmBuffer)));
              sessionPromise.then(session => {
                session.sendRealtimeInput({
                  media: { data: base64, mimeType: 'audio/pcm;rate=16000' }
                });
              });
            };
          },
          onmessage: (message: LiveServerMessage) => {
            if (message.serverContent?.modelTurn) {
              const parts = message.serverContent.modelTurn.parts;
              for (const part of parts) {
                if (part.inlineData && part.inlineData.data) {
                  audioStreamerRef.current?.addPCM16(part.inlineData.data);
                }
              }
            }
            if (message.serverContent?.interrupted) {
              audioStreamerRef.current?.stop();
            }
          },
          onclose: () => {
            cleanup();
          },
          onerror: (error) => {
            console.error("Live API Error:", error);
            cleanup();
          }
        }
      });

      sessionRef.current = sessionPromise;

    } catch (error) {
      console.error("Failed to start session:", error);
      cleanup();
    }
  };

  const cleanup = () => {
    setIsConnected(false);
    setIsConnecting(false);
    setIsMicActive(false);
    setIsListening(false);
    
    if (workletNodeRef.current) {
      workletNodeRef.current.disconnect();
      workletNodeRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    if (sessionRef.current) {
      sessionRef.current.then((session: any) => session.close()).catch(() => {});
      sessionRef.current = null;
    }
  };

  const toggleSession = () => {
    if (isConnected || isConnecting) {
      cleanup();
    } else {
      startSession();
    }
  };

  const sendTextMessage = () => {
    if (!textInput.trim() || !sessionRef.current) return;
    
    sessionRef.current.then((session: any) => {
      try {
        if (session.send) {
          session.send({
            clientContent: {
              turns: [{ role: "user", parts: [{ text: textInput }] }],
              turnComplete: true,
            }
          });
        }
      } catch (e) {
        console.error("Failed to send text:", e);
      }
    });
    setTextInput('');
  };

  useEffect(() => {
    return () => cleanup();
  }, []);

  return (
    <div className="flex h-screen w-full text-white font-sans overflow-hidden" style={{ backgroundColor: '#221e34' }}>
      {/* Sidebar */}
      <div className="w-64 flex-shrink-0 flex flex-col border-r border-white/5" style={{ backgroundColor: '#1a172a' }}>
        <div className="p-6 flex items-center gap-3 text-gray-300 hover:text-white cursor-pointer transition-colors">
          <ArrowLeft size={20} />
          <span className="font-medium">Dashboard</span>
        </div>
        
        <div className="flex flex-col items-center mt-4 mb-10">
          <div className="w-20 h-20 rounded-full overflow-hidden border-2 border-[#6d58bf]/50 mb-4 relative shadow-[0_0_15px_rgba(109,88,191,0.3)]">
            <img src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?q=80&w=200&h=200&auto=format&fit=crop" alt="Dr. Maya" className="w-full h-full object-cover" />
          </div>
          <h2 className="text-xl font-semibold">Dr. Maya</h2>
          <p className="text-xs text-gray-400 mt-1">AI Therapist · Gemini Live</p>
        </div>

        <div className="px-6 flex-1">
          <h3 className="text-[11px] font-bold text-gray-500 tracking-wider mb-4 uppercase">Session Status</h3>
          <div className="space-y-3 text-sm">
            <div className="flex items-center gap-3">
              <div className={`w-2 h-2 rounded-full ${isMicActive ? 'bg-red-500' : 'bg-gray-600'}`}></div>
              <span className={isMicActive ? 'text-gray-200' : 'text-gray-500'}>Microphone active</span>
            </div>
            <div className="flex items-center gap-3">
              <div className={`w-2 h-2 rounded-full ${isListening ? 'bg-gray-400' : 'bg-gray-600'}`}></div>
              <span className={isListening ? 'text-gray-200' : 'text-gray-500'}>Listening...</span>
            </div>
            <div className="flex items-center gap-3">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-600'}`}></div>
              <span className={isConnected ? 'text-gray-200' : 'text-gray-500'}>Gemini Live connected</span>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="bg-white/5 rounded-full px-4 py-2 border border-white/5">
            <div className="text-[9px] text-gray-500 uppercase tracking-wider mb-0.5">Model</div>
            <div className="text-[11px] text-gray-300 truncate">gemini-2.5-flash-native-au...</div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col relative bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-[#2a2542] to-[#221e34]">
        {/* Top Bar */}
        <div className="h-20 flex-shrink-0 flex items-center justify-between px-8 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-600'}`}></div>
            <span className="font-semibold tracking-wide text-sm text-gray-200">LIVE THERAPY SESSION</span>
          </div>
          <button 
            onClick={toggleSession}
            disabled={isConnecting}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-full transition-colors border font-medium text-sm ${
              isConnected 
                ? 'bg-red-500/10 text-red-400 hover:bg-red-500/20 border-red-500/20' 
                : 'bg-green-500/10 text-green-400 hover:bg-green-500/20 border-green-500/20'
            } ${isConnecting ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isConnected ? (
              <>
                <PhoneOff size={16} />
                End Session
              </>
            ) : (
              <>
                <Phone size={16} />
                {isConnecting ? 'Connecting...' : 'Start Session'}
              </>
            )}
          </button>
        </div>

        {/* Center Content */}
        <div className="flex-1 flex flex-col items-center justify-center">
          <div className={`w-24 h-24 rounded-full flex items-center justify-center mb-6 transition-all duration-500 ${
            isConnected 
              ? 'bg-[#6d58bf] shadow-[0_0_50px_rgba(109,88,191,0.5)] scale-100' 
              : 'bg-gray-700/50 scale-95'
          }`}>
            <Mic size={32} className={isConnected ? 'text-white' : 'text-gray-400'} />
          </div>
          <h2 className="text-2xl font-semibold mb-2 text-gray-100">
            {isConnected ? 'Dr. Maya is listening' : 'Session Ended'}
          </h2>
          <p className="text-gray-400 text-sm">
            {isConnected ? 'Just speak — no buttons to press' : 'Click Start Session to begin'}
          </p>
        </div>

        {/* Bottom Area */}
        <div className="p-8 flex flex-col items-center flex-shrink-0">
          <div className="flex items-center gap-4 mb-6">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full border transition-colors ${
              isListening 
                ? 'bg-white/5 border-white/10' 
                : 'bg-transparent border-transparent opacity-50'
            }`}>
              <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                isListening ? 'bg-red-500' : 'bg-gray-700'
              }`}>
                <Mic size={10} className="text-white" />
              </div>
              <span className="text-xs text-gray-300">Listening</span>
            </div>
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full border transition-colors ${
              !isListening 
                ? 'bg-white/5 border-white/10' 
                : 'bg-transparent border-transparent opacity-50'
            }`}>
              <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                !isListening ? 'bg-gray-600' : 'bg-gray-700'
              }`}>
                <MicOff size={10} className="text-gray-300" />
              </div>
              <span className="text-xs text-gray-400">Waiting</span>
            </div>
          </div>

          <div className="w-full max-w-3xl relative">
            <input 
              type="text" 
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendTextMessage()}
              disabled={!isConnected}
              placeholder="Or type a message..." 
              className="w-full bg-white/5 border border-white/10 rounded-full py-3.5 pl-6 pr-16 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-white/20 focus:bg-white/10 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <button 
              onClick={sendTextMessage}
              disabled={!isConnected || !textInput.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-[#6d58bf] flex items-center justify-center hover:bg-[#5a48a3] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send size={16} className="text-white ml-0.5" />
            </button>
          </div>
          <p className="text-[10px] text-gray-500 tracking-widest uppercase mt-4">
            Microphone active · Just speak naturally
          </p>
        </div>
      </div>
    </div>
  );
}
