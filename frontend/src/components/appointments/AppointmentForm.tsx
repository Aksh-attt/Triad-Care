import React, { useState, useEffect } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { addAppointment, updateAppointment } from '../../api/appointments';
import type { Appointment } from '../../types';

interface AppointmentFormProps {
  open: boolean;
  profileId: number;
  initialData?: Appointment | null;
  onClose: () => void;
  onSaved: () => void;
}

export function AppointmentForm({
  open,
  profileId,
  initialData,
  onClose,
  onSaved,
}: AppointmentFormProps) {
  const [doctorName, setDoctorName] = useState('');
  const [specialty, setSpecialty] = useState('');
  const [dateTime, setDateTime] = useState('');
  const [location, setLocation] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialData) {
      setDoctorName(initialData.doctor_name);
      setSpecialty(initialData.specialty || '');
      // Format datetime-local string
      const dt = new Date(initialData.date_time);
      const isoLocal = new Date(dt.getTime() - dt.getTimezoneOffset() * 60000)
        .toISOString()
        .slice(0, 16);
      setDateTime(isoLocal);
      setLocation(initialData.location || '');
      setNotes(initialData.notes || '');
    } else {
      setDoctorName('');
      setSpecialty('');
      // Default to tomorrow 10:00 AM
      const tmrw = new Date();
      tmrw.setDate(tmrw.getDate() + 1);
      tmrw.setHours(10, 0, 0, 0);
      const isoLocal = new Date(tmrw.getTime() - tmrw.getTimezoneOffset() * 60000)
        .toISOString()
        .slice(0, 16);
      setDateTime(isoLocal);
      setLocation('');
      setNotes('');
    }
  }, [initialData, open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!doctorName.trim() || !dateTime) {
      setError('Please provide doctor name and appointment date/time.');
      return;
    }
    setLoading(true);
    setError(null);

    const payload = {
      doctor_name: doctorName,
      specialty,
      date_time: new Date(dateTime).toISOString(),
      location,
      notes,
    };

    try {
      if (initialData) {
        await updateAppointment(initialData.id, payload);
      } else {
        await addAppointment(profileId, payload);
      }
      onSaved();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save appointment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={initialData ? 'Edit Appointment' : 'Schedule Doctor Appointment'}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
            Doctor / Practitioner Name *
          </label>
          <input
            type="text"
            required
            placeholder="e.g. Dr. Priya Nair"
            value={doctorName}
            onChange={(e) => setDoctorName(e.target.value)}
            className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
            Specialty / Clinic Department
          </label>
          <input
            type="text"
            placeholder="e.g. Cardiologist, General Physician, Eye Specialist"
            value={specialty}
            onChange={(e) => setSpecialty(e.target.value)}
            className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
            Date & Time *
          </label>
          <input
            type="datetime-local"
            required
            value={dateTime}
            onChange={(e) => setDateTime(e.target.value)}
            className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
            Clinic / Hospital Location
          </label>
          <input
            type="text"
            placeholder="e.g. City Health Clinic, Room 302"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
            Notes / Questions for Doctor
          </label>
          <textarea
            rows={2}
            placeholder="e.g. Discuss blood pressure check and fasting glucose results..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex justify-end gap-2 pt-3 border-t border-gray-100">
          <Button variant="secondary" onClick={onClose} type="button">
            Cancel
          </Button>
          <Button variant="primary" type="submit" loading={loading}>
            {initialData ? 'Save Changes' : 'Schedule Appointment'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
