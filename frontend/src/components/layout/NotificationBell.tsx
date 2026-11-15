import React, { useEffect, useState } from 'react';
import { Bell } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { getNotifications } from '../../api/notifications';
import { useAuth } from '../../store/authStore';

export function NotificationBell() {
  const { profileId } = useAuth();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (!profileId) return;
    getNotifications(profileId)
      .then((notifs) => {
        setUnreadCount(notifs.filter((n) => !n.is_read).length);
      })
      .catch(() => {});
  }, [profileId]);

  return (
    <button
      onClick={() => navigate('/notifications')}
      className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
    >
      <Bell size={22} />
      {unreadCount > 0 && (
        <span className="absolute -top-0.5 -right-0.5 h-5 w-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center font-bold">
          {unreadCount > 9 ? '9+' : unreadCount}
        </span>
      )}
    </button>
  );
}
