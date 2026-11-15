import React, { useState } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { claimFollowup } from '../../api/followups';
import { useAuth } from '../../store/authStore';
import type { FollowupAction } from '../../types';
import { AlertTriangle } from 'lucide-react';

interface ClaimFollowupModalProps {
  open: boolean;
  doseId: number;
  onClose: () => void;
  onClaimed: () => void;
}

const ACTIONS: { value: FollowupAction; emoji: string; label: string; description: string }[] = [
  { value: 'calling', emoji: '📞', label: "I'm calling", description: 'Call the patient to remind them' },
  { value: 'going_to_check', emoji: '🏃', label: "I'm going to check", description: 'Visit the patient in person' },
  { value: 'unavailable', emoji: '❌', label: "I'm unavailable", description: 'Cannot handle right now' },
];

export function ClaimFollowupModal({ open, doseId, onClose, onClaimed }: ClaimFollowupModalProps) {
  const { user } = useAuth();
  const [selected, setSelected] = useState<FollowupAction | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClaim = async () => {
    if (!user || !selected) return;
    setLoading(true);
    setError(null);
    try {
      await claimFollowup(doseId, user.id, selected);
      onClaimed();
    } catch (err) {
      setError('Failed to claim followup. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Handle Missed Dose">
      <div className="space-y-4">
        {/* Warning */}
        <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg p-3">
          <AlertTriangle size={16} className="text-amber-600 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-amber-800 font-medium">
            Claiming responsibility does NOT mark the medication as taken.
          </p>
        </div>

        <p className="text-sm text-gray-600">Select how you will follow up with the patient:</p>

        <div className="space-y-2">
          {ACTIONS.map((action) => (
            <button
              key={action.value}
              onClick={() => setSelected(action.value)}
              className={`w-full flex items-center gap-3 p-3 rounded-xl border-2 transition-all text-left ${
                selected === action.value
                  ? 'border-teal-500 bg-teal-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <span className="text-2xl">{action.emoji}</span>
              <div>
                <p className="font-semibold text-gray-900">{action.label}</p>
                <p className="text-xs text-gray-500">{action.description}</p>
              </div>
            </button>
          ))}
        </div>

        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}

        <div className="flex gap-2 justify-end pt-2">
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button
            variant="primary"
            disabled={!selected}
            loading={loading}
            onClick={handleClaim}
          >
            Confirm
          </Button>
        </div>
      </div>
    </Modal>
  );
}
