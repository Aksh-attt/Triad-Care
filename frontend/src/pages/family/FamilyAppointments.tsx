import React, { useEffect, useState } from 'react';
import { useAuth } from '../../store/authStore';
import { getAppointments } from '../../api/appointments';
import { AppointmentCard } from '../../components/appointments/AppointmentCard';
import { AppointmentForm } from '../../components/appointments/AppointmentForm';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import { Button } from '../../components/ui/Button';
import type { Appointment } from '../../types';
import { Calendar, Plus } from 'lucide-react';

export function FamilyAppointments() {
  const { profileId, profile } = useAuth();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingAppt, setEditingAppt] = useState<Appointment | null>(null);

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

  const handleEdit = (appt: Appointment) => {
    setEditingAppt(appt);
    setModalOpen(true);
  };

  const handleAdd = () => {
    setEditingAppt(null);
    setModalOpen(true);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-blue-100 text-blue-700 flex items-center justify-center">
            <Calendar size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-gray-900">Appointments & Doctor Visits</h1>
            <p className="text-xs text-gray-500">
              Manage doctor visits, clinic consultations, and follow-ups for {profile?.name || 'Patient'}.
            </p>
          </div>
        </div>

        <Button variant="primary" onClick={handleAdd}>
          <Plus size={16} className="mr-1" /> Schedule Appointment
        </Button>
      </div>

      {appointments.length === 0 ? (
        <EmptyState
          title="No scheduled visits"
          description="There are currently no doctor appointments scheduled."
          action={{
            label: 'Schedule First Visit',
            onClick: handleAdd,
          }}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {appointments.map((appt) => (
            <AppointmentCard
              key={appt.id}
              appointment={appt}
              onEdit={handleEdit}
              onDeleted={loadAppts}
            />
          ))}
        </div>
      )}

      <AppointmentForm
        open={modalOpen}
        profileId={profileId || 1}
        initialData={editingAppt}
        onClose={() => setModalOpen(false)}
        onSaved={() => {
          setModalOpen(false);
          loadAppts();
        }}
      />
    </div>
  );
}
