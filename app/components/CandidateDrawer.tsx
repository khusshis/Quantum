import React from 'react';
import { X, ShieldCheck, AlertCircle, TrendingDown, AlignLeft, CheckCircle2, Activity, Mail, Phone, Linkedin, DollarSign, Search, Github } from 'lucide-react';
import { FEATURE_KEYS, formatFeatureName } from './FeatureConstants';

export function CandidateDrawer({ candidate, onClose }: { candidate: any, onClose: () => void }) {
  if (!candidate) return null;

  // Prepare data for the breakdown
  const features = candidate.features || {};
  const featureData = FEATURE_KEYS.map(key => {
    let val = features[key] || 0;
    if (key.includes('penalty') || key.includes('disqualifier')) {
      val = val - 1.0;
    }
    return {
      name: formatFeatureName(key),
      raw: key,
      value: val
    };
  }).sort((a, b) => b.value - a.value);

  const concerns = featureData.filter(f => f.value < 0 || (f.raw === 'honeypot_suspicion_score' && (features[f.raw] || 0) > 0.5));
  
  // Group features for dense display
  const primarySignals = featureData.filter(f => !concerns.includes(f) && f.value > 0.05).slice(0, 8);

  const signals = candidate.redrob_signals || {};
  const hasGithub = signals.github_activity_score !== undefined && signals.github_activity_score >= 0;
  const salary = candidate.expected_salary || {};

  return (
    <aside className="w-[450px] border-l border-border bg-background flex flex-col h-full absolute right-0 z-30 shadow-2xl overflow-y-auto no-scrollbar font-sans text-primary">
      <div className="px-6 py-5 border-b border-border sticky top-0 bg-background z-10">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 bg-border text-secondary border border-border-hover rounded-sm">
                RNK_{candidate.rank?.toString().padStart(3, '0') || 'N/A'}
              </span>
              <span className="font-mono text-xs font-bold text-[#10B981]">
                {candidate.score !== undefined ? (candidate.score * 100).toFixed(2) : 'N/A'}/100
              </span>
            </div>
            <h2 className="text-sm font-medium text-primary mb-1 font-mono tracking-tight flex items-center gap-2">
              {candidate.name} 
              {signals.recruiter_response_rate > 0.90 && signals.interview_completion_rate > 0.90 && (
                <div className="relative group cursor-help flex items-center justify-center">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#EAB308] shadow-[0_0_6px_rgba(234,179,8,0.6)]"></div>
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2 py-1 bg-border border border-border-hover text-primary text-[9px] rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl font-sans font-normal">
                    ⚡ Fast Mover: &gt;90% Response & Interview Show Rate
                  </div>
                </div>
              )}
              <span className="text-muted text-xs font-sans font-normal ml-1">({candidate.candidate_id})</span>
            </h2>
            <p className="text-xs text-secondary">
              {candidate.title || 'Unknown Title'} <span className="text-secondary mx-1">/</span> {candidate.company || 'Unknown Company'}
              {(candidate.location || candidate.country) && (
                <>
                  <span className="text-secondary mx-1">•</span> 
                  {candidate.location}{candidate.location && candidate.country ? ', ' : ''}{candidate.country}
                </>
              )}
            </p>
            {candidate.headline && (
              <p className="text-[11px] text-muted mt-2 leading-relaxed">{candidate.headline}</p>
            )}
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-border rounded transition-colors text-muted hover:text-primary">
            <X size={16} />
          </button>
        </div>
      </div>

      <div className="p-6 space-y-6 flex-1">
        
        {/* Anti-Hallucination Reasoning Block - Vercel/Linear style callout */}
        <section>
          <div className="bg-surface border border-border rounded overflow-hidden">
            <div className="flex items-center gap-2 px-3 py-2 border-b border-border bg-surface-hover">
              <ShieldCheck size={14} className="text-[#10B981]" />
              <span className="text-[10px] font-bold font-mono tracking-wider text-[#10B981] uppercase">
                Audited AI Reasoning
              </span>
              <span className="ml-auto text-[9px] text-secondary font-mono flex items-center gap-1">
                <CheckCircle2 size={10} className="text-[#10B981]" /> GROUNDED
              </span>
            </div>
            <div className="p-4 text-xs leading-relaxed text-primary relative">
              <AlignLeft size={14} className="absolute left-4 top-4 text-muted" />
              {candidate.reasoning ? (
            <p className="text-xs text-secondary leading-relaxed font-mono pl-6">
              {candidate.reasoning}
            </p>
          ) : (
            <p className="text-xs text-muted italic pl-6">No reasoning generated for this candidate (Raw Data).</p>
          )}
            </div>
          </div>
        </section>

        {/* Profile Summary */}
        {candidate.summary && (
          <section>
            <h3 className="text-[10px] font-bold font-mono uppercase tracking-wider text-muted mb-2 flex items-center gap-1.5">
              Profile Summary
            </h3>
            <div className="text-xs leading-relaxed text-primary bg-surface border border-border p-3.5 rounded shadow-sm">
              {candidate.summary}
            </div>
          </section>
        )}

        {/* Skills */}
        {candidate.skills && candidate.skills.length > 0 && (
          <section>
            <h3 className="text-[10px] font-bold font-mono uppercase tracking-wider text-muted mb-2">
              Top Skills
            </h3>
            <div className="flex flex-wrap gap-2">
              {candidate.skills.slice(0, 10).map((s: any, i: number) => (
                <div key={i} className="flex items-center gap-1.5 bg-surface border border-border px-2 py-1 rounded">
                  <span className="text-[11px] text-primary">{s.name}</span>
                  {(s.endorsements > 0 || s.duration_months > 0) && (
                    <span className="text-[9px] text-muted font-mono flex gap-1.5 items-center border-l border-border pl-1.5 ml-0.5">
                      {s.duration_months > 0 && <span>{Math.round(s.duration_months/12)} yr</span>}
                      {s.endorsements > 0 && s.duration_months > 0 && <span className="text-muted">•</span>}
                      {s.endorsements > 0 && <span className="text-[8px] uppercase tracking-wider text-secondary flex items-center gap-1"><span className="text-primary font-bold">{s.endorsements}</span> endorsements</span>}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Skill Assessments */}
        {signals.skill_assessment_scores && Object.keys(signals.skill_assessment_scores).length > 0 && (
          <section>
            <h3 className="text-[10px] font-bold font-mono uppercase tracking-wider text-muted mb-2">
              Verified Assessments
            </h3>
            <div className="grid grid-cols-4 gap-2">
              {Object.entries(signals.skill_assessment_scores).map(([skill, score]: [string, any], i: number) => (
                <div key={i} className="flex flex-col items-center justify-center bg-surface border border-border p-2 rounded">
                  <span className="text-[14px] font-mono font-medium text-primary leading-none mb-1">{score}%</span>
                  <span className="text-[9px] text-secondary uppercase tracking-wider text-center line-clamp-1" title={skill}>{skill}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Career History */}
        {candidate.career_history && candidate.career_history.length > 0 && (
          <section>
            <h3 className="text-[10px] font-bold font-mono uppercase tracking-wider text-muted mb-3">
              Career Timeline
            </h3>
            <div className="space-y-4 relative before:absolute before:inset-0 before:ml-[13px] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-border before:to-transparent">
              {candidate.career_history.slice(0, 3).map((job: any, i: number) => (
                <div key={i} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                  <div className="flex items-center justify-center w-6 h-6 rounded-full border border-border bg-surface-hover text-muted group-[.is-active]:text-[#10B981] shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                    <div className="w-1.5 h-1.5 bg-[#3B82F6] rounded-full"></div>
                  </div>
                  <div className="w-[calc(100%-2.5rem)] md:w-[calc(50%-1.5rem)] bg-surface border border-border p-3 rounded">
                    <div className="flex items-center justify-between mb-1">
                      <div className="text-[11px] font-bold text-primary">{job.title}</div>
                      <div className="text-[9px] text-secondary font-mono">{Math.round(job.duration_months/12 * 10)/10}y</div>
                    </div>
                    <div className="text-[10px] text-muted mb-1">{job.company}</div>
                    {job.description && (
                      <p className="text-[10px] text-secondary leading-relaxed line-clamp-2 mt-2">{job.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Education & Certs */}
        <section>
          <h3 className="text-[10px] font-bold font-mono uppercase tracking-wider text-muted mb-3">
            Education & Certifications
          </h3>
          <div className="space-y-3">
            {candidate.education && candidate.education.map((edu: any, i: number) => (
              <div key={`edu-${i}`} className="bg-surface border border-border p-3 rounded flex items-start justify-between">
                <div>
                  <div className="text-[11px] font-bold text-primary">{edu.degree} {edu.field_of_study ? `in ${edu.field_of_study}` : ''}</div>
                  <div className="text-[10px] text-secondary mt-1">{edu.institution_name || edu.institution}</div>
                  <div className="text-[9px] text-muted font-mono mt-1">
                    {edu.start_year || 'N/A'} - {edu.end_year || 'Present'}
                  </div>
                </div>
                {edu.tier && edu.tier !== 'unknown' && (
                  <span className="text-[9px] font-mono bg-[#3B82F6]/10 text-[#3B82F6] border border-[#3B82F6]/20 px-1.5 py-0.5 rounded">
                    {edu.tier.toUpperCase()}
                  </span>
                )}
              </div>
            ))}
            
            {candidate.certifications && candidate.certifications.map((cert: any, i: number) => (
              <div key={`cert-${i}`} className="bg-surface border border-border p-3 rounded flex flex-col">
                <div className="text-[11px] font-bold text-primary flex justify-between">
                  <span>{cert.name}</span>
                  <span className="font-mono text-[9px] text-muted">{cert.year}</span>
                </div>
                <div className="text-[10px] text-[#10B981] mt-1">Issued by {cert.issuer}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Behavioral Signals */}
        <section>
          <h3 className="text-[10px] font-bold font-mono uppercase tracking-wider text-muted mb-3">
            Hiring & Work Preferences
          </h3>
          <div className="bg-surface border border-border p-3 rounded grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <span className="text-[10px] text-secondary">Status</span>
              <span className={`text-[11px] font-medium ${signals.open_to_work_flag ? 'text-[#10B981]' : 'text-muted'}`}>
                {signals.open_to_work_flag ? '🟢 Open to Work' : '⚪ Passive'}
              </span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[10px] text-secondary">Preferred Mode</span>
              <span className="text-[11px] text-primary capitalize">{signals.preferred_work_mode || 'Flexible'}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[10px] text-secondary">Willing to Relocate</span>
              <span className="text-[11px] text-primary">{signals.willing_to_relocate ? 'Yes' : 'No'}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-[10px] text-secondary">Languages</span>
              <span className="text-[11px] text-primary">
                {candidate.languages && candidate.languages.length > 0 
                  ? candidate.languages.map((l:any) => `${l.language} (${l.proficiency})`).join(', ') 
                  : 'English (Professional)'}
              </span>
            </div>
          </div>
          
          <div className="bg-surface border border-border p-3 rounded mt-3">
             <div className="text-[10px] text-secondary mb-3 uppercase tracking-wider font-mono">Recruiter Reliability Metrics</div>
             <div className="grid grid-cols-3 gap-2 text-center divide-x divide-border">
               <div className="flex flex-col">
                 <span className="text-sm font-mono text-primary">{(signals.recruiter_response_rate * 100).toFixed(0)}%</span>
                 <span className="text-[9px] text-muted mt-1">Response Rate</span>
                 <span className="text-[8px] text-secondary font-mono mt-0.5">~{signals.avg_response_time_hours || 0}h avg</span>
               </div>
               <div className="flex flex-col">
                 <span className="text-sm font-mono text-primary">{(signals.interview_completion_rate * 100).toFixed(0)}%</span>
                 <span className="text-[9px] text-muted mt-1">Interview Show Rate</span>
               </div>
               <div className="flex flex-col">
                 <span className="text-sm font-mono text-primary">{signals.offer_acceptance_rate > 0 ? (signals.offer_acceptance_rate * 100).toFixed(0) + '%' : 'N/A'}</span>
                 <span className="text-[9px] text-muted mt-1">Offer Acceptance</span>
               </div>
             </div>
          </div>
        </section>

        {/* Platform Trust & Engagement */}
        <section>
          <h3 className="text-[10px] font-bold font-mono uppercase tracking-wider text-muted mb-3 flex items-center gap-1.5">
            <Activity size={12} /> Platform Trust & Engagement
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {hasGithub && (
              <div className="bg-surface border border-border p-3 rounded">
                <div className="text-[10px] text-secondary mb-1">GitHub Activity</div>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-mono font-medium text-primary leading-none">{Math.round(signals.github_activity_score)}</span>
                  {signals.github_activity_score > 80 ? (
                    <div className="relative group cursor-help flex items-center justify-center mb-1">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#F59E0B] shadow-[0_0_6px_rgba(245,158,11,0.6)]"></div>
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2 py-1 bg-border border border-border-hover text-primary text-[9px] rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl font-sans font-normal">
                        🌟 Top Open Source Contributor (Score &gt; 80)
                      </div>
                    </div>
                  ) : (
                    <div className="relative group cursor-help flex items-center justify-center mb-1">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#10B981] shadow-[0_0_6px_rgba(16,185,129,0.6)]"></div>
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2 py-1 bg-border border border-border-hover text-primary text-[9px] rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl font-sans font-normal">
                        GitHub Verified
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
            <div className="bg-surface border border-border p-3 rounded">
              <div className="text-[10px] text-secondary mb-1 flex items-center gap-1"><DollarSign size={10}/> Expected Salary</div>
              <div className="font-mono text-xs text-primary">
                {salary.min && salary.max ? `₹${salary.min}L - ₹${salary.max}L` : 'Negotiable'}
              </div>
            </div>
            <div className="bg-surface border border-border p-3 rounded">
              <div className="text-[10px] text-secondary mb-2 flex items-center gap-1"><Search size={10}/> 30d Activity</div>
              <div className="font-mono text-[9px] text-primary flex flex-col gap-1.5">
                <div className="flex justify-between"><span>Searches</span> <span className="text-[#10B981] font-bold">{signals.search_appearance_30d || 0}</span></div>
                <div className="flex justify-between"><span>Saves</span> <span className="text-[#3B82F6] font-bold">{signals.saved_by_recruiters_30d || 0}</span></div>
                <div className="flex justify-between"><span>Apps</span> <span className="text-secondary font-bold">{signals.applications_submitted_30d || 0}</span></div>
              </div>
            </div>
            <div className="bg-surface border border-border p-3 rounded flex flex-col justify-center">
              <div className="text-[10px] text-secondary mb-2">Verifications</div>
              <div className="flex gap-2">
                <Mail size={14} className={signals.verified_email ? 'text-[#10B981]' : 'text-muted'} />
                <Phone size={14} className={signals.verified_phone ? 'text-[#10B981]' : 'text-muted'} />
                <Linkedin size={14} className={signals.linkedin_connected ? 'text-[#10B981]' : 'text-muted'} />
                <Github size={14} className={hasGithub ? 'text-[#10B981]' : 'text-muted'} />
              </div>
            </div>
          </div>
        </section>

        {/* Feature Signals Breakdown */}
        <section>
          <h3 className="text-[10px] font-bold font-mono uppercase tracking-wider text-muted mb-3">Feature Contribution Analysis</h3>
          <div className="space-y-3 border border-border p-4 rounded bg-surface">
            {primarySignals.map((f, i) => {
              const outOf10 = Math.max(0, Math.min(10, f.value * 10));
              return (
              <div key={f.raw} className="flex flex-col gap-1.5">
                <div className="flex justify-between items-center text-[11px] bg-surface border border-border px-3 py-2 rounded">
                  <span className="text-secondary">{f.name}</span>
                  <span className="font-mono text-[#10B981] font-medium">{outOf10.toFixed(1)}<span className="text-secondary">/10</span></span>
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
