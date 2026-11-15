import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './store/authStore';
import { AppLayout } from './components/layout/AppLayout';
import { LoginPage } from './pages/LoginPage';

// Elderly pages
import { ElderlyDashboard } from './pages/elderly/ElderlyDashboard';
import { ElderlyMedications } from './pages/elderly/ElderlyMedications';
import { ElderlyAppointments } from './pages/elderly/ElderlyAppointments';

// Caregiver pages
import { CaregiverDashboard } from './pages/caregiver/CaregiverDashboard';
import { CaregiverFollowups } from './pages/caregiver/CaregiverFollowups';
import { CaregiverPatients } from './pages/caregiver/CaregiverPatients';

// Family pages
import { FamilyDashboard } from './pages/family/FamilyDashboard';
import { FamilyMedications } from './pages/family/FamilyMedications';
import { FamilyAppointments } from './pages/family/FamilyAppointments';
import { FamilyChanges } from './pages/family/FamilyChanges';

// Shared pages
import { AIFeatures } from './pages/shared/AIFeatures';
import { NotificationsPage } from './pages/shared/NotificationsPage';

function ProtectedRoute({
  children,
  allowedRoles,
}: {
  children: React.ReactNode;
  allowedRoles?: string[];
}) {
  const { user, isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-teal-600"></div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // Redirect to user's assigned role dashboard
    return <Navigate to={`/${user.role}`} replace />;
  }

  return <AppLayout>{children}</AppLayout>;
}

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Login Route */}
          <Route path="/" element={<LoginPage />} />

          {/* Elderly Routes */}
          <Route
            path="/elderly"
            element={
              <ProtectedRoute allowedRoles={['elderly']}>
                <ElderlyDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/elderly/medications"
            element={
              <ProtectedRoute allowedRoles={['elderly']}>
                <ElderlyMedications />
              </ProtectedRoute>
            }
          />
          <Route
            path="/elderly/appointments"
            element={
              <ProtectedRoute allowedRoles={['elderly']}>
                <ElderlyAppointments />
              </ProtectedRoute>
            }
          />

          {/* Caregiver Routes */}
          <Route
            path="/caregiver"
            element={
              <ProtectedRoute allowedRoles={['caregiver']}>
                <CaregiverDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/caregiver/followups"
            element={
              <ProtectedRoute allowedRoles={['caregiver']}>
                <CaregiverFollowups />
              </ProtectedRoute>
            }
          />
          <Route
            path="/caregiver/patients"
            element={
              <ProtectedRoute allowedRoles={['caregiver']}>
                <CaregiverPatients />
              </ProtectedRoute>
            }
          />

          {/* Family Routes */}
          <Route
            path="/family"
            element={
              <ProtectedRoute allowedRoles={['family']}>
                <FamilyDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/family/medications"
            element={
              <ProtectedRoute allowedRoles={['family']}>
                <FamilyMedications />
              </ProtectedRoute>
            }
          />
          <Route
            path="/family/appointments"
            element={
              <ProtectedRoute allowedRoles={['family']}>
                <FamilyAppointments />
              </ProtectedRoute>
            }
          />
          <Route
            path="/family/changes"
            element={
              <ProtectedRoute allowedRoles={['family']}>
                <FamilyChanges />
              </ProtectedRoute>
            }
          />

          {/* Shared Routes */}
          <Route
            path="/ai"
            element={
              <ProtectedRoute>
                <AIFeatures />
              </ProtectedRoute>
            }
          />
          <Route
            path="/notifications"
            element={
              <ProtectedRoute>
                <NotificationsPage />
              </ProtectedRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
