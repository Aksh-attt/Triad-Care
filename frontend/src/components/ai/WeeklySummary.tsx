import React, { useState } from 'react';
import { Sparkles, BarChart2, CheckCircle, XCircle, Clock, AlertCircle, Info, RefreshCw } from 'lucide-react';
import { Button } from '../ui/Button';
import { getWeeklySummary } from '../../api/ai';

interface WeeklySummaryProps {
  profileId: number;
}

interface SummaryStats {
  total: number;
  taken: number;
  missed: number;
  pending: number;
  not_confirmed: number;
  adherence_percent: number;
}

export function WeeklySummary({ profileId }: WeeklySummaryProps) {
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<string | null>(null);
  const [stats, setStats] = useState<SummaryStats | null>(null);
  const [isDemo, setIsDemo] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getWeeklySummary(profileId);
      setSummary(data.summary);
      setStats(data.stats);
      setIsDemo(!!data.is_demo);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to generate weekly summary');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-xs space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-50 border border-purple-200 text-purple-700 flex items-center justify-center">
            <Sparkles size={20} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">AI Weekly Healthcare Digest</h2>
            <p className="text-xs text-gray-500">
              Summarizes adherence facts, reasons, caregiver follow-ups, and gentle recommendations.
            </p>
          </div>
        </div>

        <Button
          variant="primary"
          loading={loading}
          onClick={fetchSummary}
          className="self-start sm:self-auto bg-purple-600 hover:bg-purple-700"
        >
          <Sparkles size={16} className="mr-1.5" />
          {summary ? 'Regenerate Digest' : 'Generate Weekly Summary'}
        </Button>
      </div>

      {isDemo && (
        <div className="bg-amber-50 border border-amber-200 p-3 rounded-xl flex items-start gap-2 text-xs text-amber-800">
          <Info size={16} className="text-amber-600 mt-0.5 flex-shrink-0" />
          <span>
            <strong>Demo Fallback Active:</strong> Displaying rule-based synthesis because GEMINI_API_KEY is not configured.
          </span>
        </div>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2">
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-center">
            <p className="text-xs text-gray-500 font-semibold uppercase">Total Scheduled</p>
            <p className="text-2xl font-black text-gray-900 mt-1">{stats.total}</p>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-xl p-3 text-center">
            <p className="text-xs text-green-700 font-semibold uppercase">Taken</p>
            <p className="text-2xl font-black text-green-700 mt-1">{stats.taken}</p>
          </div>
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 text-center">
            <p className="text-xs text-amber-700 font-semibold uppercase">Not Confirmed</p>
            <p className="text-2xl font-black text-amber-700 mt-1">{stats.not_confirmed}</p>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-center">
            <p className="text-xs text-red-700 font-semibold uppercase">Missed</p>
            <p className="text-2xl font-black text-red-700 mt-1">{stats.missed}</p>
          </div>
          <div className="col-span-2 sm:col-span-1 bg-purple-50 border border-purple-200 rounded-xl p-3 text-center">
            <p className="text-xs text-purple-700 font-semibold uppercase">Adherence Rate</p>
            <p className="text-2xl font-black text-purple-700 mt-1">{stats.adherence_percent}%</p>
          </div>
        </div>
      )}

      {summary && (
        <div className="pt-2">
          <div className="p-4 rounded-xl bg-purple-50/60 border border-purple-200">
            <div className="flex items-center gap-2 mb-2 text-xs font-bold text-purple-900 uppercase tracking-wider">
              <Sparkles size={14} className="text-purple-600" />
              <span>AI Insights & Coordination Summary</span>
            </div>
            <div className="text-sm text-gray-800 whitespace-pre-line leading-relaxed">
              {summary}
            </div>
          </div>

          <div className="mt-2 text-[11px] text-gray-400 italic">
            * Medical Disclaimer: Triad Care is a healthcare coordination tool, not a doctor. Always confirm prescription decisions with a qualified physician or pharmacist.
          </div>
        </div>
      )}
    </div>
  );
}
