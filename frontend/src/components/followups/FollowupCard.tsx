import React, { useState } from 'react';
import { format } from 'date-fns';
import { Phone, CheckCircle, Clock, AlertTriangle, ArrowRightCircle } from 'lucide-react';
import { Button } from '../ui/Button';
import { updateFollowup } from '../../api/followups';
import type { CaregiverFollowup } from '../../types';
import { useAuth } from '../../store/authStore';

interface FollowupCardProps {
  followup: CaregiverFollowup;
  onUpdated?: () => void;
}

const ACTION_MAP: Record<string, { label: string; icon: string }> = {
  calling: { label: "I'm calling", icon: '📞' },
  going_to_check: { label: "I'm going to check", icon: '🏃' },
  unavailable: { label: "I'm unavailable", icon: '❌' },
};

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  unassigned: { label: 'Unassigned', color: 'bg-gray-100 text-gray-700 border-gray-200' },
  accepted: { label: 'Accepted', color: 'bg-blue-100 text-blue-800 border-blue-200' },
  in_progress: { label: 'In Progress', color: 'bg-amber-100 text-amber-800 border-amber-200' },
  resolved: { label: 'Resolved', color: 'bg-green-100 text-green-800 border-green-200' },
  reassigned: { label: 'Reassigned', color: 'bg-purple-100 text-purple-800 border-purple-200' },
};

export function FollowupCard({ followup, onUpdated }: FollowupCardProps) {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [notes, setNotes] = useState(followup.notes || '');
  const [editingNotes, setEditingNotes] = useState(false);

  const handleStatusChange = async (newStatus: string) => {
    setLoading(true);
    try {
      await updateFollowup(followup.id, { status: newStatus });
      onUpdated?.();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveNotes = async () => {
    setLoading(true);
    try {
      await updateFollowup(followup.id, { notes });
      setEditingNotes(false);
      onUpdated?.();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const actionInfo = ACTION_MAP[followup.action] || { label: followup.action, icon: '📋' };
  const statusInfo = STATUS_MAP[followup.status] || { label: followup.status, color: 'bg-gray-100' };

  const isCaregiver = user?.role === 'caregiver';

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-xs hover:shadow-md transition-shadow">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-teal-50 border border-teal-200 flex items-center justify-center text-xl">
            {actionInfo.icon}
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-bold text-gray-900 text-base">
                {followup.caregiver_name || `Caregiver #${followup.caregiver_id}`}
              </span>
              <span className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-medium">
                {actionInfo.label}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-0.5">
              Claimed: {format(new Date(followup.accepted_at), 'MMM d, h:mm a')}
              {followup.resolved_at && (
                <span className="text-green-600 ml-2">
                  · Resolved: {format(new Date(followup.resolved_at), 'h:mm a')}
                </span>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={`text-xs px-2.5 py-1 rounded-full font-bold border ${statusInfo.color}`}>
            {statusInfo.label}
          </span>
        </div>
      </div>

      {/* Target dose information */}
      <div className="mt-3 bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-700">
        <div className="flex items-center justify-between">
          <span>
            Target Dose:{' '}
            <strong>
              {followup.dose?.medication?.name ||
                followup.dose?.medication_name ||
                `Dose #${followup.dose_schedule_id}`}
            </strong>
          </span>
          <span className="text-slate-500">
            Dose status:{' '}
            <strong className="text-slate-800">
              {followup.dose?.status?.replace(/_/g, ' ') || 'not confirmed'}
            </strong>
          </span>
        </div>
        <p className="text-[11px] text-amber-700 mt-1 font-medium">
          Note: This follow-up tracks caregiver action. Marking it resolved does not alter medication status.
        </p>
      </div>

      {/* Notes */}
      <div className="mt-3">
        {editingNotes ? (
          <div className="space-y-2">
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              placeholder="Add follow-up notes (e.g. called patient, they will take it with lunch)..."
              className="w-full text-xs border border-gray-300 rounded-lg p-2 outline-none focus:border-teal-500"
            />
            <div className="flex gap-2 justify-end">
              <Button size="sm" variant="secondary" onClick={() => setEditingNotes(false)}>
                Cancel
              </Button>
              <Button size="sm" variant="primary" loading={loading} onClick={handleSaveNotes}>
                Save Notes
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between text-xs text-gray-600">
            <span>
              {followup.notes ? (
                <span>Notes: <em className="text-gray-800">"{followup.notes}"</em></span>
              ) : (
                <span className="text-gray-400 italic">No notes recorded</span>
              )}
            </span>
            {isCaregiver && (
              <button
                onClick={() => setEditingNotes(true)}
                className="text-teal-600 hover:underline font-medium text-xs ml-2"
              >
                {followup.notes ? 'Edit notes' : '+ Add notes'}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Caregiver Status Controls */}
      {isCaregiver && followup.status !== 'resolved' && (
        <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-end gap-2">
          {followup.status === 'accepted' && (
            <Button
              size="sm"
              variant="outline"
              loading={loading}
              onClick={() => handleStatusChange('in_progress')}
            >
              Start Follow-up (In Progress)
            </Button>
          )}
          <Button
            size="sm"
            variant="success"
            loading={loading}
            onClick={() => handleStatusChange('resolved')}
          >
            <CheckCircle size={14} className="mr-1" />
            Mark Follow-up Resolved
          </Button>
        </div>
      )}
    </div>
  );
}
