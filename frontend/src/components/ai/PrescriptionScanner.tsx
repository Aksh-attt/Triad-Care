import React, { useState } from 'react';
import { UploadCloud, CheckCircle, AlertTriangle, Sparkles, Plus, Info, RefreshCw } from 'lucide-react';
import { Button } from '../ui/Button';
import { scanPrescription, comparePrescription } from '../../api/ai';
import { addMedication } from '../../api/medications';
import type { Medication } from '../../types';

interface PrescriptionScannerProps {
  profileId: number;
  existingMedications: Medication[];
  onMedicationAdded?: () => void;
}

interface ExtractedItem {
  name: string;
  dosage: string;
  unit?: string;
  frequency: string;
  instructions?: string;
  is_existing?: boolean;
  status?: string;
}

export function PrescriptionScanner({
  profileId,
  existingMedications,
  onMedicationAdded,
}: PrescriptionScannerProps) {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [comparing, setComparing] = useState(false);
  const [isDemo, setIsDemo] = useState(false);
  const [demoMessage, setDemoMessage] = useState<string | null>(null);
  const [items, setItems] = useState<ExtractedItem[]>([]);
  const [savedIndex, setSavedIndex] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      setPreviewUrl(URL.createObjectURL(selected));
      setItems([]);
      setSavedIndex([]);
      setError(null);
    }
  };

  const handleScan = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    try {
      const res = await scanPrescription(file);
      setIsDemo(!!res.is_demo);
      if (res.message) setDemoMessage(res.message);

      const rawItems: ExtractedItem[] = res.extracted_items || [];
      setItems(rawItems);

      // Run comparison
      if (rawItems.length > 0) {
        setComparing(true);
        try {
          const compRes = await comparePrescription(profileId, rawItems);
          if (compRes.comparison) {
            const enriched = rawItems.map((item, idx) => ({
              ...item,
              is_existing: compRes.comparison[idx]?.is_existing,
              status: compRes.comparison[idx]?.status,
            }));
            setItems(enriched);
          }
        } catch (cErr) {
          console.warn('Comparison failed', cErr);
        } finally {
          setComparing(false);
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Prescription scanning failed');
    } finally {
      setLoading(false);
    }
  };

  const handleItemChange = (index: number, field: keyof ExtractedItem, value: string) => {
    setItems((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const handleAddMedication = async (item: ExtractedItem, index: number) => {
    try {
      await addMedication(profileId, {
        name: item.name,
        dosage: item.dosage,
        unit: item.unit || 'mg',
        frequency: item.frequency.toLowerCase().includes('twice') ? 'twice_daily' : 'once_daily',
        timing_slots: ['morning'],
        start_date: new Date().toISOString().split('T')[0],
        instructions: item.instructions || '',
        is_active: true,
      });
      setSavedIndex((prev) => [...prev, index]);
      onMedicationAdded?.();
    } catch (err) {
      console.error(err);
      alert('Failed to save medication');
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-xs space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-teal-50 border border-teal-200 text-teal-700 flex items-center justify-center">
          <Sparkles size={20} />
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-900">AI Prescription Scanner</h2>
          <p className="text-xs text-gray-500">
            Scan and extract medications automatically using Gemini Vision OCR with manual review.
          </p>
        </div>
      </div>

      {isDemo && (
        <div className="bg-amber-50 border border-amber-200 p-3.5 rounded-xl flex items-start gap-2 text-xs text-amber-800">
          <Info size={16} className="text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <strong>Demo Fallback Active:</strong>{' '}
            {demoMessage || 'GEMINI_API_KEY environment variable is not configured. Displaying simulated extraction results.'}
          </div>
        </div>
      )}

      {/* Upload area */}
      <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:border-teal-400 transition-colors bg-slate-50/50">
        <input
          type="file"
          accept="image/*"
          id="rx-upload"
          className="hidden"
          onChange={handleFileChange}
        />
        <label htmlFor="rx-upload" className="cursor-pointer flex flex-col items-center">
          <UploadCloud size={36} className="text-gray-400 mb-2" />
          <span className="font-semibold text-sm text-gray-700">
            {file ? file.name : 'Click to upload prescription image'}
          </span>
          <span className="text-xs text-gray-400 mt-1">PNG, JPG, WEBP up to 10MB</span>
        </label>

        {previewUrl && (
          <div className="mt-4 flex flex-col items-center">
            <img
              src={previewUrl}
              alt="Prescription preview"
              className="max-h-48 rounded-lg border shadow-xs object-contain"
            />
          </div>
        )}
      </div>

      {file && (
        <div className="flex justify-end">
          <Button
            variant="primary"
            loading={loading || comparing}
            onClick={handleScan}
            className="w-full sm:w-auto"
          >
            <Sparkles size={16} className="mr-2" />
            Analyze Prescription with Gemini
          </Button>
        </div>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      {/* Extracted items review table */}
      {items.length > 0 && (
        <div className="space-y-4 pt-4 border-t border-gray-100">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-gray-900 text-base flex items-center gap-2">
              <span>Extracted Medication Details ({items.length})</span>
            </h3>
            <span className="text-xs bg-amber-100 text-amber-800 px-2.5 py-1 rounded-full font-medium flex items-center gap-1">
              <AlertTriangle size={12} /> Verification required
            </span>
          </div>

          <p className="text-xs text-gray-500">
            Triad Care requires you to verify all extracted fields before adding medicines to the patient schedule.
          </p>

          <div className="space-y-3">
            {items.map((item, idx) => {
              const isSaved = savedIndex.includes(idx);
              const isAlreadyInMedList = item.is_existing;

              return (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border transition-all ${
                    isSaved
                      ? 'bg-green-50/50 border-green-200'
                      : isAlreadyInMedList
                      ? 'bg-amber-50/40 border-amber-200'
                      : 'bg-white border-gray-200 shadow-xs'
                  }`}
                >
                  <div className="flex flex-col md:flex-row gap-3 items-start md:items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold w-6 h-6 rounded-full bg-gray-100 text-gray-700 flex items-center justify-center">
                        {idx + 1}
                      </span>
                      {isAlreadyInMedList && (
                        <span className="text-[11px] bg-amber-100 text-amber-900 font-semibold px-2 py-0.5 rounded">
                          Existing in current medications
                        </span>
                      )}
                      {!isAlreadyInMedList && (
                        <span className="text-[11px] bg-teal-100 text-teal-900 font-semibold px-2 py-0.5 rounded">
                          New Medication
                        </span>
                      )}
                    </div>

                    <div>
                      {isSaved ? (
                        <span className="text-xs text-green-700 font-bold flex items-center gap-1">
                          <CheckCircle size={14} /> Added to Medication Schedule
                        </span>
                      ) : (
                        <Button
                          size="sm"
                          variant="success"
                          onClick={() => handleAddMedication(item, idx)}
                        >
                          <Plus size={14} className="mr-1" />
                          Approve & Save
                        </Button>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-2.5 text-xs">
                    <div>
                      <label className="text-[10px] uppercase font-bold text-gray-500">Medication Name</label>
                      <input
                        type="text"
                        value={item.name}
                        onChange={(e) => handleItemChange(idx, 'name', e.target.value)}
                        className="w-full mt-0.5 p-2 border border-gray-300 rounded-lg outline-none focus:border-teal-500 font-semibold text-gray-900"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] uppercase font-bold text-gray-500">Dosage</label>
                      <input
                        type="text"
                        value={item.dosage}
                        onChange={(e) => handleItemChange(idx, 'dosage', e.target.value)}
                        className="w-full mt-0.5 p-2 border border-gray-300 rounded-lg outline-none focus:border-teal-500 text-gray-900"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] uppercase font-bold text-gray-500">Frequency</label>
                      <input
                        type="text"
                        value={item.frequency}
                        onChange={(e) => handleItemChange(idx, 'frequency', e.target.value)}
                        className="w-full mt-0.5 p-2 border border-gray-300 rounded-lg outline-none focus:border-teal-500 text-gray-900"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] uppercase font-bold text-gray-500">Instructions</label>
                      <input
                        type="text"
                        value={item.instructions || ''}
                        onChange={(e) => handleItemChange(idx, 'instructions', e.target.value)}
                        className="w-full mt-0.5 p-2 border border-gray-300 rounded-lg outline-none focus:border-teal-500 text-gray-900"
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
