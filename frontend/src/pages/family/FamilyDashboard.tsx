import React, { useEffect, useState } from 'react';
import { useAuth } from '../../store/authStore';
import { getTodayDoses } from '../../api/doses';
import { getFollowups } from '../../api/followups';
import { getAppointments } from '../../api/appointments';
import { getChangeRequests } from '../../api/changes';
import { getMedications } from '../../api/medications';
import { DoseCard } from '../../components/medications/DoseCard';
import { FollowupCard } from '../../components/followups/FollowupCard';
import { AppointmentCard } from '../../components/appointments/AppointmentCard';
import { ChangeRequestCard } from '../../components/changes/ChangeRequestCard';
import { ChangeRequestForm } from '../../components/changes/ChangeRequestForm';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { Button } from '../../components/ui/Button';
import type { DoseSchedule, CaregiverFollowup, Appointment, MedicationChangeRequest, Medication } from '../../types';
import { Heart, Activity, ShieldCheck, Calendar, FileEdit, Plus, Sparkles } from 'lucide-react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';

export function FamilyDashboard() {
  const { user, profile, profileId } = useAuth();
  const [doses, setDoses] = useState<DoseSchedule[]>([]);
  const [followups, setFollowups] = useState<CaregiverFollowup[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [changes, setChanges] = useState<MedicationChangeRequest[]>([]);
  const [medications, setMedications] = useState<Medication[]>([]);
  const [changeModalOpen, setChangeModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    if (!profileId) return;
    setLoading(true);
    try {
      const [dosesData, followupsData, apptsData, changesData, medsData] = await Promise.all([
        getTodayDoses(profileId),
        getFollowups(profileId),
        getAppointments(profileId),
        getChangeRequests(profileId),
        getMedications(profileId),
      ]);
      setDoses(dosesData);
      setFollowups(followupsData);
      setAppointments(apptsData);
      setChanges(changesData);
      setMedications(medsData);
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

  // Calculate adherence
  const total = doses.length;
  const taken = doses.filter((d) => d.status === 'taken').length;
  const missed = doses.filter((d) => d.status === 'missed').length;
  const notConfirmed = doses.filter((d) => d.status === 'not_confirmed').length;
  const pending = doses.filter((d) => d.status === 'pending').length;
  const adherenceRate = total > 0 ? Math.round((taken / total) * 100) : 0;

  const chartData = [
    { name: 'Taken', value: taken, color: '#16a34a' },
    { name: 'Pending', value: pending, color: '#94a3b8' },
    { name: 'Not Confirmed', value: notConfirmed, color: '#d97706' },
    { name: 'Missed', value: missed, color: '#dc2626' },
  ].filter((d) => d.value > 0);

  const activeFollowups = followups.filter((f) => f.status !== 'resolved');

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="bg-gradient-to-r from-navy-800 to-navy-900 rounded-3xl p-6 sm:p-8 text-white shadow-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="text-xs uppercase font-bold text-blue-300 tracking-wider">
              Family Care Coordination
            </div>
            <h1 className="text-2xl sm:text-3xl font-black mt-1">
              Welcome, {user?.name}
            </h1>
            <p className="text-xs sm:text-sm text-blue-100 mt-2">
              Monitoring health and care coordination for <strong>{profile?.name || 'Meera Sharma'}</strong>.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              onClick={() => setChangeModalOpen(true)}
              className="bg-blue-600 hover:bg-blue-700 text-xs py-2.5"
            >
              <Plus size={16} className="mr-1" /> Propose Med Change
            </Button>
          </div>
        </div>
      </div>

      {/* Adherence & Caregiver Accountability Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Adherence Overview with Recharts */}
        <div className="bg-white rounded-2xl border border-gray-200 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-base font-bold text-gray-900 flex items-center gap-1.5">
                <Activity size={18} className="text-blue-600" />
                <span>Today's Adherence</span>
              </h2>
              <span className="text-xs font-black text-green-700 bg-green-50 px-2 py-0.5 rounded-full border border-green-200">
                {adherenceRate}% Taken
              </span>
            </div>
            <p className="text-xs text-gray-500">
              {taken} of {total} doses confirmed taken today
            </p>
          </div>

          <div className="h-40 my-2 flex items-center justify-center">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    innerRadius={36}
                    outerRadius={56}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-gray-400">No dose data</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-gray-100">
            <div className="flex items-center gap-1.5 text-gray-700">
              <span className="w-2.5 h-2.5 rounded-full bg-green-600"></span>
              <span>Taken: <strong>{taken}</strong></span>
            </div>
            <div className="flex items-center gap-1.5 text-gray-700">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
              <span>Unconfirmed: <strong>{notConfirmed}</strong></span>
            </div>
            <div className="flex items-center gap-1.5 text-gray-700">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-400"></span>
              <span>Pending: <strong>{pending}</strong></span>
            </div>
            <div className="flex items-center gap-1.5 text-gray-700">
              <span className="w-2.5 h-2.5 rounded-full bg-red-600"></span>
              <span>Missed: <strong>{missed}</strong></span>
            </div>
          </div>
        </div>

        {/* Caregiver Accountability Card (Key Differentiator) */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-200 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-base font-bold text-gray-900 flex items-center gap-1.5">
                <ShieldCheck size={18} className="text-teal-600" />
                <span>Caregiver Follow-up Transparency</span>
              </h2>
              <span className="text-xs bg-teal-50 text-teal-800 font-bold px-2.5 py-0.5 rounded-full border border-teal-200">
                {activeFollowups.length} Active
              </span>
            </div>
            <p className="text-xs text-gray-500">
              Family members can see exactly which caregiver has claimed responsibility for overdue doses.
            </p>
          </div>

          <div className="my-3 space-y-2">
            {activeFollowups.length === 0 ? (
              <div className="p-4 bg-teal-50/50 rounded-xl border border-teal-100 text-xs text-teal-900 flex items-center gap-2">
                <span className="text-teal-600 text-lg">✓</span>
                <span>No overdue doses currently pending follow-up. Caregiver is on standby.</span>
              </div>
            ) : (
              activeFollowups.slice(0, 2).map((f) => (
                <div
                  key={f.id}
                  className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between gap-3 text-xs"
                >
                  <div>
                    <p className="font-bold text-gray-900">
                      {f.caregiver_name || 'Riya Patel'} is handling follow-up
                    </p>
                    <p className="text-gray-500 mt-0.5">
                      Action: <strong className="text-teal-700">{f.action.replace(/_/g, ' ')}</strong> · Target:{' '}
                      {f.dose?.medication?.name || 'Overdue Dose'}
                    </p>
                  </div>
                  <span className="font-bold text-xs uppercase px-2 py-0.5 rounded bg-amber-100 text-amber-800">
                    {f.status.replace(/_/g, ' ')}
                  </span>
                </div>
              ))
            )}
          </div>

          <div className="text-[11px] text-gray-400 pt-2 border-t border-gray-100 italic">
            "Care that connects. Responsibility that follows."
          </div>
        </div>
      </div>

      {/* Today's Medication Schedule */}
      <div className="space-y-3 pt-2">
        <h2 className="text-lg font-black text-gray-900">Today's Medication Schedule</h2>
        <div className="space-y-2.5">
          {doses.map((d) => (
            <DoseCard key={d.id} dose={d} onUpdate={loadData} />
          ))}
        </div>
      </div>

      {/* Medication Change Proposals */}
      <div className="space-y-3 pt-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-black text-gray-900 flex items-center gap-2">
            <FileEdit size={18} className="text-purple-600" />
            <span>Medication Change Proposals</span>
          </h2>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setChangeModalOpen(true)}
          >
            + Propose New Change
          </Button>
        </div>

        {changes.length === 0 ? (
          <div className="p-4 bg-white rounded-xl border border-gray-200 text-xs text-gray-500 text-center">
            No medication changes currently proposed.
          </div>
        ) : (
          <div className="space-y-3">
            {changes.slice(0, 3).map((req) => (
              <ChangeRequestCard key={req.id} request={req} onReviewed={loadData} />
            ))}
          </div>
        )}
      </div>

      {/* Upcoming Appointments */}
      <div className="space-y-3 pt-4">
        <h2 className="text-lg font-black text-gray-900 flex items-center gap-2">
          <Calendar size={18} className="text-blue-600" />
          <span>Upcoming Appointments</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {appointments.slice(0, 2).map((appt) => (
            <AppointmentCard key={appt.id} appointment={appt} onDeleted={loadData} />
          ))}
        </div>
      </div>

      <ChangeRequestForm
        open={changeModalOpen}
        profileId={profileId || 1}
        medications={medications}
        onClose={() => setChangeModalOpen(false)}
        onCreated={() => {
          setChangeModalOpen(false);
          loadData();
        }}
      />
    </div>
  );
}
