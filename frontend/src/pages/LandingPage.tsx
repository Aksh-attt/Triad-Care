import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../store/authStore';
import {
  Heart,
  Shield,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Clock,
  Check,
  Menu,
  X,
  Eye,
  ShieldAlert,
  Smile,
  Pill,
  Lock,
} from 'lucide-react';

export function LandingPage() {
  const { user, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'elderly' | 'caregiver' | 'family'>('elderly');
  const [activeStatusDemo, setActiveStatusDemo] = useState<'taken' | 'not_confirmed' | 'missed'>('not_confirmed');

  // Handle CTA navigation
  const handlePrimaryCta = () => {
    if (isAuthenticated && user) {
      navigate(`/${user.role}`);
    } else {
      navigate('/login');
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] text-[#18181B] selection:bg-[#405342] selection:text-white font-sans antialiased overflow-x-hidden">
      {/* --------------------------------------------------------------------- */}
      {/* 1. TOP NAVIGATION                                                     */}
      {/* --------------------------------------------------------------------- */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-[#FAF8F5]/90 border-b border-[#EAE6DF] transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            {/* Brand Logo */}
            <Link
              to="/"
              className="flex items-center gap-3 group focus:outline-none focus-visible:ring-2 focus-visible:ring-[#405342] rounded-lg p-1"
            >
              <div className="w-10 h-10 rounded-xl bg-[#18181B] text-[#FAF8F5] flex items-center justify-center shadow-sm group-hover:bg-[#405342] transition-colors">
                <Heart size={20} className="fill-[#FAF8F5]" />
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-bold tracking-tight text-[#18181B]">
                  Triad Care
                </span>
                <span className="text-[10px] tracking-wider uppercase text-[#71717A] -mt-1 font-semibold">
                  Connected Care
                </span>
              </div>
            </Link>

            {/* Desktop Navigation Links */}
            <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-[#52525B]">
              <a href="#problem" className="hover:text-[#18181B] transition-colors">
                The Care Gap
              </a>
              <a href="#pillars" className="hover:text-[#18181B] transition-colors">
                Three Pillars
              </a>
              <a href="#triad" className="hover:text-[#18181B] transition-colors">
                The Triad
              </a>
              <a href="#accountability" className="hover:text-[#18181B] transition-colors">
                Medication Safety
              </a>
              <a href="#visibility" className="hover:text-[#18181B] transition-colors">
                Family Visibility
              </a>
            </nav>

            {/* Header Right Actions */}
            <div className="hidden md:flex items-center gap-4">
              {loading ? (
                <div className="w-24 h-9 bg-[#EAE6DF]/60 motion-safe:animate-pulse rounded-full" />
              ) : isAuthenticated && user ? (
                <button
                  onClick={() => navigate(`/${user.role}`)}
                  className="inline-flex items-center gap-2 bg-[#18181B] text-[#FAF8F5] hover:bg-[#405342] text-xs font-semibold px-5 py-2.5 rounded-full transition-all shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#405342]"
                >
                  <span>Go to Dashboard</span>
                  <span className="text-[10px] bg-[#FAF8F5]/20 px-2 py-0.5 rounded-full uppercase">
                    {user.role}
                  </span>
                  <ArrowRight size={14} />
                </button>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="text-sm font-medium text-[#52525B] hover:text-[#18181B] px-3 py-2 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#405342] rounded-md"
                  >
                    Sign In
                  </Link>
                  <button
                    onClick={() => navigate('/login')}
                    className="inline-flex items-center gap-2 bg-[#18181B] text-[#FAF8F5] hover:bg-[#2A2B29] text-xs font-semibold px-5 py-2.5 rounded-full transition-all shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#405342]"
                  >
                    <span>Get Started</span>
                    <ArrowRight size={14} />
                  </button>
                </>
              )}
            </div>

            {/* Mobile Menu Toggle Button */}
            <div className="flex md:hidden">
              <button
                type="button"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="text-[#18181B] p-2 rounded-lg hover:bg-[#EAE6DF]/60 focus:outline-none focus:ring-2 focus:ring-[#405342]"
                aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
              >
                {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Dropdown Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden border-b border-[#EAE6DF] bg-[#FAF8F5] px-4 pt-3 pb-6 space-y-4 shadow-lg animate-in slide-in-from-top-2 max-h-[calc(100vh-5rem)] overflow-y-auto">
            <nav className="flex flex-col space-y-3 text-base font-medium text-[#18181B]">
              <a
                href="#problem"
                onClick={() => setMobileMenuOpen(false)}
                className="px-2 py-1.5 rounded-md hover:bg-[#EAE6DF]/50"
              >
                The Care Gap
              </a>
              <a
                href="#pillars"
                onClick={() => setMobileMenuOpen(false)}
                className="px-2 py-1.5 rounded-md hover:bg-[#EAE6DF]/50"
              >
                Three Pillars
              </a>
              <a
                href="#triad"
                onClick={() => setMobileMenuOpen(false)}
                className="px-2 py-1.5 rounded-md hover:bg-[#EAE6DF]/50"
              >
                The Triad
              </a>
              <a
                href="#accountability"
                onClick={() => setMobileMenuOpen(false)}
                className="px-2 py-1.5 rounded-md hover:bg-[#EAE6DF]/50"
              >
                Medication Safety
              </a>
              <a
                href="#visibility"
                onClick={() => setMobileMenuOpen(false)}
                className="px-2 py-1.5 rounded-md hover:bg-[#EAE6DF]/50"
              >
                Family Visibility
              </a>
            </nav>

            <div className="pt-4 border-t border-[#EAE6DF] flex flex-col gap-3">
              {isAuthenticated && user ? (
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    navigate(`/${user.role}`);
                  }}
                  className="w-full text-center bg-[#18181B] text-[#FAF8F5] text-sm font-semibold py-3 rounded-full"
                >
                  Go to {user.role} Dashboard
                </button>
              ) : (
                <>
                  <Link
                    to="/login"
                    onClick={() => setMobileMenuOpen(false)}
                    className="w-full text-center border border-[#EAE6DF] bg-white text-[#18181B] text-sm font-semibold py-2.5 rounded-full"
                  >
                    Sign In
                  </Link>
                  <button
                    onClick={() => {
                      setMobileMenuOpen(false);
                      navigate('/login');
                    }}
                    className="w-full text-center bg-[#18181B] text-[#FAF8F5] text-sm font-semibold py-3 rounded-full shadow-sm"
                  >
                    Get Started
                  </button>
                </>
              )}
            </div>
          </div>
        )}
      </header>

      <main id="main-content">
      {/* --------------------------------------------------------------------- */}
      {/* 2. CINEMATIC HERO SECTION                                             */}
      {/* --------------------------------------------------------------------- */}
      <section className="relative pt-16 pb-24 md:pt-28 md:pb-36 overflow-hidden">
        {/* Subtle Atmospheric Vignette */}
        <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-white via-transparent to-transparent opacity-80" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="max-w-4xl mx-auto text-center space-y-8">
            {/* Eyebrow Label */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#EAE6DF]/80 border border-[#DBD6CB] text-[#405342] text-[11px] font-bold tracking-[0.2em] uppercase">
              <span className="w-2 h-2 rounded-full bg-[#405342] motion-safe:animate-pulse" />
              <span>Care Coordination & Accountability Platform</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-[#18181B] leading-[1.08]">
              Care that connects.
              <br />
              <span className="italic font-normal text-[#405342]">
                Responsibility that follows.
              </span>
            </h1>

            {/* Supporting Prose */}
            <p className="max-w-2xl mx-auto text-base sm:text-lg lg:text-xl text-[#52525B] leading-relaxed font-normal">
              An AI-assisted elderly care ecosystem connecting elderly independence,
              caregiver follow-up accountability, and family peace of mind. Keeping loved
              ones safe without taking away their voice.
            </p>

            {/* Primary Action Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <button
                onClick={handlePrimaryCta}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 bg-[#18181B] hover:bg-[#2E2F2C] text-[#FAF8F5] text-sm sm:text-base font-semibold px-8 py-3.5 rounded-full transition-all shadow-md hover:shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#405342]"
              >
                <span>{isAuthenticated ? 'Open Dashboard' : 'Get Started'}</span>
                <ArrowRight size={16} />
              </button>

              <button
                onClick={() => navigate('/login')}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 border border-[#DBD6CB] bg-white hover:bg-[#F4F0E8] text-[#18181B] text-sm sm:text-base font-semibold px-7 py-3.5 rounded-full transition-all shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#405342]"
              >
                <Sparkles size={16} className="text-[#C29B38]" />
                <span>Experience Demo Personas</span>
              </button>
            </div>

            {/* Quick Metrics Badge */}
            <div className="pt-8 flex flex-wrap items-center justify-center gap-8 text-xs text-[#71717A]">
              <div className="flex items-center gap-2">
                <CheckCircle2 size={15} className="text-[#405342]" />
                <span>Zero Hardcoded Passcodes</span>
              </div>
              <div className="flex items-center gap-2">
                <Shield size={15} className="text-[#405342]" />
                <span>Server-Enforced Role Separation</span>
              </div>
              <div className="flex items-center gap-2">
                <Lock size={15} className="text-[#405342]" />
                <span>Argon2id + JWT Security Baseline</span>
              </div>
            </div>
          </div>

          {/* Interactive Live Ecosystem Simulator Preview Card */}
          <div className="mt-16 sm:mt-24 max-w-5xl mx-auto bg-white rounded-3xl border border-[#EAE6DF] shadow-xl overflow-hidden p-6 sm:p-10">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 border-b border-[#EAE6DF] gap-4">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#405342]">
                  Live Circle Overview
                </span>
                <h2 className="text-xl sm:text-2xl font-bold text-[#18181B]">
                  Sarah Jenkins's Care Circle
                </h2>
                <p className="text-xs text-[#71717A] mt-0.5">
                  Age 78 · Hypertension & Type II Diabetes · Monitored in real time
                </p>
              </div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#EDF2EE] text-[#405342] text-xs font-semibold">
                <span className="w-2 h-2 rounded-full bg-[#405342]" />
                <span>All 3 Members Active</span>
              </div>
            </div>

            {/* 3 Interconnected Pillars Card Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-8">
              {/* Pillar 1: Elderly (Meera / Patient) */}
              <div className="bg-[#FAF8F5] rounded-2xl p-5 border border-[#EAE6DF] flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl">👵</span>
                    <span className="text-[10px] font-bold bg-[#EAE6DF] text-[#405342] px-2 py-0.5 rounded-full uppercase">
                      Patient
                    </span>
                  </div>
                  <h3 className="font-bold text-[#18181B] text-base">Sarah Jenkins</h3>
                  <p className="text-xs text-[#71717A] mt-1">Direct confirmation & voice</p>

                  <div className="mt-4 p-3 bg-white rounded-xl border border-[#EAE6DF]/80 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-[#18181B]">Metformin 500mg</span>
                      <span className="text-[#C29B38] font-bold text-[10px] bg-amber-50 px-2 py-0.5 rounded">
                        Due 08:00 AM
                      </span>
                    </div>
                    <p className="text-[11px] text-[#71717A]">
                      High-contrast prompt awaiting one-touch approval
                    </p>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-[#EAE6DF] text-[11px] text-[#405342] font-medium flex items-center gap-1.5">
                  <Check size={14} />
                  <span>Maintains Dignity & Control</span>
                </div>
              </div>

              {/* Pillar 2: Caregiver (Riya) */}
              <div className="bg-[#FAF8F5] rounded-2xl p-5 border border-[#EAE6DF] flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl">👩‍⚕️</span>
                    <span className="text-[10px] font-bold bg-[#EAE6DF] text-[#405342] px-2 py-0.5 rounded-full uppercase">
                      Caregiver
                    </span>
                  </div>
                  <h3 className="font-bold text-[#18181B] text-base">Riya Patel, RN</h3>
                  <p className="text-xs text-[#71717A] mt-1">Accountable follow-up ownership</p>

                  <div className="mt-4 p-3 bg-white rounded-xl border border-[#EAE6DF]/80 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-[#18181B]">Unconfirmed Dose</span>
                      <span className="text-blue-700 font-bold text-[10px] bg-blue-50 px-2 py-0.5 rounded">
                        Action Claimed
                      </span>
                    </div>
                    <p className="text-[11px] text-[#71717A]">
                      Logged: "Calling Sarah to check before morning walk"
                    </p>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-[#EAE6DF] text-[11px] text-[#405342] font-medium flex items-center gap-1.5">
                  <Shield size={14} />
                  <span>Follow-up does not alter dose status</span>
                </div>
              </div>

              {/* Pillar 3: Family (Arjun) */}
              <div className="bg-[#FAF8F5] rounded-2xl p-5 border border-[#EAE6DF] flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl">👨‍💼</span>
                    <span className="text-[10px] font-bold bg-[#EAE6DF] text-[#405342] px-2 py-0.5 rounded-full uppercase">
                      Family
                    </span>
                  </div>
                  <h3 className="font-bold text-[#18181B] text-base">David Jenkins</h3>
                  <p className="text-xs text-[#71717A] mt-1">Real-time visibility & reassurance</p>

                  <div className="mt-4 p-3 bg-white rounded-xl border border-[#EAE6DF]/80 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-[#18181B]">Weekly AI Summary</span>
                      <span className="text-emerald-700 font-bold text-[10px] bg-emerald-50 px-2 py-0.5 rounded">
                        94% On-Time
                      </span>
                    </div>
                    <p className="text-[11px] text-[#71717A]">
                      No drug conflicts found; schedule changes approved
                    </p>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-[#EAE6DF] text-[11px] text-[#405342] font-medium flex items-center gap-1.5">
                  <Eye size={14} />
                  <span>Informed without intrusive calls</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* --------------------------------------------------------------------- */}
      {/* 3. THE PROBLEM: THE FRAGMENTED CARE GAP                               */}
      {/* --------------------------------------------------------------------- */}
      <section id="problem" className="py-20 sm:py-28 bg-white border-y border-[#EAE6DF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center space-y-4">
            <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-[#405342]">
              The Core Challenge
            </span>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-[#18181B]">
              Elderly care breaks down when responsibility is assumed instead of verified.
            </h2>
            <p className="text-base sm:text-lg text-[#52525B]">
              Without a synchronized system, each member of the circle operates in isolation,
              leading to missed doses, caregiver burnout, and constant family worry.
            </p>
          </div>

          <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Gap 1 */}
            <div className="bg-[#FAF8F5] rounded-2xl p-8 border border-[#EAE6DF] space-y-4">
              <div className="w-12 h-12 rounded-xl bg-amber-50 border border-amber-200 text-amber-700 flex items-center justify-center font-bold text-lg">
                01
              </div>
              <h3 className="text-xl font-bold text-[#18181B]">Disempowered Elderly</h3>
              <p className="text-sm text-[#52525B] leading-relaxed">
                Older adults are frequently spoken about instead of spoken with. When routines are
                imposed without direct confirmation, adherence declines and dignity is diminished.
              </p>
            </div>

            {/* Gap 2 */}
            <div className="bg-[#FAF8F5] rounded-2xl p-8 border border-[#EAE6DF] space-y-4">
              <div className="w-12 h-12 rounded-xl bg-red-50 border border-red-200 text-red-700 flex items-center justify-center font-bold text-lg">
                02
              </div>
              <h3 className="text-xl font-bold text-[#18181B]">Caregiver Uncertainty</h3>
              <p className="text-sm text-[#52525B] leading-relaxed">
                Caregivers cannot distinguish whether an elderly person forgot their medicine or simply
                forgot to log it. When follow-ups lack strict boundaries, critical oversights occur.
              </p>
            </div>

            {/* Gap 3 */}
            <div className="bg-[#FAF8F5] rounded-2xl p-8 border border-[#EAE6DF] space-y-4">
              <div className="w-12 h-12 rounded-xl bg-purple-50 border border-purple-200 text-purple-700 flex items-center justify-center font-bold text-lg">
                03
              </div>
              <h3 className="text-xl font-bold text-[#18181B]">Family Distance & Anxiety</h3>
              <p className="text-sm text-[#52525B] leading-relaxed">
                Family members living in other cities constantly worry, resorting to repeated interrogative
                phone calls that cause tension and friction instead of meaningful connection.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* --------------------------------------------------------------------- */}
      {/* 4. THE THREE PILLARS                                                  */}
      {/* --------------------------------------------------------------------- */}
      <section id="pillars" className="py-20 sm:py-28 bg-[#FAF8F5]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center space-y-4">
            <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-[#405342]">
              Architectural Foundation
            </span>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-[#18181B]">
              Engineered on three non-negotiable principles.
            </h2>
            <p className="text-base sm:text-lg text-[#52525B]">
              Triad Care pairs clinical safety invariants with compassionate human-centric design.
            </p>
          </div>

          <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Pillar 1: Intelligence */}
            <div className="bg-white rounded-2xl p-8 border border-[#EAE6DF] shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-[#EDF2EE] text-[#405342] flex items-center justify-center mb-6">
                  <Sparkles size={24} />
                </div>
                <h3 className="text-xl font-bold text-[#18181B]">Intelligence</h3>
                <p className="text-xs uppercase tracking-wider text-[#71717A] font-semibold mt-1">
                  AI-Powered Clinical Assist
                </p>
                <p className="mt-4 text-sm text-[#52525B] leading-relaxed">
                  Context-aware AI analyzes adherence trends, extracts complex multi-drug prescription
                  regimens via OCR scanning, and flags potential drug conflicts—all while leaving the
                  final clinical decision to humans.
                </p>
              </div>

              <div className="mt-8 pt-4 border-t border-[#EAE6DF] text-xs text-[#405342] font-semibold flex items-center gap-2">
                <span>OCR Scanning · Digest Summaries · Interaction Checks</span>
              </div>
            </div>

            {/* Pillar 2: Accountability */}
            <div className="bg-white rounded-2xl p-8 border border-[#EAE6DF] shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-[#EDF2EE] text-[#405342] flex items-center justify-center mb-6">
                  <Shield size={24} />
                </div>
                <h3 className="text-xl font-bold text-[#18181B]">Accountability</h3>
                <p className="text-xs uppercase tracking-wider text-[#71717A] font-semibold mt-1">
                  Healthcare Safety Invariants
                </p>
                <p className="mt-4 text-sm text-[#52525B] leading-relaxed">
                  Strict backend rules prevent false confirmations. When a caregiver claims a follow-up,
                  the dose remains unconfirmed until actually verified. Every change requires authenticated
                  consent from the elderly individual.
                </p>
              </div>

              <div className="mt-8 pt-4 border-t border-[#EAE6DF] text-xs text-[#405342] font-semibold flex items-center gap-2">
                <span>Decoupled Follow-ups · Tamper-Resistant · Audit Trails</span>
              </div>
            </div>

            {/* Pillar 3: Independence */}
            <div className="bg-white rounded-2xl p-8 border border-[#EAE6DF] shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-[#EDF2EE] text-[#405342] flex items-center justify-center mb-6">
                  <Smile size={24} />
                </div>
                <h3 className="text-xl font-bold text-[#18181B]">Independence</h3>
                <p className="text-xs uppercase tracking-wider text-[#71717A] font-semibold mt-1">
                  Empowering Dignified Agency
                </p>
                <p className="mt-4 text-sm text-[#52525B] leading-relaxed">
                  Tailored high-contrast interfaces designed specifically for aging vision and motor skills.
                  Elderly patients manage their daily routine directly, record reasons for skipping doses,
                  and maintain their voice.
                </p>
              </div>

              <div className="mt-8 pt-4 border-t border-[#EAE6DF] text-xs text-[#405342] font-semibold flex items-center gap-2">
                <span>One-Touch Confirmation · Reason Logging · Change Consent</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* --------------------------------------------------------------------- */}
      {/* 5. THE TRIAD IN ACTION (INTERACTIVE ROLE SWITCHER)                   */}
      {/* --------------------------------------------------------------------- */}
      <section id="triad" className="py-20 sm:py-28 bg-white border-y border-[#EAE6DF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center space-y-4">
            <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-[#405342]">
              Coordinated Workflow
            </span>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-[#18181B]">
              Three roles. One continuous circle of care.
            </h2>
            <p className="text-base sm:text-lg text-[#52525B]">
              Explore how each role interacts within the Triad to ensure safety and transparent support.
            </p>
          </div>

          {/* Role Switcher Pill Navigation */}
          <div className="mt-12 flex justify-center">
            <div
              role="tablist"
              aria-label="Care role perspectives"
              className="inline-flex p-1.5 rounded-full bg-[#FAF8F5] border border-[#EAE6DF] shadow-inner max-w-full overflow-x-auto"
            >
              <button
                type="button"
                role="tab"
                id="tab-elderly"
                aria-selected={activeTab === 'elderly'}
                aria-controls="tabpanel-elderly"
                onClick={() => setActiveTab('elderly')}
                className={`px-5 py-2.5 rounded-full text-xs sm:text-sm font-semibold transition-all whitespace-nowrap focus:outline-none focus-visible:ring-2 focus-visible:ring-[#405342] focus-visible:ring-offset-1 ${
                  activeTab === 'elderly'
                    ? 'bg-[#18181B] text-[#FAF8F5] shadow-sm'
                    : 'text-[#71717A] hover:text-[#18181B]'
                }`}
              >
                👵 Elderly Person (Meera)
              </button>
              <button
                type="button"
                role="tab"
                id="tab-caregiver"
                aria-selected={activeTab === 'caregiver'}
                aria-controls="tabpanel-caregiver"
                onClick={() => setActiveTab('caregiver')}
                className={`px-5 py-2.5 rounded-full text-xs sm:text-sm font-semibold transition-all whitespace-nowrap focus:outline-none focus-visible:ring-2 focus-visible:ring-[#405342] focus-visible:ring-offset-1 ${
                  activeTab === 'caregiver'
                    ? 'bg-[#18181B] text-[#FAF8F5] shadow-sm'
                    : 'text-[#71717A] hover:text-[#18181B]'
                }`}
              >
                👩‍⚕️ Dedicated Caregiver (Riya)
              </button>
              <button
                type="button"
                role="tab"
                id="tab-family"
                aria-selected={activeTab === 'family'}
                aria-controls="tabpanel-family"
                onClick={() => setActiveTab('family')}
                className={`px-5 py-2.5 rounded-full text-xs sm:text-sm font-semibold transition-all whitespace-nowrap focus:outline-none focus-visible:ring-2 focus-visible:ring-[#405342] focus-visible:ring-offset-1 ${
                  activeTab === 'family'
                    ? 'bg-[#18181B] text-[#FAF8F5] shadow-sm'
                    : 'text-[#71717A] hover:text-[#18181B]'
                }`}
              >
                👨‍💼 Connected Family (Arjun)
              </button>
            </div>
          </div>

          {/* Dynamic Tab Panel */}
          <div className="mt-10 max-w-4xl mx-auto bg-[#FAF8F5] rounded-3xl border border-[#EAE6DF] p-6 sm:p-12 shadow-sm transition-all">
            {activeTab === 'elderly' && (
              <div id="tabpanel-elderly" role="tabpanel" aria-labelledby="tab-elderly" className="space-y-6 animate-in fade-in duration-300">
                <div className="flex items-center justify-between border-b border-[#EAE6DF] pb-4">
                  <div>
                    <h3 className="text-2xl font-bold text-[#18181B]">
                      Elderly Persona — Meera Sharma (Age 72)
                    </h3>
                    <p className="text-sm text-[#71717A] mt-1">
                      Designed for effortless clarity, confidence, and dignified independence.
                    </p>
                  </div>
                  <span className="text-xs bg-purple-100 text-purple-900 font-bold px-3 py-1 rounded-full">
                    Active Patient
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
                  <div className="space-y-4">
                    <h4 className="font-semibold text-base text-[#18181B]">Key Responsibilities</h4>
                    <ul className="space-y-2.5 text-sm text-[#52525B]">
                      <li className="flex items-start gap-2">
                        <Check size={16} className="text-[#405342] mt-0.5 shrink-0" />
                        <span>Confirm scheduled morning and evening doses with a single touch.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Check size={16} className="text-[#405342] mt-0.5 shrink-0" />
                        <span>Record authentic reasons when skipping doses (e.g. feeling unwell, nausea).</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Check size={16} className="text-[#405342] mt-0.5 shrink-0" />
                        <span>Approve or reject medication adjustments suggested by doctors or family.</span>
                      </li>
                    </ul>
                  </div>

                  <div className="bg-white p-5 rounded-2xl border border-[#EAE6DF] space-y-3">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-[#71717A]">
                      High-Contrast Touch UI
                    </span>
                    <div className="p-3 bg-purple-50 rounded-xl border border-purple-200">
                      <p className="font-bold text-sm text-purple-950">Amlodipine 5mg</p>
                      <p className="text-xs text-purple-800">Due at 09:00 AM · Take with breakfast</p>
                      <div className="mt-3 flex gap-2">
                        <span className="bg-purple-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg">
                          ✓ Confirm Dose
                        </span>
                        <span className="bg-white text-gray-700 text-xs font-bold px-3 py-1.5 rounded-lg border border-gray-300">
                          Skip / Reason
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'caregiver' && (
              <div id="tabpanel-caregiver" role="tabpanel" aria-labelledby="tab-caregiver" className="space-y-6 animate-in fade-in duration-300">
                <div className="flex items-center justify-between border-b border-[#EAE6DF] pb-4">
                  <div>
                    <h3 className="text-2xl font-bold text-[#18181B]">
                      Caregiver Persona — Riya Patel, RN
                    </h3>
                    <p className="text-sm text-[#71717A] mt-1">
                      Accountable follow-up queue that turns concern into documented action.
                    </p>
                  </div>
                  <span className="text-xs bg-teal-100 text-teal-900 font-bold px-3 py-1 rounded-full">
                    Professional Caregiver
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
                  <div className="space-y-4">
                    <h4 className="font-semibold text-base text-[#18181B]">Key Responsibilities</h4>
                    <ul className="space-y-2.5 text-sm text-[#52525B]">
                      <li className="flex items-start gap-2">
                        <Check size={16} className="text-[#405342] mt-0.5 shrink-0" />
                        <span>Monitor unconfirmed doses and claim immediate follow-up ownership.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Check size={16} className="text-[#405342] mt-0.5 shrink-0" />
                        <span>Log transparent actions: calling patient, checking bedside, or escalating.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Check size={16} className="text-[#405342] mt-0.5 shrink-0" />
                        <span>Maintain decoupled safety: follow-up status does not tamper with medical dose history.</span>
                      </li>
                    </ul>
                  </div>

                  <div className="bg-white p-5 rounded-2xl border border-[#EAE6DF] space-y-3">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-[#71717A]">
                      Actionable Follow-Up Queue
                    </span>
                    <div className="p-3 bg-teal-50 rounded-xl border border-teal-200">
                      <p className="font-bold text-sm text-teal-950">Follow-up: Sarah Jenkins</p>
                      <p className="text-xs text-teal-800">Metformin 500mg unconfirmed for 35 mins</p>
                      <div className="mt-3 flex gap-2">
                        <span className="bg-teal-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg">
                          Claimed: Calling
                        </span>
                        <span className="bg-white text-gray-700 text-xs font-bold px-3 py-1.5 rounded-lg border border-gray-300">
                          Resolve Task
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'family' && (
              <div id="tabpanel-family" role="tabpanel" aria-labelledby="tab-family" className="space-y-6 animate-in fade-in duration-300">
                <div className="flex items-center justify-between border-b border-[#EAE6DF] pb-4">
                  <div>
                    <h3 className="text-2xl font-bold text-[#18181B]">
                      Family Persona — Arjun Sharma
                    </h3>
                    <p className="text-sm text-[#71717A] mt-1">
                      Continuous peace of mind and shared advocacy without nagging.
                    </p>
                  </div>
                  <span className="text-xs bg-blue-100 text-blue-900 font-bold px-3 py-1 rounded-full">
                    Family Circle
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
                  <div className="space-y-4">
                    <h4 className="font-semibold text-base text-[#18181B]">Key Responsibilities</h4>
                    <ul className="space-y-2.5 text-sm text-[#52525B]">
                      <li className="flex items-start gap-2">
                        <Check size={16} className="text-[#405342] mt-0.5 shrink-0" />
                        <span>View real-time adherence rates without repeatedly telephoning to interrogate.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Check size={16} className="text-[#405342] mt-0.5 shrink-0" />
                        <span>Propose regimen adjustments following doctor consultations for patient approval.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Check size={16} className="text-[#405342] mt-0.5 shrink-0" />
                        <span>Receive weekly AI digests summarizing trends, appointments, and care health.</span>
                      </li>
                    </ul>
                  </div>

                  <div className="bg-white p-5 rounded-2xl border border-[#EAE6DF] space-y-3">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-[#71717A]">
                      AI Health Digest Preview
                    </span>
                    <div className="p-3 bg-blue-50 rounded-xl border border-blue-200">
                      <p className="font-bold text-sm text-blue-950">Weekly Adherence: 94%</p>
                      <p className="text-xs text-blue-800">
                        "Meera took all doses on time except 1 skipped on Wednesday due to mild nausea."
                      </p>
                      <div className="mt-3 flex items-center gap-1.5 text-xs text-blue-900 font-semibold">
                        <CheckCircle2 size={14} className="text-blue-700" />
                        <span>Doctor appointment scheduled for Friday</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* --------------------------------------------------------------------- */}
      {/* 6. MEDICATION ACCOUNTABILITY: THE CLINICAL SAFETY INVARIANT           */}
      {/* --------------------------------------------------------------------- */}
      <section id="accountability" className="py-20 sm:py-28 bg-[#FAF8F5]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center space-y-4">
            <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-[#405342]">
              Clinical Rigor
            </span>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-[#18181B]">
              The critical difference between Taken, Missed, and Not Confirmed.
            </h2>
            <p className="text-base sm:text-lg text-[#52525B]">
              Healthcare safety requires absolute precision. In Triad Care, accepting a caregiver follow-up
              never falsely marks medication as taken.
            </p>
          </div>

          {/* Interactive State Machine Demo */}
          <div className="mt-16 max-w-4xl mx-auto bg-white rounded-3xl border border-[#EAE6DF] p-6 sm:p-10 shadow-sm">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pb-6 border-b border-[#EAE6DF]">
              <span className="text-sm font-bold text-[#18181B]">
                Explore Medication Dose States:
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setActiveStatusDemo('not_confirmed')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeStatusDemo === 'not_confirmed'
                      ? 'bg-amber-100 text-amber-900 border border-amber-300'
                      : 'bg-[#FAF8F5] text-[#71717A]'
                  }`}
                >
                  Pending / Not Confirmed
                </button>
                <button
                  type="button"
                  onClick={() => setActiveStatusDemo('taken')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeStatusDemo === 'taken'
                      ? 'bg-emerald-100 text-emerald-900 border border-emerald-300'
                      : 'bg-[#FAF8F5] text-[#71717A]'
                  }`}
                >
                  Confirmed Taken
                </button>
                <button
                  type="button"
                  onClick={() => setActiveStatusDemo('missed')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeStatusDemo === 'missed'
                      ? 'bg-red-100 text-red-900 border border-red-300'
                      : 'bg-[#FAF8F5] text-[#71717A]'
                  }`}
                >
                  Documented Missed
                </button>
              </div>
            </div>

            {/* State Explanations */}
            <div aria-live="polite" aria-atomic="true" className="pt-6 space-y-4">
              {activeStatusDemo === 'not_confirmed' && (
                <div className="p-5 bg-amber-50/60 rounded-2xl border border-amber-200/80 space-y-3">
                  <div className="flex items-center gap-2 text-amber-900 font-bold text-base">
                    <Clock size={18} />
                    <span>Status: "Not Confirmed" (Scheduled window expired)</span>
                  </div>
                  <p className="text-sm text-amber-950 leading-relaxed">
                    The scheduled dose time has passed, but the elderly patient has not yet confirmed taking it.
                    The dose is <strong>NOT automatically assumed missed</strong> or taken. Instead, it triggers a
                    prioritized follow-up for the designated caregiver.
                  </p>
                  <div className="text-xs text-amber-800 bg-white/80 p-3 rounded-xl border border-amber-200">
                    <strong>Invariant Safety Law:</strong> When caregiver Riya logs "Calling to check on Meera",
                    this records caregiver responsibility, but the medical status stays <em>not_confirmed</em> until
                    genuine patient confirmation occurs.
                  </div>
                </div>
              )}

              {activeStatusDemo === 'taken' && (
                <div className="p-5 bg-emerald-50/60 rounded-2xl border border-emerald-200/80 space-y-3">
                  <div className="flex items-center gap-2 text-emerald-900 font-bold text-base">
                    <CheckCircle2 size={18} />
                    <span>Status: "Taken" (Explicitly Confirmed)</span>
                  </div>
                  <p className="text-sm text-emerald-950 leading-relaxed">
                    Explicitly verified by the patient via the high-contrast dashboard with confirmation method,
                    timestamp, and authenticated ID. The circle receives an immediate real-time update.
                  </p>
                  <div className="text-xs text-emerald-800 bg-white/80 p-3 rounded-xl border border-emerald-200">
                    <strong>Immutable Audit Trail:</strong> The dose confirmation records the authenticated user ID
                    and exact UTC timestamp, preventing retrospective modification.
                  </div>
                </div>
              )}

              {activeStatusDemo === 'missed' && (
                <div className="p-5 bg-red-50/60 rounded-2xl border border-red-200/80 space-y-3">
                  <div className="flex items-center gap-2 text-red-900 font-bold text-base">
                    <AlertCircle size={18} />
                    <span>Status: "Missed" (Clinical Reason Logged)</span>
                  </div>
                  <p className="text-sm text-red-950 leading-relaxed">
                    Confirmed by the patient or caregiver that the dose was skipped, accompanied by a structured
                    medical reason (e.g. "Forgot", "Feeling unwell", "Medication unavailable", "Doctor advised hold").
                  </p>
                  <div className="text-xs text-red-800 bg-white/80 p-3 rounded-xl border border-red-200">
                    <strong>Clinical Transparency:</strong> Documenting the authentic reason prevents false dose
                    doubling and gives visiting physicians accurate adherence history.
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* --------------------------------------------------------------------- */}
      {/* 7. FAMILY VISIBILITY & AI INTELLIGENCE                                */}
      {/* --------------------------------------------------------------------- */}
      <section id="visibility" className="py-20 sm:py-28 bg-white border-y border-[#EAE6DF]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-[#405342]">
                Intelligent Connection
              </span>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-[#18181B] leading-tight">
                Family visibility without intrusive micromanagement.
              </h2>
              <p className="text-base sm:text-lg text-[#52525B] leading-relaxed">
                Loved ones should be able to check in with love, not interrogation. Triad Care
                provides asynchronous visibility and weekly AI syntheses so you always know
                your family member is safe.
              </p>

              <div className="space-y-4 pt-2">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#EDF2EE] text-[#405342] flex items-center justify-center shrink-0 mt-1">
                    <Sparkles size={18} />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-[#18181B]">Weekly AI Health Digest</h4>
                    <p className="text-xs text-[#52525B] mt-0.5">
                      Synthesizes weekly adherence metrics, symptom patterns, and upcoming appointments.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#EDF2EE] text-[#405342] flex items-center justify-center shrink-0 mt-1">
                    <Pill size={18} />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-[#18181B]">OCR Prescription Scanner</h4>
                    <p className="text-xs text-[#52525B] mt-0.5">
                      Extracts medication names, dosages, and frequencies from prescription photos with safety checks.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#EDF2EE] text-[#405342] flex items-center justify-center shrink-0 mt-1">
                    <ShieldAlert size={18} />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-[#18181B]">Role-Scoped Privacy</h4>
                    <p className="text-xs text-[#52525B] mt-0.5">
                      Private caregiver notes remain confidential, while critical adherence alerts reach the family.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Visual AI Card Showcase */}
            <div className="bg-[#FAF8F5] p-6 sm:p-8 rounded-3xl border border-[#EAE6DF] space-y-6">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#405342] uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles size={14} />
                  <span>Synthesized AI Report</span>
                </span>
                <span className="text-[11px] text-[#71717A]">Updated 2 hours ago</span>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-[#EAE6DF] space-y-3">
                <p className="text-xs font-semibold text-[#18181B]">
                  "Meera maintained 94% on-time adherence over the past 7 days."
                </p>
                <div className="space-y-1.5 text-xs text-[#52525B]">
                  <p>• <strong>Morning Regimen:</strong> Metformin & Amlodipine confirmed daily before 09:30 AM.</p>
                  <p>• <strong>Logged Observations:</strong> 1 dose delayed due to clinic checkup.</p>
                  <p>• <strong>Upcoming Care:</strong> Cardiologist appointment scheduled for Thursday.</p>
                </div>
              </div>

              <div className="bg-white p-4 rounded-2xl border border-[#EAE6DF] flex items-center justify-between text-xs">
                <span className="text-[#52525B]">Adherence Reliability Score</span>
                <span className="font-bold text-[#405342] bg-[#EDF2EE] px-2.5 py-1 rounded-full">
                  Tier 1 — High Stability
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* --------------------------------------------------------------------- */}
      {/* 8. CLOSING CTA BANNER                                                 */}
      {/* --------------------------------------------------------------------- */}
      <section className="py-20 sm:py-28 bg-[#18181B] text-[#FAF8F5] relative overflow-hidden">
        {/* Subtle radial glow */}
        <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-white/5 via-transparent to-transparent" />

        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-8 relative z-10">
          <span className="text-[11px] font-bold uppercase tracking-[0.25em] text-[#C29B38]">
            Begin Connected Care
          </span>

          <h2 className="text-3xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-white leading-tight">
            Better care starts with everyone connected.
          </h2>

          <p className="max-w-2xl mx-auto text-sm sm:text-base lg:text-lg text-[#A1A1AA] leading-relaxed">
            Experience the Triad Care coordination model. Test live demo accounts for Meera Sharma (Elderly),
            Riya Patel (Caregiver), and Arjun Sharma (Family).
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <button
              onClick={() => navigate('/login')}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-white text-[#18181B] hover:bg-[#F4F0E8] text-sm sm:text-base font-semibold px-8 py-3.5 rounded-full transition-all shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
            >
              <span>{isAuthenticated ? 'Go to Your Dashboard' : 'Get Started'}</span>
              <ArrowRight size={16} />
            </button>

            <Link
              to="/login"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 border border-[#3F3F46] bg-transparent hover:bg-white/10 text-white text-sm sm:text-base font-semibold px-7 py-3.5 rounded-full transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
            >
              <span>Sign In</span>
            </Link>
          </div>
        </div>
      </section>

      </main>

      {/* --------------------------------------------------------------------- */}
      {/* 9. FOOTER                                                             */}
      {/* --------------------------------------------------------------------- */}
      <footer className="bg-[#FAF8F5] border-t border-[#EAE6DF] py-12 pb-[calc(3rem+env(safe-area-inset-bottom))] text-xs text-[#71717A]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-7 h-7 rounded-lg bg-[#18181B] text-white flex items-center justify-center">
                <Heart size={14} className="fill-white" />
              </div>
              <span className="font-bold text-[#18181B] text-sm">Triad Care</span>
              <span className="text-[#A1A1AA]">·</span>
              <span className="italic">"Care that connects. Responsibility that follows."</span>
            </div>

            <div className="flex flex-wrap items-center gap-6 font-medium">
              <a href="#pillars" className="hover:text-[#18181B] transition-colors">
                Three Pillars
              </a>
              <a href="#triad" className="hover:text-[#18181B] transition-colors">
                The Triad
              </a>
              <a href="#accountability" className="hover:text-[#18181B] transition-colors">
                Medication Safety
              </a>
              <Link to="/login" className="hover:text-[#18181B] transition-colors">
                Sign In
              </Link>
            </div>
          </div>

          <div className="mt-8 pt-8 border-t border-[#EAE6DF] flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-[#A1A1AA]">
            <p>© {new Date().getFullYear()} Triad Care Platform. All rights reserved.</p>
            <p>
              Triad Care is an assistive care coordination platform and does not replace emergency clinical medical care.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;
