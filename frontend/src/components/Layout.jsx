import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { 
  Stethoscope, Menu, Bell, UserCircle, X, Mic, 
  FileText, Languages, Activity, LayoutDashboard, 
  ClipboardList, Settings, Info 
} from "lucide-react";

export default function Layout({ children }) {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // The landing page handles its own layout natively
  if (location.pathname === "/") {
    return <div className="app-wrapper animate-fade-in">{children}</div>;
  }

  const navLinks = [
    { path: "/intake", label: "New Consultation", icon: <Mic size={20} /> },
    { path: "/transcript", label: "Transcript", icon: <FileText size={20} /> },
    { path: "/translation", label: "Translation", icon: <Languages size={20} /> },
    { path: "/summary", label: "Clinical Summary", icon: <Activity size={20} /> },
    { path: "/dashboard", label: "Doctor Dashboard", icon: <LayoutDashboard size={20} /> },
    { path: "/report", label: "Doctor Report", icon: <ClipboardList size={20} /> },
    { path: "/settings", label: "Settings", icon: <Settings size={20} /> },
    { path: "/about", label: "How It Works", icon: <Info size={20} /> },
  ];

  const closeMenu = () => setIsMobileMenuOpen(false);

  return (
    <div className="app-wrapper relative">
      {/* Top Navbar */}
      <header className="top-navbar">
        <div className="flex items-center gap-4">
          <button 
            className="p-2 border-none bg-transparent cursor-pointer hover:bg-[var(--color-bg-app)] rounded-md transition-colors lg:hidden"
            onClick={() => setIsMobileMenuOpen(true)}
            aria-label="Open Menu"
          >
            <Menu size={24} className="text-[var(--color-navy)]" />
          </button>
          
          <Link to="/" className="flex items-center gap-2 text-xl font-bold no-underline" style={{ textDecoration: 'none', color: 'var(--color-navy)' }}>
            <Stethoscope size={28} style={{ color: 'var(--color-brown)' }} />
            <span className="hidden sm:block">VaaniDoc</span>
          </Link>
        </div>

        <div className="flex items-center gap-6">
          <button className="relative p-2 border-none bg-transparent cursor-pointer text-[var(--color-navy)] hover:opacity-80 transition-opacity">
            <Bell size={22} />
            <span className="absolute top-1.5 right-2 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
          </button>
          <div className="flex items-center gap-3 cursor-pointer">
            <UserCircle size={32} className="text-[var(--color-navy)]" />
            <div className="hidden sm:block text-left">
               <p className="text-sm font-semibold text-[var(--color-navy)] leading-tight">Dr. Sharma</p>
               <p className="text-[10px] text-[var(--color-text-muted)] font-bold uppercase tracking-widest leading-tight mt-0.5">General Physician</p>
            </div>
          </div>
        </div>
      </header>

      <div className="app-body">
        {/* Desktop Sidebar */}
        <aside className="sidebar-container hidden lg:flex flex-col">
          <div className="p-6 flex-1 overflow-y-auto">
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-light)] px-3 mb-4">Consultation Flow</p>
            <nav className="flex flex-col gap-2 mb-8">
              {navLinks.slice(0, 6).map((link) => {
                const isActive = location.pathname === link.path;
                return (
                  <Link
                    key={link.path}
                    to={link.path}
                    className={`nav-link ${isActive ? "nav-link-active" : ""}`}
                  >
                    <span className="nav-icon">{link.icon}</span>
                    {link.label}
                  </Link>
                )
              })}
            </nav>

            <p className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-light)] px-3 mb-4">System Settings</p>
            <nav className="flex flex-col gap-2">
              {navLinks.slice(6).map((link) => {
                const isActive = location.pathname === link.path;
                return (
                  <Link
                    key={link.path}
                    to={link.path}
                    className={`nav-link ${isActive ? "nav-link-active" : ""}`}
                  >
                    <span className="nav-icon">{link.icon}</span>
                    {link.label}
                  </Link>
                )
              })}
            </nav>
          </div>
          
          <div className="p-6 border-t border-[var(--color-border)] bg-[var(--color-white)]">
             <div className="flex items-center gap-3 px-2">
                <div className="w-2.5 h-2.5 rounded-full bg-[#059669] animate-pulse"></div>
                <p className="text-xs font-bold text-[var(--color-text-muted)] tracking-wide">SYSTEM OPERATIONAL</p>
             </div>
          </div>
        </aside>

        {/* Mobile Drawer Overlay */}
        {isMobileMenuOpen && (
          <div 
            className="mobile-drawer-overlay lg:hidden"
            onClick={closeMenu}
          />
        )}

        {/* Mobile Drawer */}
        <div className={`mobile-drawer lg:hidden ${isMobileMenuOpen ? "open" : ""}`}>
          <div className="mobile-drawer-header">
            <Link to="/" className="flex items-center gap-2 text-xl font-bold no-underline" onClick={closeMenu} style={{ textDecoration: 'none', color: 'var(--color-navy)' }}>
              <Stethoscope size={24} style={{ color: 'var(--color-brown)' }} /> VaaniDoc
            </Link>
            <button onClick={closeMenu} className="drawer-close-btn" aria-label="Close menu">
              <X size={24} />
            </button>
          </div>
          
          <div className="p-4 flex-1 overflow-y-auto">
            <p className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-light)] px-3 mb-3 mt-2">Navigation</p>
            <nav className="flex flex-col gap-2">
              {navLinks.map((link) => {
                const isActive = location.pathname === link.path;
                return (
                  <Link
                    key={link.path}
                    to={link.path}
                    onClick={closeMenu}
                    className={`nav-link ${isActive ? "nav-link-active" : ""}`}
                    style={{ padding: '14px 16px' }}
                  >
                    <span className="nav-icon">{link.icon}</span>
                    {link.label}
                  </Link>
                )
              })}
            </nav>
          </div>
        </div>

        {/* Main Page Content */}
        <main className="main-content">
          <div className="w-full h-full animate-fade-in">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
