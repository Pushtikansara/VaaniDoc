import React from "react";
import { useApp } from "../context/AppContext";
import { SUPPORTED_LANGUAGES } from "../services/languages";
import { useNavigate, Navigate } from "react-router-dom";
import { Copy, Play, Pencil, RotateCcw, ArrowRight } from "lucide-react";

export default function Transcript() {
  const { transcript, setTranscript, language, fetchTranslation, audioUrl } = useApp();
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = React.useState(false);
  const [localTranscript, setLocalTranscript] = React.useState(transcript);
  const audioRef = React.useRef(null);
  const [isPlaying, setIsPlaying] = React.useState(false);

  React.useEffect(() => {
    setLocalTranscript(transcript);
  }, [transcript]);

  const handlePlayToggle = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleAudioEnded = () => setIsPlaying(false);

  if (!transcript) {
    return <Navigate to="/intake" />;
  }

  const langLabel = SUPPORTED_LANGUAGES.find((l) => l.code === language)?.label || language;

  const handleConfirm = () => {
    fetchTranslation();
  };

  const handleReRecord = () => {
    navigate("/intake");
  };

  return (
    <div className="w-full max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="heading-page">Transcript</h1>
      </div>

      <div className="card w-full mb-8 lg:px-12 py-10 pt-8 rounded-xl shadow-sm border border-[var(--color-border)] relative overflow-hidden animate-slide-up">
        
        {/* Decorative Top Line */}
        <div className="absolute top-0 left-0 w-full h-1 bg-[var(--color-navy)]"></div>

        {/* Horizontal Stepper */}
        <div className="stepper-container">
          <div className="stepper-line"></div>
          <div className="stepper-progress" style={{ width: '20%' }}></div>
          <div className="step-item completed"><div className="step-circle">01</div><span className="step-label">Voice Input</span></div>
          <div className="step-item active"><div className="step-circle">02</div><span className="step-label">Transcript</span></div>
          <div className="step-item"><div className="step-circle">03</div><span className="step-label">Translation</span></div>
          <div className="step-item"><div className="step-circle">04</div><span className="step-label">Summary</span></div>
          <div className="step-item"><div className="step-circle">05</div><span className="step-label">Review</span></div>
          <div className="step-item"><div className="step-circle">06</div><span className="step-label">Report</span></div>
        </div>

        <div className="mt-8">
          
          <div className="flex justify-between items-center mb-4">
             <h3 className="text-[13px] font-bold text-[var(--color-navy)] uppercase tracking-wider">Patient Statement (Original)</h3>
             <span className="text-xs font-bold text-[var(--color-text-muted)] bg-[var(--color-bg-app)] px-3 py-1 rounded-md">{langLabel}</span>
          </div>

          {/* Transcript Box */}
          <div className="border border-[var(--color-border)] rounded-xl p-8 mb-6 bg-[var(--color-bg-app)] shadow-inner">
             {isEditing ? (
                <textarea 
                   className="w-full h-40 p-4 text-xl md:text-2xl text-[var(--color-navy)] leading-relaxed font-semibold bg-white border-2 border-[var(--color-navy)] rounded-lg outline-none resize-y"
                   value={localTranscript}
                   onChange={(e) => setLocalTranscript(e.target.value)}
                   autoFocus
                />
             ) : (
                <p className="text-xl md:text-2xl text-[var(--color-navy)] leading-relaxed font-semibold whitespace-pre-wrap">
                  {transcript}
                </p>
             )}
          </div>

          {/* Minimal Audio Player */}
          <div className="flex items-center justify-between pb-6 mb-8 mt-2" style={{ borderBottom: '1px solid var(--color-border)' }}>
             <div className="flex items-center flex-1" style={{ gap: '1rem' }}>
                {audioUrl && <audio ref={audioRef} src={audioUrl} onEnded={handleAudioEnded} style={{ display: 'none' }} preload="auto" />}
                
                <button 
                  onClick={handlePlayToggle} 
                  className="btn btn-primary"
                  style={{ borderRadius: 'var(--radius-pill)', width: '48px', height: '48px', padding: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                  title="Play Original Audio"
                >
                   {isPlaying ? (
                     <div style={{ width: '14px', height: '14px', backgroundColor: 'var(--color-white)', borderRadius: '3px' }} />
                   ) : (
                     <Play size={20} style={{ color: 'var(--color-white)', fill: 'currentColor', marginLeft: '4px' }} />
                   )}
                </button>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, maxWidth: '240px' }}>
                   <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-navy)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                     {isPlaying ? "Playing Original Audio" : "Play Original Audio"}
                   </span>
                   <div style={{ height: '6px', width: '100%', backgroundColor: 'var(--color-border)', borderRadius: 'var(--radius-pill)', overflow: 'hidden', position: 'relative' }}>
                      {isPlaying ? (
                         <div style={{ position: 'absolute', top: 0, left: 0, height: '6px', backgroundColor: 'var(--color-navy)', width: '100%', transition: 'all 1s' }}></div>
                      ) : (
                         <div style={{ position: 'absolute', top: 0, left: 0, height: '6px', backgroundColor: 'var(--color-text-light)', opacity: 0.5, width: '100%', transition: 'all 0.3s' }}></div>
                      )}
                   </div>
                </div>
             </div>
             
             <button 
                onClick={() => navigator.clipboard.writeText(transcript)} 
                className="btn btn-secondary"
                style={{ borderRadius: 'var(--radius-pill)', padding: '0.5rem 1rem', fontSize: '0.85rem' }}
             >
                <Copy size={16} style={{ color: 'var(--color-navy)', marginRight: '6px' }} /> Copy Text
             </button>
          </div>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
             <div className="flex gap-4 w-full sm:w-auto">
               {isEditing ? (
                 <button onClick={() => { setTranscript(localTranscript); setIsEditing(false); }} className="btn btn-primary text-xs flex-1 sm:flex-none justify-center">
                    Save Changes
                 </button>
               ) : (
                 <button onClick={() => setIsEditing(true)} className="btn btn-secondary text-xs flex-1 sm:flex-none justify-center">
                   <Pencil size={14} className="text-[var(--color-text-muted)]" /> Edit
                 </button>
               )}
               <button onClick={handleReRecord} className="btn btn-secondary text-xs flex-1 sm:flex-none justify-center">
                 <RotateCcw size={14} className="text-[var(--color-text-muted)]" /> Re-record
               </button>
             </div>
             <button onClick={handleConfirm} className="btn btn-primary text-sm px-8 shadow-sm w-full sm:w-auto justify-center">
               Confirm & Continue <ArrowRight size={16} className="ml-1" />
             </button>
          </div>

        </div>
      </div>
    </div>
  );
}
