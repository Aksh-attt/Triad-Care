import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './store/authStore';
import { AppLayout } from './components/layout/AppLayout';

// Public pages — lazy loaded
const LandingPage = lazy(() => import('./pages/LandingPage').then(m => ({ default: m.LandingPage })));
const LoginPage = lazy(() => import('./pages/LoginPage').then(m => ({ default: m.LoginPage })));

// Elderly pages — lazy loaded
const ElderlyDashboard = lazy(() => import('./pages/elderly/ElderlyDashboard').then(m => ({ default: m.ElderlyDashboard })));
const ElderlyMedications = lazy(() => import('./pages/elderly/ElderlyMedications').then(m => ({ default: m.ElderlyMedications })));
const ElderlyAppointments = lazy(() => import('./pages/elderly/ElderlyAppointments').then(m => ({ default: m.ElderlyAppointments })));

// Caregiver pages — lazy loaded
const CaregiverDashboard = lazy(() => import('./pages/caregiver/CaregiverDashboard').then(m => ({ default: m.CaregiverDashboard })));
const CaregiverFollowups = lazy(() => import('./pages/caregiver/CaregiverFollowups').then(m => ({ default: m.CaregiverFollowups })));
const CaregiverPatients = lazy(() => import('./pages/caregiver/CaregiverPatients').then(m => ({ default: m.CaregiverPatients })));

// Family pages — lazy loaded
const FamilyDashboard = lazy(() => import('./pages/family/FamilyDashboard').then(m => ({ default: m.FamilyDashboard })));
const FamilyMedications = lazy(() => import('./pages/family/FamilyMedications').then(m => ({ default: m.FamilyMedications })));
const FamilyAppointments = lazy(() => import('./pages/family/FamilyAppointments').then(m => ({ default: m.FamilyAppointments })));
const FamilyChanges = lazy(() => import('./pages/family/FamilyChanges').then(m => ({ default: m.FamilyChanges })));

// Shared pages — lazy loaded
const AIFeatures = lazy(() => import('./pages/shared/AIFeatures').then(m => ({ default: m.AIFeatures })));
const NotificationsPage = lazy(() => import('./pages/shared/NotificationsPage').then(m => ({ default: m.NotificationsPage })));

/** Full-screen loading fallback shown during code-split chunk loads */
function PageLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#FAF8F5]" aria-label="Loading page">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#405342]" />
    </div>
  );
}

function ProtectedRoute({
  children,
  allowedRoles,
}: {
  children: React.ReactNode;
  allowedRoles?: string[];
}) {
  const { user, isAuthenticated, loading } = useAuth();

  if (loading) {
    return <PageLoader />;
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
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
        <Suspense fallback={<PageLoader />}>
          <Routes>
          {/* Public Landing Page */}
          <Route path="/" element={<LandingPage />} />

          {/* Public Login Route */}
          <Route path="/login" element={<LoginPage />} />

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
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
