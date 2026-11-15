import React, { useEffect, useState } from 'react';
import { useAuth } from '../../store/authStore';
import { getNotifications, markAsRead, markAllAsRead } from '../../api/notifications';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import { Button } from '../../components/ui/Button';
import type { Notification } from '../../types';
import { Bell, CheckCheck, Clock, ShieldAlert, Calendar, FileEdit, Info } from 'lucide-react';
import { format } from 'date-fns';

export function NotificationsPage() {
  const { profileId } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  const loadNotifs = async () => {
    if (!profileId) return;
    setLoading(true);
    try {
      const data = await getNotifications(profileId);
      setNotifications(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifs();
  }, [profileId]);

  const handleMarkRead = async (id: number) => {
    try {
      await markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkAllRead = async () => {
    if (!profileId) return;
    try {
      await markAllAsRead(profileId);
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (err) {
      console.error(err);
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'medication_missed':
        return <ShieldAlert size={18} className="text-amber-600" />;
      case 'appointment_reminder':
        return <Calendar size={18} className="text-blue-600" />;
      case 'change_request':
        return <FileEdit size={18} className="text-purple-600" />;
      case 'followup_assigned':
        return <Clock size={18} className="text-teal-600" />;
      default:
        return <Info size={18} className="text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center">
            <Bell size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-gray-900">In-App Notifications</h1>
            <p className="text-xs text-gray-500">
              Real-time alerts for missed doses, caregiver follow-ups, and appointment reminders.
            </p>
          </div>
        </div>

        {unreadCount > 0 && (
          <Button variant="outline" size="sm" onClick={handleMarkAllRead}>
            <CheckCheck size={16} className="mr-1" /> Mark All as Read
          </Button>
        )}
      </div>

      {notifications.length === 0 ? (
        <EmptyState
          title="No notifications"
          description="You're all caught up! No recent alerts or updates."
        />
      ) : (
        <div className="space-y-2.5">
          {notifications.map((n) => (
            <div
              key={n.id}
              onClick={() => !n.is_read && handleMarkRead(n.id)}
              className={`p-4 rounded-xl border transition-all flex items-start gap-3.5 cursor-pointer ${
                n.is_read
                  ? 'bg-white border-gray-200 text-gray-600'
                  : 'bg-amber-50/50 border-amber-200 text-gray-900 shadow-xs'
              }`}
            >
              <div className="mt-0.5 w-8 h-8 rounded-lg bg-white border border-gray-200 flex items-center justify-center flex-shrink-0 shadow-2xs">
                {getIcon(n.type)}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h3 className={`text-sm ${n.is_read ? 'font-semibold' : 'font-bold'}`}>
                    {n.title}
                  </h3>
                  <span className="text-[11px] text-gray-400 flex-shrink-0">
                    {n.created_at ? format(new Date(n.created_at), 'MMM d, h:mm a') : 'Recent'}
                  </span>
                </div>
                <p className="text-xs text-gray-600 mt-1">{n.body}</p>
              </div>

              {!n.is_read && (
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500 flex-shrink-0 mt-1.5" />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
