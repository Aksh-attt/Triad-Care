import React, { useEffect, useState } from 'react';
import { useAuth } from '../../store/authStore';
import { getMedications } from '../../api/medications';
import { MedicationCard } from '../../components/medications/MedicationCard';
import { MedicationForm } from '../../components/medications/MedicationForm';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import { Button } from '../../components/ui/Button';
import type { Medication } from '../../types';
import { Pill, Plus } from 'lucide-react';

export function FamilyMedications() {
  const { profileId, profile } = useAuth();
  const [medications, setMedications] = useState<Medication[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingMed, setEditingMed] = useState<Medication | null>(null);

  const loadMeds = async () => {
    if (!profileId) return;
    setLoading(true);
    try {
      const data = await getMedications(profileId);
      setMedications(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMeds();
  }, [profileId]);

  const handleEdit = (med: Medication) => {
    setEditingMed(med);
    setModalOpen(true);
  };

  const handleAdd = () => {
    setEditingMed(null);
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
          <div className="w-12 h-12 rounded-2xl bg-teal-100 text-teal-700 flex items-center justify-center">
            <Pill size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-gray-900">Manage Medications</h1>
            <p className="text-xs text-gray-500">
              Active prescriptions and dose schedules for {profile?.name || 'Patient'}.
            </p>
          </div>
        </div>

        <Button variant="primary" onClick={handleAdd}>
          <Plus size={16} className="mr-1" /> Add Medication
        </Button>
      </div>

      {medications.length === 0 ? (
        <EmptyState
          title="No active medications"
          description="There are currently no active medications recorded in this profile."
          action={{
            label: 'Add First Medication',
            onClick: handleAdd,
          }}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {medications.map((med) => (
            <MedicationCard
              key={med.id}
              medication={med}
              onEdit={handleEdit}
              onDelete={loadMeds}
            />
          ))}
        </div>
      )}

      <MedicationForm
        open={modalOpen}
        profileId={profileId || 1}
        initialData={editingMed}
        onClose={() => setModalOpen(false)}
        onSaved={() => {
          setModalOpen(false);
          loadMeds();
        }}
      />
    </div>
  );
}
