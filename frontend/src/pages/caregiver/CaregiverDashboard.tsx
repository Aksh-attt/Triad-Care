import React, { useEffect, useState } from 'react';
import { useAuth } from '../../store/authStore';
import { getTodayDoses } from '../../api/doses';
import { getFollowups } from '../../api/followups';
import { DoseCard } from '../../components/medications/DoseCard';
import { FollowupCard } from '../../components/followups/FollowupCard';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import type { DoseSchedule, CaregiverFollowup } from '../../types';
import { ShieldAlert, CheckCircle, Clock, Users, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export function CaregiverDashboard() {
  const { user, profile, profileId } = useAuth();
  const [doses, setDoses] = useState<DoseSchedule[]>([]);
  const [followups, setFollowups] = useState<CaregiverFollowup[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    if (!profileId) return;
    setLoading(true);
    try {
      const [dosesData, followupsData] = await Promise.all([
        getTodayDoses(profileId),
        getFollowups(profileId),
      ]);
      setDoses(dosesData);
      setFollowups(followupsData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [profileId]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // Filter unconfirmed or overdue doses
  const unconfirmedDoses = doses.filter((d) => d.status === 'not_confirmed');
  const activeFollowups = followups.filter((f) => f.status !== 'resolved');

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="bg-gradient-to-r from-teal-800 to-cyan-900 rounded-3xl p-6 sm:p-8 text-white shadow-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="text-xs uppercase font-bold text-teal-300 tracking-wider">
              Caregiver Action Center
            </div>
            <h1 className="text-2xl sm:text-3xl font-black mt-1">
              Welcome back, {user?.name}
            </h1>
            <p className="text-xs sm:text-sm text-teal-100 mt-2">
              Managing care for <strong>{profile?.name || 'Patient'}</strong> (Age {profile?.age || 72})
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/caregiver/followups"
              className="bg-white/10 hover:bg-white/20 text-white text-xs font-semibold px-4 py-2.5 rounded-xl border border-white/20 transition-colors inline-flex items-center gap-1.5"
            >
              All Follow-ups <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-black text-xl border border-amber-200">
            {unconfirmedDoses.length}
          </div>
          <div>
            <p className="text-xs text-gray-500 font-semibold uppercase">Unconfirmed Doses</p>
            <p className="text-sm font-bold text-gray-900 mt-0.5">Need attention or follow-up</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center font-black text-xl border border-teal-200">
            {activeFollowups.length}
          </div>
          <div>
            <p className="text-xs text-gray-500 font-semibold uppercase">Active Follow-ups</p>
            <p className="text-sm font-bold text-gray-900 mt-0.5">Assigned and in-progress</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-green-50 text-green-600 flex items-center justify-center font-black text-xl border border-green-200">
            {doses.filter((d) => d.status === 'taken').length}
          </div>
          <div>
            <p className="text-xs text-gray-500 font-semibold uppercase">Confirmed Taken</p>
            <p className="text-sm font-bold text-gray-900 mt-0.5">Verified by patient/caregiver</p>
          </div>
        </div>
      </div>

      {/* Overdue / Unconfirmed Doses - Urgent Action Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-black text-gray-900 flex items-center gap-2">
            <ShieldAlert size={20} className="text-amber-600" />
            <span>Unconfirmed / Overdue Doses ({unconfirmedDoses.length})</span>
          </h2>
          <span className="text-xs text-gray-500 font-medium">
            Use "I'm handling it" to claim follow-up responsibility
          </span>
        </div>

        {unconfirmedDoses.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-2xl p-6 text-center text-gray-500 text-sm">
            ✓ No overdue or unconfirmed doses right now. All scheduled doses are accounted for.
          </div>
        ) : (
          <div className="space-y-3">
            {unconfirmedDoses.map((dose) => (
              <DoseCard key={dose.id} dose={dose} onUpdate={loadData} />
            ))}
          </div>
        )}
      </div>

      {/* Active Follow-ups Section */}
      <div className="space-y-3 pt-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-black text-gray-900 flex items-center gap-2">
            <Clock size={20} className="text-teal-600" />
            <span>Active Caregiver Follow-ups ({activeFollowups.length})</span>
          </h2>
          <span className="text-xs text-gray-500">
            Updated in real-time on family dashboard
          </span>
        </div>

        {activeFollowups.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-2xl p-6 text-center text-gray-500 text-sm">
            No active follow-ups. You're all caught up!
          </div>
        ) : (
          <div className="space-y-3">
            {activeFollowups.map((f) => (
              <FollowupCard key={f.id} followup={f} onUpdated={loadData} />
            ))}
          </div>
        )}
      </div>

      {/* Full Today's Schedule Reference */}
      <div className="space-y-3 pt-4">
        <h2 className="text-lg font-black text-gray-900">Full Schedule Today</h2>
        <div className="space-y-2.5">
          {doses.map((d) => (
            <DoseCard key={d.id} dose={d} onUpdate={loadData} compact />
          ))}
        </div>
      </div>
    </div>
  );
}
