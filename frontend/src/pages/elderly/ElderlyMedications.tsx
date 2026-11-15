import React, { useEffect, useState } from 'react';
import { useAuth } from '../../store/authStore';
import { getMedications } from '../../api/medications';
import { MedicationCard } from '../../components/medications/MedicationCard';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import type { Medication } from '../../types';
import { Pill } from 'lucide-react';

export function ElderlyMedications() {
  const { profileId, profile } = useAuth();
  const [medications, setMedications] = useState<Medication[]>([]);
  const [loading, setLoading] = useState(true);

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

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-2xl bg-purple-100 text-purple-700 flex items-center justify-center">
          <Pill size={24} />
        </div>
        <div>
          <h1 className="text-2xl font-black text-gray-900">My Prescriptions</h1>
          <p className="text-xs text-gray-500">
            Active medications prescribed for {profile?.name || 'you'}.
          </p>
        </div>
      </div>

      {medications.length === 0 ? (
        <EmptyState
          title="No active prescriptions"
          description="You currently have no active medications recorded in your profile."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {medications.map((med) => (
            <MedicationCard key={med.id} medication={med} />
          ))}
        </div>
      )}
    </div>
  );
}
