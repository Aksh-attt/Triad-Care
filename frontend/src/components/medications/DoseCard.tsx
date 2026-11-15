import React, { useState } from 'react';
import { format } from 'date-fns';
import { Check, X, Clock, AlertCircle, Phone, HelpCircle } from 'lucide-react';
import { Button } from '../ui/Button';
import { StatusBadge } from '../ui/StatusBadge';
import { confirmDose } from '../../api/doses';
import type { DoseSchedule } from '../../types';
import { useAuth } from '../../store/authStore';
import { ClaimFollowupModal } from '../followups/ClaimFollowupModal';
import { RecordReasonModal } from './RecordReasonModal';
import { clsx } from 'clsx';

interface DoseCardProps {
  dose: DoseSchedule;
  onUpdate?: () => void;
  compact?: boolean;
}

export function DoseCard({ dose, onUpdate, compact }: DoseCardProps) {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [claimOpen, setClaimOpen] = useState(false);
  const [reasonOpen, setReasonOpen] = useState(false);

  const handleTake = async () => {
    if (!user) return;
    setLoading(true);
    try {
      await confirmDose(dose.id, user.id);
      onUpdate?.();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const statusIcons: Record<string, React.ReactNode> = {
    taken: <Check size={18} className="text-green-600" />,
    missed: <X size={18} className="text-red-500" />,
    not_confirmed: <AlertCircle size={18} className="text-amber-500" />,
    pending: <Clock size={18} className="text-gray-400" />,
  };

  const medName = dose.medication_name || dose.medication?.name || `Medication #${dose.medication_id}`;
  const medDosage = dose.medication_dosage || dose.medication?.dosage || '';
  const medUnit = dose.medication_unit || dose.medication?.unit || '';

  return (
    <>
      <div
        className={clsx(
          'bg-white rounded-xl border p-4 transition-all shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4',
          dose.status === 'taken' && 'border-green-200 bg-green-50/40',
          dose.status === 'missed' && 'border-red-200 bg-red-50/40',
          dose.status === 'not_confirmed' && 'border-amber-200 bg-amber-50/40',
          dose.status === 'pending' && 'border-gray-200'
        )}
      >
        <div className="flex items-start md:items-center gap-3 min-w-0">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-white border flex items-center justify-center shadow-xs">
            {statusIcons[dose.status]}
          </div>

          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="font-bold text-gray-900 text-base">{medName}</h4>
              <span className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full font-medium">
                {medDosage} {medUnit}
              </span>
            </div>
            
            <p className="text-xs text-gray-500 mt-1 flex items-center gap-2 flex-wrap">
              <span>⏰ {format(new Date(dose.scheduled_time), 'h:mm a')}</span>
              {dose.confirmed_by_name && (
                <span className="text-green-700 font-medium">
                  ✓ Confirmed by {dose.confirmed_by_name}
                </span>
              )}
            </p>

            {dose.reason_not_taken && (
              <div className="mt-1 text-xs text-amber-800 bg-amber-100/70 px-2 py-0.5 rounded inline-block">
                Reason: <strong>{dose.reason_not_taken}</strong>
                {dose.reason_notes && ` — "${dose.reason_notes}"`}
              </div>
            )}

            {dose.followup && (
              <div className="mt-1.5 text-xs bg-teal-50 border border-teal-200 text-teal-800 px-2.5 py-1 rounded-md inline-flex items-center gap-1.5">
                <span className="font-semibold">Caregiver follow-up:</span>
                <span>{dose.followup.caregiver_name || 'Caregiver'} ({dose.followup.action.replace(/_/g, ' ')})</span>
                <span className="capitalize font-bold text-teal-700">[{dose.followup.status.replace(/_/g, ' ')}]</span>
              </div>
            )}
          </div>
        </div>

        <div className="flex-shrink-0 flex items-center gap-2 flex-wrap justify-end">
          <StatusBadge status={dose.status} />

          {dose.status === 'pending' && user?.role === 'elderly' && (
            <Button size="md" variant="success" loading={loading} onClick={handleTake}>
              ✓ I've taken it
            </Button>
          )}

          {dose.status === 'not_confirmed' && (user?.role === 'elderly' || user?.role === 'caregiver') && (
            <Button size="sm" variant="success" loading={loading} onClick={handleTake}>
              Mark Taken
            </Button>
          )}

          {(dose.status === 'not_confirmed' || dose.status === 'missed') && (
            <Button size="sm" variant="outline" onClick={() => setReasonOpen(true)}>
              <HelpCircle size={14} className="mr-1" />
              Why not taken?
            </Button>
          )}

          {dose.status === 'not_confirmed' && user?.role === 'caregiver' && (
            <Button
              size="sm"
              variant="warning"
              onClick={() => setClaimOpen(true)}
              className="bg-amber-600 hover:bg-amber-700 text-white font-semibold"
            >
              <Phone size={14} className="mr-1" />
              I'm handling it
            </Button>
          )}
        </div>
      </div>

      <ClaimFollowupModal
        open={claimOpen}
        doseId={dose.id}
        onClose={() => setClaimOpen(false)}
        onClaimed={() => {
          setClaimOpen(false);
          onUpdate?.();
        }}
      />

      <RecordReasonModal
        open={reasonOpen}
        doseId={dose.id}
        medicationName={medName}
        onClose={() => setReasonOpen(false)}
        onRecorded={() => {
          setReasonOpen(false);
          onUpdate?.();
        }}
      />
    </>
  );
}
