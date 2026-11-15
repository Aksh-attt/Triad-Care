import React, { useState, useEffect } from 'react';
import { useAuth } from '../../store/authStore';
import { getMedications } from '../../api/medications';
import { PrescriptionScanner } from '../../components/ai/PrescriptionScanner';
import { WeeklySummary } from '../../components/ai/WeeklySummary';
import type { Medication } from '../../types';
import { Sparkles, FileText, BarChart3 } from 'lucide-react';

export function AIFeatures() {
  const { profileId } = useAuth();
  const [activeTab, setActiveTab] = useState<'scanner' | 'summary'>('scanner');
  const [medications, setMedications] = useState<Medication[]>([]);

  const loadMeds = async () => {
    if (!profileId) return;
    try {
      const data = await getMedications(profileId);
      setMedications(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadMeds();
  }, [profileId]);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-teal-500 to-purple-600 text-white flex items-center justify-center shadow-sm">
          <Sparkles size={24} />
        </div>
        <div>
          <h1 className="text-2xl font-black text-gray-900">AI Healthcare Intelligence</h1>
          <p className="text-xs text-gray-500">
            Powered by Gemini API for automated prescription scanning, schedule diffing, and weekly health digests.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('scanner')}
          className={`flex items-center gap-2 pb-3 px-3 text-sm font-bold border-b-2 transition-colors ${
            activeTab === 'scanner'
              ? 'border-teal-600 text-teal-700'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <FileText size={16} />
          <span>Prescription Scanner & OCR</span>
        </button>
        <button
          onClick={() => setActiveTab('summary')}
          className={`flex items-center gap-2 pb-3 px-3 text-sm font-bold border-b-2 transition-colors ${
            activeTab === 'summary'
              ? 'border-purple-600 text-purple-700'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <BarChart3 size={16} />
          <span>Weekly Adherence Summary</span>
        </button>
      </div>

      {activeTab === 'scanner' && (
        <PrescriptionScanner
          profileId={profileId || 1}
          existingMedications={medications}
          onMedicationAdded={loadMeds}
        />
      )}

      {activeTab === 'summary' && (
        <WeeklySummary profileId={profileId || 1} />
      )}
    </div>
  );
}
