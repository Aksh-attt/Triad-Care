import React, { useEffect, useState } from 'react';
import { useAuth } from '../../store/authStore';
import { getChangeRequests } from '../../api/changes';
import { getMedications } from '../../api/medications';
import { ChangeRequestCard } from '../../components/changes/ChangeRequestCard';
import { ChangeRequestForm } from '../../components/changes/ChangeRequestForm';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import { Button } from '../../components/ui/Button';
import type { MedicationChangeRequest, Medication } from '../../types';
import { FileEdit, Plus } from 'lucide-react';

export function FamilyChanges() {
  const { profileId, profile } = useAuth();
  const [requests, setRequests] = useState<MedicationChangeRequest[]>([]);
  const [medications, setMedications] = useState<Medication[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  const loadData = async () => {
    if (!profileId) return;
    setLoading(true);
    try {
      const [reqData, medsData] = await Promise.all([
        getChangeRequests(profileId),
        getMedications(profileId),
      ]);
      setRequests(reqData);
      setMedications(medsData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-purple-100 text-purple-700 flex items-center justify-center">
            <FileEdit size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-gray-900">Medication Change Requests</h1>
            <p className="text-xs text-gray-500">
              Propose updates to doses, frequency, or new medicines for patient approval.
            </p>
          </div>
        </div>

        <Button variant="primary" onClick={() => setModalOpen(true)}>
          <Plus size={16} className="mr-1" /> Propose New Change
        </Button>
      </div>

      <div className="bg-purple-50/70 border border-purple-200 rounded-xl p-4 text-xs text-purple-900 leading-relaxed">
        <strong>How Change Approval Works:</strong> To protect the elderly patient's safety and independence,
        any proposed modification submitted here enters a "Pending" state. It does not alter active medication
        schedules until the patient confirms and approves it on their dashboard.
      </div>

      {requests.length === 0 ? (
        <EmptyState
          title="No change requests submitted"
          description="There are currently no active or past medication change requests."
          action={{
            label: 'Propose First Change',
            onClick: () => setModalOpen(true),
          }}
        />
      ) : (
        <div className="space-y-3">
          {requests.map((req) => (
            <ChangeRequestCard key={req.id} request={req} onReviewed={loadData} />
          ))}
        </div>
      )}

      <ChangeRequestForm
        open={modalOpen}
        profileId={profileId || 1}
        medications={medications}
        onClose={() => setModalOpen(false)}
        onCreated={() => {
          setModalOpen(false);
          loadData();
        }}
      />
    </div>
  );
}
