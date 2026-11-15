import React, { useState, useEffect } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { addMedication, updateMedication } from '../../api/medications';
import type { Medication } from '../../types';

interface MedicationFormProps {
  open: boolean;
  profileId: number;
  initialData?: Medication | null;
  onClose: () => void;
  onSaved: () => void;
}

const TIMING_OPTIONS = [
  { value: 'morning', label: 'Morning (8:00 AM)' },
  { value: 'afternoon', label: 'Afternoon (1:00 PM)' },
  { value: 'evening', label: 'Evening (7:00 PM)' },
  { value: 'bedtime', label: 'Bedtime (9:00 PM)' },
];

export function MedicationForm({
  open,
  profileId,
  initialData,
  onClose,
  onSaved,
}: MedicationFormProps) {
  const [name, setName] = useState('');
  const [dosage, setDosage] = useState('');
  const [unit, setUnit] = useState('mg');
  const [frequency, setFrequency] = useState('once_daily');
  const [timingSlots, setTimingSlots] = useState<string[]>(['morning']);
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState('');
  const [instructions, setInstructions] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialData) {
      setName(initialData.name);
      setDosage(initialData.dosage);
      setUnit(initialData.unit);
      setFrequency(initialData.frequency);
      setTimingSlots(initialData.timing_slots || ['morning']);
      setStartDate(initialData.start_date || new Date().toISOString().split('T')[0]);
      setEndDate(initialData.end_date || '');
      setInstructions(initialData.instructions || '');
    } else {
      setName('');
      setDosage('');
      setUnit('mg');
      setFrequency('once_daily');
      setTimingSlots(['morning']);
      setStartDate(new Date().toISOString().split('T')[0]);
      setEndDate('');
      setInstructions('');
    }
  }, [initialData, open]);

  const toggleSlot = (slot: string) => {
    if (timingSlots.includes(slot)) {
      setTimingSlots(timingSlots.filter((s) => s !== slot));
    } else {
      setTimingSlots([...timingSlots, slot]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !dosage.trim()) {
      setError('Please provide a medication name and dosage.');
      return;
    }
    setLoading(true);
    setError(null);

    const payload = {
      name,
      dosage,
      unit,
      frequency,
      timing_slots: timingSlots,
      start_date: startDate,
      end_date: endDate ? endDate : undefined,
      instructions,
      is_active: true,
    };

    try {
      if (initialData) {
        await updateMedication(initialData.id, payload);
      } else {
        await addMedication(profileId, payload);
      }
      onSaved();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save medication');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={initialData ? 'Edit Medication' : 'Add New Medication'}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
            Medication Name *
          </label>
          <input
            type="text"
            required
            placeholder="e.g. Metformin, Lisinopril"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
              Dosage *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. 500, 10"
              value={dosage}
              onChange={(e) => setDosage(e.target.value)}
              className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
              Unit
            </label>
            <select
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
              className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
            >
              <option value="mg">mg</option>
              <option value="g">g</option>
              <option value="mcg">mcg</option>
              <option value="ml">ml</option>
              <option value="tablet">tablet(s)</option>
              <option value="capsule">capsule(s)</option>
              <option value="drops">drops</option>
              <option value="puffs">puffs</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
            Frequency
          </label>
          <select
            value={frequency}
            onChange={(e) => setFrequency(e.target.value)}
            className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
          >
            <option value="once_daily">Once Daily</option>
            <option value="twice_daily">Twice Daily</option>
            <option value="thrice_daily">Three Times Daily</option>
            <option value="four_times_daily">Four Times Daily</option>
            <option value="as_needed">As Needed (PRN)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 uppercase mb-2">
            Schedule Timing Slots
          </label>
          <div className="grid grid-cols-2 gap-2">
            {TIMING_OPTIONS.map((opt) => (
              <label
                key={opt.value}
                className={`flex items-center gap-2 p-2.5 rounded-lg border text-xs font-medium cursor-pointer transition-colors ${
                  timingSlots.includes(opt.value)
                    ? 'border-teal-500 bg-teal-50 text-teal-900'
                    : 'border-gray-200 text-gray-700 hover:bg-gray-50'
                }`}
              >
                <input
                  type="checkbox"
                  checked={timingSlots.includes(opt.value)}
                  onChange={() => toggleSlot(opt.value)}
                  className="rounded text-teal-600 focus:ring-teal-500"
                />
                <span>{opt.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
            Instructions / Food Interaction
          </label>
          <input
            type="text"
            placeholder="e.g. Take with food, Before breakfast"
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
              End Date (optional)
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full text-sm border border-gray-300 rounded-lg p-2.5 outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500"
            />
          </div>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex justify-end gap-2 pt-3 border-t border-gray-100">
          <Button variant="secondary" onClick={onClose} type="button">
            Cancel
          </Button>
          <Button variant="primary" type="submit" loading={loading}>
            {initialData ? 'Save Changes' : 'Add Medication'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
