import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../store/authStore';
import { Heart, Shield, Users, Sparkles, ArrowRight, Lock } from 'lucide-react';
import { Button } from '../components/ui/Button';

export function LoginPage() {
  const { user, isAuthenticated, loading, login, demoLogin, error } = useAuth();
  const [passcode, setPasscode] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  const navigate = useNavigate();

  // Redirect authenticated users to their own role dashboard
  useEffect(() => {
    if (!loading && isAuthenticated && user) {
      navigate(`/${user.role}`, { replace: true });
    }
  }, [isAuthenticated, user, loading, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-teal-600"></div>
      </div>
    );
  }

  const handleManualLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!passcode.trim()) return;
    setLocalError(null);
    try {
      await login(passcode);
      navigate('/elderly');
    } catch (err: unknown) {
      setLocalError(err instanceof Error ? err.message : 'Invalid credentials');
    }
  };

  const handleQuickDemo = async (role: string) => {
    setLocalError(null);
    try {
      await demoLogin(role);
      navigate(`/${role}`);
    } catch (err: unknown) {
      setLocalError(err instanceof Error ? err.message : 'Demo login failed');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-2xl text-center">
        {/* Return to Landing Page */}
        <div className="mb-4 flex justify-center">
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-gray-900 transition-colors py-1 px-3 rounded-full border border-gray-200 bg-white/80 shadow-sm"
          >
            ← Back to Home
          </Link>
        </div>

        {/* Brand */}
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-teal-600 text-white shadow-lg mb-4">
          <Heart size={32} className="fill-white" />
        </div>
        <h1 className="text-3xl font-black text-gray-900 tracking-tight sm:text-4xl">
          Triad Care
        </h1>
        <p className="mt-2 text-base text-gray-600 font-medium">
          An AI-powered elderly care coordination and accountability platform connecting elderly individuals, caregivers, and family members.
        </p>
        <p className="mt-1 text-xs text-teal-700 italic">
          "Care that connects. Responsibility that follows."
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-3xl space-y-8">
        {/* Quick Demo One-Click Personas */}
        <div className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <Sparkles size={18} className="text-amber-500" />
              <span>Select Demo Persona (Instant Access)</span>
            </h2>
            <span className="text-xs bg-teal-50 text-teal-800 font-bold px-2.5 py-1 rounded-full border border-teal-200">
              Judges & Reviewers
            </span>
          </div>
          <p className="text-xs text-gray-500 mb-6">
            Switch effortlessly between all three roles to test the full accountability workflow.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Elderly Persona */}
            <div className="border-2 border-purple-100 hover:border-purple-400 bg-purple-50/30 rounded-xl p-5 flex flex-col justify-between transition-all hover:shadow-md">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-3xl">👵</span>
                  <span className="text-[10px] font-bold bg-purple-100 text-purple-800 px-2 py-0.5 rounded-full uppercase">
                    Elderly Role
                  </span>
                </div>
                <h3 className="font-bold text-gray-900 text-base">Meera Sharma</h3>
                <p className="text-xs text-gray-500 mt-1">
                  Age 72 · Diabetes & Hypertension
                </p>
                <div className="mt-3 text-[11px] text-gray-600 space-y-1">
                  <p>• High-contrast daily schedule</p>
                  <p>• One-touch dose confirmation</p>
                  <p>• Approve medication changes</p>
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-purple-100">
                <Button
                  variant="primary"
                  className="w-full bg-purple-600 hover:bg-purple-700 text-xs py-2.5"
                  loading={loading}
                  onClick={() => handleQuickDemo('elderly')}
                >
                  Enter as Meera <ArrowRight size={14} className="ml-1" />
                </Button>
              </div>
            </div>

            {/* Caregiver Persona */}
            <div className="border-2 border-teal-100 hover:border-teal-400 bg-teal-50/30 rounded-xl p-5 flex flex-col justify-between transition-all hover:shadow-md">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-3xl">👩‍⚕️</span>
                  <span className="text-[10px] font-bold bg-teal-100 text-teal-800 px-2 py-0.5 rounded-full uppercase">
                    Caregiver Role
                  </span>
                </div>
                <h3 className="font-bold text-gray-900 text-base">Riya Patel</h3>
                <p className="text-xs text-gray-500 mt-1">
                  Assigned Dedicated Caregiver
                </p>
                <div className="mt-3 text-[11px] text-gray-600 space-y-1">
                  <p>• <strong>"I'm handling it"</strong> feature</p>
                  <p>• Claim overdue dose follow-ups</p>
                  <p>• Record follow-up progress</p>
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-teal-100">
                <Button
                  variant="primary"
                  className="w-full bg-teal-600 hover:bg-teal-700 text-xs py-2.5"
                  loading={loading}
                  onClick={() => handleQuickDemo('caregiver')}
                >
                  Enter as Riya <ArrowRight size={14} className="ml-1" />
                </Button>
              </div>
            </div>

            {/* Family Member Persona */}
            <div className="border-2 border-blue-100 hover:border-blue-400 bg-blue-50/30 rounded-xl p-5 flex flex-col justify-between transition-all hover:shadow-md">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-3xl">👨‍👧</span>
                  <span className="text-[10px] font-bold bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full uppercase">
                    Family Role
                  </span>
                </div>
                <h3 className="font-bold text-gray-900 text-base">Arjun Sharma</h3>
                <p className="text-xs text-gray-500 mt-1">
                  Son & Healthcare Coordinator
                </p>
                <div className="mt-3 text-[11px] text-gray-600 space-y-1">
                  <p>• Monitor real-time adherence</p>
                  <p>• Track caregiver accountability</p>
                  <p>• Propose prescription changes</p>
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-blue-100">
                <Button
                  variant="primary"
                  className="w-full bg-blue-600 hover:bg-blue-700 text-xs py-2.5"
                  loading={loading}
                  onClick={() => handleQuickDemo('family')}
                >
                  Enter as Arjun <ArrowRight size={14} className="ml-1" />
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Manual Passcode Login */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
          <form onSubmit={handleManualLogin} className="max-w-md mx-auto space-y-4">
            <div className="text-center">
              <h3 className="text-sm font-bold text-gray-900 flex items-center justify-center gap-1.5">
                <Lock size={14} className="text-gray-500" />
                <span>Enter Passcode or Password</span>
              </h3>
            </div>

            <div className="flex gap-2">
              <input
                type="password"
                maxLength={4}
                placeholder="4-digit passcode"
                value={passcode}
                onChange={(e) => setPasscode(e.target.value)}
                className="flex-1 text-center tracking-widest text-lg font-bold border border-gray-300 rounded-lg p-2.5 focus:border-teal-500 focus:ring-1 focus:ring-teal-500 outline-none"
              />
              <Button variant="primary" type="submit" loading={loading}>
                Log In
              </Button>
            </div>

            {(error || localError) && (
              <p className="text-xs text-red-600 text-center font-medium">
                {error || localError}
              </p>
            )}
          </form>
        </div>

        {/* Product philosophy banner */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
          <div className="p-4 bg-white/60 rounded-xl border border-gray-200">
            <Sparkles className="mx-auto text-teal-600 mb-1" size={20} />
            <h4 className="font-bold text-xs text-gray-900">Intelligence</h4>
            <p className="text-[11px] text-gray-500 mt-0.5">Gemini Vision OCR & automated adherence analytics</p>
          </div>
          <div className="p-4 bg-white/60 rounded-xl border border-gray-200">
            <Shield className="mx-auto text-teal-600 mb-1" size={20} />
            <h4 className="font-bold text-xs text-gray-900">Accountability</h4>
            <p className="text-[11px] text-gray-500 mt-0.5">"I'm handling it" feature tracks real responsibility</p>
          </div>
          <div className="p-4 bg-white/60 rounded-xl border border-gray-200">
            <Users className="mx-auto text-teal-600 mb-1" size={20} />
            <h4 className="font-bold text-xs text-gray-900">Independence</h4>
            <p className="text-[11px] text-gray-500 mt-0.5">Elderly patients control and approve all changes</p>
          </div>
        </div>
      </div>
    </div>
  );
}
