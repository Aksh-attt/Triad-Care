import React, { useEffect, useState } from 'react';
import { useAuth } from '../../store/authStore';
import { getFollowups } from '../../api/followups';
import { FollowupCard } from '../../components/followups/FollowupCard';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import type { CaregiverFollowup } from '../../types';
import { CheckSquare } from 'lucide-react';

export function CaregiverFollowups() {
  const { profileId } = useAuth();
  const [followups, setFollowups] = useState<CaregiverFollowup[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'active' | 'resolved'>('all');

  const loadFollowups = async () => {
    if (!profileId) return;
    setLoading(true);
    try {
      const data = await getFollowups(profileId);
      setFollowups(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFollowups();
  }, [profileId]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const filtered = followups.filter((f) => {
    if (filter === 'active') return f.status !== 'resolved';
    if (filter === 'resolved') return f.status === 'resolved';
    return true;
  });

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-teal-100 text-teal-700 flex items-center justify-center">
            <CheckSquare size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-gray-900">Caregiver Follow-up Log</h1>
            <p className="text-xs text-gray-500">
              Audit trail of every follow-up initiated under "I'm handling it".
            </p>
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1 bg-gray-100 p-1 rounded-xl self-start sm:self-auto text-xs font-semibold">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              filter === 'all' ? 'bg-white shadow-xs text-gray-900' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            All ({followups.length})
          </button>
          <button
            onClick={() => setFilter('active')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              filter === 'active' ? 'bg-white shadow-xs text-gray-900' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Active ({followups.filter((f) => f.status !== 'resolved').length})
          </button>
          <button
            onClick={() => setFilter('resolved')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              filter === 'resolved' ? 'bg-white shadow-xs text-gray-900' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Resolved ({followups.filter((f) => f.status === 'resolved').length})
          </button>
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          title="No follow-up records found"
          description="There are currently no follow-up logs matching this filter."
        />
      ) : (
        <div className="space-y-3">
          {filtered.map((f) => (
            <FollowupCard key={f.id} followup={f} onUpdated={loadFollowups} />
          ))}
        </div>
      )}
    </div>
  );
}
