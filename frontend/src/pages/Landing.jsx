import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Stethoscope, Globe, Mic, ShieldCheck, ArrowRight, Menu, X } from "lucide-react";

export default function Landing() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="w-full min-h-screen bg-[var(--color-bg-app)] animate-fade-in relative flex flex-col items-center">
      
      {/* Background Decor */}
      <div className="absolute top-0 right-0 w-full max-w-[800px] h-[800px] bg-[var(--color-cream)] rounded-full translate-x-1/3 -translate-y-1/4 opacity-40 mix-blend-multiply pointer-events-none md:block hidden"></div>
      <div className="absolute bottom-0 left-0 w-full max-w-[600px] h-[600px] bg-[var(--color-sage)] rounded-full -translate-x-1/3 translate-y-1/3 opacity-20 mix-blend-multiply pointer-events-none md:block hidden"></div>

      {/* Navbar */}
      <nav className="flex justify-between items-center py-5 px-6 max-w-[1200px] mx-auto w-full relative z-10 sticky top-0 bg-[var(--color-bg-app)]/90 backdrop-blur-md">
        <Link to="/" className="flex items-center gap-2 text-2xl font-bold text-[var(--color-navy)] no-underline" style={{textDecoration: 'none'}}>
          <Stethoscope size={28} className="text-[var(--color-brown)]" /> VaaniDoc
        </Link>
        <div className="hidden md:flex items-center gap-8 text-[15px] font-semibold text-[var(--color-navy)]">
          <Link to="/#features" className="hover:text-[var(--color-brown)] transition-colors no-underline" style={{textDecoration: 'none'}}>Features</Link>
          <Link to="/about" className="hover:text-[var(--color-brown)] transition-colors no-underline" style={{textDecoration: 'none'}}>How it Works</Link>
          <Link to="/about" className="hover:text-[var(--color-brown)] transition-colors no-underline" style={{textDecoration: 'none'}}>About Us</Link>
        </div>
        <div className="hidden md:block">
          <Link to="/intake" className="btn btn-primary px-5 py-2.5 shadow-sm text-[15px]" style={{textDecoration: 'none'}}>
            Start Health Intake
          </Link>
        </div>
        <div className="md:hidden flex items-center">
           <button onClick={() => setIsMobileMenuOpen(true)} className="p-2 border-none bg-transparent cursor-pointer">
              <Menu size={24} className="text-[var(--color-navy)]" />
           </button>
        </div>
      </nav>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 bg-white z-50 flex flex-col p-6 animate-fade-in md:hidden" style={{minHeight: '100vh', position: 'fixed', top: 0, left: 0, width: '100vw', background: 'white', zIndex: 999}}>
          <div className="flex justify-between items-center mb-8 border-b border-[var(--color-border)] pb-4 h-[72px]">
            <Link to="/" className="flex items-center gap-2 text-2xl font-bold text-[var(--color-navy)] no-underline" style={{textDecoration: 'none'}} onClick={() => setIsMobileMenuOpen(false)}>
              <Stethoscope size={28} className="text-[var(--color-brown)]" /> VaaniDoc
            </Link>
            <button onClick={() => setIsMobileMenuOpen(false)} className="p-2 border-none bg-transparent cursor-pointer">
              <X size={24} className="text-[var(--color-navy)]" />
            </button>
          </div>
          <div className="flex flex-col gap-6 text-[18px] font-semibold text-[var(--color-navy)]">
            <Link to="/#features" onClick={() => setIsMobileMenuOpen(false)} style={{textDecoration: 'none'}} className="no-underline text-[var(--color-navy)]">Features</Link>
            <Link to="/about" onClick={() => setIsMobileMenuOpen(false)} style={{textDecoration: 'none'}} className="no-underline text-[var(--color-navy)]">How it Works</Link>
            <Link to="/about" onClick={() => setIsMobileMenuOpen(false)} style={{textDecoration: 'none'}} className="no-underline text-[var(--color-navy)]">About Us</Link>
            <Link to="/intake" onClick={() => setIsMobileMenuOpen(false)} className="btn btn-primary btn-large justify-center mt-4 w-full" style={{textDecoration: 'none'}}>
              Start Health Intake
            </Link>
          </div>
        </div>
      )}

      {/* Hero Content */}
      <main className="flex-1 w-full mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 items-center relative z-10 py-8 lg:py-16" style={{maxWidth: '1200px', gap: '40px'}}>
        
        {/* Left Side */}
        <div className="animate-slide-up flex flex-col justify-center">
          <div className="eyebrow-badge">
            AI-Powered Clinical Documentation
          </div>

          <h1 className="hero-title font-bold text-[var(--color-navy)] mb-5 font-heading tracking-tight">
            Healthcare Without <br className="hidden lg:block" />
            <span style={{ color: 'var(--color-brown)' }}>Language Barriers</span>
          </h1>
          
          <p className="hero-desc text-[var(--color-navy)] mb-8 font-medium">
            Speak naturally in your language. VaaniDoc transforms your conversation into structured clinical documentation for doctors.
          </p>

          <div className="feature-group" style={{maxWidth: '600px'}}>
             
             {/* Card 1 */}
             <div className="feature-box">
               <div className="text-[var(--color-navy)] mb-2">
                 <Globe size={26} />
               </div>
               <p className="feature-t">22 Indian Languages</p>
               <p className="feature-d">Powered by IndicConformer & IndicTrans2</p>
             </div>

             {/* Card 2 */}
             <div className="feature-box">
               <div className="text-[var(--color-navy)] mb-2">
                 <Mic size={26} />
               </div>
               <p className="feature-t">Voice-first Intake</p>
               <p className="feature-d">Natural conversation over typing</p>
             </div>

             {/* Card 3 */}
             <div className="feature-box">
               <div className="text-[var(--color-navy)] mb-2">
                 <ShieldCheck size={26} />
               </div>
               <p className="feature-t">Privacy-first Session</p>
               <p className="feature-d">Secure clinical data extraction</p>
             </div>

          </div>

          <div className="cta-group">
            <Link to="/intake" className="btn btn-primary btn-large justify-center group flex items-center shrink-0 border-none" style={{textDecoration: 'none', width: 'auto', minWidth: '200px'}}>
              Start Health Intake <ArrowRight size={18} className="ml-1 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link to="/about" className="btn btn-secondary btn-large justify-center flex items-center shrink-0" style={{textDecoration: 'none', width: 'auto', minWidth: '160px'}}>
              Learn More
            </Link>
          </div>
        </div>

        {/* Right Side Visual Illustration */}
        <div className="relative w-full h-[400px] lg:h-full min-h-[400px] flex items-center justify-center lg:justify-end animate-slide-up stagger-1 mt-8 lg:mt-0">
          <div className="absolute w-[350px] h-[350px] lg:w-[450px] lg:h-[450px] bg-[var(--color-sage)] rounded-full opacity-20 -z-10 animate-float"></div>
          <img 
            src="/hero.png" 
            alt="AI Doctor Interface" 
            className="relative z-10 w-full max-w-[500px] lg:max-w-[550px] object-contain drop-shadow-xl animate-float"
            style={{ animationDuration: '6s', animationDelay: '0.5s' }}
          />
        </div>
      </main>
    </div>
  );
}
