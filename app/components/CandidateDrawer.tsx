import React from 'react';
import { X, ShieldCheck, AlertCircle, TrendingDown, AlignLeft, CheckCircle2, Activity, Mail, Phone, Linkedin, DollarSign, Search } from 'lucide-react';
import { FEATURE_KEYS, formatFeatureName } from './FeatureConstants';

export function CandidateDrawer({ candidate, onClose }: { candidate: any, onClose: () => void }) {
  if (!candidate) return null;

  // Prepare data for the breakdown
  const featureData = FEATURE_KEYS.map(key => {
    let val = candidate.features[key] || 0;
    if (key.includes('penalty') || key.includes('disqualifier')) {
      val = val - 1.0;
    }
    return {
      name: formatFeatureName(key),
      raw: key,
      value: val
    };
  }).sort((a, b) => b.value - a.value);

  const concerns = featureData.filter(f => f.value < 0 || (f.raw === 'honeypot_suspicion_score' && candidate.features[f.raw] > 0.5));
  
  // Group features for dense display
  const primarySignals = featureData.filter(f => !concerns.includes(f) && f.value > 0.05).slice(0, 8);

  const signals = candidate.redrob_signals || {};
  const hasGithub = signals.github_activity_score !== undefined && signals.github_activity_score >= 0;
  const salary = candidate.expected_salary || {};

  return (
    <aside className="w-[450px] border-l border-[#27272A] bg-[#0A0A0A] flex flex-col h-full absolute right-0 z-30 shadow-2xl overflow-y-auto no-scrollbar font-sans text-[#EDEDED]">
      <div className="px-6 py-5 border-b border-[#27272A] sticky top-0 bg-[#0A0A0A] z-10">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 bg-[#27272A] text-[#A1A1AA] border border-[#3F3F46] rounded-sm">
                RNK_{candidate.rank.toString().padStart(3, '0')}
              </span>
              <span className="font-mono text-xs font-bold text-[#10B981]">
                {(candidate.score * 100).toFixed(2)}/100
              </span>
            </div>
            <h2 className="text-sm font-medium text-white mb-1 font-mono tracking-tight">{candidate.candidate_id}</h2>
            <p className="text-xs text-[#A1A1AA]">{candidate.title || 'Unknown Title'} <span className="text-[#52525B] mx-1">/</span> {candidate.company || 'Unknown Company'}</p>
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-[#27272A] rounded transition-colors text-[#71717A] hover:text-[#EDEDED]">
            <X size={16} />
          </button>
        </div>
      </div>

      <div className="p-6 space-y-6 flex-1">
        
        {/* Anti-Hallucination Reasoning Block - Vercel/Linear style callout */}
        <section>
          <div className="bg-[#121212] border border-[#27272A] rounded overflow-hidden">
            <div className="flex items-center gap-2 px-3 py-2 border-b border-[#27272A] bg-[#18181B]">
              <ShieldCheck size={14} className="text-[#10B981]" />
              <span className="text-[10px] font-bold font-mono tracking-wider text-[#10B981] uppercase">
                Audited AI Reasoning
              </span>
              <span className="ml-auto text-[9px] text-[#52525B] font-mono flex items-center gap-1">
                <CheckCircle2 size={10} className="text-[#10B981]" /> GROUNDED
              </span>
            </div>
            <div className="p-4 text-xs leading-relaxed text-[#D4D4D8] relative">
              <AlignLeft size={14} className="absolute left-4 top-4 text-[#3F3F46]" />
              <div className="pl-6 font-mono text-[11px] leading-relaxed">
                {candidate.reasoning}
              </div>
            </div>
          </div>
        </section>

        {/* Platform Trust & Engagement */}
        <section>
          <h3 className="text-[10px] font-bold font-mono uppercase tracking-wider text-[#71717A] mb-3 flex items-center gap-1.5">
            <Activity size={12} /> Platform Trust & Engagement
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {hasGithub && (
              <div className="bg-[#121212] border border-[#27272A] p-3 rounded">
                <div className="text-[10px] text-[#A1A1AA] mb-1">GitHub Activity</div>
                <div className="flex items-end gap-2">
                  <span className="text-lg font-mono font-medium text-[#EDEDED] leading-none">{Math.round(signals.github_activity_score)}</span>
                  <span className="text-[9px] text-[#10B981] font-mono leading-none mb-0.5 border border-[#10B981]/30 bg-[#10B981]/10 px-1 py-0.5 rounded-sm">VERIFIED</span>
                </div>
              </div>
            )}
            <div className="bg-[#121212] border border-[#27272A] p-3 rounded">
              <div className="text-[10px] text-[#A1A1AA] mb-1 flex items-center gap-1"><DollarSign size={10}/> Expected Salary</div>
              <div className="font-mono text-xs text-[#EDEDED]">
                {salary.min && salary.max ? `₹${salary.min}L - ₹${salary.max}L` : 'Negotiable'}
              </div>
            </div>
            <div className="bg-[#121212] border border-[#27272A] p-3 rounded">
              <div className="text-[10px] text-[#A1A1AA] mb-1 flex items-center gap-1"><Search size={10}/> 30d Visibility</div>
              <div className="font-mono text-xs text-[#EDEDED]">
                {signals.search_appearance_30d || 0} searches
              </div>
            </div>
            <div className="bg-[#121212] border border-[#27272A] p-3 rounded flex flex-col justify-center">
              <div className="text-[10px] text-[#A1A1AA] mb-2">Verifications</div>
              <div className="flex gap-2">
                <Mail size={14} className={signals.verified_email ? 'text-[#10B981]' : 'text-[#3F3F46]'} />
                <Phone size={14} className={signals.verified_phone ? 'text-[#10B981]' : 'text-[#3F3F46]'} />
                <Linkedin size={14} className={signals.linkedin_connected ? 'text-[#10B981]' : 'text-[#3F3F46]'} />
              </div>
            </div>
          </div>
        </section>

        {/* Feature Signals Breakdown */}
        <section>
          <h3 className="text-[10px] font-bold font-mono uppercase tracking-wider text-[#71717A] mb-3">Feature Contribution Analysis</h3>
          <div className="space-y-3 border border-[#27272A] p-4 rounded bg-[#121212]">
            {primarySignals.map((f, i) => {
              const outOf10 = Math.max(0, Math.min(10, f.value * 10));
              return (
              <div key={f.raw} className="flex flex-col gap-1.5">
                <div className="flex justify-between items-center text-[10px]">
                  <span className="text-[#A1A1AA]">{f.name}</span>
                  <span className="font-mono text-[#EDEDED]">{outOf10.toFixed(1)}/10</span>
                </div>
                <div className="w-full h-1 bg-[#27272A] rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-[#3B82F6]" 
                    style={{ width: `${outOf10 * 10}%` }}
                  />
                </div>
              </div>
            )})}
          </div>
        </section>

        {/* Concerns */}
        {concerns.length > 0 && (
          <section>
            <h3 className="text-[10px] font-bold font-mono uppercase tracking-wider text-[#F87171] mb-3 flex items-center gap-1.5">
              <AlertCircle size={12} /> Detected Concerns
            </h3>
            <div className="space-y-2">
              {concerns.map(c => {
                const severity = Math.min(10, Math.abs(c.value) * 10);
                return (
                <div key={c.raw} className="flex justify-between items-center bg-[#EF4444]/10 border border-[#EF4444]/20 px-3 py-2 rounded text-[11px]">
                  <span className="text-[#FCA5A5] flex items-center gap-2">
                    <TrendingDown size={12} className="text-[#EF4444]" />
                    {c.name}
                  </span>
                  <span className="font-mono font-medium text-[#F87171]">{severity.toFixed(1)}/10 Impact</span>
                </div>
              )})}
            </div>
          </section>
        )}

      </div>
    </aside>
  );
}
