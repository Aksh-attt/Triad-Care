import React, { createContext, useContext, useReducer, useEffect } from 'react';
import type { User, PatientProfile } from '../types';
import { login as apiLogin, getDemoUsers } from '../api/auth';
import { getPatient } from '../api/patients';

interface AuthState {
  user: User | null;
  profileId: number | null;
  profile: PatientProfile | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  demoUsers: User[];
}

type AuthAction =
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; profileId: number; profile: PatientProfile } }
  | { type: 'LOGOUT' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_DEMO_USERS'; payload: User[] };

const initialState: AuthState = {
  user: null,
  profileId: null,
  profile: null,
  isAuthenticated: false,
  loading: false,
  error: null,
  demoUsers: [],
};

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        profileId: action.payload.profileId,
        profile: action.payload.profile,
        isAuthenticated: true,
        loading: false,
        error: null,
      };
    case 'LOGOUT':
      return { ...initialState, demoUsers: state.demoUsers };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    case 'SET_DEMO_USERS':
      return { ...state, demoUsers: action.payload };
    default:
      return state;
  }
}

interface AuthContextType extends AuthState {
  login: (passcode: string) => Promise<void>;
  loginWithUser: (user: User, profileId: number) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  useEffect(() => {
    // Load demo users on mount
    getDemoUsers()
      .then((users) => dispatch({ type: 'SET_DEMO_USERS', payload: users }))
      .catch(() => {
        // Silently fail - demo users not critical
      });

    // Restore session from localStorage (supporting triadcare keys with fallback)
    const savedUser = localStorage.getItem('triadcare_user') || localStorage.getItem('caresync_user');
    const savedProfileId = localStorage.getItem('triadcare_profile_id') || localStorage.getItem('caresync_profile_id');
    if (savedUser && savedProfileId) {
      const user = JSON.parse(savedUser) as User;
      const profileId = parseInt(savedProfileId);
      getPatient(profileId)
        .then((profile) => {
          dispatch({ type: 'LOGIN_SUCCESS', payload: { user, profileId, profile } });
        })
        .catch(() => {
          localStorage.removeItem('triadcare_user');
          localStorage.removeItem('triadcare_profile_id');
          localStorage.removeItem('caresync_user');
          localStorage.removeItem('caresync_profile_id');
        });
    }
  }, []);

  const login = async (passcode: string) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });
    try {
      const data = await apiLogin(passcode);
      const user = data.user;
      const profile_id = data.profile_id || (data.memberships && data.memberships.length > 0 ? data.memberships[0].profile_id : 1);
      const profile = await getPatient(profile_id);
      dispatch({ type: 'LOGIN_SUCCESS', payload: { user, profileId: profile_id, profile } });
      localStorage.setItem('triadcare_user', JSON.stringify(user));
      localStorage.setItem('triadcare_profile_id', String(profile_id));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Login failed';
      dispatch({ type: 'SET_ERROR', payload: msg });
      throw err;
    }
  };

  const loginWithUser = async (user: User, profileId: number) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const profile = await getPatient(profileId);
      dispatch({ type: 'LOGIN_SUCCESS', payload: { user, profileId, profile } });
      localStorage.setItem('triadcare_user', JSON.stringify(user));
      localStorage.setItem('triadcare_profile_id', String(profileId));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Login failed';
      dispatch({ type: 'SET_ERROR', payload: msg });
      throw err;
    }
  };

  const logout = () => {
    localStorage.removeItem('triadcare_user');
    localStorage.removeItem('triadcare_profile_id');
    localStorage.removeItem('caresync_user');
    localStorage.removeItem('caresync_profile_id');
    dispatch({ type: 'LOGOUT' });
  };

  return (
    <AuthContext.Provider value={{ ...state, login, loginWithUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
