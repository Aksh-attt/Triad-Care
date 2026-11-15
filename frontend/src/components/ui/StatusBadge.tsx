import React from 'react';
import { Badge } from './Badge';
import type { DoseStatus, FollowupStatus } from '../../types';

interface StatusBadgeProps {
  status: DoseStatus | FollowupStatus | string;
}

const doseStatusMap: Record<string, { label: string; variant: 'default' | 'success' | 'danger' | 'warning' | 'info' | 'purple' }> = {
  pending: { label: 'Pending', variant: 'default' },
  taken: { label: 'Taken', variant: 'success' },
  missed: { label: 'Missed', variant: 'danger' },
  not_confirmed: { label: 'Not Confirmed', variant: 'warning' },
  unassigned: { label: 'Unassigned', variant: 'default' },
  accepted: { label: 'Accepted', variant: 'info' },
  in_progress: { label: 'In Progress', variant: 'warning' },
  resolved: { label: 'Resolved', variant: 'success' },
  reassigned: { label: 'Reassigned', variant: 'purple' },
  pending_change: { label: 'Pending', variant: 'warning' },
  approved: { label: 'Approved', variant: 'success' },
  rejected: { label: 'Rejected', variant: 'danger' },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = doseStatusMap[status] || { label: status, variant: 'default' as const };
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
