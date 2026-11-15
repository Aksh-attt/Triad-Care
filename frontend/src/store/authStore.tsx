import React, { createContext, useContext, useReducer, useEffect } from 'react';
import type { User, PatientProfile } from '../types';
import {
  login as apiLogin,
  demoLogin as apiDemoLogin,
  getDemoUsers,
  bootstrapCsrf,
  refreshSession,
  getMe,
  logoutApi,
} from '../api/auth';
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
  loading: true, // starts loading while attempting session restore
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
      return { ...initialState, loading: false, demoUsers: state.demoUsers };
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
  demoLogin: (role: string) => Promise<void>;
  loginWithUser: (user: User, profileId: number) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  useEffect(() => {
    // 1. Fetch demo users for the login picker
    getDemoUsers()
      .then((users) => dispatch({ type: 'SET_DEMO_USERS', payload: users }))
      .catch(() => {});

    // 2. Attempt secure session restoration via HttpOnly refresh cookie + CSRF bootstrap
    const restoreSession = async () => {
      try {
        await bootstrapCsrf();
        await refreshSession();
        const meData = await getMe();
        const user = meData.user;
        const profile_id =
          meData.profile_id ||
          (meData.memberships && meData.memberships.length > 0
            ? meData.memberships[0].profile_id
            : 1);
        const profile = await getPatient(profile_id);
        dispatch({ type: 'LOGIN_SUCCESS', payload: { user, profileId: profile_id, profile } });
      } catch {
        // No active session or refresh expired
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    restoreSession();
  }, []);

  const login = async (passcode: string) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });
    try {
      const data = await apiLogin(passcode);
      const user = data.user;
      const profile_id =
        data.profile_id ||
        (data.memberships && data.memberships.length > 0 ? data.memberships[0].profile_id : 1);
      const profile = await getPatient(profile_id);
      dispatch({ type: 'LOGIN_SUCCESS', payload: { user, profileId: profile_id, profile } });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Login failed';
      dispatch({ type: 'SET_ERROR', payload: msg });
      throw err;
    }
  };

  const demoLogin = async (role: string) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });
    try {
      const data = await apiDemoLogin(role);
      const user = data.user;
      const profile_id =
        data.profile_id ||
        (data.memberships && data.memberships.length > 0 ? data.memberships[0].profile_id : 1);
      const profile = await getPatient(profile_id);
      dispatch({ type: 'LOGIN_SUCCESS', payload: { user, profileId: profile_id, profile } });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Demo login failed';
      dispatch({ type: 'SET_ERROR', payload: msg });
      throw err;
    }
  };

  const loginWithUser = async (user: User, _profileId?: number) => {
    // Authenticate through the backend demo-login endpoint (no hardcoded PINs or unauthenticated client state)
    return demoLogin(user.role);
  };

  const logout = async () => {
    try {
      await logoutApi();
    } catch {
      // Ignore network errors on logout
    }
    dispatch({ type: 'LOGOUT' });
  };

  return (
    <AuthContext.Provider value={{ ...state, login, demoLogin, loginWithUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
