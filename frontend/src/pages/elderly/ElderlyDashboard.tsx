import React, { useEffect, useState } from 'react';
import { useAuth } from '../../store/authStore';
import { getTodayDoses } from '../../api/doses';
import { getAppointments } from '../../api/appointments';
import { getChangeRequests } from '../../api/changes';
import { DoseCard } from '../../components/medications/DoseCard';
import { ChangeRequestCard } from '../../components/changes/ChangeRequestCard';
import { AppointmentCard } from '../../components/appointments/AppointmentCard';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import { Button } from '../../components/ui/Button';
import { confirmDose } from '../../api/doses';
import type { DoseSchedule, Appointment, MedicationChangeRequest } from '../../types';
import { Sun, CheckCircle, Calendar, AlertCircle, Heart } from 'lucide-react';

export function ElderlyDashboard() {
  const { user, profile, profileId } = useAuth();
  const [doses, setDoses] = useState<DoseSchedule[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [changes, setChanges] = useState<MedicationChangeRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [takingNext, setTakingNext] = useState(false);

  const loadData = async () => {
    if (!profileId) return;
    setLoading(true);
    try {
      const [dosesData, apptsData, changesData] = await Promise.all([
        getTodayDoses(profileId),
        getAppointments(profileId),
        getChangeRequests(profileId),
      ]);
      setDoses(dosesData);
      setAppointments(apptsData);
      setChanges(changesData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [profileId]);

  // Find next pending or unconfirmed dose
  const nextDose = doses.find((d) => d.status === 'pending' || d.status === 'not_confirmed');

  const handleTakeNext = async () => {
    if (!nextDose || !user) return;
    setTakingNext(true);
    try {
      await confirmDose(nextDose.id, user.id);
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setTakingNext(false);
    }
  };

  const pendingApprovals = changes.filter((c) => c.status === 'pending');

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Warm Elderly Greeting Banner */}
      <div className="bg-gradient-to-r from-purple-700 to-indigo-800 rounded-3xl p-6 sm:p-8 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex items-center gap-2 text-purple-200 text-sm font-semibold mb-1">
            <Sun size={18} className="text-amber-300" />
            <span>{getGreeting()}, {profile?.name || user?.name}!</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight">
            How are you feeling today?
          </h1>
          <p className="text-sm text-purple-100 mt-2 max-w-xl leading-relaxed">
            Your family and caregivers are keeping track of your health with you. Here is your schedule for today.
          </p>
        </div>
      </div>

      {/* Pending Approval Alert (Section 6 Safety Requirement) */}
      {pendingApprovals.length > 0 && (
        <div className="bg-amber-50 border-2 border-amber-300 rounded-2xl p-5 shadow-xs space-y-3">
          <div className="flex items-center gap-2">
            <AlertCircle size={22} className="text-amber-600 flex-shrink-0" />
            <h2 className="text-lg font-black text-amber-900">
              Action Required: Medication Change Requests ({pendingApprovals.length})
            </h2>
          </div>
          <p className="text-xs text-amber-800">
            A family member proposed updates to your medications. Please review and confirm below:
          </p>
          <div className="space-y-3 pt-1">
            {pendingApprovals.map((req) => (
              <ChangeRequestCard key={req.id} request={req} onReviewed={loadData} />
            ))}
          </div>
        </div>
      )}

      {/* Hero Next Medication Action Card (Accessibility First) */}
      {nextDose ? (
        <div className="bg-white rounded-3xl border-2 border-teal-500 p-6 sm:p-8 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-black uppercase tracking-wider text-teal-800 bg-teal-100 px-3 py-1 rounded-full">
              Next Scheduled Medication
            </span>
            <span className="text-sm font-bold text-gray-500">
              ⏰ {new Date(nextDose.scheduled_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl sm:text-3xl font-black text-gray-900">
                {nextDose.medication_name || nextDose.medication?.name}
              </h2>
              <p className="text-base text-gray-600 font-semibold mt-1">
                {nextDose.medication_dosage || nextDose.medication?.dosage}{' '}
                {nextDose.medication_unit || nextDose.medication?.unit}
                {nextDose.medication?.instructions && (
                  <span className="ml-2 text-teal-700 bg-teal-50 px-2 py-0.5 rounded-md text-xs font-medium">
                    {nextDose.medication.instructions}
                  </span>
                )}
              </p>
            </div>

            {/* Giant Touch-Friendly Button for Elderly */}
            <Button
              variant="success"
              loading={takingNext}
              onClick={handleTakeNext}
              className="py-4 px-8 text-lg font-black rounded-2xl shadow-md bg-green-600 hover:bg-green-700 text-white min-w-[200px]"
            >
              ✓ I've taken it!
            </Button>
          </div>
        </div>
      ) : (
        <div className="bg-green-50 border border-green-200 rounded-3xl p-6 text-center text-green-800 space-y-2">
          <CheckCircle size={36} className="mx-auto text-green-600" />
          <h3 className="text-lg font-bold">All Doses Completed for Today!</h3>
          <p className="text-xs text-green-700">Great job staying on track with your prescriptions today.</p>
        </div>
      )}

      {/* Today's Medication Schedule */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-black text-gray-900">Today's Schedule</h2>
          <span className="text-xs text-gray-500 font-medium">
            {doses.filter((d) => d.status === 'taken').length} of {doses.length} taken
          </span>
        </div>

        {doses.length === 0 ? (
          <EmptyState
            title="No scheduled doses for today"
            description="Your doctor or family hasn't scheduled any medications for today."
          />
        ) : (
          <div className="space-y-3">
            {doses.map((dose) => (
              <DoseCard key={dose.id} dose={dose} onUpdate={loadData} />
            ))}
          </div>
        )}
      </div>

      {/* Upcoming Doctor Appointments */}
      <div className="space-y-4 pt-4">
        <h2 className="text-xl font-black text-gray-900 flex items-center gap-2">
          <Calendar size={20} className="text-blue-600" />
          <span>Upcoming Appointments</span>
        </h2>

        {appointments.length === 0 ? (
          <div className="p-5 bg-white rounded-2xl border border-gray-200 text-center text-gray-500 text-sm">
            No upcoming appointments scheduled.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {appointments.slice(0, 2).map((appt) => (
              <AppointmentCard key={appt.id} appointment={appt} onDeleted={loadData} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
