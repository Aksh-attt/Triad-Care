import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../store/authStore';
import { NotificationBell } from './NotificationBell';
import { login as apiLogin } from '../../api/auth';
import { getPatient } from '../../api/patients';

const DEMO_USERS = [
  { name: 'Meera', passcode: '1111', role: 'elderly', emoji: '👵' },
  { name: 'Riya', passcode: '2222', role: 'caregiver', emoji: '👩‍⚕️' },
  { name: 'Arjun', passcode: '3333', role: 'family', emoji: '👨‍👧' },
];

export function TopBar() {
  const { user, profile } = useAuth();
  const navigate = useNavigate();
  const [switching, setSwitching] = React.useState(false);

  const switchToUser = async (passcode: string) => {
    setSwitching(true);
    try {
      const res = await apiLogin(passcode);
      const newUser = res.user;
      const profileId = res.profile_id || (res.memberships && res.memberships.length > 0 ? res.memberships[0].profile_id : 1);
      localStorage.setItem('triadcare_user', JSON.stringify(newUser));
      localStorage.setItem('triadcare_profile_id', String(profileId));
      window.location.href = `/${newUser.role}`;
    } catch (err) {
      console.error('Switch failed', err);
    } finally {
      setSwitching(false);
    }
  };

  const roleColors: Record<string, string> = {
    elderly: 'text-purple-700 bg-purple-50 border-purple-200',
    caregiver: 'text-teal-700 bg-teal-50 border-teal-200',
    family: 'text-blue-700 bg-blue-50 border-blue-200',
  };

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <div>
        <h1 className="text-lg font-semibold text-gray-900">
          {profile?.name ? `Patient: ${profile.name}` : 'Triad Care'}
        </h1>
        {user && (
          <p className="text-sm text-gray-500 capitalize">
            Logged in as <span className="font-medium">{user.name}</span> · {user.role}
          </p>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* Demo role switcher */}
        <div className="flex items-center gap-1 bg-gray-50 border border-gray-200 rounded-lg p-1">
          <span className="text-xs text-gray-500 px-1 font-medium">Demo:</span>
          {DEMO_USERS.map((demo) => (
            <button
              key={demo.passcode}
              onClick={() => switchToUser(demo.passcode)}
              disabled={switching || user?.name === demo.name}
              title={`Switch to ${demo.name} (${demo.role})`}
              className={`text-xs px-2 py-1 rounded-md border font-medium transition-colors disabled:opacity-50 ${
                user?.name === demo.name
                  ? roleColors[demo.role] || 'text-gray-700 bg-gray-100 border-gray-200'
                  : 'text-gray-600 hover:bg-gray-100 border-transparent'
              }`}
            >
              {demo.emoji} {demo.name}
            </button>
          ))}
        </div>

        <NotificationBell />
      </div>
    </header>
  );
}
