import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Mic, PhoneOff, Activity, ChevronDown, Loader2, AlertCircle } from 'lucide-react';
import { AgentType } from '../types';
import { generateAgentResponse } from '../services/groqService';

// Fix for framer-motion type issues
const MotionDiv = motion.div as any;

const ELEVEN_LABS_KEY = "sk_7f594a6cee71755bc9550696841d94bdbc6718a6f5d22ed7";

// Voice Configuration (Only EL since Groq doesn't have TTS)
const VOICES = [
  { id: 'bIHbv24MWmeRgasZH58o', label: 'EL - Fin (ElevenLabs)', type: 'ElevenLabs' },
  { id: 'nPczCjzI2devNBz1zQrb', label: 'EL - Adam (ElevenLabs)', type: 'ElevenLabs' },
];

const LiveInterview = () => {
  const [isActive, setIsActive] = useState(false);
  const [status, setStatus] = useState<'idle' | 'listening' | 'speaking' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [volume, setVolume] = useState(50); // Mock volume for visuals since we don't have raw audio bytes easily
  const [selectedVoice, setSelectedVoice] = useState('bIHbv24MWmeRgasZH58o');
  const [isGeneratingTTS, setIsGeneratingTTS] = useState(false);
  
  const recognitionRef = useRef<any>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<AudioBufferSourceNode | null>(null);
  const historyRef = useRef<{ role: 'user' | 'model'; content: string }[]>([]);

  useEffect(() => {
    // Initialize Speech Recognition
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setStatus('listening');
      };

      recognition.onresult = async (event: any) => {
        const transcript = event.results[0][0].transcript;
        console.log("User said:", transcript);
        setStatus('speaking');
        
        // Add to history
        historyRef.current.push({ role: 'user', content: transcript });

        // Call Groq
        const responseText = await generateAgentResponse(transcript, AgentType.INTERVIEW_COACH, historyRef.current);
        historyRef.current.push({ role: 'model', content: responseText });

        // Play audio
        playElevenLabsAudio(responseText, selectedVoice);
      };

      recognition.onerror = (event: any) => {
        if (event.error === 'no-speech') {
            // Restart if no speech detected and we are supposed to be active
            if (isActive) recognition.start();
        } else {
            console.error("Speech Recognition Error:", event.error);
            setStatus('error');
            setErrorMessage(`Speech recognition error: ${event.error}`);
            setIsActive(false);
        }
      };

      recognition.onend = () => {
        // If we are still active and not speaking, restart listening
        // (Handled after TTS finishes)
      };

      recognitionRef.current = recognition;
    } else {
      setErrorMessage("Your browser does not support Speech Recognition. Please use Chrome.");
      setStatus('error');
    }

    return () => {
      if (recognitionRef.current) recognitionRef.current.stop();
      if (audioContextRef.current) audioContextRef.current.close();
    };
  }, [isActive, selectedVoice]);

  const playElevenLabsAudio = async (text: string, voiceId: string) => {
    if (!text.trim()) return;
    
    setIsGeneratingTTS(true);
    try {
      const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId}/stream?optimize_streaming_latency=3`, {
        method: 'POST',
        headers: {
          'xi-api-key': ELEVEN_LABS_KEY,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          model_id: "eleven_turbo_v2_5",
          voice_settings: { stability: 0.5, similarity_boost: 0.7 }
        }),
      });

      if (!response.ok) throw new Error("ElevenLabs API Error");

      const arrayBuffer = await response.arrayBuffer();
      
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      
      const ctx = audioContextRef.current;
      const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
      
      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);
      
      source.onended = () => {
        setIsGeneratingTTS(false);
        // Once done speaking, start listening again if still active
        if (isActive && recognitionRef.current) {
            try {
                recognitionRef.current.start();
                setStatus('listening');
            } catch(e) {
                console.error(e);
            }
        }
      };
      
      sourceRef.current = source;
      source.start();
      
    } catch (err) {
      console.error("ElevenLabs TTS Error:", err);
      setIsGeneratingTTS(false);
      if (isActive && recognitionRef.current) {
        try { recognitionRef.current.start(); } catch(e){}
        setStatus('listening');
      }
    }
  };

  const startSession = () => {
    if (!recognitionRef.current) {
        setErrorMessage("Speech Recognition not supported in this browser.");
        setStatus('error');
        return;
    }
    
    setErrorMessage('');
    setIsActive(true);
    historyRef.current = []; // Reset history
    
    // First, have the AI introduce itself
    setStatus('speaking');
    const intro = "Hello, I'm your technical interviewer. What role are you interviewing for today?";
    historyRef.current.push({ role: 'model', content: intro });
    playElevenLabsAudio(intro, selectedVoice);
  };

  const endSession = () => {
     if (recognitionRef.current) recognitionRef.current.stop();
     if (sourceRef.current) {
         sourceRef.current.stop();
         sourceRef.current.disconnect();
     }
     
     setIsActive(false);
     setStatus('idle');
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <MotionDiv 
          layout
          className={`relative rounded-[2rem] overflow-hidden shadow-glass transition-all duration-500 bg-white/70 backdrop-blur-xl border border-white/60 ${
            isActive ? 'ring-4 ring-blue-100' : ''
          }`}
        >
          {/* Status Bar */}
          <div className="absolute top-0 left-0 w-full p-6 flex justify-between items-start z-10">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${isActive ? 'bg-red-500 animate-pulse' : 'bg-slate-400'}`} />
              <span className="text-xs font-bold uppercase tracking-widest text-slate-500">
                {status === 'listening' ? 'Listening...' : status === 'speaking' ? 'Agent Speaking' : 'Ready'}
              </span>
            </div>
            {isActive && (
              <div className="px-3 py-1 rounded-full bg-white/50 backdrop-blur-md text-xs font-mono text-primary border border-white/50 shadow-sm flex items-center gap-2">
                 Voice: ElevenLabs
                 {isGeneratingTTS && <Loader2 size={10} className="animate-spin" />}
              </div>
            )}
          </div>

          {/* Main Visualizer Area */}
          <div className="h-96 flex flex-col items-center justify-center relative bg-gradient-to-b from-white/0 to-blue-50/50">
             {status === 'error' && (
                 <div className="text-red-500 text-center px-6 bg-red-50 py-6 rounded-2xl border border-red-100 max-w-xs mx-auto shadow-sm">
                     <AlertCircle size={32} className="mx-auto mb-3 text-red-500" />
                     <p className="font-bold text-slate-900 mb-1">Connection Error</p>
                     <p className="text-xs text-slate-600 leading-relaxed">{errorMessage}</p>
                     <button onClick={() => setStatus('idle')} className="mt-4 px-4 py-2 bg-white text-red-600 rounded-lg text-xs font-bold shadow-sm hover:bg-red-50 transition-colors">
                        Try Again
                     </button>
                 </div>
             )}

             {status === 'idle' && (
                 <div className="text-center space-y-6 w-full px-10">
                     <div className="w-24 h-24 rounded-full bg-blue-50 flex items-center justify-center mx-auto text-primary border border-blue-100 shadow-sm relative">
                         <Mic size={36} />
                         <div className="absolute inset-0 rounded-full border border-blue-200 animate-ping opacity-20"></div>
                     </div>
                     <div>
                        <h3 className="text-xl font-bold text-slate-900">Start Interview</h3>
                        <p className="text-sm text-slate-500 max-w-xs mx-auto mt-1">
                            Connect with our AI interviewer (Powered by Groq + Web Speech).
                        </p>
                     </div>
                     
                     {/* Voice Selector */}
                     <div className="relative inline-block w-full max-w-[200px]">
                        <select 
                          value={selectedVoice}
                          onChange={(e) => setSelectedVoice(e.target.value)}
                          className="w-full appearance-none bg-white border border-slate-200 text-slate-700 text-xs font-bold py-2 px-4 pr-8 rounded-xl focus:outline-none focus:border-primary/50 shadow-sm cursor-pointer hover:bg-slate-50 transition-colors text-center"
                        >
                          {VOICES.map(v => (
                            <option key={v.id} value={v.id}>{v.label}</option>
                          ))}
                        </select>
                        <div className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-slate-400">
                          <ChevronDown size={14} />
                        </div>
                     </div>
                 </div>
             )}

             {(status === 'listening' || status === 'speaking') && (
                 <div className="relative w-full h-full flex items-center justify-center">
                    {/* Abstract Voice Visualizer */}
                    <div className="absolute inset-0 flex items-center justify-center">
                        {[1, 2, 3].map((i) => (
                             <MotionDiv
                               key={i}
                               animate={{ 
                                   scale: status === 'speaking' ? [1, 1.2, 1] : [1, 1.05, 1],
                                   opacity: [0.1, 0, 0.1]
                               }}
                               transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.2 }}
                               className="absolute border rounded-full w-32 h-32 border-indigo-500"
                             />
                        ))}
                        <div className="w-32 h-32 rounded-full flex items-center justify-center shadow-xl z-10 relative bg-gradient-to-br from-indigo-600 to-purple-600 shadow-indigo-500/30">
                             {isGeneratingTTS ? (
                                 <Loader2 className="text-white w-12 h-12 animate-spin" />
                             ) : (
                                 <Activity className={`text-white w-12 h-12 ${status === 'speaking' ? 'animate-pulse' : ''}`} />
                             )}
                             <MotionDiv 
                                animate={{ scale: 1.2 }}
                                className="absolute inset-0 bg-white/30 rounded-full -z-10"
                             />
                        </div>
                    </div>
                 </div>
             )}
          </div>

          {/* Controls */}
          <div className="p-6 bg-white/50 backdrop-blur-md border-t border-white/50 flex justify-center gap-6">
            {!isActive ? (
               <button 
                  onClick={startSession}
                  disabled={status === 'error'}
                  className="flex items-center gap-3 px-8 py-4 bg-primary text-white rounded-2xl font-bold hover:bg-blue-600 transition-colors disabled:opacity-50 shadow-lg shadow-blue-500/20"
               >
                   <Mic size={20} />
                   Start Session
               </button>
            ) : (
                <button 
                   onClick={endSession}
                   className="flex items-center gap-3 px-8 py-4 bg-red-50 text-red-500 border border-red-100 rounded-2xl font-bold hover:bg-red-100 transition-colors"
                >
                    <PhoneOff size={20} />
                    End Call
                </button>
            )}
          </div>
        </MotionDiv>
      </div>
    </div>
  );
};

export default LiveInterview;
