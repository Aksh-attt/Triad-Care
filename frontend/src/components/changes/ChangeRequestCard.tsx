import React, { useState } from 'react';
import { format } from 'date-fns';
import { FileEdit, CheckCircle2, XCircle, Clock, AlertCircle } from 'lucide-react';
import { Button } from '../ui/Button';
import { reviewChangeRequest } from '../../api/changes';
import type { MedicationChangeRequest } from '../../types';
import { useAuth } from '../../store/authStore';

interface ChangeRequestCardProps {
  request: MedicationChangeRequest;
  onReviewed?: () => void;
}

export function ChangeRequestCard({ request, onReviewed }: ChangeRequestCardProps) {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);

  const handleReview = async (status: 'approved' | 'rejected') => {
    if (!user) return;
    setLoading(true);
    try {
      await reviewChangeRequest(request.id, status, user.id);
      onReviewed?.();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const isElderly = user?.role === 'elderly';
  const isPending = request.status === 'pending';

  const formatChangeType = (type: string) => {
    switch (type) {
      case 'dosage_change':
        return 'Dosage Adjustment';
      case 'frequency_change':
        return 'Frequency Adjustment';
      case 'discontinue':
        return 'Discontinue Medicine';
      case 'new_medicine':
        return 'New Medication Proposal';
      default:
        return type.replace(/_/g, ' ');
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-xs hover:shadow-md transition-shadow">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-purple-50 border border-purple-200 text-purple-700 flex items-center justify-center flex-shrink-0">
            <FileEdit size={18} />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-bold text-gray-900 text-base">
                {request.medication_name || (request.proposed_details as any)?.name || 'Medication Change'}
              </span>
              <span className="text-xs bg-purple-100 text-purple-800 font-semibold px-2.5 py-0.5 rounded-full capitalize">
                {formatChangeType(request.change_type)}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-0.5">
              Proposed by <span className="font-semibold text-gray-700">{request.requested_by_name || 'Family member'}</span>
              {request.created_at && (
                <span className="ml-1 text-gray-400">
                  · {format(new Date(request.created_at), 'MMM d, h:mm a')}
                </span>
              )}
            </p>
          </div>
        </div>

        <div>
          {request.status === 'pending' && (
            <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-bold bg-amber-50 text-amber-800 border border-amber-200">
              <Clock size={12} /> Pending Patient Approval
            </span>
          )}
          {request.status === 'approved' && (
            <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-bold bg-green-50 text-green-800 border border-green-200">
              <CheckCircle2 size={12} /> Approved
            </span>
          )}
          {request.status === 'rejected' && (
            <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-bold bg-red-50 text-red-800 border border-red-200">
              <XCircle size={12} /> Rejected
            </span>
          )}
        </div>
      </div>

      {/* Details box */}
      <div className="mt-3 bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-700 space-y-1">
        <p>
          <strong>Proposed Change:</strong>{' '}
          {request.change_type === 'dosage_change' && (
            <span>
              Adjust dose to{' '}
              <strong className="text-purple-700">
                {(request.proposed_details as any)?.new_dosage || (request.proposed_details as any)?.dosage || 'new dosage'}{' '}
                {(request.proposed_details as any)?.unit || 'mg'}
              </strong>
            </span>
          )}
          {request.change_type === 'discontinue' && (
            <span className="text-red-700 font-semibold">Discontinue this medication</span>
          )}
          {request.change_type === 'new_medicine' && (
            <span>
              Add {(request.proposed_details as any)?.name} {(request.proposed_details as any)?.dosage}{' '}
              {(request.proposed_details as any)?.unit} ({(request.proposed_details as any)?.frequency})
            </span>
          )}
          {request.change_type === 'frequency_change' && (
            <span>Change frequency to {(request.proposed_details as any)?.frequency}</span>
          )}
        </p>
        <p className="text-gray-600">
          <strong>Reason provided:</strong> "{request.reason}"
        </p>
      </div>

      {/* Elderly Approval Action */}
      {isPending && isElderly && (
        <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between gap-3">
          <p className="text-xs text-gray-500">
            Do you approve this change to your medication schedule?
          </p>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="danger"
              loading={loading}
              onClick={() => handleReview('rejected')}
            >
              <XCircle size={14} className="mr-1" />
              Reject
            </Button>
            <Button
              size="sm"
              variant="success"
              loading={loading}
              onClick={() => handleReview('approved')}
            >
              <CheckCircle2 size={14} className="mr-1" />
              Approve Change
            </Button>
          </div>
        </div>
      )}

      {/* Non-elderly pending note */}
      {isPending && !isElderly && (
        <div className="mt-3 text-[11px] text-amber-700 bg-amber-50 p-2 rounded border border-amber-200">
          Awaiting approval from the elderly patient before this change becomes active.
        </div>
      )}
    </div>
  );
}
