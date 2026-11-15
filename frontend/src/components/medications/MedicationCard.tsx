import React from 'react';
import { Pill, Clock, AlertCircle, Edit, Trash2 } from 'lucide-react';
import { Button } from '../ui/Button';
import type { Medication } from '../../types';
import { deleteMedication } from '../../api/medications';
import { useAuth } from '../../store/authStore';

interface MedicationCardProps {
  medication: Medication;
  onEdit?: (med: Medication) => void;
  onDelete?: () => void;
}

export function MedicationCard({ medication, onEdit, onDelete }: MedicationCardProps) {
  const { user } = useAuth();
  const [deleting, setDeleting] = React.useState(false);

  const handleDelete = async () => {
    if (!window.confirm(`Are you sure you want to discontinue ${medication.name}?`)) return;
    setDeleting(true);
    try {
      await deleteMedication(medication.id);
      onDelete?.();
    } catch (err) {
      console.error(err);
    } finally {
      setDeleting(false);
    }
  };

  const timingLabels: Record<string, string> = {
    morning: '🌅 Morning (8 AM)',
    afternoon: '☀️ Afternoon (1 PM)',
    evening: '🌆 Evening (7 PM)',
    bedtime: '🌙 Bedtime (9 PM)',
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-xs hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-lg bg-teal-50 border border-teal-200 text-teal-700 flex items-center justify-center flex-shrink-0">
            <Pill size={20} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-gray-900 text-lg">{medication.name}</h3>
              <span className="text-xs bg-teal-100 text-teal-800 font-semibold px-2.5 py-0.5 rounded-full">
                {medication.dosage} {medication.unit}
              </span>
            </div>
            <p className="text-sm text-gray-500 capitalize mt-0.5">
              Frequency: {medication.frequency.replace(/_/g, ' ')}
            </p>
          </div>
        </div>

        {/* Action buttons (only for caregiver or family) */}
        {(user?.role === 'caregiver' || user?.role === 'family') && (
          <div className="flex items-center gap-1">
            {onEdit && (
              <button
                onClick={() => onEdit(medication)}
                className="p-1.5 text-gray-500 hover:text-navy-600 hover:bg-gray-100 rounded-md transition-colors"
                title="Edit Medication"
              >
                <Edit size={16} />
              </button>
            )}
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
              title="Discontinue Medication"
            >
              <Trash2 size={16} />
            </button>
          </div>
        )}
      </div>

      {medication.instructions && (
        <div className="mt-3 text-xs bg-slate-50 border border-slate-200 p-2.5 rounded-lg text-slate-700 flex items-start gap-1.5">
          <AlertCircle size={14} className="text-slate-500 mt-0.5 flex-shrink-0" />
          <span>Instructions: <strong>{medication.instructions}</strong></span>
        </div>
      )}

      <div className="mt-4 pt-3 border-t border-gray-100 flex flex-wrap gap-1.5">
        <span className="text-xs text-gray-400 mr-1 flex items-center">
          <Clock size={12} className="mr-1" /> Slots:
        </span>
        {medication.timing_slots && medication.timing_slots.length > 0 ? (
          medication.timing_slots.map((slot) => (
            <span
              key={slot}
              className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded-md font-medium"
            >
              {timingLabels[slot] || slot}
            </span>
          ))
        ) : (
          <span className="text-xs text-gray-400 italic">No specific slots set</span>
        )}
      </div>
    </div>
  );
}
