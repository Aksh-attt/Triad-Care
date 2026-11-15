import React from 'react';
import { format } from 'date-fns';
import { Calendar, MapPin, User, FileText, Trash2, Edit } from 'lucide-react';
import type { Appointment } from '../../types';
import { deleteAppointment } from '../../api/appointments';
import { useAuth } from '../../store/authStore';

interface AppointmentCardProps {
  appointment: Appointment;
  onEdit?: (appt: Appointment) => void;
  onDeleted?: () => void;
}

export function AppointmentCard({ appointment, onEdit, onDeleted }: AppointmentCardProps) {
  const { user } = useAuth();
  const [deleting, setDeleting] = React.useState(false);

  const handleDelete = async () => {
    if (!window.confirm(`Delete appointment with ${appointment.doctor_name}?`)) return;
    setDeleting(true);
    try {
      await deleteAppointment(appointment.id);
      onDeleted?.();
    } catch (err) {
      console.error(err);
    } finally {
      setDeleting(false);
    }
  };

  const apptDate = new Date(appointment.date_time);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-xs hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-200 text-blue-700 flex flex-col items-center justify-center flex-shrink-0">
            <span className="text-[10px] uppercase font-bold tracking-wider">{format(apptDate, 'MMM')}</span>
            <span className="text-lg font-black leading-none">{format(apptDate, 'd')}</span>
          </div>

          <div>
            <h3 className="font-bold text-gray-900 text-lg">{appointment.doctor_name}</h3>
            {appointment.specialty && (
              <p className="text-sm text-blue-600 font-medium">{appointment.specialty}</p>
            )}
            <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
              <Calendar size={13} className="text-gray-400" />
              {format(apptDate, 'EEEE, MMMM d, yyyy · h:mm a')}
            </p>
          </div>
        </div>

        {(user?.role === 'caregiver' || user?.role === 'family') && (
          <div className="flex items-center gap-1">
            {onEdit && (
              <button
                onClick={() => onEdit(appointment)}
                className="p-1.5 text-gray-500 hover:text-navy-600 hover:bg-gray-100 rounded-md transition-colors"
                title="Edit Appointment"
              >
                <Edit size={16} />
              </button>
            )}
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
              title="Delete Appointment"
            >
              <Trash2 size={16} />
            </button>
          </div>
        )}
      </div>

      <div className="mt-4 pt-3 border-t border-gray-100 space-y-1.5">
        {appointment.location && (
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <MapPin size={14} className="text-gray-400 flex-shrink-0" />
            <span>{appointment.location}</span>
          </div>
        )}
        {appointment.notes && (
          <div className="flex items-start gap-2 text-xs text-gray-600">
            <FileText size={14} className="text-gray-400 flex-shrink-0 mt-0.5" />
            <span>{appointment.notes}</span>
          </div>
        )}
      </div>
    </div>
  );
}
