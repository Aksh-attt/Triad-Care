import React, { useEffect, useState } from 'react';
import { useAuth } from '../../store/authStore';
import { getPatient } from '../../api/patients';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import type { PatientProfile } from '../../types';
import { User, Phone, Stethoscope, AlertTriangle, ShieldCheck, Heart } from 'lucide-react';

export function CaregiverPatients() {
  const { profileId } = useAuth();
  const [profile, setProfile] = useState<PatientProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!profileId) return;
    setLoading(true);
    getPatient(profileId)
      .then(setProfile)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [profileId]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!profile) {
    return <div>Patient profile not found.</div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-2xl bg-teal-100 text-teal-700 flex items-center justify-center">
          <User size={24} />
        </div>
        <div>
          <h1 className="text-2xl font-black text-gray-900">Assigned Patient Profile</h1>
          <p className="text-xs text-gray-500">
            Clinical background, emergency details, and medical conditions for {profile.name}.
          </p>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-gray-100">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-purple-100 text-purple-700 font-black text-2xl flex items-center justify-center">
              {profile.name.charAt(0)}
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">{profile.name}</h2>
              <p className="text-xs text-gray-500 font-medium mt-0.5">
                Age: {profile.age} years old · Shared Healthcare Profile
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs bg-green-50 text-green-700 font-bold px-3 py-1 rounded-full border border-green-200 flex items-center gap-1">
              <ShieldCheck size={14} /> Active Shared Care
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Medical Conditions */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
              <Heart size={14} className="text-red-500" />
              <span>Diagnosed Conditions</span>
            </h3>
            <div className="flex flex-wrap gap-2">
              {profile.medical_conditions && profile.medical_conditions.length > 0 ? (
                profile.medical_conditions.map((cond) => (
                  <span
                    key={cond}
                    className="text-xs bg-slate-100 text-slate-800 font-semibold px-3 py-1.5 rounded-lg border border-slate-200"
                  >
                    {cond}
                  </span>
                ))
              ) : (
                <span className="text-xs text-gray-400">None recorded</span>
              )}
            </div>
          </div>

          {/* Allergies */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
              <AlertTriangle size={14} className="text-amber-500" />
              <span>Allergies</span>
            </h3>
            <div className="flex flex-wrap gap-2">
              {profile.allergies && profile.allergies.length > 0 ? (
                profile.allergies.map((all) => (
                  <span
                    key={all}
                    className="text-xs bg-red-50 text-red-800 font-bold px-3 py-1.5 rounded-lg border border-red-200"
                  >
                    ⚠️ {all}
                  </span>
                ))
              ) : (
                <span className="text-xs text-gray-400">No known allergies</span>
              )}
            </div>
          </div>

          {/* Primary Doctor */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
              <Stethoscope size={14} className="text-blue-500" />
              <span>Primary Care Physician</span>
            </h3>
            <p className="text-sm font-semibold text-gray-900 bg-slate-50 p-3 rounded-lg border border-slate-200">
              {profile.primary_doctor || 'Not specified'}
            </p>
          </div>

          {/* Emergency Contact */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
              <Phone size={14} className="text-teal-500" />
              <span>Emergency Family Contact</span>
            </h3>
            <div className="text-sm bg-slate-50 p-3 rounded-lg border border-slate-200">
              <p className="font-semibold text-gray-900">{profile.emergency_contact_name || 'Family Contact'}</p>
              <p className="text-xs text-teal-700 font-mono mt-0.5">{profile.emergency_contact_phone || 'None provided'}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
