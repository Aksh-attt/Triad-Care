import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  Home,
  Pill,
  Calendar,
  Users,
  CheckSquare,
  Bell,
  Sparkles,
  LogOut,
  FileEdit,
} from 'lucide-react';
import { useAuth } from '../../store/authStore';
import { clsx } from 'clsx';

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
}

export function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const navItems: NavItem[] = React.useMemo(() => {
    if (!user) return [];
    if (user.role === 'elderly') {
      return [
        { to: '/elderly', label: 'Dashboard', icon: <Home size={20} /> },
        { to: '/elderly/medications', label: 'Medications', icon: <Pill size={20} /> },
        { to: '/elderly/appointments', label: 'Appointments', icon: <Calendar size={20} /> },
        { to: '/ai', label: 'AI Features', icon: <Sparkles size={20} /> },
        { to: '/notifications', label: 'Notifications', icon: <Bell size={20} /> },
      ];
    }
    if (user.role === 'caregiver') {
      return [
        { to: '/caregiver', label: 'Dashboard', icon: <Home size={20} /> },
        { to: '/caregiver/followups', label: 'Follow-ups', icon: <CheckSquare size={20} /> },
        { to: '/caregiver/patients', label: 'Patients', icon: <Users size={20} /> },
        { to: '/ai', label: 'AI Features', icon: <Sparkles size={20} /> },
        { to: '/notifications', label: 'Notifications', icon: <Bell size={20} /> },
      ];
    }
    if (user.role === 'family') {
      return [
        { to: '/family', label: 'Dashboard', icon: <Home size={20} /> },
        { to: '/family/medications', label: 'Medications', icon: <Pill size={20} /> },
        { to: '/family/appointments', label: 'Appointments', icon: <Calendar size={20} /> },
        { to: '/family/changes', label: 'Change Requests', icon: <FileEdit size={20} /> },
        { to: '/ai', label: 'AI Features', icon: <Sparkles size={20} /> },
        { to: '/notifications', label: 'Notifications', icon: <Bell size={20} /> },
      ];
    }
    return [];
  }, [user]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const roleColors: Record<string, string> = {
    elderly: 'bg-purple-600',
    caregiver: 'bg-teal-600',
    family: 'bg-navy-600',
  };

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col min-h-screen">
      {/* Logo */}
      <div className="p-5 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-teal-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">T</span>
          </div>
          <span className="text-xl font-bold">Triad Care</span>
        </div>
        {user && (
          <div className="mt-3 flex items-center gap-2">
            <div className={clsx('w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold', roleColors[user.role] || 'bg-gray-600')}>
              {user.name.charAt(0)}
            </div>
            <div>
              <p className="text-sm font-medium leading-tight">{user.name}</p>
              <p className="text-xs text-gray-400 capitalize">{user.role}</p>
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/elderly' || item.to === '/caregiver' || item.to === '/family'}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
                isActive
                  ? 'bg-teal-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              )
            }
          >
            {item.icon}
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Logout */}
      <div className="p-3 border-t border-gray-700">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 w-full rounded-lg text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
        >
          <LogOut size={20} />
          Log Out
        </button>
      </div>
    </aside>
  );
}
