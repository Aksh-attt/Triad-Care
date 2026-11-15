import React, { useState } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { recordDoseReason } from '../../api/doses';
import { useAuth } from '../../store/authStore';
import { HelpCircle } from 'lucide-react';

interface RecordReasonModalProps {
  open: boolean;
  doseId: number;
  medicationName?: string;
  onClose: () => void;
  onRecorded: () => void;
}

const REASONS = [
  { value: 'Forgot', label: 'Forgot', description: 'Patient simply forgot or was distracted' },
  { value: 'Medicine unavailable', label: 'Medicine unavailable', description: 'Ran out or pharmacy refill pending' },
  { value: 'Feeling unwell', label: 'Feeling unwell', description: 'Nausea, dizziness, or adverse side effects' },
  { value: 'Unsure / cannot remember', label: 'Unsure / cannot remember', description: 'Unsure whether dose was taken earlier' },
  { value: 'Other', label: 'Other', description: 'Other specific reason' },
];

export function RecordReasonModal({
  open,
  doseId,
  medicationName,
  onClose,
  onRecorded,
}: RecordReasonModalProps) {
  const { user } = useAuth();
  const [selectedReason, setSelectedReason] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!user || !selectedReason) return;
    setLoading(true);
    setError(null);
    try {
      await recordDoseReason(doseId, selectedReason, notes, user.id);
      onRecorded();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to record reason');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Why wasn't it taken?">
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-gray-600 bg-blue-50 border border-blue-200 p-3 rounded-lg">
          <HelpCircle size={18} className="text-blue-600 flex-shrink-0" />
          <span>
            Recording reasons helps family and caregivers provide better care.
            {medicationName && <strong className="ml-1 text-blue-900">({medicationName})</strong>}
          </span>
        </div>

        <div className="space-y-2">
          {REASONS.map((r) => (
            <label
              key={r.value}
              className={`flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${
                selectedReason === r.value
                  ? 'border-navy-600 bg-navy-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <input
                type="radio"
                name="reason"
                value={r.value}
                checked={selectedReason === r.value}
                onChange={() => setSelectedReason(r.value)}
                className="mt-1 text-navy-600 focus:ring-navy-500"
              />
              <div className="flex-1">
                <p className="font-semibold text-gray-900 text-sm">{r.label}</p>
                <p className="text-xs text-gray-500">{r.description}</p>
              </div>
            </label>
          ))}
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
            Additional details (optional)
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={2}
            placeholder="e.g. Needs prescription refill by tomorrow..."
            className="w-full text-sm rounded-lg border border-gray-300 p-2.5 focus:border-navy-500 focus:ring-1 focus:ring-navy-500 outline-none"
          />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            disabled={!selectedReason}
            loading={loading}
            onClick={handleSubmit}
          >
            Save Reason
          </Button>
        </div>
      </div>
    </Modal>
  );
}
