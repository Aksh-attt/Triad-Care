import React, { useState } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { createChangeRequest } from '../../api/changes';
import type { Medication } from '../../types';
import { useAuth } from '../../store/authStore';

interface ChangeRequestFormProps {
  open: boolean;
  profileId: number;
  medications: Medication[];
  onClose: () => void;
  onCreated: () => void;
}

export function ChangeRequestForm({
  open,
  profileId,
  medications,
  onClose,
  onCreated,
}: ChangeRequestFormProps) {
  const { user } = useAuth();
  const [changeType, setChangeType] = useState('dosage_change');
  const [selectedMedId, setSelectedMedId] = useState<string>(
    medications.length > 0 ? String(medications[0].id) : ''
  );
  const [newMedName, setNewMedName] = useState('');
  const [newDosage, setNewDosage] = useState('');
  const [unit, setUnit] = useState('mg');
  const [frequency, setFrequency] = useState('once_daily');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    if (!reason.trim()) {
      setError('Please provide a medical reason or context for this change.');
      return;
    }

    setLoading(true);
    setError(null);

    let proposedDetails: Record<string, unknown> = {};
    let medId: number | undefined = undefined;

    if (changeType === 'dosage_change') {
      medId = parseInt(selectedMedId);
      proposedDetails = { new_dosage: newDosage, unit };
    } else if (changeType === 'frequency_change') {
      medId = parseInt(selectedMedId);
      proposedDetails = { frequency };
    } else if (changeType === 'discontinue') {
      medId = parseInt(selectedMedId);
      proposedDetails = { action: 'discontinue' };
    } else if (changeType === 'new_medicine') {
      proposedDetails = {
        name: newMedName,
        dosage: newDosage,
        unit,
        frequency,
        timing_slots: ['morning'],
      };
    }

    try {
      await createChangeRequest(profileId, {
        requested_by_user_id: user.id,
        medication_id: medId,
        change_type: changeType,
        proposed_details: proposedDetails,
        reason,
      });
      onCreated();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create change request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Propose Medication Change">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="bg-purple-50 border border-purple-200 text-purple-900 p-3 rounded-lg text-xs leading-relaxed">
          <strong>Safety Policy:</strong> Changes proposed by family members require patient review
          and approval before any medication schedule is altered.
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
            Type of Change *
          </label>
          <select
            value={changeType}
            onChange={(e) => setChangeType(e.target.value)}
            className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-purple-500"
          >
            <option value="dosage_change">Adjust Medication Dosage</option>
            <option value="frequency_change">Adjust Frequency / Timing</option>
            <option value="discontinue">Discontinue Medication</option>
            <option value="new_medicine">Propose New Medication</option>
          </select>
        </div>

        {changeType !== 'new_medicine' ? (
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
              Select Medication *
            </label>
            <select
              value={selectedMedId}
              onChange={(e) => setSelectedMedId(e.target.value)}
              className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-purple-500"
            >
              {medications.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.dosage} {m.unit}) — {m.frequency}
                </option>
              ))}
            </select>
          </div>
        ) : (
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
              New Medication Name *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Atorvastatin"
              value={newMedName}
              onChange={(e) => setNewMedName(e.target.value)}
              className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-purple-500"
            />
          </div>
        )}

        {(changeType === 'dosage_change' || changeType === 'new_medicine') && (
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                New Dosage *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. 100"
                value={newDosage}
                onChange={(e) => setNewDosage(e.target.value)}
                className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-purple-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                Unit
              </label>
              <select
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-purple-500"
              >
                <option value="mg">mg</option>
                <option value="mcg">mcg</option>
                <option value="ml">ml</option>
                <option value="tablet">tablet(s)</option>
              </select>
            </div>
          </div>
        )}

        {(changeType === 'frequency_change' || changeType === 'new_medicine') && (
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
              Frequency
            </label>
            <select
              value={frequency}
              onChange={(e) => setFrequency(e.target.value)}
              className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-purple-500"
            >
              <option value="once_daily">Once Daily</option>
              <option value="twice_daily">Twice Daily</option>
              <option value="thrice_daily">Three Times Daily</option>
              <option value="as_needed">As Needed</option>
            </select>
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
            Reason / Doctor's Guidance *
          </label>
          <textarea
            required
            rows={3}
            placeholder="e.g. Discussed with Dr. Sharma during today's visit, requested dosage increase to better regulate blood sugar..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-purple-500"
          />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex justify-end gap-2 pt-3 border-t border-gray-100">
          <Button variant="secondary" onClick={onClose} type="button">
            Cancel
          </Button>
          <Button variant="primary" type="submit" loading={loading}>
            Submit Proposal for Approval
          </Button>
        </div>
      </form>
    </Modal>
  );
}
