import React, { useEffect, useState } from 'react';
import { useAuth } from '../../store/authStore';
import { getAppointments } from '../../api/appointments';
import { AppointmentCard } from '../../components/appointments/AppointmentCard';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import type { Appointment } from '../../types';
import { Calendar } from 'lucide-react';

export function ElderlyAppointments() {
  const { profileId, profile } = useAuth();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  const loadAppts = async () => {
    if (!profileId) return;
    setLoading(true);
    try {
      const data = await getAppointments(profileId);
      setAppointments(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAppts();
  }, [profileId]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-2xl bg-blue-100 text-blue-700 flex items-center justify-center">
          <Calendar size={24} />
        </div>
        <div>
          <h1 className="text-2xl font-black text-gray-900">Doctor Visits & Appointments</h1>
          <p className="text-xs text-gray-500">
            Upcoming medical consultations for {profile?.name || 'you'}.
          </p>
        </div>
      </div>

      {appointments.length === 0 ? (
        <EmptyState
          title="No upcoming visits"
          description="You have no upcoming doctor visits scheduled at this time."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {appointments.map((appt) => (
            <AppointmentCard key={appt.id} appointment={appt} onDeleted={loadAppts} />
          ))}
        </div>
      )}
    </div>
  );
}
